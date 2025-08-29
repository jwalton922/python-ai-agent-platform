from typing import Dict, Any, List, Optional
import traceback
import json
import re
import uuid
import asyncio
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from backend.storage.file_storage import file_storage as storage
from backend.mcp.tool_registry import tool_registry
from backend.llm.factory import llm_provider
from backend.models.activity import ActivityCreate, ActivityType
from backend.api.routes.agent_workflow_integration import detect_workflow_request, extract_workflow_instructions

router = APIRouter()

# Store for async chat sessions
async_chat_sessions: Dict[str, Dict[str, Any]] = {}


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
    error: Optional[str] = Field(None, description="Error message if any")
    workflow_generated: Optional[Dict[str, Any]] = Field(None, description="Generated workflow if applicable")


class AsyncChatRequest(BaseModel):
    agent_id: str = Field(..., description="ID of the agent to chat with")
    message: str = Field(..., description="User message")
    chat_history: List[ChatMessage] = Field(default_factory=list, description="Previous chat messages")


class AsyncChatResponse(BaseModel):
    chat_id: str = Field(..., description="UUID for this chat session")
    status: str = Field(..., description="Status of the chat: pending, processing, completed, failed")
    message: str = Field(None, description="Status message")


class ChatStatusResponse(BaseModel):
    chat_id: str = Field(..., description="UUID for this chat session")
    status: str = Field(..., description="Status: pending, processing, completed, failed, timeout")
    progress: List[Dict[str, Any]] = Field(default_factory=list, description="Progress updates")
    result: Optional[ChatResponse] = Field(None, description="Final result when completed")
    error: Optional[str] = Field(None, description="Error message if failed")
    created_at: str = Field(..., description="When the chat was created")
    updated_at: str = Field(..., description="Last update time")


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
                        # Get the created workflow data with full details
                        workflow_data = {
                            "id": result.get("workflow_id"),
                            "name": result.get("workflow_name"),
                            "description": result.get("description"),
                            "node_count": result.get("node_count"),
                            "edge_count": result.get("edge_count"),
                            "nodes": result.get("nodes", []),
                            "edges": result.get("edges", []),
                            "variables": result.get("variables", [])
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


async def _process_chat_async(
    chat_id: str,
    agent_id: str,
    message: str,
    chat_history: List[ChatMessage]
):
    """Background task to process chat asynchronously"""
    try:
        # Update session status
        async_chat_sessions[chat_id]["status"] = "processing"
        async_chat_sessions[chat_id]["updated_at"] = datetime.utcnow().isoformat()
        
        # Log start of async chat processing
        await _log_activity_with_uuid(
            ActivityType.AGENT_EXECUTION,
            chat_id=chat_id,
            agent_id=agent_id,
            title=f"Async Chat Started",
            description=f"Started async chat processing for message: {message[:100]}...",
            data={
                "chat_id": chat_id,
                "user_message": message,
                "status": "processing",
                "chat_type": "async"
            }
        )
        
        # Get the agent
        agent = storage.get_agent(agent_id)
        if not agent:
            raise Exception(f"Agent {agent_id} not found")
        
        # Add progress update
        async_chat_sessions[chat_id]["progress"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "type": "agent_loaded",
            "message": f"Loaded agent: {agent.name}"
        })
        
        # Get available tools for the agent
        available_tools = []
        for tool_id in agent.mcp_tool_permissions:
            tool = tool_registry.get_tool(tool_id)
            if tool:
                available_tools.append(tool)
        
        # Format tools for LLM
        tool_descriptions = _format_tools_for_llm(available_tools)
        
        # Check if this is a workflow creation request
        is_workflow_request = await detect_workflow_request(message)
        
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
        
        # Log LLM call start
        await _log_activity_with_uuid(
            ActivityType.AGENT_EXECUTION,
            chat_id=chat_id,
            agent_id=agent_id,
            title="LLM Call Starting",
            description=f"Starting LLM call for chat {chat_id}",
            data={
                "chat_id": chat_id,
                "prompt_length": len(message),
                "system_prompt_length": len(system_prompt),
                "available_tools": len(available_tools)
            }
        )
        
        # Add progress update
        async_chat_sessions[chat_id]["progress"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "type": "llm_call_start",
            "message": "Calling LLM for response generation"
        })
        
        # Make the initial LLM call
        response = await llm_provider.generate_simple(
            prompt=message,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=1000
        )
        print("LLM response:", response )
        # Log LLM call completion
        await _log_activity_with_uuid(
            ActivityType.AGENT_EXECUTION,
            chat_id=chat_id,
            agent_id=agent_id,
            title="LLM Call Completed",
            description=f"LLM call completed for chat {chat_id}",
            data={
                "chat_id": chat_id,
                "response_length": len(response),
                "has_tool_calls": "TOOL_CALL:" in response
            }
        )
        
        # Add progress update
        async_chat_sessions[chat_id]["progress"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "type": "llm_call_complete",
            "message": f"LLM response received ({len(response)} chars)"
        })
        
        # Check if the response contains tool calls
        tool_results = []
        final_response = response
        
        if "TOOL_CALL:" in response:
            # Parse and execute tool calls
            tool_results = await _execute_tool_calls_async(response, available_tools, agent_id, chat_id)
            
            # If we have tool results, make a follow-up LLM call with the results
            if tool_results:
                tool_results_text = "\n".join([f"Tool: {tr['tool']} -> {tr['result']}" for tr in tool_results])
                follow_up_prompt = f"Based on the tool results:\n{tool_results_text}\n\nPlease provide your final response to the user's message: {message}"
                
                # Log follow-up LLM call
                await _log_activity_with_uuid(
                    ActivityType.AGENT_EXECUTION,
                    chat_id=chat_id,
                    agent_id=agent_id,
                    title="Follow-up LLM Call",
                    description=f"Making follow-up LLM call after tool execution",
                    data={
                        "chat_id": chat_id,
                        "tool_results_count": len(tool_results)
                    }
                )
                
                async_chat_sessions[chat_id]["progress"].append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "type": "follow_up_llm_call",
                    "message": "Processing tool results with LLM"
                })
                
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
                        workflow_data = {
                            "id": result.get("workflow_id"),
                            "name": result.get("workflow_name"),
                            "description": result.get("description"),
                            "node_count": result.get("node_count"),
                            "edge_count": result.get("edge_count"),
                            "nodes": result.get("nodes", []),
                            "edges": result.get("edges", []),
                            "variables": result.get("variables", [])
                        }
                        break
        
        # Create the final result
        result = ChatResponse(
            message=final_response if not workflow_data else f"I've created a workflow for you: {workflow_data.get('name', 'Generated Workflow')}. {workflow_data.get('description', '')}",
            tool_calls=tool_results,
            success=True,
            workflow_generated=workflow_data
        )
        
        # Update session with result
        async_chat_sessions[chat_id]["status"] = "completed"
        async_chat_sessions[chat_id]["result"] = result.dict(exclude_none=True)
        async_chat_sessions[chat_id]["updated_at"] = datetime.utcnow().isoformat()
        
        # Add final progress update
        async_chat_sessions[chat_id]["progress"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "type": "completed",
            "message": "Chat processing completed successfully"
        })
        
        # Log completion
        await _log_activity_with_uuid(
            ActivityType.AGENT_EXECUTION,
            chat_id=chat_id,
            agent_id=agent_id,
            title="Async Chat Completed",
            description=f"Async chat completed successfully",
            data={
                "chat_id": chat_id,
                "response_length": len(final_response),
                "tool_calls_count": len(tool_results),
                "workflow_generated": workflow_data is not None
            }
        )
        
    except Exception as e:
        # Log error
        error_msg = str(e)
        print(f"Async chat failed for {chat_id}: {error_msg}")
        traceback.print_exc()
        
        # Update session with error
        async_chat_sessions[chat_id]["status"] = "failed"
        async_chat_sessions[chat_id]["error"] = error_msg
        async_chat_sessions[chat_id]["updated_at"] = datetime.utcnow().isoformat()
        
        # Add error progress update
        async_chat_sessions[chat_id]["progress"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "type": "error",
            "message": f"Error: {error_msg}"
        })
        
        # Log failure
        await _log_activity_with_uuid(
            ActivityType.AGENT_EXECUTION,
            chat_id=chat_id,
            agent_id=agent_id,
            title="Async Chat Failed",
            description=f"Async chat failed: {error_msg}",
            data={
                "chat_id": chat_id,
                "error": error_msg,
                "error_type": type(e).__name__
            },
            success=False,
            error=error_msg
        )


