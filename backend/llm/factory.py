import os
from typing import Optional, Dict, Any
from backend.llm.base import LLMProvider
from backend.llm.openai_provider import OpenAIProvider, MockOpenAIProvider
from backend.llm.anthropic_provider import AnthropicProvider, MockAnthropicProvider


class LLMFactory:
    """Factory for creating LLM providers"""
    
    _providers = {
        "openai": OpenAIProvider,
        "mock_openai": MockOpenAIProvider,
        "anthropic": AnthropicProvider,
        "mock_anthropic": MockAnthropicProvider,
    }
    
    @classmethod
    def create_provider(
        self,
        provider_type: str,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        **kwargs
    ) -> LLMProvider:
        """Create an LLM provider instance"""
        if provider_type not in self._providers:
            raise ValueError(f"Unknown provider type: {provider_type}")
        
        provider_class = self._providers[provider_type]
        
        # Set default models for each provider
        default_models = {
            "openai": "gpt-3.5-turbo",
            "mock_openai": "mock-gpt-3.5-turbo",
            "anthropic": "claude-3-haiku-20240307",
            "mock_anthropic": "mock-claude-3-haiku"
        }
        
        if model is None:
            model = default_models.get(provider_type, "default")
        
        return provider_class(model=model, api_key=api_key, **kwargs)
    
    @classmethod
    def create_default_provider(self) -> LLMProvider:
        """Create the default LLM provider based on environment"""
        # Check environment preference first
        preferred_provider = os.getenv("AGENT_PLATFORM_DEFAULT_LLM_PROVIDER", "").lower()
        
        # Check for API keys
        openai_key = os.getenv("OPENAI_API_KEY")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        
        # Use explicit preference if set and available
        if preferred_provider == "anthropic" and anthropic_key:
            return self.create_provider("anthropic", api_key=anthropic_key)
        elif preferred_provider == "openai" and openai_key:
            return self.create_provider("openai", api_key=openai_key)
        
        # Auto-detect based on available keys
        if anthropic_key:
            return self.create_provider("anthropic", api_key=anthropic_key)
        elif openai_key:
            return self.create_provider("openai", api_key=openai_key)
        else:
            # Fall back to mock provider (prefer Claude mock for development)
            return self.create_provider("mock_anthropic")
    
    @classmethod
    def list_providers(self) -> list[str]:
        """List available provider types"""
        return list(self._providers.keys())


# Global LLM provider instance
llm_provider = LLMFactory.create_default_provider()