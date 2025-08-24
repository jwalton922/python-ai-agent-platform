from typing import Dict, Any
from backend.models.mcp_tool import MockMCPTool, MCPToolSchema
from backend.models.activity import ActivityCreate, ActivityType
from backend.storage.file_storage import file_storage as storage


class FileTool(MockMCPTool):
    """Mock file system tool for reading and writing files"""
    
    def __init__(self):
        super().__init__("file_tool", "File System Tool", "filesystem")
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        action = params.get("action", "")
        
        if action == "read":
            return await self._read_file(params)
        elif action == "write":
            return await self._write_file(params)
        elif action == "list":
            return await self._list_files(params)
        else:
            raise ValueError(f"Unknown file action: {action}")
    
    async def _read_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        filepath = params.get("filepath", "")
        
        # Mock file reading
        return {
            "filepath": filepath,
            "content": f"Mock content of {filepath}",
            "size": 1024,
            "modified": "2023-01-01T12:00:00Z"
        }
    
    async def _write_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        filepath = params.get("filepath", "")
        content = params.get("content", "")
        
        # Mock file writing
        return {
            "filepath": filepath,
            "status": "written",
            "size": len(content),
            "modified": "2023-01-01T12:00:00Z"
        }
    
    async def _list_files(self, params: Dict[str, Any]) -> Dict[str, Any]:
        directory = params.get("directory", "/")
        
        # Mock directory listing
        mock_files = [
            {
                "name": f"file{i}.txt",
                "type": "file",
                "size": 1024 * i,
                "modified": "2023-01-01T12:00:00Z"
            }
            for i in range(1, 6)
        ]
        
        return {
            "directory": directory,
            "files": mock_files,
            "total": len(mock_files)
        }
    
    def get_schema(self) -> MCPToolSchema:
        return MCPToolSchema(
            input_schema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["read", "write", "list"],
                        "description": "File operation to perform"
                    },
                    "filepath": {
                        "type": "string",
                        "description": "Path to the file (for read/write actions)"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write (for write action)"
                    },
                    "directory": {
                        "type": "string",
                        "description": "Directory to list (for list action)",
                        "default": "/"
                    }
                },
                "required": ["action"]
            },
            output_schema={
                "type": "object",
                "description": "Result of file operation"
            },
            description="Tool for file system operations"
        )
    
    async def log_activity(self, action: str, params: Dict[str, Any], result: Dict[str, Any], success: bool, error: str = None):
        activity_data = ActivityCreate(
            type=ActivityType.TOOL_INVOCATION,
            tool_id=self.tool_id,
            title=f"File {params.get('action', 'operation')}",
            description=f"Executed file tool with action: {params.get('action', 'unknown')}",
            data={"params": params, "result": result},
            success=success,
            error=error
        )
        storage.create_activity(activity_data)