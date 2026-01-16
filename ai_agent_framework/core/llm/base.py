"""Base LLM interface."""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Optional, Dict, Any
from pydantic import BaseModel


class Message(BaseModel):
    """Chat message model."""
    role: str  # system, user, assistant
    content: str


class LLMResponse(BaseModel):
    """LLM response model."""
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None
    finish_reason: Optional[str] = None


class BaseLLM(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(
        self,
        model_name: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ):
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.kwargs = kwargs
    
    @abstractmethod
    async def generate(
        self,
        messages: List[Message],
        **kwargs
    ) -> LLMResponse:
        """Generate a response from the LLM.
        
        Args:
            messages: List of chat messages
            **kwargs: Additional parameters
            
        Returns:
            LLMResponse with generated content
        """
        pass
    
    @abstractmethod
    async def stream_generate(
        self,
        messages: List[Message],
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream generate responses from the LLM.
        
        Args:
            messages: List of chat messages
            **kwargs: Additional parameters
            
        Yields:
            String chunks of the response
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the provider name."""
        pass
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text. Override for accurate counting."""
        return len(text) // 4  # Rough estimate
