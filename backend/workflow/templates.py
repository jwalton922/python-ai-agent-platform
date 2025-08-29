"""
Workflow templates for common use cases
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List
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


class WorkflowTemplateLibrary:
    """Library of workflow templates for common use cases"""
    
    @staticmethod
    def customer_support_workflow() -> EnhancedWorkflow:
        """Customer support workflow with sentiment analysis and routing"""
        
        variables = [
            WorkflowVariable(
                name="customer_message",
                type="string",
                required=True,
                description="Customer's message or inquiry"
            ),
            WorkflowVariable(
                name="customer_id",
                type="string",
                required=False,
                description="Customer ID if available"
            ),
            WorkflowVariable(
                name="priority_level",
                type="number",
                required=False,
                default=1,
                description="Priority level (1-5, where 5 is highest)"
            )
        ]
        
        # Input analysis
        sentiment_analyzer = EnhancedWorkflowNode(
            id="sentiment_analysis",
            type=NodeType.AGENT,
            name="Sentiment Analyzer",
            description="Analyze customer sentiment and urgency",
            position={"x": 100, "y": 100},
            agent_id="sentiment_analyzer",
            input_mapping=[
                DataMapping(source="${global.customer_message}", target="message"),
                DataMapping(source="${global.customer_id}", target="customer_id")
            ]
        )
        
        # Routing decision
        routing_decision = EnhancedWorkflowNode(
            id="support_routing",
            type=NodeType.DECISION,
            name="Route to Appropriate Handler",
            description="Route based on sentiment and priority",
            position={"x": 300, "y": 100},
            condition_branches=[
                ConditionBranch(
                    name="high_priority",
                    expression="${sentiment_analysis.sentiment} == 'negative' or ${global.priority_level} >= 4",
                    target="escalation_handler",
                    priority=1
                ),
                ConditionBranch(
                    name="billing_inquiry",
                    expression="'billing' in ${sentiment_analysis.categories}",
                    target="billing_specialist",
                    priority=2
                ),
                ConditionBranch(
                    name="technical_issue",
                    expression="'technical' in ${sentiment_analysis.categories}",
                    target="tech_support",
                    priority=3
                )
            ],
            default_target="general_support"
        )
        
        # Support handlers
        escalation_handler = EnhancedWorkflowNode(
            id="escalation_handler",
            type=NodeType.AGENT,
            name="Escalation Handler",
            description="Handle high-priority and negative sentiment cases",
            position={"x": 600, "y": 50},
            agent_id="escalation_specialist"
        )
        
        billing_specialist = EnhancedWorkflowNode(
            id="billing_specialist",
            type=NodeType.AGENT,
            name="Billing Specialist",
            description="Handle billing-related inquiries",
            position={"x": 600, "y": 150},
            agent_id="billing_agent"
        )
        
        tech_support = EnhancedWorkflowNode(
            id="tech_support",
            type=NodeType.AGENT,
            name="Technical Support",
            description="Handle technical issues",
            position={"x": 600, "y": 250},
            agent_id="tech_support_agent"
        )
        
        general_support = EnhancedWorkflowNode(
            id="general_support",
            type=NodeType.AGENT,
            name="General Support",
            description="Handle general inquiries",
            position={"x": 600, "y": 350},
            agent_id="general_support_agent"
        )
        
        # Follow-up storage
        case_storage = EnhancedWorkflowNode(
            id="case_storage",
            type=NodeType.STORAGE,
            name="Store Case Record",
            description="Store support case for tracking",
            position={"x": 800, "y": 200},
            config=NodeConfig(
                storage_config=StorageConfig(
                    operation=StorageOperation.SAVE,
                    backend="database",
                    key="support_case_${workflow.execution_id}"
                )
            )
        )
        
        edges = [
            EnhancedWorkflowEdge(
                id="sentiment_to_routing",
                source_node_id="sentiment_analysis",
                target_node_id="support_routing"
            ),
            EnhancedWorkflowEdge(
                id="escalation_route",
                source_node_id="support_routing",
                target_node_id="escalation_handler",
                condition="${support_routing.decision} == 'high_priority'"
            ),
            EnhancedWorkflowEdge(
                id="billing_route",
                source_node_id="support_routing",
                target_node_id="billing_specialist",
                condition="${support_routing.decision} == 'billing_inquiry'"
            ),
            EnhancedWorkflowEdge(
                id="tech_route",
                source_node_id="support_routing",
                target_node_id="tech_support",
                condition="${support_routing.decision} == 'technical_issue'"
            ),
            EnhancedWorkflowEdge(
                id="general_route",
                source_node_id="support_routing",
                target_node_id="general_support",
                condition="${support_routing.decision} == 'default'"
            ),
            # All handlers connect to storage
            EnhancedWorkflowEdge(id="escalation_to_storage", source_node_id="escalation_handler", target_node_id="case_storage"),
            EnhancedWorkflowEdge(id="billing_to_storage", source_node_id="billing_specialist", target_node_id="case_storage"),
            EnhancedWorkflowEdge(id="tech_to_storage", source_node_id="tech_support", target_node_id="case_storage"),
            EnhancedWorkflowEdge(id="general_to_storage", source_node_id="general_support", target_node_id="case_storage"),
        ]
        
        return EnhancedWorkflow(
            id=str(uuid.uuid4()),
            name="Customer Support Workflow",
            description="Intelligent customer support with sentiment analysis and routing",
            version="1.0.0",
            nodes=[sentiment_analyzer, routing_decision, escalation_handler, 
                   billing_specialist, tech_support, general_support, case_storage],
            edges=edges,
            variables=variables,
            execution_mode=ExecutionMode.SEQUENTIAL,
            settings=WorkflowSettings(
                max_execution_time_ms=180000,
                max_total_tokens=3000,
                continue_on_error=False
            ),
            monitoring=WorkflowMonitoring(
                metrics_enabled=True,
                capture_inputs=True,
                capture_outputs=True
            ),
            tags=["customer-support", "sentiment-analysis", "routing", "template"]
        )
    
    @staticmethod
    def content_creation_workflow() -> EnhancedWorkflow:
        """Content creation workflow with research, writing, and approval"""
        
        variables = [
            WorkflowVariable(
                name="content_topic",
                type="string",
                required=True,
                description="Topic for content creation"
            ),
            WorkflowVariable(
                name="content_type",
                type="string",
                required=True,
                description="Type of content (blog, article, social, etc.)"
            ),
            WorkflowVariable(
                name="target_audience",
                type="string",
                required=False,
                description="Target audience for the content"
            ),
            WorkflowVariable(
                name="word_count",
                type="number",
                required=False,
                default=500,
                description="Target word count"
            )
        ]
        
        # Research phase
        research_coordinator = EnhancedWorkflowNode(
            id="research_coordinator",
            type=NodeType.AGENT,
            name="Research Coordinator",
            description="Plan and coordinate research activities",
            position={"x": 100, "y": 150},
            agent_id="research_planner"
        )
        
        # Parallel research
        parallel_research = EnhancedWorkflowNode(
            id="parallel_research",
            type=NodeType.PARALLEL,
            name="Conduct Research",
            description="Parallel research from multiple sources",
            position={"x": 300, "y": 150},
            parallel_branches=[
                ParallelBranch(
                    id="web_research",
                    name="Web Research",
                    nodes=["web_researcher"],
                    required=True
                ),
                ParallelBranch(
                    id="expert_analysis",
                    name="Expert Analysis",
                    nodes=["expert_analyzer"],
                    required=False
                ),
                ParallelBranch(
                    id="trend_analysis",
                    name="Trend Analysis",
                    nodes=["trend_analyzer"],
                    required=False
                )
            ],
            wait_strategy=WaitStrategy.ALL
        )
        
        # Research agents
        web_researcher = EnhancedWorkflowNode(
            id="web_researcher",
            type=NodeType.AGENT,
            name="Web Research Agent",
            description="Research topic using web sources",
            position={"x": 500, "y": 50},
            agent_id="web_research_agent"
        )
        
        expert_analyzer = EnhancedWorkflowNode(
            id="expert_analyzer",
            type=NodeType.AGENT,
            name="Expert Analysis Agent",
            description="Provide expert analysis and insights",
            position={"x": 500, "y": 150},
            agent_id="expert_analysis_agent"
        )
        
        trend_analyzer = EnhancedWorkflowNode(
            id="trend_analyzer",
            type=NodeType.AGENT,
            name="Trend Analysis Agent",
            description="Analyze current trends and patterns",
            position={"x": 500, "y": 250},
            agent_id="trend_analysis_agent"
        )
        
        # Aggregate research
        research_aggregator = EnhancedWorkflowNode(
            id="research_aggregator",
            type=NodeType.AGGREGATOR,
            name="Combine Research",
            description="Aggregate all research findings",
            position={"x": 700, "y": 150},
            aggregation_method=AggregationMethod.MERGE,
            aggregation_config={
                "sources": [
                    "web_researcher.output",
                    "expert_analyzer.output", 
                    "trend_analyzer.output"
                ]
            }
        )
        
        # Content creation
        content_writer = EnhancedWorkflowNode(
            id="content_writer",
            type=NodeType.AGENT,
            name="Content Writer",
            description="Create content based on research",
            position={"x": 900, "y": 150},
            agent_id="content_writer_agent",
            input_mapping=[
                DataMapping(source="${research_aggregator.aggregated_data}", target="research_data"),
                DataMapping(source="${global.content_type}", target="content_type"),
                DataMapping(source="${global.target_audience}", target="audience"),
                DataMapping(source="${global.word_count}", target="word_count")
            ]
        )
        
        # Quality check
        quality_reviewer = EnhancedWorkflowNode(
            id="quality_reviewer",
            type=NodeType.AGENT,
            name="Quality Reviewer",
            description="Review content quality and accuracy",
            position={"x": 1100, "y": 150},
            agent_id="quality_review_agent"
        )
        
        # Human approval
        editorial_approval = EnhancedWorkflowNode(
            id="editorial_approval",
            type=NodeType.HUMAN_IN_LOOP,
            name="Editorial Approval",
            description="Human editor review and approval",
            position={"x": 1300, "y": 150},
            config=NodeConfig(
                human_config=HumanInputConfig(
                    ui_template="Please review the following content:\n\n${content_writer.output}\n\nQuality score: ${quality_reviewer.score}",
                    notification_channels=["email", "slack"],
                    timeout_ms=172800000,  # 48 hours
                    approval_options=["approve", "request_revisions", "reject"]
                )
            )
        )
        
        # Revision loop (if needed)
        revision_check = EnhancedWorkflowNode(
            id="revision_check",
            type=NodeType.DECISION,
            name="Check for Revisions",
            description="Determine if revisions are needed",
            position={"x": 1500, "y": 150},
            condition_branches=[
                ConditionBranch(
                    name="approved",
                    expression="${editorial_approval.human_input.decision} == 'approve'",
                    target="final_storage",
                    priority=1
                ),
                ConditionBranch(
                    name="needs_revision",
                    expression="${editorial_approval.human_input.decision} == 'request_revisions'",
                    target="content_writer",
                    priority=2
                )
            ],
            default_target="error_handler"
        )
        
        # Final storage
        final_storage = EnhancedWorkflowNode(
            id="final_storage",
            type=NodeType.STORAGE,
            name="Store Final Content",
            description="Store approved content",
            position={"x": 1700, "y": 150},
            config=NodeConfig(
                storage_config=StorageConfig(
                    operation=StorageOperation.SAVE,
                    backend="file",
                    key="content_${global.content_type}_${workflow.execution_id}"
                )
            )
        )
        
        # Error handler
        error_handler = EnhancedWorkflowNode(
            id="error_handler",
            type=NodeType.ERROR_HANDLER,
            name="Handle Errors",
            description="Handle workflow errors",
            position={"x": 1500, "y": 300},
            error_types=["timeout", "approval_rejected", "quality_failure"]
        )
        
        edges = [
            # Main flow
            EnhancedWorkflowEdge(id="coord_to_parallel", source_node_id="research_coordinator", target_node_id="parallel_research"),
            EnhancedWorkflowEdge(id="parallel_to_web", source_node_id="parallel_research", target_node_id="web_researcher"),
            EnhancedWorkflowEdge(id="parallel_to_expert", source_node_id="parallel_research", target_node_id="expert_analyzer"),
            EnhancedWorkflowEdge(id="parallel_to_trend", source_node_id="parallel_research", target_node_id="trend_analyzer"),
            
            # Research to aggregator
            EnhancedWorkflowEdge(id="web_to_agg", source_node_id="web_researcher", target_node_id="research_aggregator"),
            EnhancedWorkflowEdge(id="expert_to_agg", source_node_id="expert_analyzer", target_node_id="research_aggregator"),
            EnhancedWorkflowEdge(id="trend_to_agg", source_node_id="trend_analyzer", target_node_id="research_aggregator"),
            
            # Writing and review flow
            EnhancedWorkflowEdge(id="agg_to_writer", source_node_id="research_aggregator", target_node_id="content_writer"),
            EnhancedWorkflowEdge(id="writer_to_quality", source_node_id="content_writer", target_node_id="quality_reviewer"),
            EnhancedWorkflowEdge(id="quality_to_approval", source_node_id="quality_reviewer", target_node_id="editorial_approval"),
            EnhancedWorkflowEdge(id="approval_to_check", source_node_id="editorial_approval", target_node_id="revision_check"),
            
            # Decision outcomes
            EnhancedWorkflowEdge(
                id="approved_to_storage", 
                source_node_id="revision_check", 
                target_node_id="final_storage",
                condition="${revision_check.decision} == 'approved'"
            ),
            EnhancedWorkflowEdge(
                id="revision_loop", 
                source_node_id="revision_check", 
                target_node_id="content_writer",
                condition="${revision_check.decision} == 'needs_revision'"
            ),
            EnhancedWorkflowEdge(
                id="error_handling", 
                source_node_id="revision_check", 
                target_node_id="error_handler",
                condition="${revision_check.decision} == 'default'"
            )
        ]
        
        return EnhancedWorkflow(
            id=str(uuid.uuid4()),
            name="Content Creation Workflow",
            description="Research-driven content creation with human approval",
            version="1.0.0",
            nodes=[
                research_coordinator, parallel_research, web_researcher, expert_analyzer,
                trend_analyzer, research_aggregator, content_writer, quality_reviewer,
                editorial_approval, revision_check, final_storage, error_handler
            ],
            edges=edges,
            variables=variables,
            execution_mode=ExecutionMode.SEQUENTIAL,
            global_error_handler="error_handler",
            settings=WorkflowSettings(
                max_execution_time_ms=259200000,  # 72 hours (includes human approval time)
                max_total_tokens=10000,
                max_parallel_executions=3,
                continue_on_error=False
            ),
            monitoring=WorkflowMonitoring(
                metrics_enabled=True,
                capture_inputs=True,
                capture_outputs=True,
                capture_intermediate=True
            ),
            tags=["content-creation", "research", "parallel", "human-approval", "template"]
        )
    
    @staticmethod
    def data_processing_pipeline() -> EnhancedWorkflow:
        """Data processing pipeline with validation, transformation, and storage"""
        
        variables = [
            WorkflowVariable(
                name="data_source",
                type="string",
                required=True,
                description="Source of data to process"
            ),
            WorkflowVariable(
                name="processing_rules",
                type="array",
                required=False,
                default=[],
                description="Processing rules to apply"
            ),
            WorkflowVariable(
                name="output_format",
                type="string",
                required=False,
                default="json",
                description="Desired output format"
            )
        ]
        
        # Data ingestion
        data_loader = EnhancedWorkflowNode(
            id="data_loader",
            type=NodeType.AGENT,
            name="Data Loader",
            description="Load data from source",
            position={"x": 100, "y": 200},
            agent_id="data_loader_agent"
        )
        
        # Validation
        data_validator = EnhancedWorkflowNode(
            id="data_validator",
            type=NodeType.AGENT,
            name="Data Validator",
            description="Validate data quality and structure",
            position={"x": 300, "y": 200},
            agent_id="data_validation_agent"
        )
        
        # Quality check decision
        quality_check = EnhancedWorkflowNode(
            id="quality_check",
            type=NodeType.DECISION,
            name="Quality Gate",
            description="Determine if data quality is acceptable",
            position={"x": 500, "y": 200},
            condition_branches=[
                ConditionBranch(
                    name="high_quality",
                    expression="${data_validator.quality_score} >= 0.9",
                    target="batch_processor",
                    priority=1
                ),
                ConditionBranch(
                    name="medium_quality",
                    expression="${data_validator.quality_score} >= 0.7",
                    target="data_cleaner",
                    priority=2
                )
            ],
            default_target="quality_error_handler"
        )
        
        # Data cleaning
        data_cleaner = EnhancedWorkflowNode(
            id="data_cleaner",
            type=NodeType.AGENT,
            name="Data Cleaner",
            description="Clean and repair data quality issues",
            position={"x": 700, "y": 300},
            agent_id="data_cleaning_agent"
        )
        
        # Batch processing
        batch_processor = EnhancedWorkflowNode(
            id="batch_processor",
            type=NodeType.LOOP,
            name="Process Data Batches",
            description="Process data in batches",
            position={"x": 700, "y": 100},
            loop_config=LoopConfig(
                type="for_each",
                source="${data_validator.data_batches}",
                max_iterations=1000,
                parallel=True
            ),
            loop_body_nodes=["record_transformer", "record_validator"]
        )
        
        # Transform individual records
        record_transformer = EnhancedWorkflowNode(
            id="record_transformer",
            type=NodeType.TRANSFORM,
            name="Transform Record",
            description="Apply transformations to individual records",
            position={"x": 900, "y": 50},
            transformations=[
                DataMapping(source="${loop_item.raw_data}", target="structured_data.content"),
                DataMapping(source="${loop_item.timestamp}", target="structured_data.processed_at"),
                DataMapping(source="${global.processing_rules}", target="transformation_rules")
            ]
        )
        
        # Validate transformed records
        record_validator = EnhancedWorkflowNode(
            id="record_validator",
            type=NodeType.AGENT,
            name="Validate Record",
            description="Validate transformed records",
            position={"x": 900, "y": 150},
            agent_id="record_validation_agent"
        )
        
        # Aggregate results
        results_aggregator = EnhancedWorkflowNode(
            id="results_aggregator",
            type=NodeType.AGGREGATOR,
            name="Aggregate Results",
            description="Combine all processed records",
            position={"x": 1100, "y": 200},
            aggregation_method=AggregationMethod.CONCAT,
            aggregation_config={
                "sources": [
                    "batch_processor.results",
                    "data_cleaner.cleaned_data"
                ]
            }
        )
        
        # Final storage
        data_storage = EnhancedWorkflowNode(
            id="data_storage",
            type=NodeType.STORAGE,
            name="Store Processed Data",
            description="Store final processed data",
            position={"x": 1300, "y": 200},
            config=NodeConfig(
                storage_config=StorageConfig(
                    operation=StorageOperation.SAVE,
                    backend="database",
                    key="processed_data_${workflow.execution_id}",
                    versioning=True,
                    compression=True
                )
            )
        )
        
        # Error handlers
        quality_error_handler = EnhancedWorkflowNode(
            id="quality_error_handler",
            type=NodeType.ERROR_HANDLER,
            name="Quality Error Handler",
            description="Handle data quality failures",
            position={"x": 500, "y": 400},
            error_types=["quality_failure", "validation_error"],
            fallback_node="error_notification"
        )
        
        error_notification = EnhancedWorkflowNode(
            id="error_notification",
            type=NodeType.AGENT,
            name="Error Notification",
            description="Send error notifications",
            position={"x": 700, "y": 400},
            agent_id="notification_agent"
        )
        
        edges = [
            # Main processing flow
            EnhancedWorkflowEdge(id="load_to_validate", source_node_id="data_loader", target_node_id="data_validator"),
            EnhancedWorkflowEdge(id="validate_to_quality", source_node_id="data_validator", target_node_id="quality_check"),
            
            # Quality routing
            EnhancedWorkflowEdge(
                id="high_quality_path",
                source_node_id="quality_check",
                target_node_id="batch_processor",
                condition="${quality_check.decision} == 'high_quality'"
            ),
            EnhancedWorkflowEdge(
                id="medium_quality_path",
                source_node_id="quality_check",
                target_node_id="data_cleaner",
                condition="${quality_check.decision} == 'medium_quality'"
            ),
            EnhancedWorkflowEdge(
                id="quality_error_path",
                source_node_id="quality_check",
                target_node_id="quality_error_handler",
                condition="${quality_check.decision} == 'default'"
            ),
            
            # Batch processing
            EnhancedWorkflowEdge(id="batch_to_transform", source_node_id="batch_processor", target_node_id="record_transformer"),
            EnhancedWorkflowEdge(id="transform_to_validate", source_node_id="record_transformer", target_node_id="record_validator"),
            
            # Aggregation and storage
            EnhancedWorkflowEdge(id="batch_to_agg", source_node_id="batch_processor", target_node_id="results_aggregator"),
            EnhancedWorkflowEdge(id="clean_to_agg", source_node_id="data_cleaner", target_node_id="results_aggregator"),
            EnhancedWorkflowEdge(id="agg_to_storage", source_node_id="results_aggregator", target_node_id="data_storage"),
            
            # Error handling
            EnhancedWorkflowEdge(id="error_to_notification", source_node_id="quality_error_handler", target_node_id="error_notification")
        ]
        
        return EnhancedWorkflow(
            id=str(uuid.uuid4()),
            name="Data Processing Pipeline",
            description="Comprehensive data processing with validation and transformation",
            version="1.0.0",
            nodes=[
                data_loader, data_validator, quality_check, data_cleaner, batch_processor,
                record_transformer, record_validator, results_aggregator, data_storage,
                quality_error_handler, error_notification
            ],
            edges=edges,
            variables=variables,
            execution_mode=ExecutionMode.SEQUENTIAL,
            global_error_handler="quality_error_handler",
            settings=WorkflowSettings(
                max_execution_time_ms=1800000,  # 30 minutes
                max_total_tokens=15000,
                max_parallel_executions=10,
                save_intermediate_state=True,
                enable_checkpoints=True
            ),
            monitoring=WorkflowMonitoring(
                metrics_enabled=True,
                capture_inputs=True,
                capture_outputs=True,
                capture_intermediate=True
            ),
            tags=["data-processing", "validation", "batch", "transformation", "template"]
        )


# Template registry
WORKFLOW_TEMPLATES = {
    "customer_support": WorkflowTemplateLibrary.customer_support_workflow,
    "content_creation": WorkflowTemplateLibrary.content_creation_workflow,
    "data_processing": WorkflowTemplateLibrary.data_processing_pipeline
}


def create_workflow_from_template(template_name: str, customizations: Dict[str, Any] = None) -> EnhancedWorkflow:
    """Create a workflow from a template with optional customizations"""
    if template_name not in WORKFLOW_TEMPLATES:
        raise ValueError(f"Template '{template_name}' not found. Available: {list(WORKFLOW_TEMPLATES.keys())}")
    
    # Create workflow from template
    workflow = WORKFLOW_TEMPLATES[template_name]()
    
    # Apply customizations if provided
    if customizations:
        if 'name' in customizations:
            workflow.name = customizations['name']
        if 'description' in customizations:
            workflow.description = customizations['description']
        if 'variables' in customizations:
            # Merge or replace variables
            workflow.variables.extend(customizations['variables'])
        if 'settings' in customizations:
            # Update settings
            for key, value in customizations['settings'].items():
                if hasattr(workflow.settings, key):
                    setattr(workflow.settings, key, value)
        if 'tags' in customizations:
            workflow.tags.extend(customizations['tags'])
    
    # Generate new ID
    workflow.id = str(uuid.uuid4())
    
    return workflow


def list_available_templates() -> List[Dict[str, Any]]:
    """List all available workflow templates"""
    templates = []
    
    for name, template_func in WORKFLOW_TEMPLATES.items():
        try:
            sample_workflow = template_func()
            templates.append({
                "name": name,
                "display_name": sample_workflow.name,
                "description": sample_workflow.description,
                "node_count": len(sample_workflow.nodes),
                "complexity": "high" if len(sample_workflow.nodes) > 10 else "medium" if len(sample_workflow.nodes) > 5 else "low",
                "tags": sample_workflow.tags,
                "execution_mode": sample_workflow.execution_mode.value,
                "has_human_approval": any(node.type == NodeType.HUMAN_IN_LOOP for node in sample_workflow.nodes),
                "has_parallel_processing": any(node.type == NodeType.PARALLEL for node in sample_workflow.nodes),
                "has_loops": any(node.type == NodeType.LOOP for node in sample_workflow.nodes)
            })
        except Exception as e:
            print(f"Error loading template {name}: {e}")
    
    return templates


if __name__ == "__main__":
    # Demo usage
    print("Available workflow templates:")
    for template in list_available_templates():
        print(f"- {template['display_name']} ({template['name']})")
        print(f"  {template['description']}")
        print(f"  Nodes: {template['node_count']}, Complexity: {template['complexity']}")
        print()