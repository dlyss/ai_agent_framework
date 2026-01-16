"""Qwen (通义千问) LLM implementation via DashScope."""

from typing import AsyncGenerator, List, Optional
import dashscope
from dashscope import Generation

from core.llm.base import BaseLLM, Message, LLMResponse
from app.config import get_settings


class QwenLLM(BaseLLM):
    """Qwen LLM provider implementation using DashScope API."""
    
    MODELS = {
        "qwen-turbo": "qwen-turbo",
        "qwen-plus": "qwen-plus",
        "qwen-max": "qwen-max",
        "qwen-max-longcontext": "qwen-max-longcontext",
    }
    
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
        dashscope.api_key = api_key or settings.dashscope_api_key
    
    async def generate(
        self,
        messages: List[Message],
        **kwargs
    ) -> LLMResponse:
        """Generate response using DashScope API."""
        response = Generation.call(
            model=self.model_name,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=kwargs.get("temperature", self.temperature),
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            result_format="message",
        )
        
        if response.status_code == 200:
            return LLMResponse(
                content=response.output.choices[0].message.content,
                model=self.model_name,
                usage={
                    "prompt_tokens": response.usage.get("input_tokens", 0),
                    "completion_tokens": response.usage.get("output_tokens", 0),
                    "total_tokens": response.usage.get("total_tokens", 0),
                },
                finish_reason=response.output.choices[0].finish_reason
            )
        else:
            raise Exception(f"Qwen API error: {response.code} - {response.message}")
    
    async def stream_generate(
        self,
        messages: List[Message],
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream generate responses using DashScope API."""
        responses = Generation.call(
            model=self.model_name,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=kwargs.get("temperature", self.temperature),
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            result_format="message",
            stream=True,
            incremental_output=True,
        )
        
        for response in responses:
            if response.status_code == 200:
                content = response.output.choices[0].message.content
                if content:
                    yield content
            else:
                raise Exception(f"Qwen API error: {response.code} - {response.message}")
    
    def get_provider_name(self) -> str:
        """Get provider name."""
        return "qwen"
