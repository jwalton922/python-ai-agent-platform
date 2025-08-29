"""
Sample enhanced workflows for testing and demonstration
"""

import uuid
from datetime import datetime
from backend.models.workflow_enhanced import (
    EnhancedWorkflow,
    EnhancedWorkflowNode,
    EnhancedWorkflowEdge,
    NodeType,
    ExecutionMode,
    WorkflowVariable,
    WorkflowSettings,
    WorkflowMonitoring,
    ConditionBranch,
    LoopConfig,
    ParallelBranch,
    DataMapping,
    HumanInputConfig,
    StorageConfig,
    StorageOperation,
    NodeConfig,
    WaitStrategy,
    AggregationMethod
)


def create_simple_agent_workflow() -> EnhancedWorkflow:
    """Create a simple workflow with one agent"""
    
    # Define workflow variables
    variables = [
        WorkflowVariable(
            name="user_message",
            type="string",
            required=True,
            description="Message from the user"
        ),
        WorkflowVariable(
            name="response_format",
            type="string",
            required=False,
            default="json",
            description="Desired response format"
        )
    ]
    
    # Create agent node
    agent_node = EnhancedWorkflowNode(
        id="agent_001",
        type=NodeType.AGENT,
        name="Customer Service Agent",
        description="Handle customer inquiries",
        position={"x": 100, "y": 100},
        agent_id="customer_service_agent",  # Would reference existing agent
        input_mapping=[
            DataMapping(
                source="${global.user_message}",
                target="message"
            ),
            DataMapping(
                source="${global.response_format}",
                target="format"
            )
        ],
        output_mapping=[
            DataMapping(
                source="output",
                target="agent_response"
            )
        ]
    )
    
    return EnhancedWorkflow(
        id=str(uuid.uuid4()),
        name="Simple Agent Workflow",
        description="A basic workflow with a single agent",
        version="1.0.0",
        nodes=[agent_node],
        edges=[],
        variables=variables,
        execution_mode=ExecutionMode.SEQUENTIAL,
        settings=WorkflowSettings(
            max_execution_time_ms=60000,
            max_total_tokens=1000
        ),
        monitoring=WorkflowMonitoring(
            metrics_enabled=True,
            capture_inputs=True,
            capture_outputs=True
        ),
        tags=["simple", "customer-service", "single-agent"]
    )


