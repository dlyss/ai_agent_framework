"""LangChain 1.x LLM wrapper implementation."""

from typing import AsyncGenerator, List, Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_core.output_parsers import StrOutputParser

from core.llm.base import BaseLLM, Message, LLMResponse
from app.config import get_settings


class LangChainLLM(BaseLLM):
    """LLM implementation using LangChain 1.x ChatOpenAI.
    
    This wrapper provides compatibility with our BaseLLM interface
    while using the modern LangChain 1.x API internally.
    
    Features:
    - Uses langchain_openai.ChatOpenAI
    - Supports invoke/ainvoke (LangChain 1.x API)
    - Supports streaming via astream
    - Compatible with existing codebase
    """
    
    def __init__(
        self,
        model_name: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        **kwargs
    ):
        """Initialize LangChain LLM.
        
        Args:
            model_name: Model identifier (e.g., "gpt-3.5-turbo", "gpt-4")
            temperature: Sampling temperature
            max_tokens: Maximum tokens for generation
            api_key: OpenAI API key (optional, uses env if not provided)
            api_base: OpenAI API base URL (optional)
            **kwargs: Additional parameters passed to ChatOpenAI
        """
        super().__init__(model_name, temperature, max_tokens, **kwargs)
        settings = get_settings()
        
        self.chat_model = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key or settings.openai_api_key,
            base_url=api_base or settings.openai_api_base,
            **{k: v for k, v in kwargs.items() if k not in ['model_name', 'temperature', 'max_tokens']}
        )
        
        self.output_parser = StrOutputParser()
    
    def _convert_messages(self, messages: List[Message]) -> List[BaseMessage]:
        """Convert our Message format to LangChain message format."""
        lc_messages = []
        for msg in messages:
            if msg.role == "system":
                lc_messages.append(SystemMessage(content=msg.content))
            elif msg.role == "user":
                lc_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                lc_messages.append(AIMessage(content=msg.content))
            else:
                lc_messages.append(HumanMessage(content=msg.content))
        return lc_messages
    
    async def generate(
        self,
        messages: List[Message],
        **kwargs
    ) -> LLMResponse:
        """Generate response using LangChain 1.x ainvoke.
        
        Args:
            messages: List of conversation messages
            **kwargs: Additional generation parameters
            
        Returns:
            LLMResponse with generated content
        """
        lc_messages = self._convert_messages(messages)
        
        # Update model parameters if provided
        model = self.chat_model
        if "temperature" in kwargs or "max_tokens" in kwargs:
            model = self.chat_model.bind(
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens", self.max_tokens)
            )
        
        # Use ainvoke (LangChain 1.x async API)
        response = await model.ainvoke(lc_messages)
        
        # Extract usage info if available
        usage = {}
        if hasattr(response, 'response_metadata'):
            token_usage = response.response_metadata.get('token_usage', {})
            usage = {
                "prompt_tokens": token_usage.get('prompt_tokens', 0),
                "completion_tokens": token_usage.get('completion_tokens', 0),
                "total_tokens": token_usage.get('total_tokens', 0),
            }
        
        return LLMResponse(
            content=response.content,
            model=self.model_name,
            usage=usage,
            finish_reason="stop"
        )
    
    async def stream_generate(
        self,
        messages: List[Message],
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream generate using LangChain 1.x astream.
        
        Args:
            messages: List of conversation messages
            **kwargs: Additional generation parameters
            
        Yields:
            Response chunks as strings
        """
        lc_messages = self._convert_messages(messages)
        
        model = self.chat_model
        if "temperature" in kwargs or "max_tokens" in kwargs:
            model = self.chat_model.bind(
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens", self.max_tokens)
            )
        
        # Use astream (LangChain 1.x streaming API)
        async for chunk in model.astream(lc_messages):
            if chunk.content:
                yield chunk.content
    
    def get_provider_name(self) -> str:
        """Get provider name."""
        return "langchain_openai"
    
    def count_tokens(self, text: str) -> int:
        """Estimate token count.
        
        Note: This is an approximation. For exact counts,
        use the tiktoken library directly.
        """
        # Rough estimate: ~4 characters per token for English
        return len(text) // 4


class LangChainQwenLLM(BaseLLM):
    """Qwen LLM using LangChain 1.x with DashScope.
    
    Uses langchain_community for DashScope integration.
    """
    
    def __init__(
        self,
        model_name: str = "qwen-turbo",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        api_key: Optional[str] = None,
        **kwargs
    ):
        super().__init__(model_name, temperature, max_tokens, **kwargs)
        settings = get_settings()
        
        # Import DashScope chat model from langchain_community
        try:
            from langchain_community.chat_models import ChatTongyi
            self.chat_model = ChatTongyi(
                model=model_name,
                dashscope_api_key=api_key or settings.dashscope_api_key,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except ImportError:
            raise ImportError(
                "langchain_community is required for Qwen support. "
                "Install with: pip install langchain-community"
            )
    
    def _convert_messages(self, messages: List[Message]) -> List[BaseMessage]:
        """Convert our Message format to LangChain message format."""
        lc_messages = []
        for msg in messages:
            if msg.role == "system":
                lc_messages.append(SystemMessage(content=msg.content))
            elif msg.role == "user":
                lc_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                lc_messages.append(AIMessage(content=msg.content))
            else:
                lc_messages.append(HumanMessage(content=msg.content))
        return lc_messages
    
    async def generate(
        self,
        messages: List[Message],
        **kwargs
    ) -> LLMResponse:
        """Generate using Qwen via DashScope."""
        lc_messages = self._convert_messages(messages)
        response = await self.chat_model.ainvoke(lc_messages)
        
        return LLMResponse(
            content=response.content,
            model=self.model_name,
            usage={},
            finish_reason="stop"
        )
    
    async def stream_generate(
        self,
        messages: List[Message],
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream generate using Qwen."""
        lc_messages = self._convert_messages(messages)
        
        async for chunk in self.chat_model.astream(lc_messages):
            if chunk.content:
                yield chunk.content
    
    def get_provider_name(self) -> str:
        return "qwen_dashscope"
    
    def count_tokens(self, text: str) -> int:
        return len(text) // 4
