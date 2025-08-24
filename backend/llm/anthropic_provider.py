import os
from typing import List, Optional
import asyncio
from anthropic import AsyncAnthropic
from backend.llm.base import LLMProvider, LLMMessage, LLMResponse, LLMRole


class AnthropicProvider(LLMProvider):
    """Anthropic Claude LLM Provider implementation"""
    
    def __init__(
        self, 
        model: str = "claude-3-haiku-20240307", 
        api_key: Optional[str] = None, 
        **kwargs
    ):
        super().__init__(model, api_key, **kwargs)
        
        # Use provided API key or environment variable
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        
        if self.api_key:
            self.client = AsyncAnthropic(api_key=self.api_key)
        else:
            self.client = None
    
    async def generate(
        self, 
        messages: List[LLMMessage], 
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate a response from Anthropic Claude API"""
        if not self.client:
            raise ValueError("Anthropic API key not configured")
        
        try:
            # Convert our messages to Anthropic format
            # Claude expects system message separate from conversation
            system_message = None
            conversation_messages = []
            
            for msg in messages:
                if msg.role == LLMRole.SYSTEM:
                    # Use the last system message if multiple exist
                    system_message = msg.content
                else:
                    conversation_messages.append({
                        "role": "user" if msg.role == LLMRole.USER else "assistant",
                        "content": msg.content
                    })
            
            # Ensure we have at least one user message
            if not conversation_messages or conversation_messages[0]["role"] != "user":
                conversation_messages.insert(0, {
                    "role": "user", 
                    "content": "Please respond based on the context provided."
                })
            
            # Set default max_tokens if not provided (Claude requires this)
            if max_tokens is None:
                max_tokens = 1000
            
            # Make the API call
            response = await self.client.messages.create(
                model=self.model,
                messages=conversation_messages,
                system=system_message,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            
            # Extract the response content
            content = ""
            if response.content and len(response.content) > 0:
                # Claude returns content as a list of content blocks
                for block in response.content:
                    if hasattr(block, 'text'):
                        content += block.text
                    else:
                        content += str(block)
            
            # Build our response object
            return LLMResponse(
                content=content,
                usage={
                    "input_tokens": response.usage.input_tokens if response.usage else None,
                    "output_tokens": response.usage.output_tokens if response.usage else None,
                    "total_tokens": (response.usage.input_tokens + response.usage.output_tokens) if response.usage else None,
                },
                model=response.model,
                finish_reason=response.stop_reason,
                raw_response=response.model_dump() if hasattr(response, 'model_dump') else str(response)
            )
            
        except Exception as e:
            raise RuntimeError(f"Anthropic API call failed: {str(e)}")
    
    async def generate_simple(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """Simple text-in, text-out generation"""
        messages = []
        
        # Add system prompt if provided
        if system_prompt:
            messages.append(LLMMessage(role=LLMRole.SYSTEM, content=system_prompt))
        
        # Add user prompt
        messages.append(LLMMessage(role=LLMRole.USER, content=prompt))
        
        # Generate response
        response = await self.generate(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        return response.content
    
    def is_available(self) -> bool:
        """Check if Anthropic provider is properly configured"""
        return self.client is not None and self.api_key is not None


class MockAnthropicProvider(LLMProvider):
    """Mock Anthropic provider for testing and development"""
    
    def __init__(self, model: str = "mock-claude-3-haiku", api_key: Optional[str] = None, **kwargs):
        super().__init__(model, api_key, **kwargs)
    
    async def generate(
        self, 
        messages: List[LLMMessage], 
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate a mock Claude response"""
        # Simulate API delay
        await asyncio.sleep(0.1)
        
        # Extract the last user message for context
        user_messages = [msg for msg in messages if msg.role == LLMRole.USER]
        last_user_message = user_messages[-1].content if user_messages else "No user input"
        
        # Generate Claude-style mock response
        mock_content = f"I'm Claude, and I'd be happy to help with your request: '{last_user_message[:50]}...'. This is a mock response for development."
        
        return LLMResponse(
            content=mock_content,
            usage={
                "input_tokens": 25,
                "output_tokens": 30,
                "total_tokens": 55,
            },
            model=self.model,
            finish_reason="end_turn",
            raw_response={"mock": True, "provider": "anthropic"}
        )
    
    async def generate_simple(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """Simple mock Claude generation"""
        await asyncio.sleep(0.1)
        return f"I'm Claude (mock). Regarding '{prompt[:50]}...': This is a mock response for development purposes."
    
    def is_available(self) -> bool:
        """Mock Claude provider is always available"""
        return True