def create_decision_workflow() -> EnhancedWorkflow:
    """Create a workflow with decision branching"""
    
    variables = [
        WorkflowVariable(
            name="customer_sentiment",
            type="string",
            required=True,
            description="Customer sentiment (positive, negative, neutral)"
        ),
        WorkflowVariable(
            name="urgency_level",
            type="number",
            required=True,
            description="Urgency level from 1-10"
        )
    ]
    
    # Sentiment analysis agent
    sentiment_agent = EnhancedWorkflowNode(
        id="sentiment_analyzer",
        type=NodeType.AGENT,
        name="Sentiment Analyzer",
        description="Analyze customer sentiment",
        position={"x": 100, "y": 100},
        agent_id="sentiment_agent",
        input_mapping=[
            DataMapping(
                source="${global.customer_sentiment}",
                target="text"
            )
        ]
    )
    
    # Decision node for routing
    decision_node = EnhancedWorkflowNode(
        id="routing_decision",
        type=NodeType.DECISION,
        name="Route Based on Sentiment",
        description="Route to appropriate handler",
        position={"x": 300, "y": 100},
        condition_branches=[
            ConditionBranch(
                name="high_priority",
                expression="${sentiment_analyzer.sentiment} == 'negative' and ${global.urgency_level} >= 8",
                target="escalation_agent",
                priority=1
            ),
            ConditionBranch(
                name="standard_support",
                expression="${sentiment_analyzer.sentiment} == 'positive' or ${global.urgency_level} < 5",
                target="standard_agent",
                priority=2
            )
        ],
        default_target="general_agent"
    )
    
    # Different handler agents
    escalation_agent = EnhancedWorkflowNode(
        id="escalation_agent",
        type=NodeType.AGENT,
        name="Escalation Handler",
        description="Handle high-priority issues",
        position={"x": 500, "y": 50},
        agent_id="escalation_agent"
    )
    
    standard_agent = EnhancedWorkflowNode(
        id="standard_agent",
        type=NodeType.AGENT,
        name="Standard Support",
        description="Handle standard inquiries",
        position={"x": 500, "y": 150},
        agent_id="standard_agent"
    )
    
    general_agent = EnhancedWorkflowNode(
        id="general_agent",
        type=NodeType.AGENT,
        name="General Support",
        description="Handle general inquiries",
        position={"x": 500, "y": 250},
        agent_id="general_agent"
    )
    
    # Create edges
    edges = [
        EnhancedWorkflowEdge(
            id="edge_1",
            source_node_id="sentiment_analyzer",
            target_node_id="routing_decision"
        ),
        EnhancedWorkflowEdge(
            id="edge_2",
            source_node_id="routing_decision",
            target_node_id="escalation_agent",
            condition="${routing_decision.decision} == 'high_priority'"
        ),
        EnhancedWorkflowEdge(
            id="edge_3",
            source_node_id="routing_decision",
            target_node_id="standard_agent",
            condition="${routing_decision.decision} == 'standard_support'"
        ),
        EnhancedWorkflowEdge(
            id="edge_4",
            source_node_id="routing_decision",
            target_node_id="general_agent",
            condition="${routing_decision.decision} == 'default'"
        )
    ]
    
    return EnhancedWorkflow(
        id=str(uuid.uuid4()),
        name="Decision Routing Workflow",
        description="Route customers based on sentiment and urgency",
        version="1.0.0",
        nodes=[sentiment_agent, decision_node, escalation_agent, standard_agent, general_agent],
        edges=edges,
        variables=variables,
        execution_mode=ExecutionMode.SEQUENTIAL,
        settings=WorkflowSettings(
            max_execution_time_ms=120000,
            max_total_tokens=2000
        ),
        tags=["routing", "sentiment", "decision", "customer-support"]
    )


