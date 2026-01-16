"""Chat schemas."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class MessageSchema(BaseModel):
    """Chat message schema."""
    role: str = Field(..., description="Message role: system, user, or assistant")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Chat request schema."""
    messages: List[MessageSchema] = Field(..., description="Conversation messages")
    model: Optional[str] = Field(None, description="Model to use")
    provider: Optional[str] = Field(None, description="Provider: openai, qwen, llama")
    temperature: Optional[float] = Field(0.7, ge=0, le=2)
    max_tokens: Optional[int] = Field(2048, ge=1, le=32000)
    stream: bool = Field(False, description="Enable streaming response")
    session_id: Optional[str] = Field(None, description="Session ID for memory")


class ChatResponse(BaseModel):
    """Chat response schema."""
    content: str
    model: str
    provider: str
    usage: Optional[Dict[str, int]] = None
    finish_reason: Optional[str] = None


class ChatStreamChunk(BaseModel):
    """Chat stream chunk schema."""
    content: str
    done: bool = False


class ProviderInfo(BaseModel):
    """Provider information."""
    name: str
    models: List[str]
    description: str = ""


class ModelListResponse(BaseModel):
    """Model list response."""
    providers: List[ProviderInfo]
