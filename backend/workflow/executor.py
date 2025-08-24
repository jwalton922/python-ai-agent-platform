from typing import Dict, Any, List, Optional
import asyncio
from collections import defaultdict, deque
from backend.models.workflow import Workflow, WorkflowNode, WorkflowEdge, WorkflowStatus
from backend.models.agent import Agent
from backend.models.activity import ActivityCreate, ActivityType
from backend.storage.file_storage import file_storage as storage
from backend.mcp.tool_registry import tool_registry
from backend.llm.factory import llm_provider
from backend.llm.base import LLMMessage, LLMRole


class WorkflowExecutor:
    """Executes workflows by processing DAGs and running agents"""
    
    def __init__(self):
        self.running_workflows: Dict[str, bool] = {}
    
    async def execute_workflow(self, workflow_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a workflow with the given context"""
        if workflow_id in self.running_workflows:
            raise ValueError(f"Workflow {workflow_id} is already running")
        
        workflow = storage.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        self.running_workflows[workflow_id] = True
        
        try:
            # Log workflow start with comprehensive details
            await self._log_activity(
                ActivityType.WORKFLOW_START,
                workflow_id=workflow_id,
                title=f"Started workflow: {workflow.name}",
                description=f"Beginning execution of workflow {workflow.name} with {len(workflow.nodes)} nodes and {len(workflow.edges)} edges",
                data={
                    "workflow_name": workflow.name,
                    "workflow_description": workflow.description,
                    "context": context or {},
                    "node_count": len(workflow.nodes),
                    "edge_count": len(workflow.edges),
                    "nodes": [{"id": n.id, "agent_id": n.agent_id, "config": n.config} for n in workflow.nodes],
                    "edges": [{"source": e.source_node_id, "target": e.target_node_id} for e in workflow.edges],
                    "execution_order": execution_order if 'execution_order' in locals() else None,
                    "trigger_conditions": workflow.trigger_conditions,
                    "metadata": workflow.metadata
                }
            )
            
            # Build execution graph
            execution_order = self._build_execution_order(workflow.nodes, workflow.edges)
            
            # Execute nodes in topological order
            node_results = {}
            execution_context = context or {}
            
            for node_id in execution_order:
                node = self._get_node_by_id(workflow.nodes, node_id)
                if node:
                    result = await self._execute_node(node, execution_context, node_results)
                    node_results[node_id] = result
                    
                    # Update context with node result
                    execution_context[f"node_{node_id}_result"] = result
            
            # Log workflow completion with detailed results
            await self._log_activity(
                ActivityType.WORKFLOW_COMPLETE,
                workflow_id=workflow_id,
                title=f"Completed workflow: {workflow.name}",
                description=f"Successfully executed workflow {workflow.name} - processed {len(node_results)} nodes",
                data={
                    "workflow_name": workflow.name,
                    "results": node_results,
                    "final_context": execution_context,
                    "nodes_executed": len(node_results),
                    "execution_order": execution_order,
                    "node_details": [
                        {
                            "node_id": node_id,
                            "success": result.get("success", False),
                            "agent_name": result.get("agent_name", "Unknown"),
                            "tool_calls_count": len(result.get("tool_calls", [])),
                            "llm_provider": result.get("llm_provider", "Unknown")
                        }
                        for node_id, result in node_results.items()
                    ]
                }
            )
            
            return {
                "status": "completed",
                "results": node_results,
                "context": execution_context
            }
            
        except Exception as e:
            # Log workflow failure
            await self._log_activity(
                ActivityType.WORKFLOW_FAILED,
                workflow_id=workflow_id,
                title=f"Failed workflow: {workflow.name}",
                description=f"Workflow {workflow.name} failed with error: {str(e)}",
                data={"error": str(e)},
                success=False,
                error=str(e)
            )
            raise
            
        finally:
            del self.running_workflows[workflow_id]
    
    def _build_execution_order(self, nodes: List[WorkflowNode], edges: List[WorkflowEdge]) -> List[str]:
        """Build topological execution order for workflow nodes"""
        # Build adjacency lists
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        
        # Initialize all nodes
        for node in nodes:
            in_degree[node.id] = 0
        
        # Build graph
        for edge in edges:
            graph[edge.source_node_id].append(edge.target_node_id)
            in_degree[edge.target_node_id] += 1
        
        # Topological sort using Kahn's algorithm
        queue = deque([node_id for node_id in in_degree if in_degree[node_id] == 0])
        execution_order = []
        
        while queue:
            node_id = queue.popleft()
            execution_order.append(node_id)
            
            for neighbor in graph[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Check for cycles
        if len(execution_order) != len(nodes):
            raise ValueError("Workflow contains cycles")
        
        return execution_order
    
    def _get_node_by_id(self, nodes: List[WorkflowNode], node_id: str) -> Optional[WorkflowNode]:
        """Get a node by its ID"""
        for node in nodes:
            if node.id == node_id:
                return node
        return None
    
    async def _execute_node(self, node: WorkflowNode, context: Dict[str, Any], node_results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single workflow node"""
        # Get the agent
        agent = storage.get_agent(node.agent_id)
        if not agent:
            raise ValueError(f"Agent {node.agent_id} not found")
        
        # Prepare agent input from context and node config - simplified to avoid recursion
        agent_input = {
            "node_id": node.id,
            "config": node.config or {}
        }
        
        # Log agent execution start with comprehensive details
        await self._log_activity(
            ActivityType.AGENT_EXECUTION,
            agent_id=agent.id,
            title=f"Executing agent: {agent.name}",
            description=f"Running agent {agent.name} for node {node.id} with {len(agent.mcp_tool_permissions)} tools available",
            data={
                "node_id": node.id,
                "node_config": node.config or {},
                "agent_name": agent.name,
                "agent_instructions": agent.instructions,
                "agent_id": agent.id,
                "input": agent_input,
                "available_tools": agent.mcp_tool_permissions,
                "node_position": getattr(node, 'position', None),
                "agent_metadata": agent.metadata if hasattr(agent, 'metadata') else {}
            }
        )
        
        # Execute the agent using LLM
        result = await self._execute_agent_with_llm(agent, agent_input)
        
        return result
    
    async def _execute_agent_with_llm(self, agent: Agent, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent using real LLM with MCP tool integration"""
        try:
            # Prepare available tools for this agent
            available_tools = self._get_available_tools(agent)
            tool_descriptions = self._format_tools_for_llm(available_tools)
            
            # Prepare the context for the LLM
            context_info = []
            
            # Add node configuration if available
            if "config" in input_data and input_data["config"]:
                context_info.append(f"Node configuration: {input_data['config']}")
            
            # Add node ID
            if "node_id" in input_data:
                context_info.append(f"Current node: {input_data['node_id']}")
            
            # Add available tools info
            if tool_descriptions:
                context_info.append(f"Available tools: {tool_descriptions}")
            
            # Build the enhanced system prompt with tool information
            system_prompt = agent.instructions
            if available_tools:
                system_prompt += f"\n\nYou have access to the following tools:\n{tool_descriptions}"
                system_prompt += "\n\nTo use a tool, respond with: TOOL_CALL:tool_name:action:{{parameters as JSON}}"
                system_prompt += "\nExample: TOOL_CALL:email_tool:read:{{\"folder\":\"inbox\",\"limit\":5}}"
            
            # Build the user prompt
            user_prompt = "Process this workflow step."
            if context_info:
                user_prompt += f"\n\nContext:\n" + "\n".join(context_info)
            
            # Make the initial LLM call
            response = await llm_provider.generate_simple(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=500
            )
            
            # Check if the response contains tool calls
            tool_results = []
            final_response = response
            
            if "TOOL_CALL:" in response:
                # Parse and execute tool calls
                tool_results = await self._execute_tool_calls(response, available_tools, agent.id)
                
                # If we have tool results, make a follow-up LLM call with the results
                if tool_results:
                    tool_results_text = "\n".join([f"Tool: {tr['tool']} -> {tr['result']}" for tr in tool_results])
                    follow_up_prompt = f"Based on the tool results:\n{tool_results_text}\n\nPlease provide your final response."
                    
                    final_response = await llm_provider.generate_simple(
                        prompt=follow_up_prompt,
                        system_prompt=agent.instructions + "\n\nProvide a helpful summary based on the tool results.",
                        temperature=0.7,
                        max_tokens=500
                    )
            
            return {
                "agent_id": agent.id,
                "agent_name": agent.name,
                "output": final_response,
                "tool_calls": tool_results,
                "available_tools": [tool.tool_id for tool in available_tools],
                "llm_provider": type(llm_provider).__name__,
                "success": True
            }
            
        except Exception as e:
            # Fall back to mock response if LLM fails
            return {
                "agent_id": agent.id,
                "agent_name": agent.name,
                "output": f"Error executing agent: {str(e)}. Falling back to mock response.",
                "llm_provider": "fallback",
                "success": False,
                "error": str(e)
            }
    
    def _get_available_tools(self, agent: Agent) -> List:
        """Get available MCP tools for the agent"""
        available_tools = []
        for tool_id in agent.mcp_tool_permissions:
            tool = tool_registry.get_tool(tool_id)
            if tool:
                available_tools.append(tool)
        return available_tools
    
    def _format_tools_for_llm(self, tools) -> str:
        """Format tools description for LLM"""
        if not tools:
            return ""
        
        descriptions = []
        for tool in tools:
            schema = tool.get_schema()
            # Access the description from the MCPToolSchema object
            description = schema.description if hasattr(schema, 'description') else 'Tool for various actions'
            
            # For email tool, list known actions
            if tool.tool_id == "email_tool":
                actions = "send, read"
            elif tool.tool_id == "slack_tool":
                actions = "post, read"
            elif tool.tool_id == "file_tool":
                actions = "read, write, list"
            else:
                actions = "execute"
                
            descriptions.append(f"- {tool.name} ({tool.tool_id}): {description} [Actions: {actions}]")
        
        return "\n".join(descriptions)
    
    async def _execute_tool_calls(self, response: str, available_tools, agent_id: str) -> List[Dict[str, Any]]:
        """Parse and execute tool calls from LLM response"""
        tool_results = []
        
        # Simple parsing for TOOL_CALL:tool_name:action:{parameters}
        import re
        pattern = r'TOOL_CALL:(\w+):(\w+):(\{.*?\})'
        matches = re.findall(pattern, response, re.DOTALL)
        
        for tool_id, action, params_json in matches:
            # Find the tool
            tool = None
            for available_tool in available_tools:
                if available_tool.tool_id == tool_id:
                    tool = available_tool
                    break
            
            if not tool:
                tool_results.append({
                    "tool": tool_id,
                    "action": action,
                    "error": f"Tool {tool_id} not available to this agent",
                    "success": False
                })
                continue
            
            try:
                # Parse parameters
                import json
                params = json.loads(params_json)
                params["action"] = action  # Add action to parameters
                
                # Execute the tool
                result = await tool.execute(params)
                
                # Log comprehensive tool execution with all inputs
                await self._log_activity(
                    ActivityType.TOOL_INVOCATION,
                    agent_id=agent_id,
                    tool_id=tool_id,
                    title=f"Executed {tool.name}",
                    description=f"Agent executed {tool.name} with action: {action} - Input params: {len(params)} fields",
                    data={
                        "tool_name": tool.name,
                        "tool_id": tool_id,
                        "action": action,
                        "all_input_params": params,
                        "input_params_detailed": {
                            "param_count": len(params) if isinstance(params, dict) else 0,
                            "param_keys": list(params.keys()) if isinstance(params, dict) else [],
                            "param_types": {k: type(v).__name__ for k, v in params.items()} if isinstance(params, dict) else {},
                            "param_sizes": {k: len(str(v)) for k, v in params.items()} if isinstance(params, dict) else {},
                            "has_sensitive_data": any(key.lower() in ['password', 'token', 'key', 'secret'] for key in (params.keys() if isinstance(params, dict) else [])),
                            "raw_params_json": params_json,
                            "parsed_successfully": True
                        },
                        "tool_schema": {
                            "schema": tool.get_schema().model_dump() if hasattr(tool.get_schema(), 'model_dump') else str(tool.get_schema()),
                            "tool_description": getattr(tool.get_schema(), 'description', 'No description available'),
                            "tool_capabilities": getattr(tool, 'capabilities', []) if hasattr(tool, 'capabilities') else []
                        },
                        "execution_result": result,
                        "result_metadata": {
                            "result_type": type(result).__name__,
                            "result_size": len(str(result)),
                            "result_is_dict": isinstance(result, dict),
                            "result_keys": list(result.keys()) if isinstance(result, dict) else [],
                            "execution_successful": True
                        },
                        "execution_context": {
                            "called_from": "workflow_executor",
                            "agent_context": True,
                            "workflow_execution": True,
                            "llm_initiated": True
                        }
                    }
                )
                
                tool_results.append({
                    "tool": tool_id,
                    "action": action,
                    "params": params,
                    "result": result,
                    "success": True
                })
                
            except Exception as e:
                # Log comprehensive tool failure with all inputs
                await self._log_activity(
                    ActivityType.TOOL_INVOCATION,
                    agent_id=agent_id,
                    tool_id=tool_id,
                    title=f"Tool execution failed: {tool.name if 'tool' in locals() and tool else tool_id}",
                    description=f"Tool {tool_id} failed with action: {action} - Error: {str(e)}",
                    data={
                        "tool_name": tool.name if 'tool' in locals() and tool else "Unknown",
                        "tool_id": tool_id,
                        "action": action,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "all_input_params": params if 'params' in locals() else {},
                        "input_params_detailed": {
                            "param_count": len(params) if 'params' in locals() and isinstance(params, dict) else 0,
                            "param_keys": list(params.keys()) if 'params' in locals() and isinstance(params, dict) else [],
                            "param_types": {k: type(v).__name__ for k, v in params.items()} if 'params' in locals() and isinstance(params, dict) else {},
                            "param_sizes": {k: len(str(v)) for k, v in params.items()} if 'params' in locals() and isinstance(params, dict) else {},
                            "has_sensitive_data": any(key.lower() in ['password', 'token', 'key', 'secret'] for key in (params.keys() if 'params' in locals() and isinstance(params, dict) else [])),
                            "raw_params_json": params_json,
                            "parsing_failed": 'params' not in locals(),
                            "parsing_error": str(e) if 'params' not in locals() else None
                        },
                        "tool_schema": {
                            "schema": tool.get_schema().model_dump() if 'tool' in locals() and tool and hasattr(tool.get_schema(), 'model_dump') else "Schema unavailable",
                            "tool_description": getattr(tool.get_schema(), 'description', 'No description available') if 'tool' in locals() and tool else "Tool not found",
                            "tool_available": 'tool' in locals() and tool is not None
                        },
                        "failure_context": {
                            "called_from": "workflow_executor",
                            "agent_context": True,
                            "workflow_execution": True,
                            "llm_initiated": True,
                            "failure_stage": "tool_execution" if 'tool' in locals() and tool else "tool_lookup"
                        }
                    },
                    success=False,
                    error=str(e)
                )
                
                tool_results.append({
                    "tool": tool_id,
                    "action": action,
                    "error": str(e),
                    "success": False
                })
        
        return tool_results
    
    async def _log_activity(
        self,
        activity_type: ActivityType,
        title: str,
        description: str,
        data: Dict[str, Any] = None,
        agent_id: str = None,
        workflow_id: str = None,
        tool_id: str = None,
        success: bool = True,
        error: str = None
    ):
        """Log an activity"""
        activity_data = ActivityCreate(
            type=activity_type,
            agent_id=agent_id,
            workflow_id=workflow_id,
            tool_id=tool_id,
            title=title,
            description=description,
            data=data or {},
            success=success,
            error=error
        )
        storage.create_activity(activity_data)


# Global workflow executor instance
workflow_executor = WorkflowExecutor()