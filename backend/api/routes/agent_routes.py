from typing import List, Dict, Any
import traceback
from fastapi import APIRouter, HTTPException, status
from backend.models.agent import Agent, AgentCreate, AgentUpdate
from backend.models.activity import ActivityCreate, ActivityType
from backend.storage.file_storage import file_storage as storage

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


@router.post("/", response_model=Agent, status_code=status.HTTP_201_CREATED)
async def create_agent(agent_data: AgentCreate) -> Agent:
    """Create a new agent"""
    try:
        agent = storage.create_agent(agent_data)
        
        # Log comprehensive agent creation activity
        await _log_activity(
            ActivityType.AGENT_CREATION,
            agent_id=agent.id,
            title=f"Created agent: {agent.name}",
            description=f"New agent '{agent.name}' created with {len(agent.mcp_tool_permissions)} tool permissions",
            data={
                "agent_name": agent.name,
                "agent_id": agent.id,
                "agent_description": agent.description,
                "agent_instructions": agent.instructions,
                "mcp_tool_permissions": agent.mcp_tool_permissions,
                "tool_permissions_count": len(agent.mcp_tool_permissions),
                "input_schema": agent.input_schema,
                "output_schema": agent.output_schema,
                "trigger_conditions": agent.trigger_conditions,
                "trigger_conditions_count": len(agent.trigger_conditions) if agent.trigger_conditions else 0,
                "metadata": agent.metadata,
                "created_at": str(agent.created_at),
                "creation_context": "api_route",
                "agent_configuration": {
                    "has_description": bool(agent.description),
                    "has_custom_input_schema": bool(agent.input_schema),
                    "has_custom_output_schema": bool(agent.output_schema),
                    "has_triggers": bool(agent.trigger_conditions),
                    "has_metadata": bool(agent.metadata)
                }
            }
        )
        
        return agent
    except Exception as e:
        # Log agent creation failure
        print(f"Failed to create agent: {e}")
        traceback.print_exc()
        await _log_activity(
            ActivityType.AGENT_CREATION,
            title=f"Failed to create agent",
            description=f"Agent creation failed: {str(e)}",
            data={
                "error": str(e),
                "error_type": type(e).__name__,
                "attempted_agent_name": agent_data.name,
                "attempted_tool_permissions": agent_data.mcp_tool_permissions,
                "failure_context": "agent_creation_route",
                "input_data": agent_data.model_dump()
            },
            success=False,
            error=str(e)
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create agent: {str(e)}"
        )


@router.get("/", response_model=List[Agent])
async def list_agents() -> List[Agent]:
    """List all agents"""
    return storage.list_agents()


@router.get("/{agent_id}", response_model=Agent)
async def get_agent(agent_id: str) -> Agent:
    """Get a specific agent by ID"""
    agent = storage.get_agent(agent_id)
    if not agent:
        # Log agent not found
        await _log_activity(
            ActivityType.AGENT_RETRIEVAL,
            agent_id=agent_id,
            title=f"Agent not found: {agent_id[:8]}",
            description=f"Attempted to retrieve non-existent agent {agent_id}",
            data={
                "requested_agent_id": agent_id,
                "operation": "get_agent",
                "result": "not_found",
                "context": "api_route"
            },
            success=False,
            error=f"Agent {agent_id} not found"
        )
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )
    
    # Log successful agent retrieval
    await _log_activity(
        ActivityType.AGENT_RETRIEVAL,
        agent_id=agent_id,
        title=f"Retrieved agent: {agent.name}",
        description=f"Successfully retrieved agent '{agent.name}' with {len(agent.mcp_tool_permissions)} tools",
        data={
            "agent_name": agent.name,
            "agent_id": agent.id,
            "tool_permissions_count": len(agent.mcp_tool_permissions),
            "has_description": bool(agent.description),
            "created_at": str(agent.created_at),
            "updated_at": str(agent.updated_at) if agent.updated_at else None,
            "operation": "get_agent",
            "result": "success",
            "context": "api_route"
        }
    )
    
    return agent


