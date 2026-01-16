"""OpenAI LLM implementation."""

from typing import AsyncGenerator, List, Optional
import tiktoken
from openai import AsyncOpenAI

from core.llm.base import BaseLLM, Message, LLMResponse
from app.config import get_settings


class OpenAILLM(BaseLLM):
    """OpenAI LLM provider implementation."""
    
    def __init__(
        self,
        model_name: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        **kwargs
    ):
        super().__init__(model_name, temperature, max_tokens, **kwargs)
        settings = get_settings()
        self.client = AsyncOpenAI(
            api_key=api_key or settings.openai_api_key,
            base_url=api_base or settings.openai_api_base
        )
        try:
            self.encoding = tiktoken.encoding_for_model(model_name)
        except KeyError:
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    async def generate(
        self,
        messages: List[Message],
        **kwargs
    ) -> LLMResponse:
        """Generate response using OpenAI API."""
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=kwargs.get("temperature", self.temperature),
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            **{k: v for k, v in kwargs.items() if k not in ["temperature", "max_tokens"]}
        )
        
        return LLMResponse(
            content=response.choices[0].message.content or "",
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            },
            finish_reason=response.choices[0].finish_reason
        )
    
    async def stream_generate(
        self,
        messages: List[Message],
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream generate responses using OpenAI API."""
        stream = await self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=kwargs.get("temperature", self.temperature),
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            stream=True,
            **{k: v for k, v in kwargs.items() if k not in ["temperature", "max_tokens"]}
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    def get_provider_name(self) -> str:
        """Get provider name."""
        return "openai"
    
    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken."""
        return len(self.encoding.encode(text))
