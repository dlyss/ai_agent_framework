"""RAG schemas."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class DocumentInput(BaseModel):
    """Document input for RAG."""
    content: str = Field(..., description="Document content")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    id: Optional[str] = None


class DocumentsUploadRequest(BaseModel):
    """Bulk document upload request."""
    documents: List[DocumentInput]
    collection_name: Optional[str] = None


class DocumentsUploadResponse(BaseModel):
    """Document upload response."""
    ids: List[str]
    count: int
    collection_name: str


class RAGQueryRequest(BaseModel):
    """RAG query request."""
    question: str = Field(..., description="User question")
    collection_name: Optional[str] = None
    top_k: int = Field(5, ge=1, le=20)
    filters: Optional[Dict[str, Any]] = None
    include_sources: bool = True
    stream: bool = False


class SourceDocument(BaseModel):
    """Source document in RAG response."""
    id: str
    content: str
    score: float
    metadata: Dict[str, Any] = {}


class RAGQueryResponse(BaseModel):
    """RAG query response."""
    answer: str
    sources: Optional[List[SourceDocument]] = None
    model: str
    usage: Optional[Dict[str, int]] = None


class CollectionInfo(BaseModel):
    """Collection information."""
    name: str
    document_count: int
    dimension: int


class CollectionListResponse(BaseModel):
    """Collection list response."""
    collections: List[CollectionInfo]


class CollectionCreateRequest(BaseModel):
    """Collection creation request."""
    name: str = Field(..., min_length=1, max_length=100)
    dimension: int = Field(768, description="Vector dimension")
    description: str = ""
