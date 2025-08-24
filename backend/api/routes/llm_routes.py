from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from backend.llm.factory import LLMFactory, llm_provider
from backend.llm.base import LLMMessage, LLMRole

router = APIRouter()


class LLMProviderInfo(BaseModel):
    provider_type: str
    model: str
    is_available: bool


class LLMTestRequest(BaseModel):
    prompt: str
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = 100


class LLMTestResponse(BaseModel):
    response: str
    provider: str
    model: str
    success: bool
    error: Optional[str] = None


@router.get("/provider", response_model=LLMProviderInfo)
async def get_current_provider():
    """Get information about the current LLM provider"""
    return LLMProviderInfo(
        provider_type=type(llm_provider).__name__.replace("Provider", "").lower(),
        model=llm_provider.model,
        is_available=llm_provider.is_available()
    )


@router.get("/providers")
async def list_available_providers():
    """List all available LLM provider types"""
    return {
        "providers": LLMFactory.list_providers(),
        "current": type(llm_provider).__name__.replace("Provider", "").lower()
    }


@router.post("/test", response_model=LLMTestResponse)
async def test_llm(request: LLMTestRequest):
    """Test the current LLM provider with a simple prompt"""
    try:
        if not llm_provider.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="LLM provider is not available. Check configuration."
            )
        
        response = await llm_provider.generate_simple(
            prompt=request.prompt,
            system_prompt=request.system_prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        return LLMTestResponse(
            response=response,
            provider=type(llm_provider).__name__,
            model=llm_provider.model,
            success=True
        )
        
    except Exception as e:
        return LLMTestResponse(
            response="",
            provider=type(llm_provider).__name__,
            model=llm_provider.model,
            success=False,
            error=str(e)
        )


@router.post("/chat")
async def chat_with_llm(messages: list[Dict[str, str]], temperature: float = 0.7):
    """Chat with the LLM using a conversation format"""
    try:
        if not llm_provider.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="LLM provider is not available. Check configuration."
            )
        
        # Convert dict messages to LLMMessage objects
        llm_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role not in ["system", "user", "assistant"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid role: {role}. Must be system, user, or assistant."
                )
            
            try:
                llm_messages.append(LLMMessage(role=LLMRole(role), content=content))
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid role value: {str(e)}"
                )
        
        response = await llm_provider.generate(
            messages=llm_messages,
            temperature=temperature
        )
        
        return {
            "response": response.content,
            "usage": response.usage,
            "model": response.model,
            "provider": type(llm_provider).__name__
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM generation failed: {str(e)}"
        )