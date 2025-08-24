import pytest
from backend.models.agent import Agent, AgentCreate
from backend.models.workflow import Workflow, WorkflowCreate, WorkflowNode, WorkflowEdge
from backend.models.base import TriggerType, WorkflowStatus


def test_agent_creation():
    """Test agent model creation"""
    agent_data = AgentCreate(
        name="Test Agent",
        description="A test agent",
        instructions="You are a helpful assistant",
        mcp_tool_permissions=["email_tool", "slack_tool"],
        trigger_conditions=[TriggerType.MANUAL]
    )
    
    agent = Agent(id="test_id", **agent_data.dict())
    
    assert agent.id == "test_id"
    assert agent.name == "Test Agent"
    assert agent.instructions == "You are a helpful assistant"
    assert len(agent.mcp_tool_permissions) == 2
    assert TriggerType.MANUAL in agent.trigger_conditions


def test_workflow_creation():
    """Test workflow model creation"""
    node1 = WorkflowNode(
        id="node1",
        agent_id="agent1",
        position={"x": 100, "y": 200}
    )
    
    node2 = WorkflowNode(
        id="node2",
        agent_id="agent2",
        position={"x": 300, "y": 200}
    )
    
    edge = WorkflowEdge(
        id="edge1",
        source_node_id="node1",
        target_node_id="node2"
    )
    
    workflow_data = WorkflowCreate(
        name="Test Workflow",
        description="A test workflow",
        nodes=[node1, node2],
        edges=[edge],
        trigger_conditions=[TriggerType.MANUAL]
    )
    
    workflow = Workflow(id="workflow_id", **workflow_data.dict())
    
    assert workflow.id == "workflow_id"
    assert workflow.name == "Test Workflow"
    assert len(workflow.nodes) == 2
    assert len(workflow.edges) == 1
    assert workflow.status == WorkflowStatus.IDLE


def test_workflow_node_validation():
    """Test workflow node validation"""
    node = WorkflowNode(
        id="test_node",
        agent_id="test_agent",
        position={"x": 0, "y": 0},
        config={"setting": "value"}
    )
    
    assert node.id == "test_node"
    assert node.agent_id == "test_agent"
    assert node.position == {"x": 0, "y": 0}
    assert node.config == {"setting": "value"}


def test_workflow_edge_validation():
    """Test workflow edge validation"""
    edge = WorkflowEdge(
        id="test_edge",
        source_node_id="source",
        target_node_id="target",
        condition="result.success == true",
        data_mapping={"output": "input"}
    )
    
    assert edge.id == "test_edge"
    assert edge.source_node_id == "source"
    assert edge.target_node_id == "target"
    assert edge.condition == "result.success == true"
    assert edge.data_mapping == {"output": "input"}