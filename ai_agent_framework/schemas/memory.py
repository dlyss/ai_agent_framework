"""Memory schemas."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class MemoryItemInput(BaseModel):
    """Memory item input."""
    content: str = Field(..., description="Memory content")
    role: str = Field("user", description="Role: user, assistant, system")
    importance: float = Field(0.5, ge=0, le=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MemoryItemResponse(BaseModel):
    """Memory item response."""
    id: str
    content: str
    role: str
    importance: float
    timestamp: datetime
    metadata: Dict[str, Any] = {}


class MemorySearchRequest(BaseModel):
    """Memory search request."""
    query: str
    limit: int = Field(10, ge=1, le=100)
    include_short_term: bool = True
    include_long_term: bool = True


class MemorySearchResponse(BaseModel):
    """Memory search response."""
    items: List[MemoryItemResponse]
    total: int


class ConversationHistoryRequest(BaseModel):
    """Conversation history request."""
    session_id: str
    max_turns: Optional[int] = None
    max_tokens: int = 4000


class ConversationHistoryResponse(BaseModel):
    """Conversation history response."""
    messages: List[Dict[str, str]]
    total_items: int


class MemoryStatsResponse(BaseModel):
    """Memory statistics response."""
    short_term_count: int
    long_term_count: int
    short_term_max_size: int


class MemoryClearRequest(BaseModel):
    """Memory clear request."""
    session_id: Optional[str] = None
    clear_short_term: bool = True
    clear_long_term: bool = False
