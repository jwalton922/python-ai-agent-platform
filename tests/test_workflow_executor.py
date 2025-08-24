import pytest
from backend.workflow.executor import WorkflowExecutor
from backend.models.workflow import Workflow, WorkflowNode, WorkflowEdge
from backend.models.agent import Agent, AgentCreate
from backend.models.base import WorkflowStatus, TriggerType
from backend.storage.file_storage import file_storage as storage


@pytest.fixture
def setup_test_data():
    """Set up test agents and workflows"""
    # Clear storage
    storage.agents.clear()
    storage.workflows.clear()
    storage.activities.clear()
    
    # Create test agents
    agent1_data = AgentCreate(
        name="Agent 1",
        instructions="First agent instructions"
    )
    agent1 = storage.create_agent(agent1_data)
    
    agent2_data = AgentCreate(
        name="Agent 2", 
        instructions="Second agent instructions"
    )
    agent2 = storage.create_agent(agent2_data)
    
    # Create test workflow
    node1 = WorkflowNode(
        id="node1",
        agent_id=agent1.id,
        position={"x": 100, "y": 100}
    )
    
    node2 = WorkflowNode(
        id="node2",
        agent_id=agent2.id,
        position={"x": 200, "y": 100}
    )
    
    edge = WorkflowEdge(
        id="edge1",
        source_node_id="node1",
        target_node_id="node2"
    )
    
    workflow = Workflow(
        id="test_workflow",
        name="Test Workflow",
        nodes=[node1, node2],
        edges=[edge],
        trigger_conditions=[TriggerType.MANUAL],
        status=WorkflowStatus.IDLE
    )
    
    storage.workflows[workflow.id] = workflow
    
    return {
        "agent1": agent1,
        "agent2": agent2,
        "workflow": workflow
    }


@pytest.mark.asyncio
async def test_workflow_execution_order(setup_test_data):
    """Test that workflow nodes execute in correct order"""
    executor = WorkflowExecutor()
    workflow = setup_test_data["workflow"]
    
    # Build execution order
    execution_order = executor._build_execution_order(workflow.nodes, workflow.edges)
    
    # node1 should come before node2 due to the edge
    assert execution_order.index("node1") < execution_order.index("node2")


@pytest.mark.asyncio
async def test_workflow_execution(setup_test_data):
    """Test complete workflow execution"""
    executor = WorkflowExecutor()
    workflow = setup_test_data["workflow"]
    
    context = {"test_input": "test_value"}
    
    result = await executor.execute_workflow(workflow.id, context)
    
    assert result["status"] == "completed"
    assert "results" in result
    assert "node1" in result["results"]
    assert "node2" in result["results"]
    
    # Check that context was passed through
    assert result["context"]["test_input"] == "test_value"


@pytest.mark.asyncio
async def test_workflow_execution_with_no_edges(setup_test_data):
    """Test workflow execution with isolated nodes"""
    # Create a workflow with no edges
    workflow = setup_test_data["workflow"]
    workflow.edges = []  # Remove all edges
    
    executor = WorkflowExecutor()
    
    result = await executor.execute_workflow(workflow.id, {})
    
    assert result["status"] == "completed"
    assert len(result["results"]) == 2  # Both nodes should execute


@pytest.mark.asyncio
async def test_workflow_execution_error_handling():
    """Test workflow execution error handling"""
    executor = WorkflowExecutor()
    
    # Try to execute non-existent workflow
    with pytest.raises(ValueError, match="Workflow nonexistent not found"):
        await executor.execute_workflow("nonexistent", {})


@pytest.mark.asyncio
async def test_llm_agent_execution(setup_test_data):
    """Test LLM agent execution"""
    executor = WorkflowExecutor()
    agent = setup_test_data["agent1"]
    
    input_data = {"node_id": "test_node", "config": {"setting": "value"}}
    
    result = await executor._execute_agent_with_llm(agent, input_data)
    
    assert result["agent_id"] == agent.id
    assert result["agent_name"] == agent.name
    assert "output" in result
    assert "llm_provider" in result
    # Should succeed with mock provider or fail gracefully
    assert isinstance(result["success"], bool)


def test_build_execution_order_with_cycle():
    """Test that cycles in workflow are detected"""
    executor = WorkflowExecutor()
    
    nodes = [
        WorkflowNode(id="node1", agent_id="agent1", position={"x": 0, "y": 0}),
        WorkflowNode(id="node2", agent_id="agent2", position={"x": 0, "y": 0}),
        WorkflowNode(id="node3", agent_id="agent3", position={"x": 0, "y": 0})
    ]
    
    # Create a cycle: node1 -> node2 -> node3 -> node1
    edges = [
        WorkflowEdge(id="edge1", source_node_id="node1", target_node_id="node2"),
        WorkflowEdge(id="edge2", source_node_id="node2", target_node_id="node3"),
        WorkflowEdge(id="edge3", source_node_id="node3", target_node_id="node1")
    ]
    
    with pytest.raises(ValueError, match="Workflow contains cycles"):
        executor._build_execution_order(nodes, edges)


def test_get_node_by_id():
    """Test getting node by ID"""
    executor = WorkflowExecutor()
    
    nodes = [
        WorkflowNode(id="node1", agent_id="agent1", position={"x": 0, "y": 0}),
        WorkflowNode(id="node2", agent_id="agent2", position={"x": 0, "y": 0})
    ]
    
    node = executor._get_node_by_id(nodes, "node1")
    assert node is not None
    assert node.id == "node1"
    
    node = executor._get_node_by_id(nodes, "nonexistent")
    assert node is None