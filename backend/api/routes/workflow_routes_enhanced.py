from typing import List, Dict, Any, Optional
from datetime import datetime
import traceback
from fastapi import APIRouter, HTTPException, status, Query, BackgroundTasks
from backend.models.workflow_enhanced import (
    EnhancedWorkflow,
    WorkflowExecutionRequest,
    WorkflowExecutionResult,
    WorkflowExecutionState,
    NodeType,
    ExecutionMode,
    WorkflowVariable
)
from backend.models.activity import ActivityCreate, ActivityType
from backend.storage.file_storage import file_storage as storage
from backend.workflow.executor_enhanced import enhanced_workflow_executor
import hashlib
import time

router = APIRouter()


async def _log_activity(
    activity_type: ActivityType,
    title: str,
    description: str,
    data: Dict[str, Any] = None,
    workflow_id: str = None,
    success: bool = True,
    error: str = None
):
    """Log an activity"""
    activity_data = ActivityCreate(
        type=activity_type,
        workflow_id=workflow_id,
        title=title,
        description=description,
        data=data or {},
        success=success,
        error=error
    )
    storage.create_activity(activity_data)


@router.post("/", response_model=EnhancedWorkflow, status_code=status.HTTP_201_CREATED)
async def create_enhanced_workflow(workflow_data: EnhancedWorkflow) -> EnhancedWorkflow:
    """Create a new enhanced workflow with advanced features"""
    try:
        # Validate workflow structure
        validation_result = await validate_workflow_structure(workflow_data)
        if not validation_result["valid"]:
            raise ValueError(f"Workflow validation failed: {validation_result['errors']}")
        
        # Store workflow
        workflow = storage.create_enhanced_workflow(workflow_data)
        
        # Log creation
        await _log_activity(
            ActivityType.WORKFLOW_CREATION,
            workflow_id=workflow.id,
            title=f"Created enhanced workflow: {workflow.name}",
            description=f"Created workflow v{workflow.version} with {len(workflow.nodes)} nodes",
            data={
                "workflow_name": workflow.name,
                "workflow_version": workflow.version,
                "node_count": len(workflow.nodes),
                "node_types": list(set(node.type.value for node in workflow.nodes)),
                "execution_mode": workflow.execution_mode.value,
                "has_error_handler": workflow.global_error_handler is not None,
                "has_monitoring": workflow.monitoring.metrics_enabled,
                "max_execution_time": workflow.settings.max_execution_time_ms,
                "variables_count": len(workflow.variables)
            }
        )
        
        return workflow
        
    except Exception as e:
        print(f"Failed to create enhanced workflow: {e}")
        traceback.print_exc()
        await _log_activity(
            ActivityType.WORKFLOW_CREATION,
            title="Failed to create enhanced workflow",
            description=str(e),
            data={"error": str(e), "workflow_name": workflow_data.name},
            success=False,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[EnhancedWorkflow])
async def list_enhanced_workflows(
    node_type: Optional[NodeType] = Query(None),
    execution_mode: Optional[ExecutionMode] = Query(None),
    tag: Optional[str] = Query(None)
) -> List[EnhancedWorkflow]:
    """List enhanced workflows with filtering"""
    workflows = storage.list_enhanced_workflows()
    
    # Filter by node type if specified
    if node_type:
        workflows = [
            w for w in workflows
            if any(node.type == node_type for node in w.nodes)
        ]
    
    # Filter by execution mode
    if execution_mode:
        workflows = [
            w for w in workflows
            if w.execution_mode == execution_mode
        ]
    
    # Filter by tag
    if tag:
        workflows = [
            w for w in workflows
            if tag in w.tags
        ]
    
    return workflows


@router.get("/{workflow_id}", response_model=EnhancedWorkflow)
async def get_enhanced_workflow(workflow_id: str) -> EnhancedWorkflow:
    """Get a specific enhanced workflow"""
    workflow = storage.get_enhanced_workflow(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )
    return workflow


