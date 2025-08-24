import os
from typing import List, Optional
import asyncio
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion
from backend.llm.base import LLMProvider, LLMMessage, LLMResponse, LLMRole


class OpenAIProvider(LLMProvider):
    """OpenAI LLM Provider implementation"""
    
    def __init__(
        self, 
        model: str = "gpt-3.5-turbo", 
        api_key: Optional[str] = None, 
        **kwargs
    ):
        super().__init__(model, api_key, **kwargs)
        
        # Use provided API key or environment variable
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key)
        else:
            self.client = None
    
    async def generate(
        self, 
        messages: List[LLMMessage], 
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate a response from OpenAI API"""
        if not self.client:
            raise ValueError("OpenAI API key not configured")
        
        try:
            # Convert our messages to OpenAI format
            openai_messages = [
                {"role": msg.role.value, "content": msg.content}
                for msg in messages
            ]
            
            # Make the API call
            response: ChatCompletion = await self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            # Extract the response content
            content = response.choices[0].message.content or ""
            
            # Build our response object
            return LLMResponse(
                content=content,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
                    "completion_tokens": response.usage.completion_tokens if response.usage else None,
                    "total_tokens": response.usage.total_tokens if response.usage else None,
                },
                model=response.model,
                finish_reason=response.choices[0].finish_reason,
                raw_response=response.model_dump()
            )
            
        except Exception as e:
            raise RuntimeError(f"OpenAI API call failed: {str(e)}")
    
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
        """Check if OpenAI provider is properly configured"""
        return self.client is not None and self.api_key is not None


class MockOpenAIProvider(LLMProvider):
    """Mock OpenAI provider for testing and development"""
    
    def __init__(self, model: str = "mock-gpt-3.5-turbo", api_key: Optional[str] = None, **kwargs):
        super().__init__(model, api_key, **kwargs)
    
    async def generate(
        self, 
        messages: List[LLMMessage], 
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate a mock response"""
        # Simulate API delay
        await asyncio.sleep(0.1)
        
        # Extract the last user message for context
        user_messages = [msg for msg in messages if msg.role == LLMRole.USER]
        last_user_message = user_messages[-1].content if user_messages else "No user input"
        
        # Generate mock response
        mock_content = f"Mock AI response to: '{last_user_message[:50]}...'"
        
        return LLMResponse(
            content=mock_content,
            usage={
                "prompt_tokens": 20,
                "completion_tokens": 15,
                "total_tokens": 35,
            },
            model=self.model,
            finish_reason="stop",
            raw_response={"mock": True}
        )
    
    async def generate_simple(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """Simple mock generation"""
        await asyncio.sleep(0.1)
        return f"Mock response to: '{prompt[:50]}...'"
    
    def is_available(self) -> bool:
        """Mock provider is always available"""
        return True