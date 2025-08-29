"""
Comprehensive tests for the enhanced workflow system
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch
import json

from backend.models.workflow_enhanced import (
    EnhancedWorkflow,
    EnhancedWorkflowNode,
    EnhancedWorkflowEdge,
    NodeType,
    ExecutionMode,
    WorkflowVariable,
    WorkflowSettings,
    WorkflowExecutionState,
    WorkflowStatus,
    ConditionBranch,
    LoopConfig,
    DataMapping
)
from backend.workflow.executor_enhanced import enhanced_workflow_executor
from backend.workflow.testing import (
    workflow_test_runner,
    workflow_test_generator,
    workflow_debugger,
    workflow_simulator
)
from backend.storage.file_storage import file_storage


class TestEnhancedWorkflowModels:
    """Test enhanced workflow data models"""
    
    def test_enhanced_workflow_creation(self):
        """Test creating an enhanced workflow"""
        workflow = EnhancedWorkflow(
            id="test-workflow-1",
            name="Test Workflow",
            description="A test workflow",
            version="1.0.0",
            nodes=[],
            edges=[],
            variables=[],
            execution_mode=ExecutionMode.SEQUENTIAL,
            settings=WorkflowSettings(),
            tags=["test"]
        )
        
        assert workflow.id == "test-workflow-1"
        assert workflow.name == "Test Workflow"
        assert workflow.execution_mode == ExecutionMode.SEQUENTIAL
        assert workflow.status == WorkflowStatus.IDLE
        assert "test" in workflow.tags
    
    def test_workflow_node_validation(self):
        """Test workflow node validation"""
        # Agent node should require agent_id
        with pytest.raises(ValueError):
            EnhancedWorkflow(
                id="test",
                name="Test",
                version="1.0.0",
                nodes=[
                    EnhancedWorkflowNode(
                        id="agent1",
                        type=NodeType.AGENT,
                        name="Agent Node",
                        position={"x": 0, "y": 0}
                        # Missing agent_id
                    )
                ],
                edges=[]
            )
    
    def test_workflow_variables(self):
        """Test workflow variable definitions"""
        variables = [
            WorkflowVariable(
                name="input_text",
                type="string",
                required=True,
                description="Input text to process"
            ),
            WorkflowVariable(
                name="max_tokens",
                type="number",
                required=False,
                default=1000,
                description="Maximum tokens to use"
            )
        ]
        
        workflow = EnhancedWorkflow(
            id="test",
            name="Test",
            version="1.0.0",
            variables=variables,
            nodes=[],
            edges=[]
        )
        
        assert len(workflow.variables) == 2
        assert workflow.variables[0].name == "input_text"
        assert workflow.variables[0].required is True
        assert workflow.variables[1].default == 1000


class TestWorkflowExecution:
    """Test workflow execution functionality"""
    
    @pytest.fixture
    def simple_workflow(self):
        """Create a simple test workflow"""
        agent_node = EnhancedWorkflowNode(
            id="agent1",
            type=NodeType.AGENT,
            name="Test Agent",
            position={"x": 100, "y": 100},
            agent_id="test_agent"
        )
        
        return EnhancedWorkflow(
            id="test-workflow",
            name="Simple Test Workflow",
            version="1.0.0",
            nodes=[agent_node],
            edges=[],
            variables=[
                WorkflowVariable(
                    name="message",
                    type="string",
                    required=True
                )
            ]
        )
    
    @pytest.mark.asyncio
    async def test_workflow_execution_plan(self, simple_workflow):
        """Test building workflow execution plan"""
        execution_plan = enhanced_workflow_executor._build_execution_plan(simple_workflow)
        
        assert len(execution_plan) == 1
        assert execution_plan[0] == "agent1"
    
    @pytest.mark.asyncio
    async def test_workflow_execution_state(self):
        """Test workflow execution state management"""
        state = WorkflowExecutionState(
            execution_id="test-exec-1",
            workflow_id="test-workflow",
            workflow_version="1.0.0",
            status=WorkflowStatus.RUNNING,
            started_at=datetime.utcnow(),
            global_variables={"message": "test"}
        )
        
        assert state.execution_id == "test-exec-1"
        assert state.status == WorkflowStatus.RUNNING
        assert state.global_variables["message"] == "test"
        assert len(state.completed_nodes) == 0
    
    @pytest.mark.asyncio
    @patch('backend.workflow.executor_enhanced.enhanced_workflow_executor.node_executors')
    async def test_mock_workflow_execution(self, mock_executors, simple_workflow):
        """Test workflow execution with mocked executors"""
        # Mock agent executor
        mock_agent_executor = Mock()
        mock_agent_executor.execute.return_value = {
            "agent_id": "test_agent",
            "output": "Test response",
            "success": True
        }
        mock_executors.get.return_value = mock_agent_executor
        
        # Execute workflow
        result = await enhanced_workflow_executor.execute_workflow(
            simple_workflow,
            {"message": "Hello world"}
        )
        
        assert result.status == WorkflowStatus.COMPLETED
        assert result.workflow_id == "test-workflow"


class TestNodeExecutors:
    """Test individual node executor functionality"""
    
    @pytest.mark.asyncio
    async def test_decision_node_executor(self):
        """Test decision node execution"""
        from backend.workflow.executor_enhanced import DecisionNodeExecutor
        
        executor = DecisionNodeExecutor(enhanced_workflow_executor)
        
        # Create decision node
        decision_node = EnhancedWorkflowNode(
            id="decision1",
            type=NodeType.DECISION,
            name="Test Decision",
            position={"x": 0, "y": 0},
            condition_branches=[
                ConditionBranch(
                    name="positive",
                    expression="context.sentiment == 'positive'",
                    target="positive_handler",
                    priority=1
                )
            ],
            default_target="default_handler"
        )
        
        context = {"sentiment": "positive"}
        state = WorkflowExecutionState(
            execution_id="test",
            workflow_id="test",
            workflow_version="1.0.0",
            status=WorkflowStatus.RUNNING,
            started_at=datetime.utcnow()
        )
        
        # Note: This would need proper condition evaluation implementation
        # For now, just test the structure
        assert decision_node.condition_branches[0].name == "positive"
    
    @pytest.mark.asyncio
    async def test_transform_node_executor(self):
        """Test transform node execution"""
        from backend.workflow.executor_enhanced import TransformNodeExecutor
        
        executor = TransformNodeExecutor(enhanced_workflow_executor)
        
        transform_node = EnhancedWorkflowNode(
            id="transform1",
            type=NodeType.TRANSFORM,
            name="Test Transform",
            position={"x": 0, "y": 0},
            transformations=[
                DataMapping(
                    source="input.text",
                    target="output.processed_text",
                    transform="uppercase"
                )
            ]
        )
        
        context = {"input": {"text": "hello world"}}
        state = WorkflowExecutionState(
            execution_id="test",
            workflow_id="test",
            workflow_version="1.0.0",
            status=WorkflowStatus.RUNNING,
            started_at=datetime.utcnow()
        )
        
        result = await executor.execute(transform_node, context, state)
        
        assert result["success"] is True
        assert "transformed_data" in result


class TestWorkflowStorage:
    """Test workflow storage functionality"""
    
    def test_create_enhanced_workflow(self):
        """Test creating and storing enhanced workflow"""
        workflow = EnhancedWorkflow(
            id="storage-test",
            name="Storage Test Workflow",
            version="1.0.0",
            nodes=[],
            edges=[]
        )
        
        saved_workflow = file_storage.create_enhanced_workflow(workflow)
        
        assert saved_workflow.id == "storage-test"
        assert saved_workflow.created_at is not None
    
    def test_get_enhanced_workflow(self):
        """Test retrieving enhanced workflow"""
        workflow = EnhancedWorkflow(
            id="retrieve-test",
            name="Retrieve Test Workflow",
            version="1.0.0",
            nodes=[],
            edges=[]
        )
        
        file_storage.create_enhanced_workflow(workflow)
        
        retrieved_workflow = file_storage.get_enhanced_workflow("retrieve-test")
        
        assert retrieved_workflow is not None
        assert retrieved_workflow.id == "retrieve-test"
        assert retrieved_workflow.name == "Retrieve Test Workflow"
    
    def test_list_enhanced_workflows(self):
        """Test listing enhanced workflows"""
        initial_count = len(file_storage.list_enhanced_workflows())
        
        workflow1 = EnhancedWorkflow(
            id="list-test-1",
            name="List Test 1",
            version="1.0.0",
            nodes=[],
            edges=[]
        )
        
        workflow2 = EnhancedWorkflow(
            id="list-test-2",
            name="List Test 2",
            version="1.0.0",
            nodes=[],
            edges=[]
        )
        
        file_storage.create_enhanced_workflow(workflow1)
        file_storage.create_enhanced_workflow(workflow2)
        
        workflows = file_storage.list_enhanced_workflows()
        
        assert len(workflows) >= initial_count + 2


class TestWorkflowTesting:
    """Test workflow testing utilities"""
    
    @pytest.fixture
    def test_workflow(self):
        """Create a workflow for testing"""
        return EnhancedWorkflow(
            id="testing-workflow",
            name="Testing Workflow",
            version="1.0.0",
            nodes=[
                EnhancedWorkflowNode(
                    id="agent1",
                    type=NodeType.AGENT,
                    name="Test Agent",
                    position={"x": 0, "y": 0},
                    agent_id="test_agent"
                )
            ],
            edges=[],
            variables=[
                WorkflowVariable(
                    name="input",
                    type="string",
                    required=True
                )
            ]
        )
    
    @pytest.mark.asyncio
    async def test_workflow_validation(self, test_workflow):
        """Test workflow structure validation"""
        from backend.api.routes.workflow_routes_enhanced import validate_workflow_structure
        
        validation_result = await validate_workflow_structure(test_workflow)
        
        assert "valid" in validation_result
        assert "errors" in validation_result
        assert "warnings" in validation_result
    
    def test_test_case_generation(self, test_workflow):
        """Test automatic test case generation"""
        test_cases = workflow_test_generator.generate_test_cases(test_workflow, count=3)
        
        assert len(test_cases) == 3
        assert test_cases[0]["name"] == "Happy Path Test"
        assert "input" in test_cases[0]
        assert "assertions" in test_cases[0]
    
    @pytest.mark.asyncio
    async def test_workflow_simulation(self, test_workflow):
        """Test workflow execution simulation"""
        simulation_result = await workflow_simulator.simulate(
            test_workflow,
            {"input": "test message"},
            iterations=2
        )
        
        assert simulation_result["workflow_id"] == "testing-workflow"
        assert simulation_result["iterations"] == 2
        assert len(simulation_result["simulated_executions"]) == 2
        assert "avg_duration_ms" in simulation_result
        assert "success_rate" in simulation_result


class TestWorkflowIntegration:
    """Test end-to-end workflow functionality"""
    
    @pytest.mark.asyncio
    async def test_complete_workflow_lifecycle(self):
        """Test complete workflow creation, storage, and execution lifecycle"""
        # Create workflow
        workflow = EnhancedWorkflow(
            id="integration-test",
            name="Integration Test Workflow",
            description="End-to-end test workflow",
            version="1.0.0",
            nodes=[
                EnhancedWorkflowNode(
                    id="start_agent",
                    type=NodeType.AGENT,
                    name="Start Agent",
                    position={"x": 100, "y": 100},
                    agent_id="integration_agent"
                )
            ],
            edges=[],
            variables=[
                WorkflowVariable(
                    name="test_input",
                    type="string",
                    required=True
                )
            ],
            settings=WorkflowSettings(
                max_execution_time_ms=30000,
                max_total_tokens=500
            ),
            tags=["integration", "test"]
        )
        
        # Store workflow
        saved_workflow = file_storage.create_enhanced_workflow(workflow)
        assert saved_workflow.id == "integration-test"
        
        # Retrieve workflow
        retrieved_workflow = file_storage.get_enhanced_workflow("integration-test")
        assert retrieved_workflow is not None
        assert retrieved_workflow.name == "Integration Test Workflow"
        
        # Validate workflow
        from backend.api.routes.workflow_routes_enhanced import validate_workflow_structure
        validation_result = await validate_workflow_structure(retrieved_workflow)
        assert validation_result["valid"] is True
        
        # Generate test cases
        test_cases = workflow_test_generator.generate_test_cases(retrieved_workflow, count=2)
        assert len(test_cases) == 2
        
        # Simulate execution
        simulation = await workflow_simulator.simulate(
            retrieved_workflow,
            {"test_input": "integration test"},
            iterations=1
        )
        assert simulation["workflow_id"] == "integration-test"


class TestWorkflowAPI:
    """Test workflow API endpoints"""
    
    def test_enhanced_workflow_creation_data(self):
        """Test data structures for enhanced workflow API"""
        workflow_data = {
            "name": "API Test Workflow",
            "description": "Test workflow via API",
            "version": "1.0.0",
            "nodes": [
                {
                    "id": "api_agent",
                    "type": "agent",
                    "name": "API Agent",
                    "position": {"x": 100, "y": 100},
                    "agent_id": "api_test_agent"
                }
            ],
            "edges": [],
            "variables": [
                {
                    "name": "api_input",
                    "type": "string",
                    "required": True
                }
            ],
            "execution_mode": "SEQUENTIAL",
            "settings": {
                "max_execution_time_ms": 60000,
                "max_total_tokens": 1000
            },
            "monitoring": {
                "metrics_enabled": True,
                "capture_inputs": True,
                "capture_outputs": True
            },
            "tags": ["api", "test"]
        }
        
        # Validate structure
        assert "name" in workflow_data
        assert "nodes" in workflow_data
        assert "edges" in workflow_data
        assert len(workflow_data["nodes"]) == 1
        assert workflow_data["nodes"][0]["type"] == "agent"


if __name__ == "__main__":
    # Run tests manually if needed
    pytest.main([__file__, "-v"])