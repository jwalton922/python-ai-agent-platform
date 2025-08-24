from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status
from backend.models.workflow import Workflow, WorkflowCreate, WorkflowUpdate
from backend.models.activity import ActivityCreate, ActivityType
from backend.storage.file_storage import file_storage as storage
from backend.workflow.executor import workflow_executor

router = APIRouter()


async def _log_activity(
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


@router.post("/", response_model=Workflow, status_code=status.HTTP_201_CREATED)
async def create_workflow(workflow_data: WorkflowCreate) -> Workflow:
    """Create a new workflow"""
    try:
        workflow = storage.create_workflow(workflow_data)
        
        # Log comprehensive workflow creation activity
        await _log_activity(
            ActivityType.WORKFLOW_CREATION,
            workflow_id=workflow.id,
            title=f"Created workflow: {workflow.name}",
            description=f"New workflow '{workflow.name}' created with {len(workflow.nodes)} nodes and {len(workflow.edges)} edges",
            data={
                "workflow_name": workflow.name,
                "workflow_id": workflow.id,
                "workflow_description": workflow.description,
                "nodes_count": len(workflow.nodes),
                "edges_count": len(workflow.edges),
                "status": workflow.status.value,
                "trigger_conditions": workflow.trigger_conditions,
                "trigger_conditions_count": len(workflow.trigger_conditions) if workflow.trigger_conditions else 0,
                "metadata": workflow.metadata,
                "created_at": str(workflow.created_at),
                "nodes": [
                    {
                        "id": node.id,
                        "agent_id": node.agent_id,
                        "config": node.config,
                        "position": getattr(node, 'position', None)
                    } for node in workflow.nodes
                ],
                "edges": [
                    {
                        "source": edge.source_node_id,
                        "target": edge.target_node_id,
                        "condition": getattr(edge, 'condition', None)
                    } for edge in workflow.edges
                ],
                "creation_context": "api_route",
                "workflow_configuration": {
                    "has_description": bool(workflow.description),
                    "has_triggers": bool(workflow.trigger_conditions),
                    "has_metadata": bool(workflow.metadata),
                    "is_dag": len(workflow.edges) >= 0,  # Could add cycle detection later
                    "complexity_score": len(workflow.nodes) + len(workflow.edges)
                }
            }
        )
        
        return workflow
    except Exception as e:
        # Log workflow creation failure
        await _log_activity(
            ActivityType.WORKFLOW_CREATION,
            title=f"Failed to create workflow",
            description=f"Workflow creation failed: {str(e)}",
            data={
                "error": str(e),
                "error_type": type(e).__name__,
                "attempted_workflow_name": workflow_data.name,
                "attempted_nodes_count": len(workflow_data.nodes),
                "attempted_edges_count": len(workflow_data.edges),
                "failure_context": "workflow_creation_route",
                "input_data": {
                    "name": workflow_data.name,
                    "description": workflow_data.description,
                    "nodes_count": len(workflow_data.nodes),
                    "edges_count": len(workflow_data.edges)
                }
            },
            success=False,
            error=str(e)
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create workflow: {str(e)}"
        )


@router.get("/", response_model=List[Workflow])
async def list_workflows() -> List[Workflow]:
    """List all workflows"""
    return storage.list_workflows()


@router.get("/{workflow_id}", response_model=Workflow)
async def get_workflow(workflow_id: str) -> Workflow:
    """Get a specific workflow by ID"""
    workflow = storage.get_workflow(workflow_id)
    if not workflow:
        # Log workflow not found
        await _log_activity(
            ActivityType.WORKFLOW_RETRIEVAL,
            workflow_id=workflow_id,
            title=f"Workflow not found: {workflow_id[:8]}",
            description=f"Attempted to retrieve non-existent workflow {workflow_id}",
            data={
                "requested_workflow_id": workflow_id,
                "operation": "get_workflow",
                "result": "not_found",
                "context": "api_route"
            },
            success=False,
            error=f"Workflow {workflow_id} not found"
        )
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )
    
    # Log successful workflow retrieval
    await _log_activity(
        ActivityType.WORKFLOW_RETRIEVAL,
        workflow_id=workflow_id,
        title=f"Retrieved workflow: {workflow.name}",
        description=f"Successfully retrieved workflow '{workflow.name}' with {len(workflow.nodes)} nodes",
        data={
            "workflow_name": workflow.name,
            "workflow_id": workflow.id,
            "nodes_count": len(workflow.nodes),
            "edges_count": len(workflow.edges),
            "status": workflow.status.value,
            "has_description": bool(workflow.description),
            "created_at": str(workflow.created_at),
            "updated_at": str(workflow.updated_at) if workflow.updated_at else None,
            "operation": "get_workflow",
            "result": "success",
            "context": "api_route"
        }
    )
    
    return workflow


