from typing import Dict, Any, List
import traceback
import json
import re
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.storage.file_storage import file_storage as storage
from backend.mcp.tool_registry import tool_registry
from backend.llm.factory import llm_provider
from backend.models.activity import ActivityCreate, ActivityType
from backend.api.routes.agent_workflow_integration import detect_workflow_request, extract_workflow_instructions

router = APIRouter()


class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    agent_id: str = Field(..., description="ID of the agent to chat with")
    message: str = Field(..., description="User message")
    chat_history: List[ChatMessage] = Field(default_factory=list, description="Previous chat messages")


class ChatResponse(BaseModel):
    message: str = Field(..., description="Agent response")
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list, description="Tools used")
    success: bool = Field(..., description="Whether the chat was successful")
    error: str = Field(None, description="Error message if any")
    workflow_generated: Dict[str, Any] = Field(None, description="Generated workflow if applicable")


@router.post("/", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest) -> ChatResponse:
    """Chat with a specific agent"""
    try:
        # Get the agent
        agent = storage.get_agent(request.agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {request.agent_id} not found")
        
        # Get available tools for the agent
        available_tools = []
        for tool_id in agent.mcp_tool_permissions:
            tool = tool_registry.get_tool(tool_id)
            if tool:
                available_tools.append(tool)
        
        # Format tools for LLM
        tool_descriptions = _format_tools_for_llm(available_tools)
        
        # Check if this is a workflow creation request
        is_workflow_request = await detect_workflow_request(request.message)
        
        # Build enhanced system prompt
        system_prompt = agent.instructions
        if is_workflow_request and "workflow_tool" in agent.mcp_tool_permissions:
            system_prompt += "\n\nThe user is asking you to create a workflow. You have access to the workflow_tool for this."
            system_prompt += "\n\nTo create a workflow, use the workflow tool with this format:"
            system_prompt += "\nTOOL_CALL:workflow_tool:create:{\"instructions\": \"user's workflow requirements\", \"workflow_name\": \"descriptive name\"}"
        
        if available_tools:
            system_prompt += f"\n\nYou have access to the following tools:\n{tool_descriptions}"
            system_prompt += "\n\nTo use a tool, respond with: TOOL_CALL:tool_name:action:{parameters as JSON}"
            system_prompt += "\nExample: TOOL_CALL:email_tool:read:{\"folder\":\"inbox\",\"limit\":5}"
        
        # Make the initial LLM call
        response = await llm_provider.generate_simple(
            prompt=request.message,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=1000
        )
        
        # Check if the response contains tool calls
        tool_results = []
        final_response = response
        
        if "TOOL_CALL:" in response:
            # Parse and execute tool calls
            tool_results = await _execute_tool_calls(response, available_tools, request.agent_id)
            
            # If we have tool results, make a follow-up LLM call with the results
            if tool_results:
                tool_results_text = "\n".join([f"Tool: {tr['tool']} -> {tr['result']}" for tr in tool_results])
                follow_up_prompt = f"Based on the tool results:\n{tool_results_text}\n\nPlease provide your final response to the user's message: {request.message}"
                
                final_response = await llm_provider.generate_simple(
                    prompt=follow_up_prompt,
                    system_prompt=agent.instructions + "\n\nProvide a helpful response based on the tool results.",
                    temperature=0.7,
                    max_tokens=1000
                )
        
        # Check if workflow was created through tool calls
        workflow_data = None
        if tool_results:
            for tool_result in tool_results:
                if tool_result.get("tool") == "workflow_tool" and tool_result.get("success"):
                    result = tool_result.get("result", {})
                    if result.get("workflow_id"):
                        # Get the created workflow data
                        workflow_data = {
                            "id": result.get("workflow_id"),
                            "name": result.get("workflow_name"),
                            "description": result.get("description"),
                            "node_count": result.get("node_count"),
                            "edge_count": result.get("edge_count")
                        }
                        break
        
        # Log comprehensive chat activity
        await _log_activity(
            ActivityType.AGENT_EXECUTION,
            agent_id=request.agent_id,
            title=f"Chat with {agent.name}",
            description=f"User chatted with agent {agent.name} - {len(tool_results)} tool(s) used, response length: {len(final_response)} chars",
            data={
                "user_message": request.message,
                "user_message_length": len(request.message),
                "agent_response": final_response,
                "agent_response_length": len(final_response),
                "tool_calls": tool_results,
                "tool_calls_count": len(tool_results),
                "chat_history_length": len(request.chat_history),
                "agent_name": agent.name,
                "agent_instructions": agent.instructions,
                "available_tools": agent.mcp_tool_permissions,
                "available_tools_count": len(agent.mcp_tool_permissions),
                "llm_provider": type(llm_provider).__name__,
                "system_prompt_used": system_prompt,
                "tools_used": [tr.get('tool') for tr in tool_results if tr.get('success')],
                "tools_failed": [tr.get('tool') for tr in tool_results if not tr.get('success')],
                "follow_up_call_made": len(tool_results) > 0,
                "chat_metadata": {
                    "agent_metadata": agent.metadata if hasattr(agent, 'metadata') else {},
                    "request_timestamp": str(storage._get_current_time() if hasattr(storage, '_get_current_time') else 'N/A'),
                    "chat_context": "direct_chat",
                    "interaction_type": "user_initiated"
                }
            }
        )
        
        return ChatResponse(
            message=final_response if not workflow_data else f"I've created a workflow for you: {workflow_data.get('name', 'Generated Workflow')}. {workflow_data.get('description', '')}",
            tool_calls=tool_results,
            success=True,
            workflow_generated=workflow_data
        )
        
    except Exception as e:
        # Log chat failure with comprehensive error details
        print(f"Chat with agent failed: {e}")
        traceback.print_exc()
        await _log_activity(
            ActivityType.AGENT_EXECUTION,
            agent_id=request.agent_id if request else "unknown",
            title=f"Chat Failed",
            description=f"Chat with agent failed: {str(e)}",
            data={
                "error": str(e),
                "error_type": type(e).__name__,
                "user_message": request.message if request else "N/A",
                "agent_id": request.agent_id if request else "unknown",
                "chat_history_length": len(request.chat_history) if request else 0,
                "failure_context": "chat_route_exception",
                "llm_provider": type(llm_provider).__name__ if 'llm_provider' in locals() else "unknown",
                "available_tools": agent.mcp_tool_permissions if 'agent' in locals() and agent else [],
                "error_metadata": {
                    "occurred_in": "chat_with_agent_route",
                    "agent_loaded": 'agent' in locals() and agent is not None,
                    "tools_loaded": 'available_tools' in locals() and len(available_tools) > 0,
                    "system_prompt_built": 'system_prompt' in locals()
                }
            },
            success=False,
            error=str(e)
        )
        
        return ChatResponse(
            message=f"Sorry, I encountered an error: {str(e)}",
            tool_calls=[],
            success=False,
            error=str(e)
        )


def _format_tools_for_llm(tools) -> str:
    """Format tools description for LLM"""
    if not tools:
        return ""
    
    descriptions = []
    for tool in tools:
        schema = tool.get_schema()
        description = schema.description if hasattr(schema, 'description') else 'Tool for various actions'
        
        # For email tool, list known actions
        if tool.tool_id == "email_tool":
            actions = "send, read"
        elif tool.tool_id == "slack_tool":
            actions = "post, read"
        elif tool.tool_id == "file_tool":
            actions = "read, write, list"
        elif tool.tool_id == "workflow_tool":
            actions = "create, list, get, execute, delete"
        else:
            actions = "execute"
            
        descriptions.append(f"- {tool.name} ({tool.tool_id}): {description} [Actions: {actions}]")
    
    return "\n".join(descriptions)


async def _execute_tool_calls(response: str, available_tools, agent_id: str) -> List[Dict[str, Any]]:
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
            
            # For workflow_tool, the action is already in the TOOL_CALL format
            if tool_id == "workflow_tool":
                if "action" not in params:
                    params["action"] = action
            else:
                params["action"] = action  # Add action to parameters for other tools
            
            # Execute the tool
            result = await tool.execute(params)
            
            # Log comprehensive tool execution with all inputs
            await _log_activity(
                ActivityType.TOOL_INVOCATION,
                agent_id=agent_id,
                tool_id=tool_id,
                title=f"Executed {tool.name}",
                description=f"Agent executed {tool.name} with action: {action} - Input params: {len(params)} fields, Result: {len(str(result))} chars",
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
                        "parsed_successfully": True,
                        "action_included": "action" in params
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
                        "called_from": "chat_route",
                        "agent_context": True,
                        "user_triggered": True,
                        "chat_interaction": True,
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
            print(f"Tool invocation failed: {e}")
            traceback.print_exc()
            await _log_activity(
                ActivityType.TOOL_INVOCATION,
                agent_id=agent_id,
                tool_id=tool_id,
                title=f"Tool execution failed: {tool.name if 'tool' in locals() and tool else tool_id}",
                description=f"Chat tool {tool_id} failed with action: {action} - Error: {str(e)}",
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
                        "parsing_error": str(e) if 'params' not in locals() else None,
                        "action_included": "action" in params if 'params' in locals() and isinstance(params, dict) else False
                    },
                    "tool_schema": {
                        "schema": tool.get_schema().model_dump() if 'tool' in locals() and tool and hasattr(tool.get_schema(), 'model_dump') else "Schema unavailable",
                        "tool_description": getattr(tool.get_schema(), 'description', 'No description available') if 'tool' in locals() and tool else "Tool not found",
                        "tool_available": 'tool' in locals() and tool is not None
                    },
                    "failure_context": {
                        "called_from": "chat_route",
                        "agent_context": True,
                        "user_triggered": True,
                        "chat_interaction": True,
                        "llm_initiated": True,
                        "failure_stage": "tool_execution" if 'tool' in locals() and tool else "tool_lookup_or_parsing"
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