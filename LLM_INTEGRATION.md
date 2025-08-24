# LLM Integration Documentation

## Overview

The AI Agent Platform now includes a flexible LLM (Large Language Model) integration system that allows AI agents to call real language models for text generation and conversation.

## Features

✅ **Pluggable LLM Interface**: Abstract base class for different LLM providers  
✅ **OpenAI Integration**: Complete OpenAI API implementation with error handling  
✅ **Mock Provider**: Development and testing provider that works without API keys  
✅ **Automatic Fallback**: Falls back to mock responses if real LLM fails  
✅ **Configuration Management**: Environment-based configuration with sensible defaults  
✅ **Comprehensive Testing**: Full test coverage for all LLM functionality  

## Architecture

```
backend/llm/
├── base.py              # Abstract LLM interface
├── openai_provider.py   # OpenAI implementation + Mock provider  
└── factory.py           # LLM provider factory and management
```

### LLM Provider Interface

All LLM providers implement the `LLMProvider` abstract base class:

```python
class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, messages: List[LLMMessage], **kwargs) -> LLMResponse
    
    @abstractmethod 
    async def generate_simple(self, prompt: str, system_prompt: str = None, **kwargs) -> str
    
    @abstractmethod
    def is_available(self) -> bool
```

### Available Providers

1. **OpenAIProvider** - Real OpenAI API integration (GPT models)
2. **AnthropicProvider** - Real Anthropic API integration (Claude models) ⭐
3. **MockOpenAIProvider** - Development/testing mock provider
4. **MockAnthropicProvider** - Development/testing mock provider

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here

# LLM Provider Settings
AGENT_PLATFORM_DEFAULT_LLM_PROVIDER=openai
AGENT_PLATFORM_DEFAULT_LLM_MODEL=gpt-3.5-turbo
```

### Automatic Provider Selection

The system automatically selects the best available provider:

1. **With OPENAI_API_KEY** → Uses real OpenAI API
2. **Without API key** → Uses mock provider for development

## API Endpoints

### Get Current Provider
```bash
GET /api/llm/provider
```
Returns information about the currently active LLM provider.

**Response:**
```json
{
  "provider_type": "openai",
  "model": "gpt-3.5-turbo", 
  "is_available": true
}
```

### List Available Providers
```bash
GET /api/llm/providers
```
Lists all available LLM provider types.

**Response:**
```json
{
  "providers": ["openai", "mock_openai"],
  "current": "openai"
}
```

### Test LLM
```bash
POST /api/llm/test
```
Test the current provider with a simple prompt.

**Request:**
```json
{
  "prompt": "Write a Python function to calculate fibonacci numbers",
  "system_prompt": "You are a helpful programming assistant",
  "temperature": 0.7,
  "max_tokens": 500
}
```

**Response:**
```json
{
  "response": "Here's a Python function to calculate fibonacci numbers:\n\ndef fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
  "provider": "OpenAIProvider",
  "model": "gpt-3.5-turbo",
  "success": true,
  "error": null
}
```

### Chat with LLM
```bash
POST /api/llm/chat
```
Have a conversation with the LLM using message history.

**Request:**
```json
[
  {"role": "system", "content": "You are a helpful assistant"},
  {"role": "user", "content": "Explain quantum computing"},
  {"role": "assistant", "content": "Quantum computing is..."},
  {"role": "user", "content": "Can you give a simple example?"}
]
```

**Response:**
```json
{
  "response": "Sure! Here's a simple example...",
  "usage": {
    "prompt_tokens": 45,
    "completion_tokens": 120,
    "total_tokens": 165
  },
  "model": "gpt-3.5-turbo",
  "provider": "OpenAIProvider"
}
```

## Workflow Integration

AI agents in workflows now automatically use the LLM system for text generation. When a workflow executes:

1. **Agent Instructions** → Used as system prompt
2. **Workflow Context** → Passed as user prompt
3. **Node Configuration** → Additional context
4. **LLM Response** → Returned as agent output

### Example Workflow Execution

```bash
# Create an agent
POST /api/agents/
{
  "name": "Code Reviewer",
  "instructions": "You are an expert code reviewer. Analyze code for best practices, performance, and maintainability."
}