@router.put("/{workflow_id}", response_model=Workflow)
async def update_workflow(workflow_id: str, workflow_update: WorkflowUpdate) -> Workflow:
    """Update an existing workflow"""
    # Get original workflow for comparison
    original_workflow = storage.get_workflow(workflow_id)
    if not original_workflow:
        # Log workflow not found for update
        await _log_activity(
            ActivityType.WORKFLOW_UPDATE,
            workflow_id=workflow_id,
            title=f"Workflow update failed: {workflow_id[:8]}",
            description=f"Attempted to update non-existent workflow {workflow_id}",
            data={
                "requested_workflow_id": workflow_id,
                "update_data": workflow_update.model_dump(exclude_unset=True),
                "operation": "update_workflow",
                "result": "not_found",
                "context": "api_route"
            },
            success=False,
            error=f"Workflow {workflow_id} not found"
        )
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )
    
    # Perform the update
    updated_workflow = storage.update_workflow(workflow_id, workflow_update)
    
    # Log comprehensive workflow update activity
    update_fields = workflow_update.model_dump(exclude_unset=True)
    await _log_activity(
        ActivityType.WORKFLOW_UPDATE,
        workflow_id=workflow_id,
        title=f"Updated workflow: {updated_workflow.name}",
        description=f"Workflow '{updated_workflow.name}' updated - {len(update_fields)} field(s) modified",
        data={
            "workflow_name": updated_workflow.name,
            "workflow_id": workflow_id,
            "updated_fields": list(update_fields.keys()),
            "updated_fields_count": len(update_fields),
            "update_data": update_fields,
            "original_data": {
                "name": original_workflow.name,
                "description": original_workflow.description,
                "status": original_workflow.status.value,
                "nodes_count": len(original_workflow.nodes),
                "edges_count": len(original_workflow.edges),
                "updated_at": str(original_workflow.updated_at) if original_workflow.updated_at else None
            },
            "new_data": {
                "name": updated_workflow.name,
                "description": updated_workflow.description,
                "status": updated_workflow.status.value,
                "nodes_count": len(updated_workflow.nodes),
                "edges_count": len(updated_workflow.edges),
                "updated_at": str(updated_workflow.updated_at)
            },
            "operation": "update_workflow",
            "result": "success",
            "context": "api_route",
            "changes_analysis": {
                "name_changed": original_workflow.name != updated_workflow.name,
                "description_changed": original_workflow.description != updated_workflow.description,
                "status_changed": original_workflow.status != updated_workflow.status,
                "structure_changed": (
                    len(original_workflow.nodes) != len(updated_workflow.nodes) or
                    len(original_workflow.edges) != len(updated_workflow.edges)
                )
            }
        }
    )
    
    return updated_workflow


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(workflow_id: str):
    """Delete a workflow"""
    # Get workflow details before deletion for logging
    workflow_to_delete = storage.get_workflow(workflow_id)
    
    success = storage.delete_workflow(workflow_id)
    if not success:
        # Log workflow not found for deletion
        await _log_activity(
            ActivityType.WORKFLOW_DELETION,
            workflow_id=workflow_id,
            title=f"Workflow deletion failed: {workflow_id[:8]}",
            description=f"Attempted to delete non-existent workflow {workflow_id}",
            data={
                "requested_workflow_id": workflow_id,
                "operation": "delete_workflow",
                "result": "not_found",
                "context": "api_route"
            },
            success=False,
            error=f"Workflow {workflow_id} not found"
        )
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )
    
    # Log successful workflow deletion with comprehensive details
    await _log_activity(
        ActivityType.WORKFLOW_DELETION,
        workflow_id=workflow_id,
        title=f"Deleted workflow: {workflow_to_delete.name if workflow_to_delete else 'Unknown'}",
        description=f"Successfully deleted workflow '{workflow_to_delete.name if workflow_to_delete else 'Unknown'}' with {len(workflow_to_delete.nodes) if workflow_to_delete else 0} nodes",
        data={
            "deleted_workflow": {
                "workflow_name": workflow_to_delete.name if workflow_to_delete else "Unknown",
                "workflow_id": workflow_id,
                "workflow_description": workflow_to_delete.description if workflow_to_delete else None,
                "nodes_count": len(workflow_to_delete.nodes) if workflow_to_delete else 0,
                "edges_count": len(workflow_to_delete.edges) if workflow_to_delete else 0,
                "status": workflow_to_delete.status.value if workflow_to_delete else "unknown",
                "created_at": str(workflow_to_delete.created_at) if workflow_to_delete else None,
                "updated_at": str(workflow_to_delete.updated_at) if workflow_to_delete and workflow_to_delete.updated_at else None,
                "agents_involved": list(set(node.agent_id for node in workflow_to_delete.nodes)) if workflow_to_delete else []
            },
            "operation": "delete_workflow",
            "result": "success",
            "context": "api_route",
            "deletion_metadata": {
                "permanent": True,
                "cascade_effects": "execution_history_preserved",
                "recovery_possible": False,
                "affected_agents": len(set(node.agent_id for node in workflow_to_delete.nodes)) if workflow_to_delete else 0
            }
        }
    )