def create_parallel_workflow() -> EnhancedWorkflow:
    """Create a workflow with parallel processing"""
    
    variables = [
        WorkflowVariable(
            name="product_query",
            type="string",
            required=True,
            description="Product-related query"
        )
    ]
    
    # Input processing agent
    input_processor = EnhancedWorkflowNode(
        id="input_processor",
        type=NodeType.AGENT,
        name="Query Processor",
        description="Process and understand the query",
        position={"x": 100, "y": 200},
        agent_id="query_processor"
    )
    
    # Parallel processing node
    parallel_node = EnhancedWorkflowNode(
        id="parallel_research",
        type=NodeType.PARALLEL,
        name="Parallel Research",
        description="Research multiple aspects simultaneously",
        position={"x": 300, "y": 200},
        parallel_branches=[
            ParallelBranch(
                id="product_specs",
                name="Product Specifications",
                nodes=["product_specs_agent"],
                required=True
            ),
            ParallelBranch(
                id="pricing_info",
                name="Pricing Information",
                nodes=["pricing_agent"],
                required=True
            ),
            ParallelBranch(
                id="availability_check",
                name="Availability Check",
                nodes=["inventory_agent"],
                required=False
            )
        ],
        wait_strategy=WaitStrategy.ALL
    )
    
    # Parallel branch agents
    product_specs_agent = EnhancedWorkflowNode(
        id="product_specs_agent",
        type=NodeType.AGENT,
        name="Product Specs Research",
        description="Research product specifications",
        position={"x": 500, "y": 100},
        agent_id="product_research_agent"
    )
    
    pricing_agent = EnhancedWorkflowNode(
        id="pricing_agent",
        type=NodeType.AGENT,
        name="Pricing Research",
        description="Get pricing information",
        position={"x": 500, "y": 200},
        agent_id="pricing_agent"
    )
    
    inventory_agent = EnhancedWorkflowNode(
        id="inventory_agent",
        type=NodeType.AGENT,
        name="Inventory Check",
        description="Check product availability",
        position={"x": 500, "y": 300},
        agent_id="inventory_agent"
    )
    
    # Aggregator to combine results
    aggregator = EnhancedWorkflowNode(
        id="result_aggregator",
        type=NodeType.AGGREGATOR,
        name="Combine Results",
        description="Combine all research results",
        position={"x": 700, "y": 200},
        aggregation_method=AggregationMethod.MERGE,
        aggregation_config={
            "sources": [
                "product_specs_agent.output",
                "pricing_agent.output",
                "inventory_agent.output"
            ]
        }
    )
    
    # Final response agent
    response_agent = EnhancedWorkflowNode(
        id="response_generator",
        type=NodeType.AGENT,
        name="Response Generator",
        description="Generate final response",
        position={"x": 900, "y": 200},
        agent_id="response_generator"
    )
    
    # Create edges
    edges = [
        EnhancedWorkflowEdge(
            id="edge_1",
            source_node_id="input_processor",
            target_node_id="parallel_research"
        ),
        EnhancedWorkflowEdge(
            id="edge_2",
            source_node_id="parallel_research",
            target_node_id="product_specs_agent"
        ),
        EnhancedWorkflowEdge(
            id="edge_3",
            source_node_id="parallel_research",
            target_node_id="pricing_agent"
        ),
        EnhancedWorkflowEdge(
            id="edge_4",
            source_node_id="parallel_research",
            target_node_id="inventory_agent"
        ),
        EnhancedWorkflowEdge(
            id="edge_5",
            source_node_id="product_specs_agent",
            target_node_id="result_aggregator"
        ),
        EnhancedWorkflowEdge(
            id="edge_6",
            source_node_id="pricing_agent",
            target_node_id="result_aggregator"
        ),
        EnhancedWorkflowEdge(
            id="edge_7",
            source_node_id="inventory_agent",
            target_node_id="result_aggregator"
        ),
        EnhancedWorkflowEdge(
            id="edge_8",
            source_node_id="result_aggregator",
            target_node_id="response_generator"
        )
    ]
    
    return EnhancedWorkflow(
        id=str(uuid.uuid4()),
        name="Parallel Research Workflow",
        description="Research multiple aspects of a product query in parallel",
        version="1.0.0",
        nodes=[
            input_processor, parallel_node, product_specs_agent,
            pricing_agent, inventory_agent, aggregator, response_agent
        ],
        edges=edges,
        variables=variables,
        execution_mode=ExecutionMode.PARALLEL,
        settings=WorkflowSettings(
            max_execution_time_ms=180000,
            max_total_tokens=5000,
            max_parallel_executions=3
        ),
        tags=["parallel", "research", "product", "aggregation"]
    )