@router.put("/{agent_id}", response_model=Agent)
async def update_agent(agent_id: str, agent_update: AgentUpdate) -> Agent:
    """Update an existing agent"""
    # Get original agent for comparison
    original_agent = storage.get_agent(agent_id)
    if not original_agent:
        # Log agent not found for update
        await _log_activity(
            ActivityType.AGENT_UPDATE,
            agent_id=agent_id,
            title=f"Agent update failed: {agent_id[:8]}",
            description=f"Attempted to update non-existent agent {agent_id}",
            data={
                "requested_agent_id": agent_id,
                "update_data": agent_update.model_dump(exclude_unset=True),
                "operation": "update_agent",
                "result": "not_found",
                "context": "api_route"
            },
            success=False,
            error=f"Agent {agent_id} not found"
        )
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )
    
    # Perform the update
    updated_agent = storage.update_agent(agent_id, agent_update)
    
    # Log comprehensive agent update activity
    update_fields = agent_update.model_dump(exclude_unset=True)
    await _log_activity(
        ActivityType.AGENT_UPDATE,
        agent_id=agent_id,
        title=f"Updated agent: {updated_agent.name}",
        description=f"Agent '{updated_agent.name}' updated - {len(update_fields)} field(s) modified",
        data={
            "agent_name": updated_agent.name,
            "agent_id": agent_id,
            "updated_fields": list(update_fields.keys()),
            "updated_fields_count": len(update_fields),
            "update_data": update_fields,
            "original_data": {
                "name": original_agent.name,
                "description": original_agent.description,
                "instructions": original_agent.instructions,
                "tool_permissions_count": len(original_agent.mcp_tool_permissions),
                "updated_at": str(original_agent.updated_at) if original_agent.updated_at else None
            },
            "new_data": {
                "name": updated_agent.name,
                "description": updated_agent.description,
                "instructions": updated_agent.instructions,
                "tool_permissions_count": len(updated_agent.mcp_tool_permissions),
                "updated_at": str(updated_agent.updated_at)
            },
            "operation": "update_agent",
            "result": "success",
            "context": "api_route",
            "changes_analysis": {
                "name_changed": original_agent.name != updated_agent.name,
                "description_changed": original_agent.description != updated_agent.description,
                "instructions_changed": original_agent.instructions != updated_agent.instructions,
                "tools_changed": set(original_agent.mcp_tool_permissions) != set(updated_agent.mcp_tool_permissions)
            }
        }
    )
    
    return updated_agent


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(agent_id: str):
    """Delete an agent"""
    # Get agent details before deletion for logging
    agent_to_delete = storage.get_agent(agent_id)
    
    success = storage.delete_agent(agent_id)
    if not success:
        # Log agent not found for deletion
        await _log_activity(
            ActivityType.AGENT_DELETION,
            agent_id=agent_id,
            title=f"Agent deletion failed: {agent_id[:8]}",
            description=f"Attempted to delete non-existent agent {agent_id}",
            data={
                "requested_agent_id": agent_id,
                "operation": "delete_agent",
                "result": "not_found",
                "context": "api_route"
            },
            success=False,
            error=f"Agent {agent_id} not found"
        )
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )
    
    # Log successful agent deletion with comprehensive details
    await _log_activity(
        ActivityType.AGENT_DELETION,
        agent_id=agent_id,
        title=f"Deleted agent: {agent_to_delete.name if agent_to_delete else 'Unknown'}",
        description=f"Successfully deleted agent '{agent_to_delete.name if agent_to_delete else 'Unknown'}'",
        data={
            "deleted_agent": {
                "agent_name": agent_to_delete.name if agent_to_delete else "Unknown",
                "agent_id": agent_id,
                "agent_description": agent_to_delete.description if agent_to_delete else None,
                "tool_permissions": agent_to_delete.mcp_tool_permissions if agent_to_delete else [],
                "tool_permissions_count": len(agent_to_delete.mcp_tool_permissions) if agent_to_delete else 0,
                "created_at": str(agent_to_delete.created_at) if agent_to_delete else None,
                "updated_at": str(agent_to_delete.updated_at) if agent_to_delete and agent_to_delete.updated_at else None
            },
            "operation": "delete_agent",
            "result": "success",
            "context": "api_route",
            "deletion_metadata": {
                "permanent": True,
                "cascade_effects": "workflows_using_agent_may_fail",
                "recovery_possible": False
            }
        }
    )