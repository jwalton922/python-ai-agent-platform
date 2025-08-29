import asyncio
import json
import re
import time
import traceback
from typing import Dict, Any, List, Optional, Set, Tuple
from collections import defaultdict, deque
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import hashlib

from backend.models.workflow_enhanced import (
    EnhancedWorkflow, EnhancedWorkflowNode, EnhancedWorkflowEdge,
    NodeType, WorkflowStatus, ExecutionMode, WaitStrategy,
    AggregationMethod, StorageOperation, ErrorHandlingStrategy,
    WorkflowExecutionState, WorkflowExecutionResult,
    ConditionBranch, DataMapping, LoopConfig, ParallelBranch
)
from backend.models.agent import Agent
from backend.models.activity import ActivityCreate, ActivityType
from backend.storage.file_storage import file_storage as storage
from backend.mcp.tool_registry import tool_registry
from backend.llm.factory import llm_provider


class NodeExecutor:
    """Base class for node executors"""
    
    def __init__(self, executor: 'EnhancedWorkflowExecutor'):
        self.executor = executor
    
    async def execute(
        self,
        node: EnhancedWorkflowNode,
        context: Dict[str, Any],
        state: WorkflowExecutionState
    ) -> Dict[str, Any]:
        raise NotImplementedError


class AgentNodeExecutor(NodeExecutor):
    """Executor for agent nodes"""
    
    async def execute(
        self,
        node: EnhancedWorkflowNode,
        context: Dict[str, Any],
        state: WorkflowExecutionState
    ) -> Dict[str, Any]:
        agent = storage.get_agent(node.agent_id)
        if not agent:
            raise ValueError(f"Agent {node.agent_id} not found")
        
        # Prepare agent instructions
        instructions = agent.instructions
        if node.instructions_override:
            instructions = node.instructions_override
        elif node.instructions_append:
            instructions = f"{instructions}\n\n{node.instructions_append}"
        
        # Map inputs
        try:
            agent_input = self._map_inputs(node.input_mapping or [], context, state)
        except Exception as e:
            # If input mapping fails, use context directly
            print(f"Input mapping failed: {e}")
            traceback.print_exc()
            agent_input = context.get("global", {})
        
        # Add node config
        if node.config.agent_config:
            agent_input.update(node.config.agent_config)
        
        # Execute agent with LLM
        start_time = datetime.utcnow()
        try:
            result = await self._execute_agent_with_llm(
                agent, instructions, agent_input, node, state
            )
            
            # Log successful agent execution (non-blocking)
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            try:
                # Create activity data synchronously but with safer data
                activity_data = ActivityCreate(
                    type=ActivityType.AGENT_EXECUTION,
                    agent_id=agent.id,
                    workflow_id=state.workflow_id,
                    title=f"Agent execution: {agent.name}",
                    description=f"Successfully executed agent {agent.name} in node {node.id}",
                    data={
                        "node_id": node.id,
                        "node_name": node.name,
                        "agent_name": agent.name,
                        "tokens_used": result.get("tokens_used", 0),
                        "duration_ms": duration_ms,
                        "input_summary": str(agent_input)[:200] + "..." if len(str(agent_input)) > 200 else str(agent_input),
                        "output_summary": str(result.get("output", ""))[:200] + "..." if len(str(result.get("output", ""))) > 200 else str(result.get("output", ""))
                    },
                    success=True
                )
                # Store in background task to avoid blocking
                asyncio.create_task(self._store_activity(activity_data))
            except Exception as e:
                print(f"Failed to create agent activity log: {e}")
                traceback.print_exc()
            
        except Exception as e:
            # Log failed agent execution (non-blocking)
            print(f"Agent execution failed with exception: {e}")
            traceback.print_exc()
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            try:
                activity_data = ActivityCreate(
                    type=ActivityType.AGENT_EXECUTION,
                    agent_id=agent.id if agent else None,
                    workflow_id=state.workflow_id,
                    title=f"Agent execution failed: {agent.name if agent else 'Unknown'}",
                    description=f"Failed to execute agent {agent.name if agent else 'Unknown'} in node {node.id}: {str(e)}",
                    data={
                        "node_id": node.id,
                        "node_name": node.name,
                        "agent_name": agent.name if agent else "Unknown",
                        "tokens_used": 0,
                        "duration_ms": duration_ms,
                        "input_summary": str(agent_input)[:200] if agent_input else "",
                        "error": str(e)
                    },
                    success=False,
                    error=str(e)
                )
                asyncio.create_task(self._store_activity(activity_data))
            except Exception as log_e:
                print(f"Failed to create agent failure activity log: {log_e}")
                traceback.print_exc()
            
            return {
                "agent_id": node.agent_id,
                "agent_name": agent.name if agent else "Unknown",
                "error": f"Agent execution failed: {str(e)}",
                "success": False
            }
        
        # Map outputs
        if node.output_mapping:
            try:
                result = self._map_outputs(node.output_mapping, result, context)
            except Exception as e:
                print(f"Output mapping failed: {e}")
                traceback.print_exc()
                return {
                    "agent_id": node.agent_id,
                    "agent_name": agent.name if agent else "Unknown",
                    "error": f"Output mapping failed: {str(e)}",
                    "success": False
                }
        
        # Ensure result has success field
        if not isinstance(result, dict):
            result = {"output": result, "success": True}
        elif "success" not in result:
            result["success"] = True
            
        return result
    
    async def _execute_agent_with_llm(
        self,
        agent: Agent,
        instructions: str,
        input_data: Dict[str, Any],
        node: EnhancedWorkflowNode,
        state: WorkflowExecutionState
    ) -> Dict[str, Any]:
        try:
            # Get available tools
            available_tools = []
            for tool_id in agent.mcp_tool_permissions:
                tool = tool_registry.get_tool(tool_id)
                if tool:
                    available_tools.append(tool)
            
            # Build prompts
            system_prompt = instructions
            if available_tools:
                tool_desc = self._format_tools_for_llm(available_tools)
                system_prompt += f"\n\nAvailable tools:\n{tool_desc}"
                system_prompt += "\n\nTo use a tool, respond with: TOOL_CALL:tool_name:action:{{parameters}}"
            
            user_prompt = json.dumps(input_data, indent=2)
            
            # LLM call with token tracking
            start_tokens = state.total_tokens_used
            
            response = await llm_provider.generate_simple(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=node.config.agent_config.get("temperature", 0.7) if node.config.agent_config else 0.7,
                max_tokens=node.config.token_limits.max_tokens if node.config.token_limits else 1000
            )
            
            # Update token usage (simplified - would need actual token counting)
            tokens_used = len(response.split()) * 1.3  # Rough estimate
            state.total_tokens_used += int(tokens_used)
            
            # Handle tool calls if present
            tool_results = []
            if "TOOL_CALL:" in response:
                tool_results = await self._execute_tool_calls(response, available_tools, agent.id)
                
                if tool_results:
                    # Follow-up LLM call with tool results
                    tool_results_text = "\n".join([
                        f"Tool: {tr['tool']} -> {tr.get('result', tr.get('error', 'No result'))}"
                        for tr in tool_results
                    ])
                    follow_up = f"Tool results:\n{tool_results_text}\n\nProvide final response."
                    
                    response = await llm_provider.generate_simple(
                        prompt=follow_up,
                        system_prompt=instructions,
                        temperature=0.7,
                        max_tokens=500
                    )
                    
                    state.total_tokens_used += int(len(response.split()) * 1.3)
            
            return {
                "agent_id": agent.id,
                "agent_name": agent.name,
                "output": response,
                "tool_calls": tool_results,
                "tokens_used": int(state.total_tokens_used - start_tokens),
                "success": True
            }
            
        except Exception as e:
            print(f"Agent LLM execution failed: {e}")
            traceback.print_exc()
            return {
                "agent_id": agent.id,
                "agent_name": agent.name,
                "error": str(e) if e else "Unknown agent execution error",
                "success": False
            }
    
    def _format_tools_for_llm(self, tools) -> str:
        descriptions = []
        for tool in tools:
            schema = tool.get_schema()
            desc = schema.description if hasattr(schema, 'description') else 'Tool'
            descriptions.append(f"- {tool.name} ({tool.tool_id}): {desc}")
        return "\n".join(descriptions)
    
    async def _execute_tool_calls(self, response: str, available_tools, agent_id: str) -> List[Dict[str, Any]]:
        tool_results = []
        pattern = r'TOOL_CALL:(\w+):(\w+):(\{.*?\})'
        matches = re.findall(pattern, response, re.DOTALL)
        
        for tool_id, action, params_json in matches:
            tool = next((t for t in available_tools if t.tool_id == tool_id), None)
            
            if not tool:
                tool_results.append({
                    "tool": tool_id,
                    "error": f"Tool {tool_id} not available",
                    "success": False
                })
                continue
            
            try:
                params = json.loads(params_json)
                params["action"] = action
                result = await tool.execute(params)
                
                # Log successful tool execution activity (non-blocking)
                try:
                    if hasattr(tool, 'log_activity'):
                        asyncio.create_task(self._log_tool_activity(tool, action, params, result, True))
                except Exception as log_error:
                    print(f"Failed to log tool activity: {log_error}")
                    traceback.print_exc()
                
                tool_results.append({
                    "tool": tool_id,
                    "action": action,
                    "params": params,
                    "result": result,
                    "success": True
                })
            except Exception as e:
                print(f"Tool execution failed: {tool_id} - {e}")
                traceback.print_exc()
                
                # Log failed tool execution activity (non-blocking)
                try:
                    if hasattr(tool, 'log_activity'):
                        asyncio.create_task(self._log_tool_activity(tool, action, params, {}, False, str(e)))
                except Exception as log_error:
                    print(f"Failed to log tool failure activity: {log_error}")
                    traceback.print_exc()
                
                tool_results.append({
                    "tool": tool_id,
                    "action": action,
                    "error": str(e),
                    "success": False
                })
        
        return tool_results
    
    async def _store_activity(self, activity_data: ActivityCreate):
        """Store activity data asynchronously without blocking workflow execution"""
        try:
            storage.create_activity(activity_data)
        except Exception as e:
            print(f"Failed to store activity: {e}")
            traceback.print_exc()
    
    async def _log_tool_activity(self, tool, action: str, params: dict, result: dict, success: bool, error: str = None):
        """Log tool activity asynchronously without blocking workflow execution"""
        try:
            activity_data = ActivityCreate(
                type=ActivityType.TOOL_INVOCATION,
                tool_id=tool.tool_id,
                title=f"{tool.name} - {action}",
                description=f"Executed tool {tool.tool_id} with action: {action}",
                data={
                    "tool_name": tool.name,
                    "tool_id": tool.tool_id,
                    "action": action,
                    "all_input_params": params or {},
                    "execution_result": result or {},
                    "input_params_detailed": {
                        "param_count": len(params) if isinstance(params, dict) else 0,
                        "param_keys": list(params.keys()) if isinstance(params, dict) else [],
                        "param_types": {k: type(v).__name__ for k, v in params.items()} if isinstance(params, dict) else {},
                        "param_sizes": {k: len(str(v)) for k, v in params.items()} if isinstance(params, dict) else {},
                        "has_sensitive_data": any(key.lower() in ['password', 'token', 'key', 'secret'] for key in (params.keys() if isinstance(params, dict) else [])),
                    },
                    "result_metadata": {
                        "result_type": type(result).__name__,
                        "result_size": len(str(result)),
                        "result_is_dict": isinstance(result, dict),
                        "result_keys": list(result.keys()) if isinstance(result, dict) else [],
                        "execution_successful": success
                    },
                    "execution_context": {
                        "called_from": "workflow_execution",
                        "workflow_context": True,
                        "direct_api_call": False,
                        "user_triggered": False
                    }
                },
                success=success,
                error=error
            )
            storage.create_activity(activity_data)
        except Exception as e:
            print(f"Failed to log tool activity: {e}")
            traceback.print_exc()
    
    def _map_inputs(
        self,
        mappings: List[DataMapping],
        context: Dict[str, Any],
        state: WorkflowExecutionState
    ) -> Dict[str, Any]:
        result = {}
        
        for mapping in mappings:
            # Extract value from source path
            value = self._extract_value(mapping.source, context, state)
            
            # Apply transformation if specified
            if mapping.transform:
                value = self._apply_transform(value, mapping.transform)
            
            # Use default if value is None
            if value is None and mapping.default is not None:
                value = mapping.default
            
            # Set value at target path
            self._set_value(result, mapping.target, value)
        
        return result
    
    def _map_outputs(
        self,
        mappings: List[DataMapping],
        result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        mapped = {}
        
        for mapping in mappings:
            # Try to extract from result directly first, then from wrapped result
            value = self._extract_value(mapping.source, result, None)
            if value is None:
                value = self._extract_value(mapping.source, {"result": result, "context": context}, None)
            
            if mapping.transform:
                value = self._apply_transform(value, mapping.transform)
            
            if value is None and mapping.default is not None:
                value = mapping.default
            
            self._set_value(mapped, mapping.target, value)
        
        return mapped
    
    def _extract_value(self, path: str, data: Dict[str, Any], state: Optional[WorkflowExecutionState]) -> Any:
        """Extract value from nested dict using dot notation"""
        if path.startswith("${") and path.endswith("}"):
            path = path[2:-1]
        
        # Handle special variables
        if path.startswith("state."):
            if state:
                path = path[6:]
                data = {
                    "node_outputs": state.node_outputs,
                    "global_variables": state.global_variables,
                    "completed_nodes": state.completed_nodes
                }
            else:
                return None
        
        parts = path.split(".")
        current = data
        
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
            
            if current is None:
                return None
        
        return current
    
    def _set_value(self, data: Dict[str, Any], path: str, value: Any):
        """Set value in nested dict using dot notation"""
        parts = path.split(".")
        current = data
        
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        current[parts[-1]] = value
    
    def _apply_transform(self, value: Any, transform: str) -> Any:
        """Apply transformation expression to value"""
        try:
            # Simple transformations
            if transform == "uppercase":
                return str(value).upper()
            elif transform == "lowercase":
                return str(value).lower()
            elif transform == "json_parse":
                return json.loads(value) if isinstance(value, str) else value
            elif transform == "json_stringify":
                return json.dumps(value)
            elif transform.startswith("split:"):
                delimiter = transform[6:]
                return str(value).split(delimiter)
            elif transform.startswith("join:"):
                delimiter = transform[5:]
                return delimiter.join(value) if isinstance(value, list) else str(value)
            else:
                # Could evaluate as Python expression with sandboxing
                return value
        except Exception as e:
            print(f"Variable substitution failed: {e}")
            traceback.print_exc()
            return value


class DecisionNodeExecutor(NodeExecutor):
    """Executor for decision nodes"""
    
    async def execute(
        self,
        node: EnhancedWorkflowNode,
        context: Dict[str, Any],
        state: WorkflowExecutionState
    ) -> Dict[str, Any]:
        # Evaluate conditions in priority order
        branches = sorted(node.condition_branches or [], key=lambda b: b.priority, reverse=True)
        
        for branch in branches:
            if self._evaluate_condition(branch.expression, context, state):
                return {
                    "decision": branch.name,
                    "target_node": branch.target,
                    "evaluated_expression": branch.expression,
                    "success": True
                }
        
        # Use default target if no conditions match
        if node.default_target:
            return {
                "decision": "default",
                "target_node": node.default_target,
                "success": True
            }
        
        return {
            "decision": "no_match",
            "error": "No conditions matched and no default target",
            "success": False
        }
    
    def _evaluate_condition(self, expression: str, context: Dict[str, Any], state: WorkflowExecutionState) -> bool:
        """Evaluate condition expression"""
        try:
            # Build evaluation context
            eval_context = {
                "context": context,
                "state": state.node_outputs if state else {},
                "globals": state.global_variables if state else {}
            }
            
            # Replace variable references
            expr = expression
            for match in re.finditer(r'\$\{([^}]+)\}', expression):
                var_path = match.group(1)
                value = self.executor._extract_value(var_path, eval_context, state)
                expr = expr.replace(match.group(0), json.dumps(value))
            
            # Evaluate expression (would need proper sandboxing in production)
            return eval(expr, {"__builtins__": {}}, eval_context)
        except Exception as e:
            print(f"Condition evaluation failed: {e}")
            traceback.print_exc()
            return False


class TransformNodeExecutor(NodeExecutor):
    """Executor for transform nodes"""
    
    async def execute(
        self,
        node: EnhancedWorkflowNode,
        context: Dict[str, Any],
        state: WorkflowExecutionState
    ) -> Dict[str, Any]:
        result = {}
        
        # Apply transformations
        for transform in (node.transformations or []):
            value = self.executor._extract_value(transform.source, context, state)
            
            if transform.transform:
                value = self.executor._apply_transform(value, transform.transform)
            
            if value is None and transform.default is not None:
                value = transform.default
            
            self.executor._set_value(result, transform.target, value)
        
        # Validate against schema if provided
        if node.validation_schema:
            # Would implement JSON schema validation here
            pass
        
        return {
            "transformed_data": result,
            "transformations_applied": len(node.transformations or []),
            "success": True
        }


class LoopNodeExecutor(NodeExecutor):
    """Executor for loop nodes"""
    
    async def execute(
        self,
        node: EnhancedWorkflowNode,
        context: Dict[str, Any],
        state: WorkflowExecutionState
    ) -> Dict[str, Any]:
        loop_config = node.loop_config
        if not loop_config:
            return {"error": "Loop configuration missing", "success": False}
        
        results = []
        iterations = 0
        
        if loop_config.type == "for_each":
            items = self.executor._extract_value(loop_config.source, context, state)
            if not isinstance(items, list):
                return {"error": "Source is not iterable", "success": False}
            
            for i, item in enumerate(items):
                if iterations >= loop_config.max_iterations:
                    break
                
                # Check break condition
                if loop_config.break_condition:
                    if self._evaluate_condition(loop_config.break_condition, {"item": item, "index": i}, state):
                        break
                
                # Check continue condition
                if loop_config.continue_condition:
                    if self._evaluate_condition(loop_config.continue_condition, {"item": item, "index": i}, state):
                        continue
                
                # Execute loop body
                loop_context = {**context, "loop_item": item, "loop_index": i}
                
                if node.loop_body_nodes:
                    # Execute nodes in loop body
                    body_results = {}
                    for body_node_id in node.loop_body_nodes:
                        # Would execute body nodes here
                        pass
                    results.append(body_results)
                
                iterations += 1
        
        elif loop_config.type == "while":
            while iterations < loop_config.max_iterations:
                if not self._evaluate_condition(loop_config.condition, context, state):
                    break
                
                # Execute loop body
                loop_context = {**context, "loop_iteration": iterations}
                # Would execute body nodes here
                
                iterations += 1
        
        elif loop_config.type == "range":
            # Parse range from source (e.g., "0:10" or "0:10:2")
            range_parts = loop_config.source.split(":")
            start = int(range_parts[0])
            stop = int(range_parts[1])
            step = int(range_parts[2]) if len(range_parts) > 2 else 1
            
            for i in range(start, stop, step):
                if iterations >= loop_config.max_iterations:
                    break
                
                loop_context = {**context, "loop_index": i}
                # Would execute body nodes here
                
                iterations += 1
        
        # Handle accumulator
        if loop_config.accumulator:
            self.executor._set_value(state.global_variables, loop_config.accumulator, results)
        
        return {
            "iterations": iterations,
            "results": results,
            "success": True
        }
    
    def _evaluate_condition(self, expression: str, context: Dict[str, Any], state: WorkflowExecutionState) -> bool:
        try:
            return eval(expression, {"__builtins__": {}}, context)
        except Exception as e:
            print(f"Condition evaluation failed: {e}")
            traceback.print_exc()
            return False


class ParallelNodeExecutor(NodeExecutor):
    """Executor for parallel nodes"""
    
    async def execute(
        self,
        node: EnhancedWorkflowNode,
        context: Dict[str, Any],
        state: WorkflowExecutionState
    ) -> Dict[str, Any]:
        branches = node.parallel_branches or []
        wait_strategy = node.wait_strategy or WaitStrategy.ALL
        
        # Create tasks for each branch
        tasks = []
        for branch in branches:
            task = self._execute_branch(branch, context, state)
            tasks.append((branch.id, task))
        
        # Execute based on wait strategy
        results = {}
        errors = []
        
        if wait_strategy == WaitStrategy.ALL:
            # Wait for all branches
            for branch_id, task in tasks:
                try:
                    result = await task
                    results[branch_id] = result
                except Exception as e:
                    errors.append({"branch": branch_id, "error": str(e)})
                    if branches[next(i for i, b in enumerate(branches) if b.id == branch_id)].required:
                        raise
        
        elif wait_strategy == WaitStrategy.ANY:
            # Wait for first successful branch
            done, pending = await asyncio.wait(
                [task for _, task in tasks],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            for task in done:
                try:
                    result = await task
                    # Find which branch this was
                    for branch_id, branch_task in tasks:
                        if branch_task == task:
                            results[branch_id] = result
                            break
                    break
                except Exception as e:
                    print(f"Branch execution failed: {e}")
                    traceback.print_exc()
                    continue
            
            # Cancel pending tasks
            for task in pending:
                task.cancel()
        
        elif wait_strategy == WaitStrategy.RACE:
            # Return first to complete (success or failure)
            done, pending = await asyncio.wait(
                [task for _, task in tasks],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            for task in done:
                result = await task
                for branch_id, branch_task in tasks:
                    if branch_task == task:
                        results[branch_id] = result
                        break
                break
            
            for task in pending:
                task.cancel()
        
        elif wait_strategy == WaitStrategy.N_OF_M:
            # Wait for N branches to complete
            n = node.wait_count or 1
            completed = 0
            
            while completed < n and tasks:
                done, pending = await asyncio.wait(
                    [task for _, task in tasks if task not in results.values()],
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                for task in done:
                    try:
                        result = await task
                        for branch_id, branch_task in tasks:
                            if branch_task == task:
                                results[branch_id] = result
                                completed += 1
                                break
                    except Exception as e:
                        print(f"Time-limited branch execution failed: {e}")
                        traceback.print_exc()
                        continue
        
        return {
            "branch_results": results,
            "errors": errors,
            "branches_completed": len(results),
            "success": len(errors) == 0 or not any(
                b.required for b in branches
                if b.id in [e["branch"] for e in errors]
            )
        }
    
    async def _execute_branch(
        self,
        branch: ParallelBranch,
        context: Dict[str, Any],
        state: WorkflowExecutionState
    ) -> Dict[str, Any]:
        # Would execute nodes in branch
        await asyncio.sleep(0.1)  # Simulate work
        return {"branch": branch.name, "completed": True}


class HumanInLoopNodeExecutor(NodeExecutor):
    """Executor for human-in-the-loop nodes"""
    
    async def execute(
        self,
        node: EnhancedWorkflowNode,
        context: Dict[str, Any],
        state: WorkflowExecutionState
    ) -> Dict[str, Any]:
        config = node.config.human_config
        if not config:
            return {"error": "Human input configuration missing", "success": False}
        
        # Create approval request
        request_id = hashlib.md5(f"{node.id}_{state.execution_id}_{time.time()}".encode()).hexdigest()
        
        approval_request = {
            "request_id": request_id,
            "node_id": node.id,
            "workflow_id": state.workflow_id,
            "execution_id": state.execution_id,
            "ui_template": config.ui_template,
            "context": context,
            "options": config.approval_options,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Send notifications
        for channel in config.notification_channels:
            await self._send_notification(channel, approval_request)
        
        # Wait for response (with timeout)
        timeout = config.timeout_ms / 1000 if config.timeout_ms else 3600
        escalation_timeout = config.escalation_after_ms / 1000 if config.escalation_after_ms else None
        
        start_time = time.time()
        response = None
        
        while time.time() - start_time < timeout:
            # Check for escalation
            if escalation_timeout and time.time() - start_time > escalation_timeout:
                if config.escalation_to:
                    for channel in config.escalation_to:
                        await self._send_notification(channel, {
                            **approval_request,
                            "escalated": True
                        })
                    escalation_timeout = None  # Only escalate once
            
            # Check for response (would poll a queue or database)
            response = await self._check_for_response(request_id)
            if response:
                break
            
            await asyncio.sleep(5)  # Poll every 5 seconds
        
        if not response:
            return {
                "error": "Timeout waiting for human input",
                "request_id": request_id,
                "success": False
            }
        
        # Validate response against schema
        if config.input_schema:
            # Would validate here
            pass
        
        return {
            "human_input": response,
            "request_id": request_id,
            "response_time_ms": int((time.time() - start_time) * 1000),
            "success": True
        }
    
    async def _send_notification(self, channel: str, request: Dict[str, Any]):
        # Would send actual notification
        print(f"Notification sent to {channel}: {request['request_id']}")
    
    async def _check_for_response(self, request_id: str) -> Optional[Dict[str, Any]]:
        # Would check for actual response
        return None


class StorageNodeExecutor(NodeExecutor):
    """Executor for storage nodes"""
    
    async def execute(
        self,
        node: EnhancedWorkflowNode,
        context: Dict[str, Any],
        state: WorkflowExecutionState
    ) -> Dict[str, Any]:
        config = node.config.storage_config
        if not config:
            return {"error": "Storage configuration missing", "success": False}
        
        # Generate key
        key = self._generate_key(config.key, context, state)
        
        try:
            if config.operation == StorageOperation.SAVE:
                data = self.executor._extract_value("context", {"context": context}, state)
                await self._save_to_storage(key, data, config)
                return {"operation": "save", "key": key, "success": True}
            
            elif config.operation == StorageOperation.LOAD:
                data = await self._load_from_storage(key, config)
                return {"operation": "load", "key": key, "data": data, "success": True}
            
            elif config.operation == StorageOperation.UPDATE:
                existing = await self._load_from_storage(key, config)
                data = self.executor._extract_value("context", {"context": context}, state)
                if isinstance(existing, dict) and isinstance(data, dict):
                    existing.update(data)
                    await self._save_to_storage(key, existing, config)
                return {"operation": "update", "key": key, "success": True}
            
            elif config.operation == StorageOperation.DELETE:
                await self._delete_from_storage(key, config)
                return {"operation": "delete", "key": key, "success": True}
            
            elif config.operation == StorageOperation.APPEND:
                existing = await self._load_from_storage(key, config)
                data = self.executor._extract_value("context", {"context": context}, state)
                if isinstance(existing, list):
                    existing.append(data)
                    await self._save_to_storage(key, existing, config)
                return {"operation": "append", "key": key, "success": True}
            
        except Exception as e:
            return {"error": str(e), "operation": config.operation.value, "key": key, "success": False}
    
    def _generate_key(self, key_template: str, context: Dict[str, Any], state: WorkflowExecutionState) -> str:
        # Replace variables in key template
        key = key_template
        for match in re.finditer(r'\$\{([^}]+)\}', key_template):
            var_path = match.group(1)
            value = self.executor._extract_value(var_path, context, state)
            key = key.replace(match.group(0), str(value))
        return key
    
    async def _save_to_storage(self, key: str, data: Any, config):
        # Would implement actual storage based on backend
        if config.backend == "memory":
            # Store in memory (state)
            pass
        elif config.backend == "file":
            # Store in file
            pass
        elif config.backend == "database":
            # Store in database
            pass
    
    async def _load_from_storage(self, key: str, config) -> Any:
        # Would implement actual loading
        return {}
    
    async def _delete_from_storage(self, key: str, config):
        # Would implement actual deletion
        pass


class ErrorHandlerNodeExecutor(NodeExecutor):
    """Executor for error handler nodes"""
    
    async def execute(
        self,
        node: EnhancedWorkflowNode,
        context: Dict[str, Any],
        state: WorkflowExecutionState
    ) -> Dict[str, Any]:
        # Extract error information from context
        error_info = context.get("error", {})
        
        # Check if this handler should handle the error
        if node.error_types:
            error_type = error_info.get("type", "unknown")
            if error_type not in node.error_types:
                return {
                    "handled": False,
                    "reason": f"Error type {error_type} not in handled types",
                    "success": False
                }
        
        # Log error
        await self.executor._log_activity(
            ActivityType.WORKFLOW_FAILED,
            workflow_id=state.workflow_id,
            title=f"Error handled by {node.name}",
            description=str(error_info),
            data={"error": error_info, "handler_node": node.id},
            success=False,
            error=str(error_info)
        )
        
        # Execute fallback if specified
        if node.fallback_node:
            return {
                "handled": True,
                "fallback_node": node.fallback_node,
                "error_info": error_info,
                "success": True
            }
        
        return {
            "handled": True,
            "error_info": error_info,
            "recovery_action": "logged",
            "success": True
        }


class AggregatorNodeExecutor(NodeExecutor):
    """Executor for aggregator nodes"""
    
    async def execute(
        self,
        node: EnhancedWorkflowNode,
        context: Dict[str, Any],
        state: WorkflowExecutionState
    ) -> Dict[str, Any]:
        method = node.aggregation_method or AggregationMethod.MERGE
        
        # Get data to aggregate from context
        sources = node.aggregation_config.get("sources", []) if node.aggregation_config else []
        data_to_aggregate = []
        
        for source in sources:
            value = self.executor._extract_value(source, context, state)
            if value is not None:
                data_to_aggregate.append(value)
        
        # Perform aggregation
        result = None
        
        if method == AggregationMethod.MERGE:
            result = {}
            for item in data_to_aggregate:
                if isinstance(item, dict):
                    result.update(item)
        
        elif method == AggregationMethod.CONCAT:
            result = []
            for item in data_to_aggregate:
                if isinstance(item, list):
                    result.extend(item)
                else:
                    result.append(item)
        
        elif method == AggregationMethod.FIRST:
            result = data_to_aggregate[0] if data_to_aggregate else None
        
        elif method == AggregationMethod.LAST:
            result = data_to_aggregate[-1] if data_to_aggregate else None
        
        elif method == AggregationMethod.AVERAGE:
            numeric_values = [v for v in data_to_aggregate if isinstance(v, (int, float))]
            result = sum(numeric_values) / len(numeric_values) if numeric_values else 0
        
        elif method == AggregationMethod.SUM:
            numeric_values = [v for v in data_to_aggregate if isinstance(v, (int, float))]
            result = sum(numeric_values)
        
        elif method == AggregationMethod.CUSTOM:
            # Would execute custom aggregation logic
            result = data_to_aggregate
        
        return {
            "aggregated_data": result,
            "sources_count": len(data_to_aggregate),
            "method": method.value,
            "success": True
        }


class EnhancedWorkflowExecutor:
    """Enhanced workflow executor with support for all node types"""
    
    def __init__(self):
        self.running_workflows: Dict[str, WorkflowExecutionState] = {}
        self.node_executors = {
            NodeType.AGENT: AgentNodeExecutor(self),
            NodeType.DECISION: DecisionNodeExecutor(self),
            NodeType.TRANSFORM: TransformNodeExecutor(self),
            NodeType.LOOP: LoopNodeExecutor(self),
            NodeType.PARALLEL: ParallelNodeExecutor(self),
            NodeType.HUMAN_IN_LOOP: HumanInLoopNodeExecutor(self),
            NodeType.STORAGE: StorageNodeExecutor(self),
            NodeType.ERROR_HANDLER: ErrorHandlerNodeExecutor(self),
            NodeType.AGGREGATOR: AggregatorNodeExecutor(self),
        }
        self.storage_cache = {}
        self.executor_pool = ThreadPoolExecutor(max_workers=10)
    
    async def execute_workflow(
        self,
        workflow: EnhancedWorkflow,
        input_data: Dict[str, Any],
        execution_id: Optional[str] = None,
        checkpoint_id: Optional[str] = None
    ) -> WorkflowExecutionResult:
        """Execute an enhanced workflow"""
        
        execution_id = execution_id or hashlib.md5(
            f"{workflow.id}_{time.time()}".encode()
        ).hexdigest()
        
        # Initialize or restore execution state
        if checkpoint_id:
            state = await self._load_checkpoint(checkpoint_id)
        else:
            state = WorkflowExecutionState(
                execution_id=execution_id,
                workflow_id=workflow.id,
                workflow_version=workflow.version,
                status=WorkflowStatus.RUNNING,
                started_at=datetime.utcnow(),
                global_variables=input_data
            )
        
        self.running_workflows[execution_id] = state
        
        try:
            # Log workflow start
            await self._log_activity(
                ActivityType.WORKFLOW_START,
                workflow_id=workflow.id,
                title=f"Started workflow: {workflow.name}",
                description=f"Executing workflow version {workflow.version}",
                data={
                    "execution_id": execution_id,
                    "input": input_data,
                    "node_count": len(workflow.nodes),
                    "execution_mode": workflow.execution_mode.value
                }
            )
            
            # Build execution plan
            execution_plan = self._build_execution_plan(workflow)
            
            # Execute based on mode
            if workflow.execution_mode == ExecutionMode.SEQUENTIAL:
                await self._execute_sequential(workflow, state, execution_plan)
            elif workflow.execution_mode == ExecutionMode.PARALLEL:
                await self._execute_parallel(workflow, state, execution_plan)
            else:
                # Other modes would be implemented similarly
                await self._execute_sequential(workflow, state, execution_plan)
            
            # Mark as completed
            state.status = WorkflowStatus.COMPLETED
            state.completed_at = datetime.utcnow()
            
            # Log completion
            await self._log_activity(
                ActivityType.WORKFLOW_COMPLETE,
                workflow_id=workflow.id,
                title=f"Completed workflow: {workflow.name}",
                description=f"Successfully executed {len(state.completed_nodes)} nodes",
                data={
                    "execution_id": execution_id,
                    "duration_ms": int((state.completed_at - state.started_at).total_seconds() * 1000),
                    "nodes_executed": len(state.completed_nodes),
                    "total_tokens": state.total_tokens_used,
                    "total_cost": state.total_cost_usd
                }
            )
            
            # Build result
            return WorkflowExecutionResult(
                execution_id=execution_id,
                workflow_id=workflow.id,
                status=state.status,
                output=state.node_outputs,
                node_results=state.node_outputs,
                started_at=state.started_at,
                completed_at=state.completed_at,
                duration_ms=int((state.completed_at - state.started_at).total_seconds() * 1000),
                tokens_used=state.total_tokens_used,
                cost_usd=state.total_cost_usd,
                api_calls_made=state.total_api_calls,
                errors=state.errors
            )
            
        except Exception as e:
            # Handle error
            print(f"Workflow execution failed: {e}")
            traceback.print_exc()
            state.status = WorkflowStatus.FAILED
            state.last_error = str(e)
            state.errors.append({
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "node": state.pending_nodes[0] if state.pending_nodes else None
            })
            
            # Log failure
            await self._log_activity(
                ActivityType.WORKFLOW_FAILED,
                workflow_id=workflow.id,
                title=f"Workflow failed: {workflow.name}",
                description=str(e),
                data={"execution_id": execution_id, "error": str(e)},
                success=False,
                error=str(e)
            )
            
            raise
            
        finally:
            del self.running_workflows[execution_id]
    
    def _build_execution_plan(self, workflow: EnhancedWorkflow) -> List[str]:
        """Build execution plan using topological sort"""
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        
        # Initialize nodes
        for node in workflow.nodes:
            in_degree[node.id] = 0
        
        # Build graph from edges
        for edge in workflow.edges:
            graph[edge.source_node_id].append(edge.target_node_id)
            in_degree[edge.target_node_id] += 1
        
        # Topological sort
        queue = deque([node_id for node_id in in_degree if in_degree[node_id] == 0])
        execution_order = []
        
        while queue:
            node_id = queue.popleft()
            execution_order.append(node_id)
            
            for neighbor in graph[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        if len(execution_order) != len(workflow.nodes):
            raise ValueError("Workflow contains cycles")
        
        return execution_order
    
    async def _execute_sequential(
        self,
        workflow: EnhancedWorkflow,
        state: WorkflowExecutionState,
        execution_plan: List[str]
    ):
        """Execute nodes sequentially"""
        for node_id in execution_plan:
            node = self._get_node_by_id(workflow.nodes, node_id)
            if not node:
                continue
            
            # Skip if already completed (for resume from checkpoint)
            if node_id in state.completed_nodes:
                continue
            
            # Mark as pending
            state.pending_nodes = [node_id]
            
            # Create checkpoint if enabled
            if workflow.settings.enable_checkpoints:
                await self._create_checkpoint(state)
            
            # Execute node with retry logic
            result = await self._execute_node_with_retry(node, state, workflow)
            
            # Store result
            state.node_outputs[node_id] = result
            state.completed_nodes.append(node_id)
            state.pending_nodes.remove(node_id)
            
            # Check for errors
            if not result.get("success", False):
                error_msg = result.get('error', 'Unknown error - no error message provided')
                if workflow.settings.continue_on_error:
                    state.failed_nodes.append(node_id)
                else:
                    raise Exception(f"Node {node_id} failed: {error_msg}")
    
    async def _execute_parallel(
        self,
        workflow: EnhancedWorkflow,
        state: WorkflowExecutionState,
        execution_plan: List[str]
    ):
        """Execute independent nodes in parallel"""
        # Group nodes by dependencies
        levels = self._group_nodes_by_level(workflow, execution_plan)
        
        for level in levels:
            # Execute all nodes in this level in parallel
            tasks = []
            for node_id in level:
                node = self._get_node_by_id(workflow.nodes, node_id)
                if node and node_id not in state.completed_nodes:
                    task = self._execute_node_with_retry(node, state, workflow)
                    tasks.append((node_id, task))
            
            # Wait for all tasks in this level
            for node_id, task in tasks:
                try:
                    result = await task
                    state.node_outputs[node_id] = result
                    state.completed_nodes.append(node_id)
                except Exception as e:
                    print(f"Parallel node execution failed for {node_id}: {e}")
                    traceback.print_exc()
                    if workflow.settings.continue_on_error:
                        state.failed_nodes.append(node_id)
                        state.node_outputs[node_id] = {"error": str(e), "success": False}
                    else:
                        raise
    
    def _group_nodes_by_level(
        self,
        workflow: EnhancedWorkflow,
        execution_plan: List[str]
    ) -> List[List[str]]:
        """Group nodes by dependency level for parallel execution"""
        levels = []
        remaining = set(execution_plan)
        completed = set()
        
        while remaining:
            current_level = []
            
            for node_id in remaining:
                # Check if all dependencies are completed
                dependencies = self._get_node_dependencies(workflow, node_id)
                if dependencies.issubset(completed):
                    current_level.append(node_id)
            
            if not current_level:
                # Circular dependency or error
                break
            
            levels.append(current_level)
            completed.update(current_level)
            remaining.difference_update(current_level)
        
        return levels
    
    def _get_node_dependencies(self, workflow: EnhancedWorkflow, node_id: str) -> Set[str]:
        """Get all nodes that must complete before this node"""
        dependencies = set()
        for edge in workflow.edges:
            if edge.target_node_id == node_id:
                dependencies.add(edge.source_node_id)
        return dependencies
    
    async def _execute_node_with_retry(
        self,
        node: EnhancedWorkflowNode,
        state: WorkflowExecutionState,
        workflow: EnhancedWorkflow
    ) -> Dict[str, Any]:
        """Execute a node with retry logic"""
        retry_config = node.config.retry or workflow.settings
        max_attempts = retry_config.max_attempts if hasattr(retry_config, 'max_attempts') else 1
        
        for attempt in range(max_attempts):
            try:
                # Get executor for node type
                executor = self.node_executors.get(node.type)
                if not executor:
                    return {"error": f"No executor for node type {node.type}", "success": False}
                
                # Build context for node
                context = {
                    "global": state.global_variables,
                    "nodes": state.node_outputs,
                    "workflow": {
                        "id": workflow.id,
                        "name": workflow.name,
                        "version": workflow.version
                    }
                }
                
                # Execute node
                result = await executor.execute(node, context, state)
                
                # Update metrics
                state.total_api_calls += 1
                
                return result
                
            except Exception as e:
                if attempt < max_attempts - 1:
                    # Calculate retry delay
                    if hasattr(retry_config, 'initial_delay_ms'):
                        delay = retry_config.initial_delay_ms * (retry_config.backoff_multiplier ** attempt)
                        delay = min(delay, retry_config.max_delay_ms)
                    else:
                        delay = 1000 * (2 ** attempt)
                    
                    await asyncio.sleep(delay / 1000)
                else:
                    # Final attempt failed
                    return {"error": str(e), "success": False, "attempts": attempt + 1}
    
    def _get_node_by_id(self, nodes: List[EnhancedWorkflowNode], node_id: str) -> Optional[EnhancedWorkflowNode]:
        """Get node by ID"""
        for node in nodes:
            if node.id == node_id:
                return node
        return None
    
    def _extract_value(self, path: str, data: Dict[str, Any], state: Optional[WorkflowExecutionState]) -> Any:
        """Extract value from nested dict using dot notation"""
        if path.startswith("${") and path.endswith("}"):
            path = path[2:-1]
        
        parts = path.split(".")
        current = data
        
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
            
            if current is None:
                return None
        
        return current
    
    def _set_value(self, data: Dict[str, Any], path: str, value: Any):
        """Set value in nested dict using dot notation"""
        parts = path.split(".")
        current = data
        
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        current[parts[-1]] = value
    
    def _apply_transform(self, value: Any, transform: str) -> Any:
        """Apply transformation to value"""
        try:
            if transform == "uppercase":
                return str(value).upper()
            elif transform == "lowercase":
                return str(value).lower()
            elif transform == "json_parse":
                return json.loads(value) if isinstance(value, str) else value
            elif transform == "json_stringify":
                return json.dumps(value)
            else:
                return value
        except Exception as e:
            print(f"JSON serialization failed: {e}")
            traceback.print_exc()
            return value
    
    async def _create_checkpoint(self, state: WorkflowExecutionState):
        """Create execution checkpoint"""
        checkpoint = {
            "checkpoint_id": hashlib.md5(f"{state.execution_id}_{time.time()}".encode()).hexdigest(),
            "execution_id": state.execution_id,
            "workflow_id": state.workflow_id,
            "timestamp": datetime.utcnow().isoformat(),
            "state": state.model_dump()
        }
        state.checkpoints.append(checkpoint)
        state.last_checkpoint = datetime.utcnow()
        
        # Would persist checkpoint to storage
    
    async def _load_checkpoint(self, checkpoint_id: str) -> WorkflowExecutionState:
        """Load execution state from checkpoint"""
        # Would load from storage
        return WorkflowExecutionState(
            execution_id="",
            workflow_id="",
            workflow_version="1.0.0",
            status=WorkflowStatus.IDLE,
            started_at=datetime.utcnow()
        )
    
    async def _log_activity(
        self,
        activity_type: ActivityType,
        title: str,
        description: str,
        data: Dict[str, Any] = None,
        workflow_id: str = None,
        success: bool = True,
        error: str = None
    ):
        """Log workflow activity"""
        activity = ActivityCreate(
            type=activity_type,
            workflow_id=workflow_id,
            title=title,
            description=description,
            data=data or {},
            success=success,
            error=error
        )
        storage.create_activity(activity)


# Global enhanced executor instance
enhanced_workflow_executor = EnhancedWorkflowExecutor()