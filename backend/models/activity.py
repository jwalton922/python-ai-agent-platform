from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from backend.models.base import TimestampMixin, ActivityType


class Activity(TimestampMixin):
    id: str = Field(..., description="Unique identifier for the activity")
    type: ActivityType = Field(..., description="Type of activity")
    agent_id: Optional[str] = Field(None, description="ID of the agent involved")
    workflow_id: Optional[str] = Field(None, description="ID of the workflow involved")
    tool_id: Optional[str] = Field(None, description="ID of the MCP tool involved")
    title: str = Field(..., description="Short title for the activity")
    description: str = Field(..., description="Detailed description of the activity")
    data: Dict[str, Any] = Field(default_factory=dict, description="Additional activity data")
    success: bool = Field(default=True, description="Whether the activity was successful")
    error: Optional[str] = Field(None, description="Error message if activity failed")


class ActivityCreate(BaseModel):
    type: ActivityType
    agent_id: Optional[str] = None
    workflow_id: Optional[str] = None
    tool_id: Optional[str] = None
    title: str
    description: str
    data: Dict[str, Any] = Field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None