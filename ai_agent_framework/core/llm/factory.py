"""LLM Factory - Create LLM instances dynamically."""

from typing import Dict, Type, Optional, Any
from core.llm.base import BaseLLM
from core.llm.openai_llm import OpenAILLM
from core.llm.qwen_llm import QwenLLM
from core.llm.llama_llm import LLaMALLM
from app.config import get_settings


class LLMFactory:
    """Factory class for creating LLM instances."""
    
    _providers: Dict[str, Type[BaseLLM]] = {
        "openai": OpenAILLM,
        "qwen": QwenLLM,
        "llama": LLaMALLM,
    }
    
    _model_mapping: Dict[str, str] = {
        # OpenAI models
        "gpt-3.5-turbo": "openai",
        "gpt-4": "openai",
        "gpt-4-turbo": "openai",
        "gpt-4o": "openai",
        "gpt-4o-mini": "openai",
        # Qwen models
        "qwen-turbo": "qwen",
        "qwen-plus": "qwen",
        "qwen-max": "qwen",
        "qwen-max-longcontext": "qwen",
        # LLaMA models
        "llama-2-7b": "llama",
        "llama-2-13b": "llama",
        "llama-2-70b": "llama",
        "llama-3-8b": "llama",
        "llama-3-70b": "llama",
    }
    
    @classmethod
    def register_provider(cls, name: str, provider_class: Type[BaseLLM]):
        """Register a new LLM provider.
        
        Args:
            name: Provider identifier
            provider_class: LLM class implementing BaseLLM
        """
        cls._providers[name] = provider_class
    
    @classmethod
    def register_model(cls, model_name: str, provider: str):
        """Register a model to provider mapping.
        
        Args:
            model_name: Model identifier
            provider: Provider name
        """
        cls._model_mapping[model_name] = provider
    
    @classmethod
    def create(
        cls,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        **kwargs
    ) -> BaseLLM:
        """Create an LLM instance.
        
        Args:
            provider: Provider name (openai, qwen, llama)
            model_name: Model name
            **kwargs: Additional parameters passed to LLM constructor
            
        Returns:
            BaseLLM instance
            
        Raises:
            ValueError: If provider is not found
        """
        settings = get_settings()
        
        # Determine provider
        if provider is None:
            if model_name and model_name in cls._model_mapping:
                provider = cls._model_mapping[model_name]
            else:
                provider = settings.default_llm_provider
        
        # Determine model
        if model_name is None:
            model_name = settings.default_model_name
        
        # Get provider class
        if provider not in cls._providers:
            raise ValueError(
                f"Unknown provider: {provider}. "
                f"Available: {list(cls._providers.keys())}"
            )
        
        provider_class = cls._providers[provider]
        
        # Set defaults from settings
        kwargs.setdefault("temperature", settings.default_temperature)
        kwargs.setdefault("max_tokens", settings.default_max_tokens)
        
        return provider_class(model_name=model_name, **kwargs)
    
    @classmethod
    def create_from_config(cls, config: Dict[str, Any]) -> BaseLLM:
        """Create LLM from configuration dictionary.
        
        Args:
            config: Configuration dict with provider, model_name, etc.
            
        Returns:
            BaseLLM instance
        """
        return cls.create(**config)
    
    @classmethod
    def list_providers(cls) -> list:
        """List available providers."""
        return list(cls._providers.keys())
    
    @classmethod
    def list_models(cls) -> Dict[str, str]:
        """List available models and their providers."""
        return cls._model_mapping.copy()
