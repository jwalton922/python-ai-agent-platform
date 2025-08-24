# Using Claude Code with AI Agent Platform

## Overview

Yes! You can absolutely use your **Claude Code subscription** with this AI Agent Platform. The platform now includes full support for Anthropic's Claude models, allowing your AI agents to leverage Claude's capabilities for:

- 🧠 Advanced reasoning and analysis
- 💻 Expert code generation and debugging  
- 📝 Clear, helpful explanations
- 🔍 Thorough problem-solving

## Quick Setup for Claude Code Users

### 1. Get Your Anthropic API Key

Your Claude Code subscription gives you access to Anthropic's API. Get your API key from:
- Anthropic Console: https://console.anthropic.com/
- Account Settings → API Keys

### 2. Configure the Platform

```bash
# Set your Anthropic API key
export ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Or add to .env file
echo "ANTHROPIC_API_KEY=your-anthropic-api-key-here" >> .env
echo "AGENT_PLATFORM_DEFAULT_LLM_PROVIDER=anthropic" >> .env
```

### 3. Start the Platform

```bash
# Install dependencies (if not done yet)
pip install -r requirements.txt

# Start the backend
python3 -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

## Available Claude Models

The platform supports all Anthropic Claude models:

### **Claude 3.5 Sonnet** (Recommended)
- Model ID: `claude-3-5-sonnet-20241022`
- Best overall performance
- Excellent for code generation and analysis

### **Claude 3 Haiku** (Fast & Efficient)
- Model ID: `claude-3-haiku-20240307` ⭐ **Default**
- Fastest responses
- Cost-effective for most tasks

### **Claude 3 Opus** (Most Capable)
- Model ID: `claude-3-opus-20240229`
- Highest reasoning capability
- Best for complex problem-solving

## Configuration Options

### Environment Variables

```bash
# Use Claude as the default provider
AGENT_PLATFORM_DEFAULT_LLM_PROVIDER=anthropic

# Choose your preferred Claude model
AGENT_PLATFORM_DEFAULT_LLM_MODEL=claude-3-5-sonnet-20241022

# Your API key
ANTHROPIC_API_KEY=your-api-key-here
```

### Model Selection in Code

```python
# Create specific Claude provider
from backend.llm.factory import LLMFactory

# Claude 3.5 Sonnet
claude_sonnet = LLMFactory.create_provider(
    "anthropic", 
    model="claude-3-5-sonnet-20241022",
    api_key="your-key"
)

# Claude 3 Haiku (fast)
claude_haiku = LLMFactory.create_provider(
    "anthropic",
    model="claude-3-haiku-20240307",
    api_key="your-key"
)
```

## Usage Examples

### 1. Test Claude Integration

```bash
# Check that Claude is active
curl http://localhost:8000/api/llm/provider

# Expected response:
# {"provider_type":"anthropic","model":"claude-3-haiku-20240307","is_available":true}

# Test Claude with a prompt
curl -X POST http://localhost:8000/api/llm/test \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a Python function to implement binary search",
    "system_prompt": "You are Claude, an AI assistant. Provide clean, well-commented code."
  }'
```

### 2. Create Claude-Powered Agents

```bash
# Create a programming assistant powered by Claude
curl -X POST http://localhost:8000/api/agents/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Claude Code Assistant",
    "description": "Expert programming help powered by Claude",
    "instructions": "I am Claude, an AI assistant created by Anthropic. I excel at helping with programming tasks, code review, debugging, and explaining technical concepts clearly and thoroughly.",
    "mcp_tool_permissions": ["file_tool"],
    "trigger_conditions": ["manual"]
  }'
```

### 3. Conversational Programming Help

```bash
curl -X POST http://localhost:8000/api/llm/chat \
  -H "Content-Type: application/json" \
  -d '[
    {
      "role": "system", 
      "content": "You are Claude, an expert programmer. Help users write clean, efficient code with detailed explanations."
    },
    {
      "role": "user", 
      "content": "I need to implement a rate limiter in Python. Can you help?"
    }
  ]'
