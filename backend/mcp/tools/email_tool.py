from typing import Dict, Any
from backend.models.mcp_tool import MockMCPTool, MCPToolSchema
from backend.models.activity import ActivityCreate, ActivityType
from backend.storage.file_storage import file_storage as storage


class EmailTool(MockMCPTool):
    """Mock email tool for sending and reading emails"""
    
    def __init__(self):
        super().__init__("email_tool", "Email Tool", "communication")
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        action = params.get("action", "")
        
        if action == "send":
            return await self._send_email(params)
        elif action == "read":
            return await self._read_emails(params)
        else:
            raise ValueError(f"Unknown email action: {action}")
    
    async def _send_email(self, params: Dict[str, Any]) -> Dict[str, Any]:
        to = params.get("to", "")
        subject = params.get("subject", "")
        body = params.get("body", "")
        
        # Mock email sending
        return {
            "status": "sent",
            "message_id": "mock_email_123",
            "to": to,
            "subject": subject,
            "timestamp": "2023-01-01T12:00:00Z"
        }
    
    async def _read_emails(self, params: Dict[str, Any]) -> Dict[str, Any]:
        folder = params.get("folder", "inbox")
        limit = params.get("limit", 10)
        
        # Mock email reading
        mock_emails = [
            {
                "id": f"email_{i}",
                "from": f"sender{i}@example.com",
                "subject": f"Mock Email {i}",
                "body": f"This is mock email content {i}",
                "timestamp": "2023-01-01T12:00:00Z",
                "read": i % 2 == 0
            }
            for i in range(1, min(limit + 1, 6))
        ]
        
        return {
            "folder": folder,
            "emails": mock_emails,
            "total": len(mock_emails)
        }
    
    def get_schema(self) -> MCPToolSchema:
        return MCPToolSchema(
            input_schema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["send", "read"],
                        "description": "Action to perform"
                    },
                    "to": {
                        "type": "string",
                        "description": "Email recipient (for send action)"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject (for send action)"
                    },
                    "body": {
                        "type": "string",
                        "description": "Email body (for send action)"
                    },
                    "folder": {
                        "type": "string",
                        "description": "Email folder (for read action)",
                        "default": "inbox"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of emails to read",
                        "default": 10
                    }
                },
                "required": ["action"]
            },
            output_schema={
                "type": "object",
                "description": "Result of email operation"
            },
            description="Tool for sending and reading emails"
        )
    
    async def log_activity(self, action: str, params: Dict[str, Any], result: Dict[str, Any], success: bool, error: str = None):
        activity_data = ActivityCreate(
            type=ActivityType.TOOL_INVOCATION,
            tool_id=self.tool_id,
            title=f"Email {params.get('action', 'operation')}",
            description=f"Executed email tool with action: {params.get('action', 'unknown')}",
            data={"params": params, "result": result},
            success=success,
            error=error
        )
        storage.create_activity(activity_data)