# Create workflow
POST /api/workflows/
{
  "name": "Code Review Process",
  "nodes": [{
    "id": "review_node",
    "agent_id": "agent-id-here",
    "config": {"focus": "security", "language": "python"}
  }]
}

# Execute workflow
POST /api/workflows/{workflow_id}/execute
{
  "context": {
    "code": "def process_data(data): return data.upper()"
  }
}
```

The agent will receive:
- **System prompt**: "You are an expert code reviewer..."
- **User prompt**: "Process this workflow step.\n\nContext:\nNode configuration: {focus: security, language: python}"

## Usage Examples

### Direct LLM Usage

```python
from backend.llm.factory import llm_provider

# Simple generation
response = await llm_provider.generate_simple(
    "Write a haiku about programming",
    system_prompt="You are a creative poet"
)

# Conversation
messages = [
    LLMMessage(role=LLMRole.SYSTEM, content="You are helpful"),
    LLMMessage(role=LLMRole.USER, content="Hello!")
]
llm_response = await llm_provider.generate(messages)
```

### Creating Custom Providers

```python
class CustomLLMProvider(LLMProvider):
    def __init__(self, model: str, api_key: str = None, **kwargs):
        super().__init__(model, api_key, **kwargs)
    
    async def generate(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        # Your implementation here
        pass
    
    async def generate_simple(self, prompt: str, system_prompt: str = None, **kwargs) -> str:
        # Your implementation here  
        pass
    
    def is_available(self) -> bool:
        # Check if provider is configured
        pass

# Register with factory
LLMFactory._providers["custom"] = CustomLLMProvider
```

## Testing

### Run LLM Tests
```bash
python3 -m pytest tests/test_llm.py -v
python3 -m pytest tests/test_llm_api.py -v
```

### Test Coverage
- ✅ Mock provider functionality
- ✅ OpenAI provider configuration
- ✅ Factory provider creation
- ✅ API endpoint responses  
- ✅ Error handling
- ✅ Workflow integration

## Error Handling

The LLM integration includes comprehensive error handling:

1. **Provider Unavailable** → Automatic fallback to mock provider
2. **API Failures** → Graceful error responses with fallback
3. **Invalid Parameters** → Proper HTTP error codes
4. **Rate Limiting** → Handled by underlying OpenAI client

## Production Deployment

### OpenAI Configuration
1. Get OpenAI API key from https://platform.openai.com/api-keys
2. Set `OPENAI_API_KEY` environment variable
3. Choose model: `gpt-3.5-turbo`, `gpt-4`, etc.
4. Configure rate limits and usage monitoring

### Environment Setup
```bash
# Production .env
OPENAI_API_KEY=sk-your-real-api-key
AGENT_PLATFORM_DEFAULT_LLM_PROVIDER=openai
AGENT_PLATFORM_DEFAULT_LLM_MODEL=gpt-3.5-turbo
AGENT_PLATFORM_DEBUG=false
```

### Monitoring
- Monitor API usage via OpenAI dashboard
- Track token consumption in activity logs
- Set up alerts for API errors or rate limits

## Future Enhancements

**Planned Features:**
- Support for more providers (Anthropic Claude, Cohere, etc.)
- Token usage tracking and billing
- Rate limiting and queuing
- Response caching
- Streaming responses
- Function calling integration
- Fine-tuned model support

## Security Notes

⚠️ **API Key Security**
- Never commit API keys to version control
- Use environment variables or secure key management
- Rotate keys regularly
- Monitor usage for unauthorized access

⚠️ **Input Validation**
- All user inputs are validated before sending to LLM
- System prompts are controlled by admin/agent configuration
- Rate limiting prevents abuse

## Support

For issues or questions about LLM integration:
1. Check the test files for usage examples
2. Review error logs in activity monitoring
3. Verify provider configuration with `/api/llm/provider`
4. Test connectivity with `/api/llm/test`