```

### 4. Code Review Workflow

```python
# Create a comprehensive code review workflow
workflow_data = {
    "name": "Claude Code Review",
    "description": "Thorough code review powered by Claude",
    "nodes": [
        {
            "id": "security_review",
            "agent_id": "your-claude-agent-id",
            "config": {"focus": "security", "depth": "detailed"}
        },
        {
            "id": "performance_review", 
            "agent_id": "your-claude-agent-id",
            "config": {"focus": "performance", "suggestions": True}
        }
    ],
    "trigger_conditions": ["manual"]
}
```

## Claude-Specific Features

### System Prompts
Claude works exceptionally well with detailed system prompts:

```python
system_prompt = """You are Claude, an AI assistant created by Anthropic. You are:
- Expert at programming and software development
- Focused on writing clean, maintainable code
- Thorough in explanations and helpful in teaching
- Careful about security and best practices
- Always honest about limitations and uncertainties"""
```

### Multi-turn Conversations
Claude excels at maintaining context across conversation turns:

```python
conversation = [
    {"role": "system", "content": "You are a helpful coding assistant."},
    {"role": "user", "content": "Help me design a REST API"},
    {"role": "assistant", "content": "I'd be happy to help you design a REST API..."},
    {"role": "user", "content": "How should I handle authentication?"}
]
```

## Cost Optimization

### Choose the Right Model

| Model | Use Case | Speed | Cost |
|-------|----------|-------|------|
| **Claude 3 Haiku** | Simple tasks, fast responses | ⚡⚡⚡ | 💰 |
| **Claude 3.5 Sonnet** | Most tasks, best balance | ⚡⚡ | 💰💰 |
| **Claude 3 Opus** | Complex reasoning | ⚡ | 💰💰💰 |

### Token Management

```python
# Set reasonable token limits
response = await claude_provider.generate_simple(
    prompt="Your prompt here",
    max_tokens=500,  # Limit response length
    temperature=0.7
)
```

## Error Handling & Fallbacks

The platform includes automatic fallbacks:

1. **With ANTHROPIC_API_KEY** → Uses real Claude API
2. **Without API key** → Uses mock Claude responses  
3. **On API failure** → Automatic fallback to mock responses

```python
# Fallback is automatic and transparent
try:
    result = await workflow_executor.execute_workflow(workflow_id, context)
    # Will use Claude if available, mock if not
except Exception as e:
    # Platform handles errors gracefully
    print(f"Workflow completed with fallback: {result}")
```

## Monitoring & Usage

### API Usage Tracking

Monitor your Claude usage through:
- **Anthropic Console**: https://console.anthropic.com/
- **Platform Activity Feed**: `/api/activities/`
- **Workflow Results**: Check `llm_provider` field in responses

### Usage Analytics

```python
# Check which provider was used
result = await execute_workflow(workflow_id)
provider_used = result["results"]["node_id"]["llm_provider"]
# Returns: "AnthropicProvider" or "MockAnthropicProvider"
```

## Best Practices for Claude Code Users

### 1. Optimize Agent Instructions
```python
# Good: Specific, detailed instructions
instructions = """You are Claude, a senior software engineer. When reviewing code:
1. Check for security vulnerabilities
2. Suggest performance improvements  
3. Ensure code follows Python PEP 8
4. Provide specific, actionable feedback
5. Include code examples in your suggestions"""

# Avoid: Vague instructions
instructions = "Help with code"
```

### 2. Use Appropriate Context
```python
# Provide relevant context in workflow execution
context = {
    "code_language": "python",
    "project_type": "web_api",
    "security_level": "high",
    "performance_critical": True
}
```

### 3. Leverage Claude's Strengths
- **Code Analysis**: Claude excels at understanding complex codebases
- **Documentation**: Excellent at writing clear, comprehensive docs
- **Debugging**: Systematic approach to finding and fixing issues
- **Architecture**: Strong at system design and architectural decisions

## Troubleshooting

### Common Issues

**"Anthropic API key not configured"**
```bash
# Check your environment
echo $ANTHROPIC_API_KEY

# Or check .env file
cat .env | grep ANTHROPIC
```

**"Provider not available"**
```bash
# Test API connectivity
curl -X GET http://localhost:8000/api/llm/provider
```

**Rate Limits**
- Claude has generous rate limits for most use cases
- The platform automatically handles rate limit errors
- Consider using Claude 3 Haiku for high-volume tasks

### Debug Mode

```bash
# Enable debug logging
export AGENT_PLATFORM_DEBUG=true

# Check provider status
curl http://localhost:8000/api/llm/providers
```

## Advanced Usage

### Custom Claude Workflows

```python
# Create specialized Claude agents for different tasks
agents = [
    {
        "name": "Claude Code Reviewer",
        "instructions": "Focus on code quality, security, and maintainability"
    },
    {
        "name": "Claude Debugger", 
        "instructions": "Systematically identify and fix bugs"
    },
    {
        "name": "Claude Architect",
        "instructions": "Design scalable system architectures"
    }
]
```

### Integration with Development Workflow

```python
# Example: Automated code review workflow
workflow = {
    "name": "PR Review Pipeline",
    "nodes": [
        {"id": "syntax_check", "agent": "claude_reviewer"},
        {"id": "security_scan", "agent": "claude_security"},
        {"id": "performance_analysis", "agent": "claude_performance"}
    ]
}
```

## Support

For Claude-specific issues:
- **Anthropic Documentation**: https://docs.anthropic.com/
- **Claude Console**: https://console.anthropic.com/
- **Platform Issues**: Check `/api/llm/provider` status

---

**Ready to get started?** Your Claude Code subscription gives you access to one of the most capable AI models available. The AI Agent Platform makes it easy to leverage Claude's capabilities for automated workflows, code assistance, and intelligent agent behavior! 🚀