@router.delete("/{workflow_id}")
async def delete_enhanced_workflow(workflow_id: str):
    """Delete an enhanced workflow"""
    workflow = storage.get_enhanced_workflow(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )
    
    try:
        # Delete the workflow
        success = storage.delete_enhanced_workflow(workflow_id)
        if success:
            # Log deletion activity
            await _log_activity(
                ActivityType.WORKFLOW_DELETION,
                workflow_id=workflow_id,
                title=f"Deleted enhanced workflow: {workflow.name}",
                description=f"Deleted workflow v{workflow.version} with {len(workflow.nodes)} nodes",
                data={
                    "workflow_name": workflow.name,
                    "workflow_version": workflow.version,
                    "node_count": len(workflow.nodes)
                }
            )
            return {"message": f"Workflow {workflow_id} deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete workflow"
            )
    except Exception as e:
        print(f"Failed to delete enhanced workflow {workflow_id}: {e}")
        traceback.print_exc()
        await _log_activity(
            ActivityType.WORKFLOW_DELETION,
            workflow_id=workflow_id,
            title="Failed to delete enhanced workflow",
            description=str(e),
            data={"error": str(e), "workflow_name": workflow.name},
            success=False,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{workflow_id}/execute")
async def execute_enhanced_workflow(
    workflow_id: str,
    request: WorkflowExecutionRequest,
    background_tasks: BackgroundTasks
) -> WorkflowExecutionResult:
    """Execute an enhanced workflow with advanced features"""
    workflow = storage.get_enhanced_workflow(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )
    
    try:
        # Set workflow_id from URL parameter if not provided in request
        if not request.workflow_id:
            request.workflow_id = workflow_id
        
        # Validate input against workflow variables
        validation_errors = validate_workflow_input(workflow, request.input)
        if validation_errors:
            raise ValueError(f"Input validation failed: {validation_errors}")
        
        # Apply overrides if provided
        if request.overrides:
            workflow = apply_workflow_overrides(workflow, request.overrides)
        
        # Execute workflow
        if request.dry_run:
            # Dry run - just validate and return expected structure
            return WorkflowExecutionResult(
                execution_id=hashlib.md5(f"{workflow_id}_{time.time()}".encode()).hexdigest(),
                workflow_id=workflow_id,
                status="completed",
                output={"message": "Dry run completed successfully"},
                node_results={},
                started_at=datetime.utcnow(),
                tokens_used=0,
                cost_usd=0.0,
                api_calls_made=0
            )
        
        # Execute workflow (async if large)
        if len(workflow.nodes) > 10:
            # Execute in background for large workflows
            background_tasks.add_task(
                enhanced_workflow_executor.execute_workflow,
                workflow,
                request.input,
                checkpoint_id=request.checkpoint_id
            )
            
            return WorkflowExecutionResult(
                execution_id=hashlib.md5(f"{workflow_id}_{time.time()}".encode()).hexdigest(),
                workflow_id=workflow_id,
                status="running",
                output={"message": "Workflow execution started in background"},
                node_results={},
                started_at=datetime.utcnow(),
                tokens_used=0,
                cost_usd=0.0,
                api_calls_made=0
            )
        else:
            # Execute synchronously for small workflows
            result = await enhanced_workflow_executor.execute_workflow(
                workflow,
                request.input,
                checkpoint_id=request.checkpoint_id
            )
            return result
            
    except Exception as e:
        print(f"Workflow execution failed for {workflow_id}: {e}")
        traceback.print_exc()
        await _log_activity(
            ActivityType.WORKFLOW_FAILED,
            workflow_id=workflow_id,
            title=f"Workflow execution failed: {workflow.name}",
            description=str(e),
            data={
                "error": str(e),
                "workflow_id": workflow_id,
                "input": request.input
            },
            success=False,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{workflow_id}/nodes/{node_id}/execute")
async def execute_workflow_node(
    workflow_id: str,
    node_id: str,
    input_data: Dict[str, Any],
    mock_dependencies: bool = False
) -> Dict[str, Any]:
    """Execute a single workflow node for testing"""
    workflow = storage.get_enhanced_workflow(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )
    
    node = next((n for n in workflow.nodes if n.id == node_id), None)
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node {node_id} not found in workflow"
        )
    
    try:
        # Create minimal execution state for testing
        state = WorkflowExecutionState(
            execution_id=hashlib.md5(f"{workflow_id}_{node_id}_{time.time()}".encode()).hexdigest(),
            workflow_id=workflow_id,
            workflow_version=workflow.version,
            status="running",
            started_at=datetime.utcnow(),
            global_variables=input_data
        )
        
        # Get appropriate executor
        executor = enhanced_workflow_executor.node_executors.get(node.type)
        if not executor:
            raise ValueError(f"No executor for node type {node.type}")
        
        # Execute node
        result = await executor.execute(node, input_data, state)
        
        return {
            "node_id": node_id,
            "node_type": node.type.value,
            "result": result,
            "tokens_used": state.total_tokens_used,
            "success": result.get("success", False)
        }
        
    except Exception as e:
        print(f"Node execution failed: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/validate")
async def validate_workflow(workflow_data: EnhancedWorkflow) -> Dict[str, Any]:
    """Validate a workflow configuration"""
    return await validate_workflow_structure(workflow_data)


@router.get("/{workflow_id}/executions")
async def list_workflow_executions(
    workflow_id: str,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
) -> List[WorkflowExecutionState]:
    """List execution history for a workflow"""
    # Would fetch from storage
    return []


@router.get("/executions/{execution_id}")
async def get_workflow_execution(execution_id: str) -> WorkflowExecutionState:
    """Get details of a specific workflow execution"""
    # Would fetch from storage
    execution = enhanced_workflow_executor.running_workflows.get(execution_id)
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution {execution_id} not found"
        )
    return execution


