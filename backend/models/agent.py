from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from backend.models.base import TimestampMixin, TriggerType


class Agent(TimestampMixin):
    id: str = Field(..., description="Unique identifier for the agent")
    name: str = Field(..., description="Human-readable name for the agent")
    description: Optional[str] = Field(None, description="Description of the agent's purpose")
    instructions: str = Field(..., description="Custom instructions/prompts for the agent")
    mcp_tool_permissions: List[str] = Field(default_factory=list, description="List of MCP tool IDs this agent can access")
    input_schema: Dict[str, Any] = Field(default_factory=dict, description="JSON schema for input validation")
    output_schema: Dict[str, Any] = Field(default_factory=dict, description="JSON schema for output validation")
    trigger_conditions: List[TriggerType] = Field(default_factory=list, description="When this agent can be triggered")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AgentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    instructions: str
    mcp_tool_permissions: List[str] = Field(default_factory=list)
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    trigger_conditions: List[TriggerType] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    mcp_tool_permissions: Optional[List[str]] = None
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    trigger_conditions: Optional[List[TriggerType]] = None
    metadata: Optional[Dict[str, Any]] = None