async def _execute_tool_calls_async(response: str, available_tools, agent_id: str, chat_id: str) -> List[Dict[str, Any]]:
    """Parse and execute tool calls from LLM response with async logging"""
    tool_results = []
    
    # Simple parsing for TOOL_CALL:tool_name:action:{parameters}
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
            params = json.loads(params_json)
            
            # For workflow_tool, the action is already in the TOOL_CALL format
            if tool_id == "workflow_tool":
                if "action" not in params:
                    params["action"] = action
            else:
                params["action"] = action  # Add action to parameters for other tools
            
            # Log tool execution start
            await _log_activity_with_uuid(
                ActivityType.TOOL_INVOCATION,
                chat_id=chat_id,
                agent_id=agent_id,
                tool_id=tool_id,
                title=f"Tool Execution: {tool.name}",
                description=f"Executing {tool.name} with action: {action}",
                data={
                    "chat_id": chat_id,
                    "tool_name": tool.name,
                    "action": action,
                    "params": params
                }
            )
            
            # Add progress update with tool details
            if chat_id in async_chat_sessions:
                async_chat_sessions[chat_id]["progress"].append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "type": "tool_execution_start",
                    "message": f"Executing tool: {tool.name} ({action})",
                    "tool_call": {
                        "tool": tool_id,
                        "action": action,
                        "params": params,
                        "success": None,  # Will be updated when completed
                        "result": None,
                        "error": None
                    }
                })
            
            # Execute the tool
            result = await tool.execute(params)
            
            # Add progress update with completion details
            if chat_id in async_chat_sessions:
                async_chat_sessions[chat_id]["progress"].append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "type": "tool_execution_complete",
                    "message": f"Tool completed: {tool.name}",
                    "tool_call": {
                        "tool": tool_id,
                        "action": action,
                        "params": params,
                        "success": True,
                        "result": result,
                        "error": None
                    }
                })
            
            # Log tool execution completion
            await _log_activity_with_uuid(
                ActivityType.TOOL_INVOCATION,
                chat_id=chat_id,
                agent_id=agent_id,
                tool_id=tool_id,
                title=f"Tool Completed: {tool.name}",
                description=f"Tool {tool.name} completed successfully",
                data={
                    "chat_id": chat_id,
                    "result": result,
                    "result_size": len(str(result))
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
            error_msg = str(e)
            print(f"Tool invocation failed: {error_msg}")
            traceback.print_exc()
            
            # Add progress update for tool failure
            if chat_id in async_chat_sessions:
                async_chat_sessions[chat_id]["progress"].append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "type": "tool_execution_error",
                    "message": f"Tool failed: {tool.name if 'tool' in locals() and tool else tool_id}",
                    "tool_call": {
                        "tool": tool_id,
                        "action": action,
                        "params": params if 'params' in locals() else {},
                        "success": False,
                        "result": None,
                        "error": error_msg
                    }
                })
            
            # Log tool failure
            await _log_activity_with_uuid(
                ActivityType.TOOL_INVOCATION,
                chat_id=chat_id,
                agent_id=agent_id,
                tool_id=tool_id,
                title=f"Tool Failed: {tool.name if 'tool' in locals() and tool else tool_id}",
                description=f"Tool execution failed: {error_msg}",
                data={
                    "chat_id": chat_id,
                    "error": error_msg,
                    "action": action
                },
                success=False,
                error=error_msg
            )
            
            tool_results.append({
                "tool": tool_id,
                "action": action,
                "error": error_msg,
                "success": False
            })
    
    return tool_results


async def _log_activity_with_uuid(
    activity_type: ActivityType,
    title: str,
    description: str,
    data: Dict[str, Any] = None,
    chat_id: str = None,
    agent_id: str = None,
    workflow_id: str = None,
    tool_id: str = None,
    success: bool = True,
    error: str = None
):
    """Log an activity with chat UUID for tracking"""
    activity_data = ActivityCreate(
        type=activity_type,
        agent_id=agent_id,
        workflow_id=workflow_id,
        tool_id=tool_id,
        title=title,
        description=description,
        data={**(data or {}), "chat_id": chat_id} if chat_id else (data or {}),
        success=success,
        error=error
    )
    storage.create_activity(activity_data)


@router.post("/async", response_model=AsyncChatResponse)
async def chat_with_agent_async(
    request: AsyncChatRequest,
    background_tasks: BackgroundTasks
) -> AsyncChatResponse:
    """Start an async chat with an agent that processes in the background"""
    try:
        # Generate a unique chat ID
        chat_id = str(uuid.uuid4())
        
        # Initialize session
        async_chat_sessions[chat_id] = {
            "chat_id": chat_id,
            "status": "pending",
            "agent_id": request.agent_id,
            "message": request.message,
            "progress": [],
            "result": None,
            "error": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Add initial progress
        async_chat_sessions[chat_id]["progress"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "type": "created",
            "message": "Chat session created"
        })
        
        # Start background processing
        background_tasks.add_task(
            _process_chat_async,
            chat_id,
            request.agent_id,
            request.message,
            request.chat_history
        )
        
        # Log async chat creation
        await _log_activity_with_uuid(
            ActivityType.AGENT_EXECUTION,
            chat_id=chat_id,
            agent_id=request.agent_id,
            title="Async Chat Created",
            description=f"Created async chat session {chat_id}",
            data={
                "chat_id": chat_id,
                "user_message": request.message,
                "chat_type": "async"
            }
        )
        
        return AsyncChatResponse(
            chat_id=chat_id,
            status="pending",
            message="Chat processing started in background"
        )
        
    except Exception as e:
        error_msg = str(e)
        print(f"Failed to create async chat: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)


@router.get("/async/{chat_id}/status", response_model=ChatStatusResponse)
async def get_chat_status(chat_id: str) -> ChatStatusResponse:
    """Get the status of an async chat session"""
    if chat_id not in async_chat_sessions:
        raise HTTPException(status_code=404, detail=f"Chat session {chat_id} not found")
    
    session = async_chat_sessions[chat_id]
    
    # Check for timeout (90 seconds)
    created_at = datetime.fromisoformat(session["created_at"])
    if datetime.utcnow() - created_at > timedelta(seconds=90):
        if session["status"] in ["pending", "processing"]:
            session["status"] = "timeout"
            session["error"] = "Chat processing timed out after 90 seconds"
    
    return ChatStatusResponse(
        chat_id=session["chat_id"],
        status=session["status"],
        progress=session["progress"],
        result=ChatResponse(**session["result"]) if session["result"] else None,
        error=session.get("error"),
        created_at=session["created_at"],
        updated_at=session["updated_at"]
    )


@router.delete("/async/{chat_id}")
async def cleanup_chat_session(chat_id: str):
    """Clean up a completed or failed async chat session"""
    if chat_id in async_chat_sessions:
        del async_chat_sessions[chat_id]
        return {"message": f"Chat session {chat_id} cleaned up"}
    else:
        raise HTTPException(status_code=404, detail=f"Chat session {chat_id} not found")