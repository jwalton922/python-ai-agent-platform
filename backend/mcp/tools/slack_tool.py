from typing import Dict, Any
from backend.models.mcp_tool import MockMCPTool, MCPToolSchema
from backend.models.activity import ActivityCreate, ActivityType
from backend.storage.file_storage import file_storage as storage


class SlackTool(MockMCPTool):
    """Mock Slack tool for posting and reading messages"""
    
    def __init__(self):
        super().__init__("slack_tool", "Slack Tool", "communication")
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        action = params.get("action", "")
        
        if action == "post":
            return await self._post_message(params)
        elif action == "read":
            return await self._read_messages(params)
        else:
            raise ValueError(f"Unknown Slack action: {action}")
    
    async def _post_message(self, params: Dict[str, Any]) -> Dict[str, Any]:
        channel = params.get("channel", "")
        message = params.get("message", "")
        
        # Mock message posting
        return {
            "status": "posted",
            "message_id": "mock_slack_msg_123",
            "channel": channel,
            "timestamp": "1672574400.123456",
            "permalink": f"https://example.slack.com/archives/{channel}/p1672574400123456"
        }
    
    async def _read_messages(self, params: Dict[str, Any]) -> Dict[str, Any]:
        channel = params.get("channel", "general")
        limit = params.get("limit", 10)
        
        # Mock message reading
        mock_messages = [
            {
                "id": f"msg_{i}",
                "user": f"user{i}",
                "text": f"This is mock Slack message {i}",
                "timestamp": f"167257440{i}.123456",
                "channel": channel
            }
            for i in range(1, min(limit + 1, 6))
        ]
        
        return {
            "channel": channel,
            "messages": mock_messages,
            "total": len(mock_messages)
        }
    
    def get_schema(self) -> MCPToolSchema:
        return MCPToolSchema(
            input_schema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["post", "read"],
                        "description": "Action to perform"
                    },
                    "channel": {
                        "type": "string",
                        "description": "Slack channel"
                    },
                    "message": {
                        "type": "string",
                        "description": "Message to post (for post action)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of messages to read",
                        "default": 10
                    }
                },
                "required": ["action", "channel"]
            },
            output_schema={
                "type": "object",
                "description": "Result of Slack operation"
            },
            description="Tool for posting and reading Slack messages"
        )
    
    async def log_activity(self, action: str, params: Dict[str, Any], result: Dict[str, Any], success: bool, error: str = None):
        activity_data = ActivityCreate(
            type=ActivityType.TOOL_INVOCATION,
            tool_id=self.tool_id,
            title=f"Slack {params.get('action', 'operation')}",
            description=f"Executed Slack tool with action: {params.get('action', 'unknown')}",
            data={"params": params, "result": result},
            success=success,
            error=error
        )
        storage.create_activity(activity_data)