import pytest
from backend.llm.base import LLMMessage, LLMRole, LLMProvider
from backend.llm.openai_provider import MockOpenAIProvider, OpenAIProvider
from backend.llm.anthropic_provider import MockAnthropicProvider, AnthropicProvider
from backend.llm.factory import LLMFactory


@pytest.mark.asyncio
async def test_mock_openai_provider():
    """Test the mock OpenAI provider"""
    provider = MockOpenAIProvider()
    
    assert provider.is_available()
    assert provider.model == "mock-gpt-3.5-turbo"
    
    # Test simple generation
    response = await provider.generate_simple("Hello, world!")
    assert isinstance(response, str)
    assert "Hello, world!" in response or "Mock response" in response
    
    # Test message-based generation
    messages = [
        LLMMessage(role=LLMRole.SYSTEM, content="You are a helpful assistant"),
        LLMMessage(role=LLMRole.USER, content="Say hello")
    ]
    
    llm_response = await provider.generate(messages)
    assert llm_response.content
    assert llm_response.usage
    assert llm_response.model == "mock-gpt-3.5-turbo"
    assert llm_response.finish_reason == "stop"


def test_openai_provider_without_key():
    """Test OpenAI provider without API key"""
    provider = OpenAIProvider(api_key=None)
    assert not provider.is_available()


@pytest.mark.asyncio
async def test_openai_provider_with_invalid_key():
    """Test OpenAI provider with invalid API key"""
    provider = OpenAIProvider(api_key="invalid-key")
    assert provider.is_available()  # Constructor succeeds
    
    # But API calls should fail
    with pytest.raises(RuntimeError, match="OpenAI API call failed"):
        await provider.generate_simple("Test prompt")


def test_llm_factory():
    """Test LLM factory functionality"""
    # Test listing providers
    providers = LLMFactory.list_providers()
    assert "openai" in providers
    assert "mock_openai" in providers
    assert "anthropic" in providers
    assert "mock_anthropic" in providers
    
    # Test creating mock providers
    mock_openai = LLMFactory.create_provider("mock_openai")
    assert isinstance(mock_openai, MockOpenAIProvider)
    assert mock_openai.is_available()
    
    mock_anthropic = LLMFactory.create_provider("mock_anthropic")
    assert isinstance(mock_anthropic, MockAnthropicProvider)
    assert mock_anthropic.is_available()
    
    # Test creating real providers
    openai_provider = LLMFactory.create_provider("openai", api_key="test-key")
    assert isinstance(openai_provider, OpenAIProvider)
    
    anthropic_provider = LLMFactory.create_provider("anthropic", api_key="test-key")
    assert isinstance(anthropic_provider, AnthropicProvider)
    
    # Test unknown provider
    with pytest.raises(ValueError, match="Unknown provider type"):
        LLMFactory.create_provider("unknown_provider")


def test_llm_factory_default_provider():
    """Test default provider creation"""
    provider = LLMFactory.create_default_provider()
    assert isinstance(provider, LLMProvider)
    # Should be mock provider unless OPENAI_API_KEY is set
    assert provider.is_available()


@pytest.mark.asyncio
async def test_llm_message_roles():
    """Test LLM message role validation"""
    # Test valid roles
    system_msg = LLMMessage(role=LLMRole.SYSTEM, content="System prompt")
    user_msg = LLMMessage(role=LLMRole.USER, content="User message")
    assistant_msg = LLMMessage(role=LLMRole.ASSISTANT, content="Assistant response")
    
    assert system_msg.role == LLMRole.SYSTEM
    assert user_msg.role == LLMRole.USER
    assert assistant_msg.role == LLMRole.ASSISTANT
    
    # Test conversation flow
    provider = MockOpenAIProvider()
    messages = [system_msg, user_msg]
    
    response = await provider.generate(messages)
    assert response.content


@pytest.mark.asyncio
async def test_mock_anthropic_provider():
    """Test the mock Anthropic provider"""
    provider = MockAnthropicProvider()
    
    assert provider.is_available()
    assert provider.model == "mock-claude-3-haiku"
    
    # Test simple generation
    response = await provider.generate_simple("Hello, I'm testing Claude!")
    assert isinstance(response, str)
    assert "Claude" in response
    assert "mock" in response.lower()
    
    # Test message-based generation
    messages = [
        LLMMessage(role=LLMRole.SYSTEM, content="You are Claude, a helpful AI assistant"),
        LLMMessage(role=LLMRole.USER, content="Tell me about yourself")
    ]
    
    llm_response = await provider.generate(messages)
    assert llm_response.content
    assert llm_response.usage
    assert llm_response.model == "mock-claude-3-haiku"
    assert llm_response.finish_reason == "end_turn"
    assert "Claude" in llm_response.content


def test_anthropic_provider_without_key():
    """Test Anthropic provider without API key"""
    provider = AnthropicProvider(api_key=None)
    assert not provider.is_available()


@pytest.mark.asyncio
async def test_anthropic_provider_with_invalid_key():
    """Test Anthropic provider with invalid API key"""
    provider = AnthropicProvider(api_key="invalid-key")
    assert provider.is_available()  # Constructor succeeds
    
    # But API calls should fail
    with pytest.raises(RuntimeError, match="Anthropic API call failed"):
        await provider.generate_simple("Test prompt")