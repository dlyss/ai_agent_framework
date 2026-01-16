"""FastAPI Application Entry Point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config import get_settings
from app.api.deps import cleanup
from app.db.database import init_db, close_db, async_session_maker
from app.db.init_data import init_default_data
from app.api.routes import (
    auth_router,
    chat_router,
    rag_router,
    memory_router,
    finetune_router,
    ws_router,
)
from utils.logger import get_logger
from utils.exceptions import AIAgentException

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting AI Agent Framework...")
    settings = get_settings()
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"Debug mode: {settings.debug}")
    
    # Initialize database (optional, skip if not available)
    db_initialized = False
    try:
        logger.info("Initializing database...")
        await init_db()
        logger.info("Database initialized")
        db_initialized = True
        
        # Initialize default data (admin user)
        logger.info("Initializing default data...")
        async with async_session_maker() as db:
            await init_default_data(db)
        logger.info("Default data initialized")
    except Exception as e:
        logger.warning(f"Database initialization skipped: {e}")
        logger.warning("Running in limited mode without database")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Agent Framework...")
    if db_initialized:
        await close_db()
    await cleanup()
    logger.info("Cleanup completed")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        description="AI Agent Framework - A comprehensive framework for building AI agents with LLM, RAG, Memory, and Fine-tuning capabilities.",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Exception handlers
    @app.exception_handler(AIAgentException)
    async def ai_agent_exception_handler(request: Request, exc: AIAgentException):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": exc.message,
                "detail": exc.detail,
                "type": exc.__class__.__name__
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation error",
                "detail": exc.errors()
            }
        )
    
    # Health check
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {
            "status": "healthy",
            "app_name": settings.app_name,
            "version": "0.1.0"
        }
    
    # API info
    @app.get("/", tags=["Info"])
    async def root():
        return {
            "name": settings.app_name,
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/health"
        }
    
    # Register routers
    api_prefix = "/api/v1"
    app.include_router(auth_router, prefix=api_prefix)
    app.include_router(chat_router, prefix=api_prefix)
    app.include_router(rag_router, prefix=api_prefix)
    app.include_router(memory_router, prefix=api_prefix)
    app.include_router(finetune_router, prefix=api_prefix)
    app.include_router(ws_router)
    
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )
