import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.storage.file_storage import file_storage as storage

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_storage():
    """Clear storage before each test"""
    storage.agents.clear()
    storage.workflows.clear()
    storage.activities.clear()


def test_health_endpoint():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_create_agent():
    """Test agent creation endpoint"""
    agent_data = {
        "name": "Test Agent",
        "description": "A test agent",
        "instructions": "You are helpful",
        "mcp_tool_permissions": ["email_tool"],
        "trigger_conditions": ["manual"]
    }
    
    response = client.post("/api/agents/", json=agent_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["name"] == "Test Agent"
    assert data["instructions"] == "You are helpful"
    assert "id" in data
    assert "created_at" in data


def test_list_agents():
    """Test agent listing endpoint"""
    # Create test agents
    for i in range(3):
        agent_data = {
            "name": f"Agent {i}",
            "instructions": f"Instructions {i}",
        }
        client.post("/api/agents/", json=agent_data)
    
    response = client.get("/api/agents/")
    assert response.status_code == 200
    
    agents = response.json()
    assert len(agents) == 3


def test_get_agent():
    """Test get specific agent endpoint"""
    # Create an agent
    agent_data = {
        "name": "Test Agent",
        "instructions": "Test instructions"
    }
    create_response = client.post("/api/agents/", json=agent_data)
    agent_id = create_response.json()["id"]
    
    # Get the agent
    response = client.get(f"/api/agents/{agent_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == agent_id
    assert data["name"] == "Test Agent"


def test_update_agent():
    """Test agent update endpoint"""
    # Create an agent
    agent_data = {
        "name": "Original Name",
        "instructions": "Original instructions"
    }
    create_response = client.post("/api/agents/", json=agent_data)
    agent_id = create_response.json()["id"]
    
    # Update the agent
    update_data = {
        "name": "Updated Name",
        "instructions": "Updated instructions"
    }
    response = client.put(f"/api/agents/{agent_id}", json=update_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["instructions"] == "Updated instructions"


def test_delete_agent():
    """Test agent deletion endpoint"""
    # Create an agent
    agent_data = {
        "name": "To Delete",
        "instructions": "Will be deleted"
    }
    create_response = client.post("/api/agents/", json=agent_data)
    agent_id = create_response.json()["id"]
    
    # Delete the agent
    response = client.delete(f"/api/agents/{agent_id}")
    assert response.status_code == 204
    
    # Verify it's gone
    get_response = client.get(f"/api/agents/{agent_id}")
    assert get_response.status_code == 404


def test_create_workflow():
    """Test workflow creation endpoint"""
    workflow_data = {
        "name": "Test Workflow",
        "description": "A test workflow",
        "nodes": [
            {
                "id": "node1",
                "agent_id": "agent1",
                "position": {"x": 100, "y": 100}
            }
        ],
        "edges": [],
        "trigger_conditions": ["manual"]
    }
    
    response = client.post("/api/workflows/", json=workflow_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["name"] == "Test Workflow"
    assert len(data["nodes"]) == 1
    assert "id" in data


def test_list_mcp_tools():
    """Test MCP tools listing endpoint"""
    response = client.get("/api/mcp-tools/")
    assert response.status_code == 200
    
    tools = response.json()
    assert len(tools) >= 3  # We have at least email, slack, file tools
    
    tool_ids = [tool["id"] for tool in tools]
    assert "email_tool" in tool_ids
    assert "slack_tool" in tool_ids
    assert "file_tool" in tool_ids


def test_get_tool_schema():
    """Test getting tool schema endpoint"""
    response = client.get("/api/mcp-tools/email_tool/schema")
    assert response.status_code == 200
    
    schema = response.json()
    assert "input_schema" in schema
    assert "output_schema" in schema
    assert "description" in schema


def test_execute_tool_action():
    """Test tool execution endpoint"""
    params = {
        "action": "send",
        "to": "test@example.com",
        "subject": "Test Subject",
        "body": "Test Body"
    }
    
    response = client.post("/api/mcp-tools/email_tool/action", json=params)
    assert response.status_code == 200
    
    data = response.json()
    assert data["tool_id"] == "email_tool"
    assert data["success"] is True
    assert "result" in data