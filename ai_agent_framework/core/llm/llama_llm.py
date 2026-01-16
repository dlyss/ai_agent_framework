"""LLaMA LLM implementation - supports both local and API modes."""

from typing import AsyncGenerator, List, Optional
import httpx
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

from core.llm.base import BaseLLM, Message, LLMResponse
from app.config import get_settings


class LLaMALLM(BaseLLM):
    """LLaMA LLM provider implementation.
    
    Supports:
    - Local model loading via transformers
    - Remote API calls (e.g., llama.cpp server, vLLM)
    """
    
    def __init__(
        self,
        model_name: str = "meta-llama/Llama-2-7b-chat-hf",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        model_path: Optional[str] = None,
        api_base: Optional[str] = None,
        use_local: bool = False,
        device: str = "auto",
        load_in_8bit: bool = False,
        load_in_4bit: bool = False,
        **kwargs
    ):
        super().__init__(model_name, temperature, max_tokens, **kwargs)
        settings = get_settings()
        
        self.use_local = use_local
        self.api_base = api_base or settings.llama_api_base
        self.model_path = model_path or settings.llama_model_path
        
        self.model = None
        self.tokenizer = None
        
        if use_local and self.model_path:
            self._load_local_model(device, load_in_8bit, load_in_4bit)
    
    def _load_local_model(
        self,
        device: str,
        load_in_8bit: bool,
        load_in_4bit: bool
    ):
        """Load model locally using transformers."""
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_path,
            trust_remote_code=True
        )
        
        load_kwargs = {
            "pretrained_model_name_or_path": self.model_path,
            "trust_remote_code": True,
            "torch_dtype": torch.float16,
        }
        
        if device == "auto":
            load_kwargs["device_map"] = "auto"
        
        if load_in_8bit:
            load_kwargs["load_in_8bit"] = True
        elif load_in_4bit:
            load_kwargs["load_in_4bit"] = True
        
        self.model = AutoModelForCausalLM.from_pretrained(**load_kwargs)
    
    def _format_messages(self, messages: List[Message]) -> str:
        """Format messages into LLaMA chat format."""
        formatted = ""
        for msg in messages:
            if msg.role == "system":
                formatted += f"<<SYS>>\n{msg.content}\n<</SYS>>\n\n"
            elif msg.role == "user":
                formatted += f"[INST] {msg.content} [/INST]\n"
            elif msg.role == "assistant":
                formatted += f"{msg.content}\n"
        return formatted
    
    async def generate(
        self,
        messages: List[Message],
        **kwargs
    ) -> LLMResponse:
        """Generate response using LLaMA."""
        if self.use_local and self.model:
            return await self._generate_local(messages, **kwargs)
        else:
            return await self._generate_api(messages, **kwargs)
    
    async def _generate_local(
        self,
        messages: List[Message],
        **kwargs
    ) -> LLMResponse:
        """Generate using local model."""
        prompt = self._format_messages(messages)
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=kwargs.get("max_tokens", self.max_tokens),
                temperature=kwargs.get("temperature", self.temperature),
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        
        response_text = self.tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:],
            skip_special_tokens=True
        )
        
        return LLMResponse(
            content=response_text,
            model=self.model_name,
            usage={
                "prompt_tokens": inputs["input_ids"].shape[1],
                "completion_tokens": outputs.shape[1] - inputs["input_ids"].shape[1],
                "total_tokens": outputs.shape[1],
            },
            finish_reason="stop"
        )
    
    async def _generate_api(
        self,
        messages: List[Message],
        **kwargs
    ) -> LLMResponse:
        """Generate using remote API (OpenAI-compatible)."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base}/v1/chat/completions",
                json={
                    "model": self.model_name,
                    "messages": [{"role": m.role, "content": m.content} for m in messages],
                    "temperature": kwargs.get("temperature", self.temperature),
                    "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                },
                timeout=120.0
            )
            response.raise_for_status()
            data = response.json()
            
            return LLMResponse(
                content=data["choices"][0]["message"]["content"],
                model=data.get("model", self.model_name),
                usage=data.get("usage"),
                finish_reason=data["choices"][0].get("finish_reason")
            )
    
    async def stream_generate(
        self,
        messages: List[Message],
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream generate responses."""
        if self.use_local and self.model:
            # For local models, generate full response and yield in chunks
            response = await self._generate_local(messages, **kwargs)
            for char in response.content:
                yield char
        else:
            # Stream from API
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{self.api_base}/v1/chat/completions",
                    json={
                        "model": self.model_name,
                        "messages": [{"role": m.role, "content": m.content} for m in messages],
                        "temperature": kwargs.get("temperature", self.temperature),
                        "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                        "stream": True,
                    },
                    timeout=120.0
                ) as response:
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data != "[DONE]":
                                import json
                                chunk = json.loads(data)
                                content = chunk["choices"][0]["delta"].get("content", "")
                                if content:
                                    yield content
    
    def get_provider_name(self) -> str:
        """Get provider name."""
        return "llama"
    
    def count_tokens(self, text: str) -> int:
        """Count tokens using tokenizer."""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        return super().count_tokens(text)
