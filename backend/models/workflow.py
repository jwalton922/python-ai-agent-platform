from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from backend.models.base import TimestampMixin, WorkflowStatus, TriggerType


class WorkflowNode(BaseModel):
    id: str = Field(..., description="Unique identifier for the node")
    agent_id: str = Field(..., description="ID of the agent to execute")
    position: Dict[str, float] = Field(..., description="Position in the DAG editor (x, y coordinates)")
    config: Dict[str, Any] = Field(default_factory=dict, description="Node-specific configuration")


class WorkflowEdge(BaseModel):
    id: str = Field(..., description="Unique identifier for the edge")
    source_node_id: str = Field(..., description="Source node ID")
    target_node_id: str = Field(..., description="Target node ID")
    condition: Optional[str] = Field(None, description="Conditional logic for this edge")
    data_mapping: Dict[str, str] = Field(default_factory=dict, description="How to map data from source to target")


class Workflow(TimestampMixin):
    id: str = Field(..., description="Unique identifier for the workflow")
    name: str = Field(..., description="Human-readable name for the workflow")
    description: Optional[str] = Field(None, description="Description of the workflow's purpose")
    nodes: List[WorkflowNode] = Field(default_factory=list, description="Nodes in the workflow DAG")
    edges: List[WorkflowEdge] = Field(default_factory=list, description="Edges connecting nodes")
    trigger_conditions: List[TriggerType] = Field(default_factory=list, description="How this workflow can be triggered")
    status: WorkflowStatus = Field(default=WorkflowStatus.IDLE, description="Current workflow status")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class WorkflowCreate(BaseModel):
    name: str
    description: Optional[str] = None
    nodes: List[WorkflowNode] = Field(default_factory=list)
    edges: List[WorkflowEdge] = Field(default_factory=list)
    trigger_conditions: List[TriggerType] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    nodes: Optional[List[WorkflowNode]] = None
    edges: Optional[List[WorkflowEdge]] = None
    trigger_conditions: Optional[List[TriggerType]] = None
    metadata: Optional[Dict[str, Any]] = None


class WorkflowExecution(TimestampMixin):
    id: str = Field(..., description="Unique identifier for the execution")
    workflow_id: str = Field(..., description="ID of the workflow being executed")
    status: WorkflowStatus = Field(..., description="Current execution status")
    context: Dict[str, Any] = Field(default_factory=dict, description="Execution context and data")
    result: Optional[Dict[str, Any]] = Field(None, description="Final execution result")
    error: Optional[str] = Field(None, description="Error message if execution failed")