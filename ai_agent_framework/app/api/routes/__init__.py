"""API Routes."""

from app.api.routes.auth import router as auth_router
from app.api.routes.chat import router as chat_router
from app.api.routes.rag import router as rag_router
from app.api.routes.memory import router as memory_router
from app.api.routes.finetune import router as finetune_router
from app.api.routes.websocket import router as ws_router

__all__ = [
    "auth_router",
    "chat_router",
    "rag_router",
    "memory_router",
    "finetune_router",
    "ws_router",
]
