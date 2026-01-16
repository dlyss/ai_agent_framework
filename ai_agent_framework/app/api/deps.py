"""Dependency injection for FastAPI."""

from typing import Optional, Dict
from functools import lru_cache

from app.config import get_settings, Settings
from core.llm.factory import LLMFactory
from core.llm.base import BaseLLM
from core.vector_store.milvus_store import MilvusVectorStore
from core.rag.embeddings import EmbeddingModel
from core.rag.retriever import Retriever
from core.rag.chain import RAGChain
from core.prompt.manager import PromptManager
from core.prompt.router import PromptRouter
from core.memory.short_term import ShortTermMemory
from core.memory.long_term import LongTermMemory
from core.memory.manager import MemoryManager


# Singleton instances
_vector_store: Optional[MilvusVectorStore] = None
_embedding_model: Optional[EmbeddingModel] = None
_prompt_manager: Optional[PromptManager] = None
_prompt_router: Optional[PromptRouter] = None

# Session-based instances
_memory_managers: Dict[str, MemoryManager] = {}


def get_vector_store() -> MilvusVectorStore:
    """Get singleton vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = MilvusVectorStore()
    return _vector_store


def get_embedding_model() -> EmbeddingModel:
    """Get singleton embedding model instance."""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = EmbeddingModel()
    return _embedding_model


def get_prompt_manager() -> PromptManager:
    """Get singleton prompt manager instance."""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager


def get_prompt_router() -> PromptRouter:
    """Get singleton prompt router instance."""
    global _prompt_router
    if _prompt_router is None:
        _prompt_router = PromptRouter(
            prompt_manager=get_prompt_manager()
        )
    return _prompt_router


def get_llm(
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
    **kwargs
) -> BaseLLM:
    """Get LLM instance.
    
    Args:
        provider: LLM provider name
        model_name: Model name
        **kwargs: Additional LLM parameters
        
    Returns:
        LLM instance
    """
    return LLMFactory.create(
        provider=provider,
        model_name=model_name,
        **kwargs
    )


def get_retriever(
    collection_name: Optional[str] = None,
    top_k: int = 5
) -> Retriever:
    """Get retriever instance.
    
    Args:
        collection_name: Vector collection name
        top_k: Number of documents to retrieve
        
    Returns:
        Retriever instance
    """
    settings = get_settings()
    return Retriever(
        vector_store=get_vector_store(),
        embedding_model=get_embedding_model(),
        collection_name=collection_name or "default_collection",
        top_k=top_k
    )


def get_rag_chain(
    collection_name: Optional[str] = None,
    provider: Optional[str] = None,
    model_name: Optional[str] = None
) -> RAGChain:
    """Get RAG chain instance.
    
    Args:
        collection_name: Vector collection name
        provider: LLM provider
        model_name: Model name
        
    Returns:
        RAGChain instance
    """
    return RAGChain(
        llm=get_llm(provider=provider, model_name=model_name),
        retriever=get_retriever(collection_name=collection_name)
    )


def get_memory_manager(
    session_id: str,
    user_id: Optional[str] = None
) -> MemoryManager:
    """Get memory manager for a session.
    
    Args:
        session_id: Session identifier
        user_id: Optional user ID for long-term memory
        
    Returns:
        MemoryManager instance
    """
    cache_key = f"{session_id}:{user_id or 'anonymous'}"
    
    if cache_key not in _memory_managers:
        short_term = ShortTermMemory(session_id=session_id)
        long_term = LongTermMemory(
            vector_store=get_vector_store(),
            embedding_model=get_embedding_model(),
            user_id=user_id
        )
        _memory_managers[cache_key] = MemoryManager(
            short_term=short_term,
            long_term=long_term,
            llm=get_llm()
        )
    
    return _memory_managers[cache_key]


def clear_memory_manager(session_id: str, user_id: Optional[str] = None):
    """Clear memory manager for a session.
    
    Args:
        session_id: Session identifier
        user_id: Optional user ID
    """
    cache_key = f"{session_id}:{user_id or 'anonymous'}"
    if cache_key in _memory_managers:
        del _memory_managers[cache_key]


async def cleanup():
    """Cleanup resources on shutdown."""
    global _vector_store, _embedding_model
    
    if _vector_store:
        await _vector_store.disconnect()
        _vector_store = None
    
    _embedding_model = None
    _memory_managers.clear()
