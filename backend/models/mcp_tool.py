from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from backend.models.base import TimestampMixin


class MCPToolSchema(BaseModel):
    input_schema: Dict[str, Any] = Field(..., description="JSON schema for tool input")
    output_schema: Dict[str, Any] = Field(..., description="JSON schema for tool output")
    description: str = Field(..., description="Human-readable description of the tool")


class MCPTool(BaseModel):
    id: str = Field(..., description="Unique identifier for the tool")
    name: str = Field(..., description="Human-readable name")
    category: str = Field(..., description="Tool category (email, slack, file, etc.)")
    schema: MCPToolSchema = Field(..., description="Tool input/output schema")
    enabled: bool = Field(default=True, description="Whether the tool is available")


class MCPToolAction(TimestampMixin):
    id: str = Field(..., description="Unique identifier for the action")
    tool_id: str = Field(..., description="ID of the MCP tool used")
    agent_id: Optional[str] = Field(None, description="ID of the agent that used the tool")
    workflow_id: Optional[str] = Field(None, description="ID of the workflow this action is part of")
    action_type: str = Field(..., description="Type of action performed")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters passed to the tool")
    result: Optional[Dict[str, Any]] = Field(None, description="Result returned by the tool")
    success: bool = Field(..., description="Whether the action was successful")
    error: Optional[str] = Field(None, description="Error message if action failed")


class MockMCPTool(ABC):
    """Abstract base class for mock MCP tool implementations"""
    
    def __init__(self, tool_id: str, name: str, category: str):
        self.tool_id = tool_id
        self.name = name
        self.category = category
    
    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with given parameters"""
        pass
    
    @abstractmethod
    def get_schema(self) -> MCPToolSchema:
        """Get the tool's input/output schema"""
        pass
    
    async def log_activity(self, action: str, params: Dict[str, Any], result: Dict[str, Any], success: bool, error: Optional[str] = None):
        """Log activity to the activity feed"""
        # This will be implemented to post to the API endpoint
        pass