def create_loop_workflow() -> EnhancedWorkflow:
    """Create a workflow with loop processing"""
    
    variables = [
        WorkflowVariable(
            name="email_list",
            type="array",
            required=True,
            description="List of email addresses to process"
        ),
        WorkflowVariable(
            name="email_template",
            type="string",
            required=True,
            description="Email template to personalize"
        )
    ]
    
    # Email validation agent
    validator = EnhancedWorkflowNode(
        id="email_validator",
        type=NodeType.AGENT,
        name="Email Validator",
        description="Validate email format",
        position={"x": 100, "y": 100},
        agent_id="email_validator"
    )
    
    # Loop through emails
    email_loop = EnhancedWorkflowNode(
        id="email_processing_loop",
        type=NodeType.LOOP,
        name="Process Each Email",
        description="Process each email in the list",
        position={"x": 300, "y": 100},
        loop_config=LoopConfig(
            type="for_each",
            source="${global.email_list}",
            max_iterations=1000,
            parallel=False
        ),
        loop_body_nodes=["personalization_agent", "send_email_agent"]
    )
    
    # Personalization agent (inside loop)
    personalization_agent = EnhancedWorkflowNode(
        id="personalization_agent",
        type=NodeType.AGENT,
        name="Email Personalizer",
        description="Personalize email content",
        position={"x": 500, "y": 50},
        agent_id="personalization_agent",
        input_mapping=[
            DataMapping(
                source="${loop_item}",  # Current email in loop
                target="email_address"
            ),
            DataMapping(
                source="${global.email_template}",
                target="template"
            )
        ]
    )
    
    # Send email agent (inside loop)
    send_email_agent = EnhancedWorkflowNode(
        id="send_email_agent",
        type=NodeType.AGENT,
        name="Email Sender",
        description="Send personalized email",
        position={"x": 500, "y": 150},
        agent_id="email_sender"
    )
    
    # Summary agent
    summary_agent = EnhancedWorkflowNode(
        id="summary_generator",
        type=NodeType.AGENT,
        name="Summary Generator",
        description="Generate processing summary",
        position={"x": 700, "y": 100},
        agent_id="summary_generator"
    )
    
    # Storage node to save results
    storage_node = EnhancedWorkflowNode(
        id="results_storage",
        type=NodeType.STORAGE,
        name="Save Results",
        description="Store processing results",
        position={"x": 900, "y": 100},
        config=NodeConfig(
            storage_config=StorageConfig(
                operation=StorageOperation.SAVE,
                backend="file",
                key="email_campaign_${workflow.execution_id}"
            )
        )
    )
    
    edges = [
        EnhancedWorkflowEdge(
            id="edge_1",
            source_node_id="email_validator",
            target_node_id="email_processing_loop"
        ),
        EnhancedWorkflowEdge(
            id="edge_2",
            source_node_id="email_processing_loop",
            target_node_id="personalization_agent"
        ),
        EnhancedWorkflowEdge(
            id="edge_3",
            source_node_id="personalization_agent",
            target_node_id="send_email_agent"
        ),
        EnhancedWorkflowEdge(
            id="edge_4",
            source_node_id="email_processing_loop",
            target_node_id="summary_generator"
        ),
        EnhancedWorkflowEdge(
            id="edge_5",
            source_node_id="summary_generator",
            target_node_id="results_storage"
        )
    ]
    
    return EnhancedWorkflow(
        id=str(uuid.uuid4()),
        name="Email Campaign Workflow",
        description="Process and send personalized emails in bulk",
        version="1.0.0",
        nodes=[
            validator, email_loop, personalization_agent,
            send_email_agent, summary_agent, storage_node
        ],
        edges=edges,
        variables=variables,
        execution_mode=ExecutionMode.SEQUENTIAL,
        settings=WorkflowSettings(
            max_execution_time_ms=600000,  # 10 minutes
            max_total_tokens=10000,
            continue_on_error=True  # Continue processing other emails if one fails
        ),
        tags=["loop", "email", "bulk-processing", "personalization"]
    )


