import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API Configuration
    app_name: str = "AI Agent Platform"
    debug: bool = False
    
    # LLM Configuration
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    default_llm_provider: str = "anthropic"  # "openai", "anthropic", or "mock_*"
    default_llm_model: str = "claude-3-haiku-20240307"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # CORS Configuration
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:8501",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8501"
    ]
    
    class Config:
        env_file = ".env"
        env_prefix = "AGENT_PLATFORM_"
        case_sensitive = False


# Global settings instance
settings = Settings()