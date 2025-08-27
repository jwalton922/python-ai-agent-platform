"""
MCP Tool for Workflow Generation and Management
"""

from typing import Dict, Any, List, Optional
import json
import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from backend.models.mcp_tool import MockMCPTool, MCPToolSchema
from backend.storage.file_storage import file_storage as storage
from backend.models.workflow_enhanced import (
    EnhancedWorkflow,
    EnhancedWorkflowNode,
    EnhancedWorkflowEdge,
    NodeType,
    WorkflowVariable,
    WorkflowSettings,
    WorkflowMonitoring,
    ErrorHandlingStrategy,
    ConditionBranch,
    LoopConfig
)
from backend.models.base import TriggerType
from backend.llm.factory import LLMFactory
from backend.llm.base import LLMMessage, LLMRole
import re
import math
from collections import defaultdict, deque


def calculate_intelligent_layout(nodes_data: List[Dict], edges_data: List[Dict]) -> Dict[str, Dict[str, float]]:
    """
    Calculate intelligent positions for workflow nodes using a hierarchical layout algorithm.
    Places nodes in layers based on their dependencies and spreads them horizontally to avoid overlap.
    """
    if not nodes_data:
        return {}
    
    # Build adjacency lists
    outgoing = defaultdict(list)  # node_id -> [target_node_ids]
    incoming = defaultdict(list)  # node_id -> [source_node_ids] 
    all_node_ids = {node["id"] for node in nodes_data}
    
    for edge in edges_data:
        source = edge.get("source_node_id") or edge.get("source")
        target = edge.get("target_node_id") or edge.get("target")
        if source and target and source in all_node_ids and target in all_node_ids:
            outgoing[source].append(target)
            incoming[target].append(source)
    
    # Find root nodes (no incoming edges) and calculate layers using topological sort
    layers = []
    remaining_nodes = set(all_node_ids)
    
    while remaining_nodes:
        # Find nodes with no remaining incoming edges
        current_layer = []
        for node_id in remaining_nodes:
            if not any(src in remaining_nodes for src in incoming[node_id]):
                current_layer.append(node_id)
        
        if not current_layer:
            # Handle cycles by picking arbitrary remaining nodes
            current_layer = [next(iter(remaining_nodes))]
        
        layers.append(current_layer)
        remaining_nodes -= set(current_layer)
    
    # Calculate positions
    positions = {}
    layer_height = 150  # Vertical spacing between layers
    node_width = 200   # Horizontal spacing between nodes
    start_y = 50       # Top margin
    
    for layer_idx, layer_nodes in enumerate(layers):
        y = start_y + layer_idx * layer_height
        
        # Center nodes horizontally in each layer
        total_width = max(len(layer_nodes) - 1, 0) * node_width
        start_x = -total_width / 2 + 300  # Offset to keep positive coordinates
        
        for node_idx, node_id in enumerate(layer_nodes):
            x = start_x + node_idx * node_width
            positions[node_id] = {"x": x, "y": y}
    
    return positions