@router.post("/{workflow_id}/execute")
async def execute_workflow(workflow_id: str, context: Dict[str, Any] = None):
    """Execute a workflow"""
    # Get workflow details for logging
    workflow = storage.get_workflow(workflow_id)
    
    try:
        # Log workflow execution request
        await _log_activity(
            ActivityType.WORKFLOW_START,
            workflow_id=workflow_id,
            title=f"Workflow execution requested: {workflow.name if workflow else workflow_id[:8]}",
            description=f"User requested execution of workflow '{workflow.name if workflow else 'Unknown'}' via API",
            data={
                "workflow_id": workflow_id,
                "workflow_name": workflow.name if workflow else "Unknown",
                "execution_context": context or {},
                "context_provided": bool(context),
                "context_keys": list(context.keys()) if context else [],
                "initiated_via": "api_route",
                "nodes_count": len(workflow.nodes) if workflow else 0,
                "edges_count": len(workflow.edges) if workflow else 0,
                "request_metadata": {
                    "user_initiated": True,
                    "execution_type": "manual",
                    "has_custom_context": bool(context)
                }
            }
        )
        
        result = await workflow_executor.execute_workflow(workflow_id, context)
        
        # Log successful execution completion (additional to executor's logging)
        await _log_activity(
            ActivityType.WORKFLOW_COMPLETE,
            workflow_id=workflow_id,
            title=f"Workflow execution completed via API: {workflow.name if workflow else workflow_id[:8]}",
            description=f"API-initiated workflow execution completed successfully",
            data={
                "workflow_id": workflow_id,
                "result_status": result.get("status", "unknown"),
                "nodes_executed": len(result.get("results", {})),
                "execution_summary": {
                    "successful": result.get("status") == "completed",
                    "via_api": True,
                    "had_context": bool(context)
                },
                "api_response": result
            }
        )
        
        return result
        
    except ValueError as e:
        # Log workflow not found error
        await _log_activity(
            ActivityType.WORKFLOW_FAILED,
            workflow_id=workflow_id,
            title=f"Workflow execution failed: Not found",
            description=f"Workflow execution failed - workflow not found: {str(e)}",
            data={
                "error": str(e),
                "error_type": "ValueError",
                "workflow_id": workflow_id,
                "failure_reason": "workflow_not_found",
                "initiated_via": "api_route",
                "context_provided": bool(context)
            },
            success=False,
            error=str(e)
        )
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
        
    except Exception as e:
        # Log general execution failure
        await _log_activity(
            ActivityType.WORKFLOW_FAILED,
            workflow_id=workflow_id,
            title=f"Workflow execution failed: {type(e).__name__}",
            description=f"Workflow execution failed with error: {str(e)}",
            data={
                "error": str(e),
                "error_type": type(e).__name__,
                "workflow_id": workflow_id,
                "workflow_name": workflow.name if workflow else "Unknown",
                "failure_reason": "execution_error",
                "initiated_via": "api_route",
                "context_provided": bool(context),
                "execution_context": context or {}
            },
            success=False,
            error=str(e)
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow execution failed: {str(e)}"
        )


@router.get("/{workflow_id}/status")
async def get_workflow_status(workflow_id: str):
    """Get workflow execution status (placeholder for now)"""
    workflow = storage.get_workflow(workflow_id)
    if not workflow:
        # Log workflow status check failure
        await _log_activity(
            ActivityType.WORKFLOW_RETRIEVAL,
            workflow_id=workflow_id,
            title=f"Workflow status check failed: {workflow_id[:8]}",
            description=f"Attempted to check status of non-existent workflow {workflow_id}",
            data={
                "requested_workflow_id": workflow_id,
                "operation": "get_workflow_status",
                "result": "not_found",
                "context": "api_route"
            },
            success=False,
            error=f"Workflow {workflow_id} not found"
        )
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )
    
    status_response = {
        "workflow_id": workflow_id,
        "status": workflow.status.value,
        "last_updated": workflow.updated_at
    }
    
    # Log workflow status check
    await _log_activity(
        ActivityType.WORKFLOW_RETRIEVAL,
        workflow_id=workflow_id,
        title=f"Workflow status checked: {workflow.name}",
        description=f"Retrieved status for workflow '{workflow.name}': {workflow.status.value}",
        data={
            "workflow_name": workflow.name,
            "workflow_id": workflow_id,
            "current_status": workflow.status.value,
            "last_updated": str(workflow.updated_at) if workflow.updated_at else None,
            "created_at": str(workflow.created_at),
            "operation": "get_workflow_status",
            "result": "success",
            "context": "api_route",
            "status_metadata": {
                "nodes_count": len(workflow.nodes),
                "edges_count": len(workflow.edges),
                "has_been_updated": workflow.updated_at is not None
            }
        }
    )
    
    return status_response