@router.post("/executions/{execution_id}/cancel")
async def cancel_workflow_execution(execution_id: str) -> Dict[str, str]:
    """Cancel a running workflow execution"""
    if execution_id in enhanced_workflow_executor.running_workflows:
        state = enhanced_workflow_executor.running_workflows[execution_id]
        state.status = "cancelled"
        del enhanced_workflow_executor.running_workflows[execution_id]
        
        await _log_activity(
            ActivityType.WORKFLOW_FAILED,
            workflow_id=state.workflow_id,
            title="Workflow execution cancelled",
            description=f"Execution {execution_id} was cancelled by user",
            data={"execution_id": execution_id},
            success=False,
            error="Cancelled by user"
        )
        
        return {"status": "cancelled", "execution_id": execution_id}
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Execution {execution_id} not found or already completed"
    )


@router.get("/{workflow_id}/debug")
async def debug_workflow(workflow_id: str) -> Dict[str, Any]:
    """Get debug information for a workflow"""
    workflow = storage.get_enhanced_workflow(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )
    
    # Analyze workflow structure
    node_types = {}
    for node in workflow.nodes:
        node_types[node.type.value] = node_types.get(node.type.value, 0) + 1
    
    # Check for cycles
    has_cycles = False
    try:
        enhanced_workflow_executor._build_execution_plan(workflow)
    except ValueError as e:
        if "cycles" in str(e):
            has_cycles = True
    
    # Find disconnected nodes
    connected_nodes = set()
    for edge in workflow.edges:
        connected_nodes.add(edge.source_node_id)
        connected_nodes.add(edge.target_node_id)
    
    all_nodes = set(node.id for node in workflow.nodes)
    disconnected_nodes = all_nodes - connected_nodes
    
    return {
        "workflow_id": workflow_id,
        "workflow_name": workflow.name,
        "workflow_version": workflow.version,
        "node_count": len(workflow.nodes),
        "edge_count": len(workflow.edges),
        "node_types": node_types,
        "has_cycles": has_cycles,
        "disconnected_nodes": list(disconnected_nodes),
        "execution_mode": workflow.execution_mode.value,
        "max_execution_time_ms": workflow.settings.max_execution_time_ms,
        "has_global_error_handler": workflow.global_error_handler is not None,
        "monitoring_enabled": workflow.monitoring.metrics_enabled,
        "variables": [
            {
                "name": var.name,
                "type": var.type,
                "required": var.required,
                "has_default": var.default is not None
            }
            for var in workflow.variables
        ],
        "complexity_score": len(workflow.nodes) + len(workflow.edges) * 2
    }


# Helper functions