def create_human_approval_workflow() -> EnhancedWorkflow:
    """Create a workflow requiring human approval"""
    
    variables = [
        WorkflowVariable(
            name="expense_request",
            type="object",
            required=True,
            description="Expense request details"
        )
    ]
    
    # Initial processing
    expense_processor = EnhancedWorkflowNode(
        id="expense_processor",
        type=NodeType.AGENT,
        name="Expense Processor",
        description="Process and validate expense request",
        position={"x": 100, "y": 100},
        agent_id="expense_processor"
    )
    
    # Decision for approval requirement
    approval_decision = EnhancedWorkflowNode(
        id="approval_required",
        type=NodeType.DECISION,
        name="Check Approval Required",
        description="Determine if human approval is needed",
        position={"x": 300, "y": 100},
        condition_branches=[
            ConditionBranch(
                name="needs_approval",
                expression="${expense_processor.amount} > 1000",
                target="human_approval",
                priority=1
            ),
            ConditionBranch(
                name="auto_approve",
                expression="${expense_processor.amount} <= 1000",
                target="auto_approval_agent",
                priority=2
            )
        ]
    )
    
    # Human approval node
    human_approval = EnhancedWorkflowNode(
        id="human_approval",
        type=NodeType.HUMAN_IN_LOOP,
        name="Manager Approval",
        description="Requires manager approval for high-value expenses",
        position={"x": 500, "y": 50},
        config=NodeConfig(
            human_config=HumanInputConfig(
                ui_template="Please review expense request: ${expense_processor.summary}",
                notification_channels=["slack", "email"],
                timeout_ms=86400000,  # 24 hours
                escalation_after_ms=43200000,  # 12 hours
                approval_options=["approve", "reject", "request_more_info"]
            )
        )
    )
    
    # Auto approval agent
    auto_approval_agent = EnhancedWorkflowNode(
        id="auto_approval_agent",
        type=NodeType.AGENT,
        name="Auto Approval",
        description="Automatically approve low-value expenses",
        position={"x": 500, "y": 150},
        agent_id="auto_approval_agent"
    )
    
    # Final processing based on decision
    final_processor = EnhancedWorkflowNode(
        id="final_processor",
        type=NodeType.AGENT,
        name="Final Processing",
        description="Process the approved/rejected expense",
        position={"x": 700, "y": 100},
        agent_id="expense_finalizer"
    )
    
    # Error handler
    error_handler = EnhancedWorkflowNode(
        id="error_handler",
        type=NodeType.ERROR_HANDLER,
        name="Error Handler",
        description="Handle processing errors",
        position={"x": 700, "y": 300},
        error_types=["timeout", "validation_error", "system_error"],
        fallback_node="notification_agent"
    )
    
    # Notification agent for errors
    notification_agent = EnhancedWorkflowNode(
        id="notification_agent",
        type=NodeType.AGENT,
        name="Error Notification",
        description="Send error notifications",
        position={"x": 900, "y": 300},
        agent_id="notification_agent"
    )
    
    edges = [
        EnhancedWorkflowEdge(
            id="edge_1",
            source_node_id="expense_processor",
            target_node_id="approval_required"
        ),
        EnhancedWorkflowEdge(
            id="edge_2",
            source_node_id="approval_required",
            target_node_id="human_approval",
            condition="${approval_required.decision} == 'needs_approval'"
        ),
        EnhancedWorkflowEdge(
            id="edge_3",
            source_node_id="approval_required",
            target_node_id="auto_approval_agent",
            condition="${approval_required.decision} == 'auto_approve'"
        ),
        EnhancedWorkflowEdge(
            id="edge_4",
            source_node_id="human_approval",
            target_node_id="final_processor",
            condition="${human_approval.human_input.decision} == 'approve'"
        ),
        EnhancedWorkflowEdge(
            id="edge_5",
            source_node_id="auto_approval_agent",
            target_node_id="final_processor"
        ),
        EnhancedWorkflowEdge(
            id="edge_6",
            source_node_id="error_handler",
            target_node_id="notification_agent"
        )
    ]
    
    return EnhancedWorkflow(
        id=str(uuid.uuid4()),
        name="Expense Approval Workflow",
        description="Process expense requests with conditional human approval",
        version="1.0.0",
        nodes=[
            expense_processor, approval_decision, human_approval,
            auto_approval_agent, final_processor, error_handler, notification_agent
        ],
        edges=edges,
        variables=variables,
        execution_mode=ExecutionMode.SEQUENTIAL,
        global_error_handler="error_handler",
        settings=WorkflowSettings(
            max_execution_time_ms=90000000,  # 25 hours (includes human wait time)
            continue_on_error=False
        ),
        tags=["approval", "human-in-loop", "expense", "decision", "error-handling"]
    )


# Export all sample workflows
SAMPLE_WORKFLOWS = [
    create_simple_agent_workflow(),
    create_decision_workflow(),
    create_parallel_workflow(),
    create_loop_workflow(),
    create_human_approval_workflow()
]


def save_sample_workflows():
    """Save sample workflows to storage for testing"""
    from backend.storage.file_storage import file_storage
    
    saved_workflows = []
    for workflow in SAMPLE_WORKFLOWS:
        try:
            saved_workflow = file_storage.create_enhanced_workflow(workflow)
            saved_workflows.append(saved_workflow)
            print(f"Saved workflow: {workflow.name} (ID: {workflow.id})")
        except Exception as e:
            print(f"Failed to save workflow {workflow.name}: {e}")
    
    return saved_workflows


if __name__ == "__main__":
    # Save sample workflows when run directly
    save_sample_workflows()