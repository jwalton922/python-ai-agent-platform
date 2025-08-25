from typing import List, Dict, Any
import traceback
from fastapi import APIRouter, HTTPException, status
from backend.models.mcp_tool import MCPTool, MCPToolAction
from backend.models.activity import ActivityCreate, ActivityType
from backend.mcp.tool_registry import tool_registry
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


@router.get("/", response_model=List[MCPTool])
async def list_mcp_tools() -> List[MCPTool]:
    """List all available MCP tools"""
    return tool_registry.list_tools()


@router.get("/{tool_id}/schema")
async def get_tool_schema(tool_id: str):
    """Get tool input/output schema"""
    tool = tool_registry.get_tool(tool_id)
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool {tool_id} not found"
        )
    return tool.get_schema()


@router.post("/{tool_id}/action")
async def execute_tool_action(
    tool_id: str,
    params: Dict[str, Any],
    agent_id: str = None,
    workflow_id: str = None
):
    """Execute an MCP tool action and log it"""
    tool = tool_registry.get_tool(tool_id)
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool {tool_id} not found"
        )
    
    try:
        result = await tool.execute(params)
        
        # Log comprehensive tool execution with all inputs via direct API route
        await _log_activity(
            ActivityType.TOOL_INVOCATION,
            agent_id=agent_id,
            workflow_id=workflow_id,
            tool_id=tool_id,
            title=f"Direct execution: {tool.name}",
            description=f"Direct API execution of {tool.name} - Input params: {len(params)} fields, Result: {len(str(result))} chars",
            data={
                "tool_name": tool.name,
                "tool_id": tool_id,
                "action": "direct_execute",
                "all_input_params": params,
                "input_params_detailed": {
                    "param_count": len(params) if isinstance(params, dict) else 0,
                    "param_keys": list(params.keys()) if isinstance(params, dict) else [],
                    "param_types": {k: type(v).__name__ for k, v in params.items()} if isinstance(params, dict) else {},
                    "param_sizes": {k: len(str(v)) for k, v in params.items()} if isinstance(params, dict) else {},
                    "has_sensitive_data": any(key.lower() in ['password', 'token', 'key', 'secret'] for key in (params.keys() if isinstance(params, dict) else [])),
                    "raw_params_provided": True,
                    "parsing_successful": True
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
                    "called_from": "direct_mcp_api",
                    "agent_context": agent_id is not None,
                    "workflow_context": workflow_id is not None,
                    "direct_api_call": True,
                    "user_triggered": True
                }
            }
        )
        
        return {
            "tool_id": tool_id,
            "success": True,
            "result": result
        }
        
    except Exception as e:
        # Log comprehensive tool failure with all inputs
        print(f"MCP tool execution failed: {e}")
        traceback.print_exc()
        await _log_activity(
            ActivityType.TOOL_INVOCATION,
            agent_id=agent_id,
            workflow_id=workflow_id,
            tool_id=tool_id,
            title=f"Direct execution failed: {tool.name}",
            description=f"Direct API execution of {tool.name} failed - Error: {str(e)}",
            data={
                "tool_name": tool.name,
                "tool_id": tool_id,
                "action": "direct_execute",
                "error": str(e),
                "error_type": type(e).__name__,
                "all_input_params": params,
                "input_params_detailed": {
                    "param_count": len(params) if isinstance(params, dict) else 0,
                    "param_keys": list(params.keys()) if isinstance(params, dict) else [],
                    "param_types": {k: type(v).__name__ for k, v in params.items()} if isinstance(params, dict) else {},
                    "param_sizes": {k: len(str(v)) for k, v in params.items()} if isinstance(params, dict) else {},
                    "has_sensitive_data": any(key.lower() in ['password', 'token', 'key', 'secret'] for key in (params.keys() if isinstance(params, dict) else [])),
                    "raw_params_provided": True,
                    "parsing_successful": True
                },
                "tool_schema": {
                    "schema": tool.get_schema().model_dump() if hasattr(tool.get_schema(), 'model_dump') else str(tool.get_schema()),
                    "tool_description": getattr(tool.get_schema(), 'description', 'No description available'),
                    "tool_available": True
                },
                "failure_context": {
                    "called_from": "direct_mcp_api",
                    "agent_context": agent_id is not None,
                    "workflow_context": workflow_id is not None,
                    "direct_api_call": True,
                    "user_triggered": True,
                    "failure_stage": "tool_execution"
                }
            },
            success=False,
            error=str(e)
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tool execution failed: {str(e)}"
        )