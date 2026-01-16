"""Prompt module - Template management and routing."""

from core.prompt.manager import PromptManager, PromptTemplate
from core.prompt.router import PromptRouter, RouterStrategy

__all__ = [
    "PromptManager",
    "PromptTemplate",
    "PromptRouter",
    "RouterStrategy",
]
