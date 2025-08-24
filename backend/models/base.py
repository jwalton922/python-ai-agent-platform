from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class TimestampMixin(BaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class TriggerType(str, Enum):
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"


class WorkflowStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ActivityType(str, Enum):
    AGENT_EXECUTION = "agent_execution"
    AGENT_CREATION = "agent_creation"
    AGENT_RETRIEVAL = "agent_retrieval"
    AGENT_UPDATE = "agent_update"
    AGENT_DELETION = "agent_deletion"
    TOOL_INVOCATION = "tool_invocation"
    WORKFLOW_START = "workflow_start"
    WORKFLOW_COMPLETE = "workflow_complete"
    WORKFLOW_FAILED = "workflow_failed"
    WORKFLOW_CREATION = "workflow_creation"
    WORKFLOW_RETRIEVAL = "workflow_retrieval"
    WORKFLOW_UPDATE = "workflow_update"
    WORKFLOW_DELETION = "workflow_deletion"