from typing import List, Dict, Any, Optional, Union, Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator
from enum import Enum
from datetime import datetime
from backend.models.base import TimestampMixin, WorkflowStatus, TriggerType


class NodeType(str, Enum):
    AGENT = "agent"
    DECISION = "decision"
    TRANSFORM = "transform"
    LOOP = "loop"
    PARALLEL = "parallel"
    EXTERNAL_TRIGGER = "external_trigger"
    HUMAN_IN_LOOP = "human_in_loop"
    STORAGE = "storage"
    ERROR_HANDLER = "error_handler"
    AGGREGATOR = "aggregator"
    SUB_WORKFLOW = "sub_workflow"


class ExecutionMode(str, Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    STREAMING = "streaming"
    BATCH = "batch"
    EVENT_DRIVEN = "event_driven"


class RetryStrategy(str, Enum):
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIXED = "fixed"
    NONE = "none"


class ErrorHandlingStrategy(str, Enum):
    FAIL = "fail"
    CONTINUE = "continue"
    FALLBACK = "fallback"
    RETRY_THEN_FAIL = "retry_then_fail"
    RETRY_THEN_CONTINUE = "retry_then_continue"


class WaitStrategy(str, Enum):
    ALL = "all"
    ANY = "any"
    RACE = "race"
    N_OF_M = "n_of_m"


class AggregationMethod(str, Enum):
    MERGE = "merge"
    CONCAT = "concat"
    CUSTOM = "custom"
    FIRST = "first"
    LAST = "last"
    AVERAGE = "average"
    SUM = "sum"


class StorageOperation(str, Enum):
    SAVE = "save"
    LOAD = "load"
    UPDATE = "update"
    DELETE = "delete"
    APPEND = "append"


class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class RetryConfig(BaseModel):
    max_attempts: int = Field(default=3, ge=0, le=10)
    strategy: RetryStrategy = Field(default=RetryStrategy.EXPONENTIAL)
    initial_delay_ms: int = Field(default=1000, ge=0)
    max_delay_ms: int = Field(default=60000, ge=0)
    backoff_multiplier: float = Field(default=2.0, ge=1.0)


class TokenLimits(BaseModel):
    max_tokens: Optional[int] = Field(default=None, ge=0)
    max_cost: Optional[float] = Field(default=None, ge=0)
    warn_at_percentage: float = Field(default=0.8, ge=0, le=1)


class DataMapping(BaseModel):
    source: str = Field(..., description="Source path using dot notation or JSONPath")
    target: str = Field(..., description="Target path using dot notation")
    transform: Optional[str] = Field(default=None, description="Optional transformation expression")
    default: Any = Field(default=None, description="Default value if source is missing")


class ConditionBranch(BaseModel):
    name: str = Field(..., description="Branch name")
    expression: str = Field(..., description="Condition expression")
    target: str = Field(..., description="Target node ID")
    priority: int = Field(default=0, description="Evaluation priority")


class LoopConfig(BaseModel):
    type: Literal["for_each", "while", "do_while", "range"] = Field(...)
    source: Optional[str] = Field(default=None, description="Source for iteration (array path or range)")
    condition: Optional[str] = Field(default=None, description="Loop condition for while loops")
    max_iterations: int = Field(default=1000, ge=1)
    parallel: bool = Field(default=False)
    accumulator: Optional[str] = Field(default=None, description="Variable to accumulate results")
    break_condition: Optional[str] = Field(default=None)
    continue_condition: Optional[str] = Field(default=None)


class ParallelBranch(BaseModel):
    id: str = Field(...)
    name: str = Field(...)
    nodes: List[str] = Field(..., description="Node IDs in this branch")
    timeout_ms: Optional[int] = Field(default=None)
    required: bool = Field(default=True, description="Whether this branch must succeed")


class HumanInputConfig(BaseModel):
    ui_template: Optional[str] = Field(default=None, description="HTML/Markdown template for UI")
    notification_channels: List[str] = Field(default_factory=list)
    timeout_ms: Optional[int] = Field(default=None)
    escalation_after_ms: Optional[int] = Field(default=None)
    escalation_to: Optional[List[str]] = Field(default=None)
    input_schema: Optional[Dict[str, Any]] = Field(default=None)
    approval_options: List[str] = Field(default=["approve", "reject", "modify"])


class StorageConfig(BaseModel):
    operation: StorageOperation = Field(...)
    backend: Literal["memory", "file", "database", "redis", "s3"] = Field(default="memory")
    key: str = Field(..., description="Storage key or key generation expression")
    ttl_seconds: Optional[int] = Field(default=None)
    encryption: bool = Field(default=False)
    versioning: bool = Field(default=False)
    compression: bool = Field(default=False)


class NodeConfig(BaseModel):
    model_config = ConfigDict(extra="allow")
    
    timeout_ms: Optional[int] = Field(default=120000, ge=0)
    retry: Optional[RetryConfig] = Field(default=None)
    error_handling: ErrorHandlingStrategy = Field(default=ErrorHandlingStrategy.FAIL)
    token_limits: Optional[TokenLimits] = Field(default=None)
    cache_results: bool = Field(default=False)
    cache_ttl_seconds: Optional[int] = Field(default=None)
    
    # Node-specific configurations
    agent_config: Optional[Dict[str, Any]] = Field(default=None)
    decision_config: Optional[Dict[str, Any]] = Field(default=None)
    transform_config: Optional[Dict[str, Any]] = Field(default=None)
    loop_config: Optional[LoopConfig] = Field(default=None)
    parallel_config: Optional[Dict[str, Any]] = Field(default=None)
    human_config: Optional[HumanInputConfig] = Field(default=None)
    storage_config: Optional[StorageConfig] = Field(default=None)


class EnhancedWorkflowNode(BaseModel):
    id: str = Field(..., description="Unique identifier for the node")
    type: NodeType = Field(..., description="Type of workflow node")
    name: str = Field(..., description="Human-readable name")
    description: Optional[str] = Field(default=None)
    
    # Position for UI rendering
    position: Dict[str, float] = Field(default_factory=dict, description="Position in the DAG editor")
    
    # Core configuration
    config: NodeConfig = Field(default_factory=NodeConfig)
    
    # Agent-specific (when type == AGENT)
    agent_id: Optional[str] = Field(default=None)
    instructions_override: Optional[str] = Field(default=None)
    instructions_append: Optional[str] = Field(default=None)
    
    # Decision-specific (when type == DECISION)
    condition_branches: Optional[List[ConditionBranch]] = Field(default=None)
    default_target: Optional[str] = Field(default=None)
    
    # Transform-specific (when type == TRANSFORM)
    transformations: Optional[List[DataMapping]] = Field(default=None)
    validation_schema: Optional[Dict[str, Any]] = Field(default=None)
    
    # Loop-specific (when type == LOOP)
    loop_config: Optional[LoopConfig] = Field(default=None)
    loop_body_nodes: Optional[List[str]] = Field(default=None)
    
    # Parallel-specific (when type == PARALLEL)
    parallel_branches: Optional[List[ParallelBranch]] = Field(default=None)
    wait_strategy: Optional[WaitStrategy] = Field(default=None)
    wait_count: Optional[int] = Field(default=None)
    
    # External trigger-specific
    trigger_type: Optional[TriggerType] = Field(default=None)
    trigger_config: Optional[Dict[str, Any]] = Field(default=None)
    
    # Error handler-specific
    error_types: Optional[List[str]] = Field(default=None)
    fallback_node: Optional[str] = Field(default=None)
    
    # Aggregator-specific
    aggregation_method: Optional[AggregationMethod] = Field(default=None)
    aggregation_config: Optional[Dict[str, Any]] = Field(default=None)
    
    # Sub-workflow specific
    sub_workflow_id: Optional[str] = Field(default=None)
    sub_workflow_version: Optional[str] = Field(default=None)
    
    # Input/Output mapping
    input_mapping: List[DataMapping] = Field(default_factory=list)
    output_mapping: List[DataMapping] = Field(default_factory=list)
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EnhancedWorkflowEdge(BaseModel):
    id: str = Field(...)
    source_node_id: str = Field(...)
    target_node_id: str = Field(...)
    
    # Conditional execution
    condition: Optional[str] = Field(default=None, description="Condition expression for edge traversal")
    priority: int = Field(default=0, description="Priority for condition evaluation")
    
    # Data flow
    data_mapping: List[DataMapping] = Field(default_factory=list)
    data_filter: Optional[str] = Field(default=None, description="Filter expression for data")
    data_transform: Optional[str] = Field(default=None, description="Transform expression for data")
    
    # Edge metadata
    label: Optional[str] = Field(default=None)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowVariable(BaseModel):
    name: str = Field(...)
    type: str = Field(..., description="Variable type (string, number, boolean, object, array)")
    required: bool = Field(default=False)
    default: Any = Field(default=None)
    description: Optional[str] = Field(default=None)
    validation: Optional[str] = Field(default=None, description="Validation expression")
    scope: Literal["global", "local"] = Field(default="global")


class WorkflowSettings(BaseModel):
    max_execution_time_ms: int = Field(default=300000, ge=0)
    max_total_tokens: Optional[int] = Field(default=None, ge=0)
    max_parallel_executions: int = Field(default=5, ge=1)
    priority: Literal["low", "medium", "high", "critical"] = Field(default="medium")
    
    # Resource limits
    max_memory_mb: Optional[int] = Field(default=None)
    max_api_calls: Optional[int] = Field(default=None)
    rate_limit_per_minute: Optional[int] = Field(default=None)
    
    # Execution behavior
    continue_on_error: bool = Field(default=False)
    save_intermediate_state: bool = Field(default=True)
    enable_checkpoints: bool = Field(default=True)
    checkpoint_interval_ms: int = Field(default=60000)
    
    # Cost management
    max_cost_usd: Optional[float] = Field(default=None)
    cost_warning_threshold: float = Field(default=0.8)


class WorkflowMonitoring(BaseModel):
    log_level: LogLevel = Field(default=LogLevel.INFO)
    trace_sampling: float = Field(default=0.1, ge=0, le=1)
    metrics_enabled: bool = Field(default=True)
    capture_inputs: bool = Field(default=True)
    capture_outputs: bool = Field(default=True)
    capture_intermediate: bool = Field(default=False)
    
    # Alerting
    alert_channels: List[str] = Field(default_factory=list)
    sla_ms: Optional[int] = Field(default=None)
    error_rate_threshold: float = Field(default=0.1, ge=0, le=1)


class WorkflowTesting(BaseModel):
    test_data: List[Dict[str, Any]] = Field(default_factory=list)
    mocks: List[Dict[str, Any]] = Field(default_factory=list)
    assertions: List[Dict[str, Any]] = Field(default_factory=list)
    coverage_threshold: float = Field(default=0.8, ge=0, le=1)


class EnhancedWorkflow(TimestampMixin):
    id: str = Field(...)
    name: str = Field(...)
    description: Optional[str] = Field(default=None)
    version: str = Field(default="1.0.0")
    
    # Workflow structure
    nodes: List[EnhancedWorkflowNode] = Field(default_factory=list)
    edges: List[EnhancedWorkflowEdge] = Field(default_factory=list)
    
    # Variables and configuration
    variables: List[WorkflowVariable] = Field(default_factory=list)
    settings: WorkflowSettings = Field(default_factory=WorkflowSettings)
    
    # Execution
    trigger_conditions: List[TriggerType] = Field(default_factory=list)
    trigger_config: Dict[str, Any] = Field(default_factory=dict)
    execution_mode: ExecutionMode = Field(default=ExecutionMode.SEQUENTIAL)
    
    # Error handling
    global_error_handler: Optional[str] = Field(default=None, description="Node ID of global error handler")
    error_handling_strategy: ErrorHandlingStrategy = Field(default=ErrorHandlingStrategy.RETRY_THEN_FAIL)
    max_retries: int = Field(default=3)
    
    # Monitoring and testing
    monitoring: WorkflowMonitoring = Field(default_factory=WorkflowMonitoring)
    testing: Optional[WorkflowTesting] = Field(default=None)
    
    # State and metadata
    status: WorkflowStatus = Field(default=WorkflowStatus.IDLE)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Relationships
    parent_workflow_id: Optional[str] = Field(default=None)
    child_workflow_ids: List[str] = Field(default_factory=list)
    
    @field_validator('nodes')
    def validate_node_types(cls, nodes):
        for node in nodes:
            if node.type == NodeType.AGENT and not node.agent_id:
                raise ValueError(f"Node {node.id} is of type AGENT but missing agent_id")
            if node.type == NodeType.DECISION and not node.condition_branches:
                raise ValueError(f"Node {node.id} is of type DECISION but missing condition_branches")
            if node.type == NodeType.LOOP and not node.loop_config:
                raise ValueError(f"Node {node.id} is of type LOOP but missing loop_config")
        return nodes


class WorkflowExecutionState(BaseModel):
    execution_id: str = Field(...)
    workflow_id: str = Field(...)
    workflow_version: str = Field(...)
    
    # Execution status
    status: WorkflowStatus = Field(...)
    started_at: datetime = Field(...)
    completed_at: Optional[datetime] = Field(default=None)
    
    # Node states
    node_states: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    completed_nodes: List[str] = Field(default_factory=list)
    pending_nodes: List[str] = Field(default_factory=list)
    failed_nodes: List[str] = Field(default_factory=list)
    
    # Execution context
    global_variables: Dict[str, Any] = Field(default_factory=dict)
    node_outputs: Dict[str, Any] = Field(default_factory=dict)
    
    # Checkpoints
    checkpoints: List[Dict[str, Any]] = Field(default_factory=list)
    last_checkpoint: Optional[datetime] = Field(default=None)
    
    # Metrics
    total_tokens_used: int = Field(default=0)
    total_cost_usd: float = Field(default=0.0)
    total_api_calls: int = Field(default=0)
    
    # Error information
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    last_error: Optional[str] = Field(default=None)


class WorkflowExecutionRequest(BaseModel):
    workflow_id: Optional[str] = Field(default=None, description="Optional workflow ID - will use URL parameter if not provided")
    input: Dict[str, Any] = Field(default_factory=dict)
    overrides: Optional[Dict[str, Any]] = Field(default=None)
    debug: bool = Field(default=False)
    dry_run: bool = Field(default=False)
    checkpoint_id: Optional[str] = Field(default=None, description="Resume from checkpoint")
    timeout_override_ms: Optional[int] = Field(default=None)


class WorkflowExecutionResult(BaseModel):
    execution_id: str = Field(...)
    workflow_id: str = Field(...)
    status: WorkflowStatus = Field(...)
    
    # Results
    output: Dict[str, Any] = Field(default_factory=dict)
    node_results: Dict[str, Any] = Field(default_factory=dict)
    
    # Execution metadata
    started_at: datetime = Field(...)
    completed_at: Optional[datetime] = Field(default=None)
    duration_ms: Optional[int] = Field(default=None)
    
    # Resource usage
    tokens_used: int = Field(default=0)
    cost_usd: float = Field(default=0.0)
    api_calls_made: int = Field(default=0)
    
    # Debug information
    execution_trace: Optional[List[Dict[str, Any]]] = Field(default=None)
    errors: List[Dict[str, Any]] = Field(default_factory=list)