"""Custom exceptions."""

from typing import Optional, Any


class AIAgentException(Exception):
    """Base exception for AI Agent Framework."""
    
    def __init__(self, message: str, detail: Optional[Any] = None):
        self.message = message
        self.detail = detail
        super().__init__(self.message)


class LLMException(AIAgentException):
    """LLM related exception."""
    pass


class VectorStoreException(AIAgentException):
    """Vector store related exception."""
    pass


class RAGException(AIAgentException):
    """RAG related exception."""
    pass


class MemoryException(AIAgentException):
    """Memory related exception."""
    pass


class FineTuneException(AIAgentException):
    """Fine-tuning related exception."""
    pass


class AuthenticationException(AIAgentException):
    """Authentication related exception."""
    pass


class ConfigurationException(AIAgentException):
    """Configuration related exception."""
    pass


class ValidationException(AIAgentException):
    """Validation related exception."""
    pass