class WorkflowTool(MockMCPTool):
    """MCP Tool for creating and managing workflows"""
    
    def __init__(self):
        super().__init__("workflow_tool", "Workflow Tool", "Automation")
        self.llm_provider = None  # Initialize lazily
    
    def get_schema(self) -> MCPToolSchema:
        return MCPToolSchema(
            input_schema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create", "list", "get", "execute", "delete"],
                        "description": "Action to perform"
                    },
                    "instructions": {
                        "type": "string",
                        "description": "Natural language instructions for workflow creation"
                    },
                    "workflow_id": {
                        "type": "string",
                        "description": "ID of the workflow for get/execute/delete actions"
                    },
                    "workflow_name": {
                        "type": "string",
                        "description": "Name for the workflow"
                    },
                    "use_available_agents": {
                        "type": "boolean",
                        "description": "Whether to use available agents in the workflow",
                        "default": True
                    },
                    "input_data": {
                        "type": "object",
                        "description": "Input data for workflow execution"
                    }
                },
                "required": ["action"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "message": {"type": "string"},
                    "workflow_id": {"type": "string"},
                    "error": {"type": "string"}
                }
            },
            description="Create, manage, and execute workflows using natural language instructions. Supports creating workflows from descriptions, listing existing workflows, executing workflows with input data, and managing workflow lifecycle."
        )
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow tool action"""
        action = params.get("action", "").lower()
        
        if action == "create":
            return await self._create_workflow(params)
        elif action == "list":
            return await self._list_workflows()
        elif action == "get":
            return await self._get_workflow(params)
        elif action == "execute":
            return await self._execute_workflow(params)
        elif action == "delete":
            return await self._delete_workflow(params)
        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}. Available actions: create, list, get, execute, delete"
            }
    
    async def _create_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new workflow from instructions"""
        instructions = params.get("instructions")
        if not instructions:
            return {
                "success": False,
                "error": "Instructions are required for workflow creation"
            }
        
        try:
            # Get available agents if requested
            available_agents = []
            if params.get("use_available_agents", True):
                agents = storage.list_agents()
                available_agents = [
                    {
                        "id": agent.id,
                        "name": agent.name,
                        "description": agent.description,
                        "capabilities": agent.mcp_tool_permissions
                    }
                    for agent in agents
                ]
            
            # Generate workflow structure using LLM
            print(f"🔧 Calling _generate_workflow_structure...")
            workflow_data = await self._generate_workflow_structure(
                instructions,
                available_agents,
                params.get("workflow_name")
            )
            print(f"🔧 _generate_workflow_structure returned data with {len(workflow_data.get('nodes', []))} nodes")
            
            # Create workflow object
            print(f"🔧 Creating workflow from data with {len(workflow_data.get('nodes', []))} nodes")  # Debug print
            try:
                workflow = self._create_workflow_from_data(workflow_data)
                print(f"🔧 Workflow object created with {len(workflow.nodes)} nodes")  # Debug print
            except Exception as e:
                print(f"❌ Failed to create workflow object: {e}")  # Debug print
                import traceback
                traceback.print_exc()
                raise
            
            # Save workflow
            try:
                saved_workflow = storage.create_enhanced_workflow(workflow)
                print(f"✅ Successfully saved workflow with {len(workflow.nodes)} nodes")  # Debug print
            except Exception as e:
                print(f"❌ Failed to save workflow: {e}")  # Debug print
                raise
            
            return {
                "success": True,
                "workflow_id": saved_workflow.id,
                "workflow_name": saved_workflow.name,
                "description": saved_workflow.description,
                "node_count": len(saved_workflow.nodes),
                "edge_count": len(saved_workflow.edges),
                "message": f"Successfully created workflow: {saved_workflow.name}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create workflow: {str(e)}"
            }
    
    def _get_llm_provider(self):
        """Get LLM provider, initializing if needed"""
        if self.llm_provider is None:
            # Use mock_anthropic which has enhanced workflow generation capability
            self.llm_provider = LLMFactory.create_provider("mock_anthropic")
        return self.llm_provider

    async def _generate_workflow_structure(
        self,
        instructions: str,
        available_agents: List[Dict[str, Any]],
        workflow_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate workflow structure using LLM"""
        
        # Create prompt
        agents_info = ""
        if available_agents:
            agents_list = "\n".join([
                f"- {agent['name']} (ID: {agent['id']}): {agent.get('description', 'No description')}"
                for agent in available_agents
            ])
            agents_info = f"\nAvailable agents for the workflow:\n{agents_list}"
        
        prompt = f"""Generate a detailed, multi-node workflow structure based on the following instructions:

Instructions: {instructions}
{f"Workflow Name: {workflow_name}" if workflow_name else ""}
{agents_info}

IMPORTANT: Create a comprehensive workflow with multiple nodes and proper flow control. Break down complex tasks into separate nodes.

Node Types and When to Use:
- "agent": Use for AI processing tasks (sentiment analysis, summarization, etc.)
- "decision": Use for conditional logic and branching (if sentiment is negative, if customer is high value, etc.)
- "transform": Use for data transformation, filtering, or formatting
- "loop": Use for processing multiple items (each email, each customer, etc.)
- "parallel": Use when tasks can run simultaneously
- "storage": Use for saving/retrieving data
- "aggregator": Use for combining results from multiple sources

External Triggers (add to trigger_conditions):
- For "once a day": ["schedule:daily"]
- For "when email comes in": ["email:received"]
- For "when file uploaded": ["file:uploaded"]
- For "webhook": ["webhook:received"]

Please provide a JSON structure with the following format:
{{
    "name": "Workflow name",
    "description": "Brief description",
    "trigger_conditions": ["trigger1", "trigger2"],
    "nodes": [
        {{
            "id": "unique_id",
            "type": "agent|decision|transform|loop|parallel|storage|aggregator",
            "name": "Node name",
            "description": "Node description",
            "agent_id": "agent_id (if type is agent)",
            "instructions": "Specific instructions for this node",
            "condition_expression": "condition for decision nodes",
            "branches": [
                {{"name": "positive", "condition": "sentiment == 'positive'", "target": "positive_handler"}},
                {{"name": "negative", "condition": "sentiment == 'negative'", "target": "negative_handler"}}
            ],
            "config": {{
                "timeout_ms": 30000,
                "error_handling": "fail|continue|fallback"
            }}
        }}
    ],
    "edges": [
        {{
            "source": "source_node_id",
            "target": "target_node_id",
            "condition": "optional condition (e.g., sentiment == 'negative' && customer_value == 'high')"
        }}
    ],
    "variables": [
        {{
            "name": "variable_name",
            "type": "string|number|boolean|object|array",
            "required": true,
            "default": null,
            "description": "Variable description"
        }}
    ]
}}

EXAMPLE for email sentiment analysis:
1. Start with a trigger node or email input
2. Create an agent node for sentiment analysis
3. Add a decision node to check sentiment
4. Create separate branches for positive/negative sentiment
5. Add another decision node for customer value (if negative)
6. Create specific action nodes (slack message, summary generation)
7. Connect all nodes with proper edges and conditions

Generate a complete, multi-node workflow structure that accomplishes: {instructions}"""
        
        # Get LLM response
        messages = [LLMMessage(role=LLMRole.USER, content=prompt)]
        llm_provider = self._get_llm_provider()
        response = await llm_provider.generate(messages)
        
        # Parse response
        print(f"🔧 LLM response received, length: {len(response.content)}")
        try:
            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response.content)
            if json_match:
                json_str = json_match.group(0)
                print(f"🔍 Found JSON block, length: {len(json_str)}")
                parsed_data = json.loads(json_str)
                nodes_count = len(parsed_data.get('nodes', []))
                print(f"✅ Successfully parsed JSON with {nodes_count} nodes")
                if nodes_count > 1:
                    print(f"🎉 Complex workflow parsed successfully! Returning complex data.")
                    return parsed_data
                else:
                    print(f"⚠️ Only {nodes_count} node found in parsed JSON")
            else:
                print(f"❌ No JSON block found in LLM response")
                print(f"🔍 Response preview: {response.content[:500]}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            print(f"🔍 Raw LLM response: {response.content[:1000]}...")
        except Exception as e:
            print(f"❌ Unexpected error in workflow parsing: {e}")
            import traceback
            traceback.print_exc()
        
        # Create default workflow if parsing fails
        # Get first available agent for fallback
        agent_id = None
        if available_agents:
            agent_id = available_agents[0]['id']
        
        return {
            "name": workflow_name or "Generated Workflow",
            "description": f"Workflow to: {instructions[:100]}",
            "nodes": [
                {
                    "id": "main_node",
                    "type": "agent",
                    "name": "Main Processing",
                    "description": "Main workflow processing",
                    "agent_id": agent_id,
                    "instructions": instructions
                }
            ],
            "edges": [],
            "variables": [
                {
                    "name": "input",
                    "type": "object",
                    "required": True,
                    "description": "Workflow input"
                }
            ]
        }
    
    def _create_workflow_from_data(self, data: Dict[str, Any]) -> EnhancedWorkflow:
        """Create an EnhancedWorkflow object from parsed data"""
        
        workflow_id = str(uuid.uuid4())
        print(f"🔧 Creating workflow ID: {workflow_id}")
        
        # Calculate intelligent layout positions for nodes
        node_data_list = data.get("nodes", [])
        edge_data_list = data.get("edges", [])
        
        print(f"🎯 Calculating intelligent layout for {len(node_data_list)} nodes and {len(edge_data_list)} edges")
        node_positions = calculate_intelligent_layout(node_data_list, edge_data_list)
        
        # Create nodes
        nodes = []
        print(f"🔧 Processing {len(node_data_list)} nodes from data")
        
        for i, node_data in enumerate(node_data_list):
            print(f"🔧 Processing node {i+1}: {node_data.get('name', 'unnamed')} ({node_data.get('type', 'unknown')})")
            node_type_str = node_data.get("type", "agent").lower()
            node_type = {
                "agent": NodeType.AGENT,
                "decision": NodeType.DECISION,
                "transform": NodeType.TRANSFORM,
                "loop": NodeType.LOOP,
                "parallel": NodeType.PARALLEL,
                "storage": NodeType.STORAGE,
                "aggregator": NodeType.AGGREGATOR
            }.get(node_type_str, NodeType.AGENT)
            
            # For agent nodes, ensure we have an agent_id
            agent_id = None
            if node_type == NodeType.AGENT:
                agent_id = node_data.get("agent_id")
                if not agent_id:
                    # Use first available agent as fallback
                    agents = storage.list_agents()
                    if agents:
                        agent_id = agents[0].id
            
            # Create the base node with intelligent positioning
            node_id = node_data.get("id", str(uuid.uuid4()))
            position = node_positions.get(node_id, {"x": 0, "y": 0})
            
            node = EnhancedWorkflowNode(
                id=node_id,
                type=node_type,
                name=node_data.get("name", "Node"),
                description=node_data.get("description"),
                position=position,
                agent_id=agent_id,
                instructions_override=node_data.get("instructions") if node_type == NodeType.AGENT else None
            )
            
            # Add type-specific attributes
            if node_type == NodeType.DECISION:
                # Handle decision branches
                branches_data = node_data.get("branches", [])
                if branches_data:
                    node.condition_branches = [
                        ConditionBranch(
                            name=branch.get("name", f"Branch {i}"),
                            expression=branch.get("condition", "true"),
                            target=branch.get("target", ""),
                            priority=i
                        )
                        for i, branch in enumerate(branches_data)
                    ]
                
                # Note: condition_expression from JSON is handled via condition_branches above
                # The condition_expression is not a direct field on EnhancedWorkflowNode
                    
            elif node_type == NodeType.LOOP:
                # Handle loop configuration
                loop_data = node_data.get("loop_config", {})
                if loop_data:
                    node.loop_config = LoopConfig(
                        type=loop_data.get("type", "for_each"),
                        source=loop_data.get("source", ""),
                        condition=loop_data.get("condition"),
                        max_iterations=loop_data.get("max_iterations", 100),
                        parallel=loop_data.get("parallel", False)
                    )
                    
            elif node_type == NodeType.TRANSFORM:
                # Handle transformation configuration
                transformations = node_data.get("transformations", [])
                if transformations:
                    node.transformations = transformations
                    
            elif node_type == NodeType.PARALLEL:
                # Handle parallel branches
                parallel_branches = node_data.get("parallel_branches", [])
                if parallel_branches:
                    node.parallel_branches = parallel_branches
            
            try:
                nodes.append(node)
                print(f"✅ Successfully created node: {node.name}")
            except Exception as e:
                print(f"❌ Failed to create node {node_data.get('name', 'unnamed')}: {e}")
                raise
        
        # Create edges
        edges = []
        edge_data_list = data.get("edges", [])
        print(f"🔧 Processing {len(edge_data_list)} edges from data")
        
        for i, edge_data in enumerate(edge_data_list):
            print(f"🔧 Processing edge {i+1}: {edge_data.get('source', '?')} → {edge_data.get('target', '?')}")
            edge = EnhancedWorkflowEdge(
                id=str(uuid.uuid4()),
                source_node_id=edge_data.get("source", ""),
                target_node_id=edge_data.get("target", ""),
                condition=edge_data.get("condition")
            )
            edges.append(edge)
        
        # Create variables
        variables = []
        for var_data in data.get("variables", []):
            variable = WorkflowVariable(
                name=var_data.get("name", "var"),
                type=var_data.get("type", "string"),
                required=var_data.get("required", False),
                default=var_data.get("default"),
                description=var_data.get("description")
            )
            variables.append(variable)
        
        # Extract and map trigger conditions to valid enum values
        raw_trigger_conditions = data.get("trigger_conditions", [])
        trigger_conditions = []
        
        for trigger in raw_trigger_conditions:
            # Map descriptive trigger conditions to enum values
            if isinstance(trigger, str):
                if "email" in trigger.lower():
                    trigger_conditions.append(TriggerType.EMAIL)
                elif "schedule" in trigger.lower() or "time" in trigger.lower() or "daily" in trigger.lower():
                    trigger_conditions.append(TriggerType.SCHEDULED)
                elif "slack" in trigger.lower():
                    trigger_conditions.append(TriggerType.SLACK)
                elif "webhook" in trigger.lower() or "api" in trigger.lower():
                    trigger_conditions.append(TriggerType.WEBHOOK)
                elif trigger.lower() == "manual":
                    trigger_conditions.append(TriggerType.MANUAL)
                else:
                    # Default to manual if we can't map it
                    trigger_conditions.append(TriggerType.MANUAL)
            else:
                trigger_conditions.append(trigger)
        
        # Create workflow
        print(f"🔧 Creating final workflow object with {len(nodes)} nodes, {len(edges)} edges, {len(variables)} variables")
        try:
            workflow = EnhancedWorkflow(
                id=workflow_id,
                name=data.get("name", "Generated Workflow"),
                description=data.get("description", ""),
                version="1.0.0",
                nodes=nodes,
                edges=edges,
                variables=variables,
                trigger_conditions=trigger_conditions,
                settings=WorkflowSettings(
                    max_execution_time_ms=300000,
                    continue_on_error=False,
                    save_intermediate_state=True,
                    enable_checkpoints=True
                ),
                monitoring=WorkflowMonitoring(
                    metrics_enabled=True,
                    capture_inputs=True,
                    capture_outputs=True
                ),
                error_handling_strategy=ErrorHandlingStrategy.RETRY_THEN_FAIL,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            print(f"✅ Successfully created EnhancedWorkflow object")
            return workflow
        except Exception as e:
            print(f"❌ Failed to create EnhancedWorkflow object: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    async def _list_workflows(self) -> Dict[str, Any]:
        """List all workflows"""
        try:
            workflows = storage.list_enhanced_workflows()
            workflow_list = [
                {
                    "id": w.id,
                    "name": w.name,
                    "description": w.description,
                    "node_count": len(w.nodes),
                    "status": w.status.value if hasattr(w.status, 'value') else str(w.status),
                    "created_at": str(w.created_at)
                }
                for w in workflows
            ]
            
            return {
                "success": True,
                "workflows": workflow_list,
                "count": len(workflow_list)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list workflows: {str(e)}"
            }
    
    async def _get_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get a specific workflow"""
        workflow_id = params.get("workflow_id")
        if not workflow_id:
            return {
                "success": False,
                "error": "workflow_id is required"
            }
        
        try:
            workflow = storage.get_enhanced_workflow(workflow_id)
            if not workflow:
                return {
                    "success": False,
                    "error": f"Workflow {workflow_id} not found"
                }
            
            return {
                "success": True,
                "workflow": {
                    "id": workflow.id,
                    "name": workflow.name,
                    "description": workflow.description,
                    "nodes": [
                        {
                            "id": n.id,
                            "type": n.type.value if hasattr(n.type, 'value') else str(n.type),
                            "name": n.name,
                            "description": n.description
                        }
                        for n in workflow.nodes
                    ],
                    "edges": [
                        {
                            "source": e.source_node_id,
                            "target": e.target_node_id,
                            "condition": e.condition
                        }
                        for e in workflow.edges
                    ],
                    "variables": [
                        {
                            "name": v.name,
                            "type": v.type,
                            "required": v.required,
                            "description": v.description
                        }
                        for v in workflow.variables
                    ] if workflow.variables else []
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get workflow: {str(e)}"
            }
    
    async def _execute_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow"""
        workflow_id = params.get("workflow_id")
        if not workflow_id:
            return {
                "success": False,
                "error": "workflow_id is required"
            }
        
        try:
            # Import executor here to avoid circular imports
            from backend.workflow.executor_enhanced import enhanced_workflow_executor
            
            workflow = storage.get_enhanced_workflow(workflow_id)
            if not workflow:
                return {
                    "success": False,
                    "error": f"Workflow {workflow_id} not found"
                }
            
            # Execute workflow
            input_data = params.get("input_data", {})
            result = await enhanced_workflow_executor.execute_workflow(
                workflow,
                input_data
            )
            
            return {
                "success": True,
                "execution_id": result.execution_id,
                "status": result.status.value if hasattr(result.status, 'value') else str(result.status),
                "output": result.output,
                "message": f"Workflow {workflow.name} executed successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to execute workflow: {str(e)}"
            }
    
    async def _delete_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a workflow"""
        workflow_id = params.get("workflow_id")
        if not workflow_id:
            return {
                "success": False,
                "error": "workflow_id is required"
            }
        
        try:
            success = storage.delete_enhanced_workflow(workflow_id)
            if success:
                return {
                    "success": True,
                    "message": f"Workflow {workflow_id} deleted successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Workflow {workflow_id} not found"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to delete workflow: {str(e)}"
            }


# Create singleton instance
workflow_tool = WorkflowTool()