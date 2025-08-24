from typing import Dict, List, Optional
from backend.models.mcp_tool import MockMCPTool, MCPTool
from backend.mcp.tools.email_tool import EmailTool
from backend.mcp.tools.slack_tool import SlackTool
from backend.mcp.tools.file_tool import FileTool


class ToolRegistry:
    """Registry for managing MCP tools"""
    
    def __init__(self):
        self.tools: Dict[str, MockMCPTool] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register the default set of mock tools"""
        tools = [
            EmailTool(),
            SlackTool(),
            FileTool(),
        ]
        
        for tool in tools:
            self.register_tool(tool)
    
    def register_tool(self, tool: MockMCPTool):
        """Register a new tool"""
        self.tools[tool.tool_id] = tool
    
    def get_tool(self, tool_id: str) -> Optional[MockMCPTool]:
        """Get a tool by its ID"""
        return self.tools.get(tool_id)
    
    def list_tools(self) -> List[MCPTool]:
        """List all available tools"""
        return [
            MCPTool(
                id=tool.tool_id,
                name=tool.name,
                category=tool.category,
                schema=tool.get_schema(),
                enabled=True
            )
            for tool in self.tools.values()
        ]


# Global tool registry instance
tool_registry = ToolRegistry()