async def validate_workflow_structure(workflow: EnhancedWorkflow) -> Dict[str, Any]:
    """Validate workflow structure and configuration"""
    errors = []
    warnings = []
    
    # Check for required fields
    if not workflow.name:
        errors.append("Workflow name is required")
    
    if not workflow.nodes:
        errors.append("Workflow must have at least one node")
    
    # Validate nodes
    node_ids = set()
    for node in workflow.nodes:
        if node.id in node_ids:
            errors.append(f"Duplicate node ID: {node.id}")
        node_ids.add(node.id)
        
        # Type-specific validation
        if node.type == NodeType.AGENT and not node.agent_id:
            errors.append(f"Agent node {node.id} missing agent_id")
        
        if node.type == NodeType.DECISION and not node.condition_branches:
            errors.append(f"Decision node {node.id} missing condition branches")
        
        if node.type == NodeType.LOOP and not node.loop_config:
            errors.append(f"Loop node {node.id} missing loop configuration")
    
    # Validate edges
    for edge in workflow.edges:
        if edge.source_node_id not in node_ids:
            errors.append(f"Edge references unknown source node: {edge.source_node_id}")
        
        if edge.target_node_id not in node_ids:
            errors.append(f"Edge references unknown target node: {edge.target_node_id}")
    
    # Check for cycles
    try:
        enhanced_workflow_executor._build_execution_plan(workflow)
    except ValueError as e:
        if "cycles" in str(e):
            errors.append("Workflow contains cycles")
    
    # Validate variables
    var_names = set()
    for var in workflow.variables:
        if var.name in var_names:
            errors.append(f"Duplicate variable name: {var.name}")
        var_names.add(var.name)
    
    # Warnings
    if len(workflow.nodes) > 50:
        warnings.append("Workflow has more than 50 nodes, consider breaking it into sub-workflows")
    
    if workflow.settings.max_execution_time_ms > 3600000:
        warnings.append("Max execution time is set to more than 1 hour")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "node_count": len(workflow.nodes),
        "edge_count": len(workflow.edges),
        "variable_count": len(workflow.variables)
    }


def validate_workflow_input(workflow: EnhancedWorkflow, input_data: Dict[str, Any]) -> List[str]:
    """Validate input data against workflow variables"""
    errors = []
    
    for var in workflow.variables:
        if var.required and var.name not in input_data:
            if var.default is None:
                errors.append(f"Required variable '{var.name}' is missing")
        
        if var.name in input_data:
            value = input_data[var.name]
            
            # Type validation
            if var.type == "string" and not isinstance(value, str):
                errors.append(f"Variable '{var.name}' must be a string")
            elif var.type == "number" and not isinstance(value, (int, float)):
                errors.append(f"Variable '{var.name}' must be a number")
            elif var.type == "boolean" and not isinstance(value, bool):
                errors.append(f"Variable '{var.name}' must be a boolean")
            elif var.type == "object" and not isinstance(value, dict):
                errors.append(f"Variable '{var.name}' must be an object")
            elif var.type == "array" and not isinstance(value, list):
                errors.append(f"Variable '{var.name}' must be an array")
    
    return errors


def apply_workflow_overrides(workflow: EnhancedWorkflow, overrides: Dict[str, Any]) -> EnhancedWorkflow:
    """Apply runtime overrides to workflow configuration"""
    # Clone workflow
    import copy
    workflow = copy.deepcopy(workflow)
    
    # Apply global overrides
    if "global" in overrides:
        global_overrides = overrides["global"]
        
        if "max_execution_time" in global_overrides:
            workflow.settings.max_execution_time_ms = global_overrides["max_execution_time"]
        
        if "max_total_tokens" in global_overrides:
            workflow.settings.max_total_tokens = global_overrides["max_total_tokens"]
    
    # Apply node overrides
    if "nodes" in overrides:
        node_overrides = overrides["nodes"]
        
        for node in workflow.nodes:
            if node.id in node_overrides:
                node_override = node_overrides[node.id]
                
                if "timeout" in node_override:
                    node.config.timeout_ms = node_override["timeout"]
                
                if "instructions_append" in node_override:
                    node.instructions_append = node_override["instructions_append"]
    
    return workflow