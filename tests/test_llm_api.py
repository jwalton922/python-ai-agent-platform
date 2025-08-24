import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_get_current_provider():
    """Test getting current LLM provider info"""
    response = client.get("/api/llm/provider")
    assert response.status_code == 200
    
    data = response.json()
    assert "provider_type" in data
    assert "model" in data
    assert "is_available" in data
    assert isinstance(data["is_available"], bool)


def test_list_available_providers():
    """Test listing available LLM providers"""
    response = client.get("/api/llm/providers")
    assert response.status_code == 200
    
    data = response.json()
    assert "providers" in data
    assert "current" in data
    assert isinstance(data["providers"], list)
    assert "openai" in data["providers"]
    assert "mock_openai" in data["providers"]


def test_llm_test_endpoint():
    """Test the LLM test endpoint"""
    test_request = {
        "prompt": "Say hello",
        "system_prompt": "You are a helpful assistant",
        "temperature": 0.7,
        "max_tokens": 50
    }
    
    response = client.post("/api/llm/test", json=test_request)
    assert response.status_code == 200
    
    data = response.json()
    assert "response" in data
    assert "provider" in data
    assert "model" in data
    assert "success" in data
    assert data["success"] is True
    assert isinstance(data["response"], str)
    assert len(data["response"]) > 0


def test_llm_chat_endpoint():
    """Test the LLM chat endpoint"""
    messages = [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello!"}
    ]
    
    response = client.post("/api/llm/chat", json=messages)
    assert response.status_code == 200
    
    data = response.json()
    assert "response" in data
    assert "usage" in data
    assert "model" in data
    assert "provider" in data
    assert isinstance(data["response"], str)


def test_llm_chat_invalid_role():
    """Test chat endpoint with invalid role"""
    messages = [
        {"role": "invalid", "content": "This should fail"}
    ]
    
    response = client.post("/api/llm/chat", json=messages)
    # Error is properly caught and reported, though wrapped in 500
    assert response.status_code == 500
    assert "Invalid role" in response.json()["detail"]


def test_llm_test_minimal_request():
    """Test LLM test with minimal request"""
    test_request = {
        "prompt": "Test"
    }
    
    response = client.post("/api/llm/test", json=test_request)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert len(data["response"]) > 0