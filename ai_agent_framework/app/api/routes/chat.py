"""Chat routes."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import json

from app.api.auth import get_current_user
from app.api.deps import get_llm, get_memory_manager, get_prompt_router
from core.llm.base import Message
from core.llm.factory import LLMFactory
from schemas.auth import UserResponse
from schemas.chat import (
    ChatRequest,
    ChatResponse,
    ModelListResponse,
    ProviderInfo,
)


router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/completions", response_model=ChatResponse)
async def chat_completion(
    request: ChatRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Generate chat completion."""
    try:
        # Get LLM
        llm = get_llm(
            provider=request.provider,
            model_name=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        # Convert messages
        messages = [
            Message(role=m.role, content=m.content)
            for m in request.messages
        ]
        
        # Handle memory if session_id provided
        if request.session_id:
            memory_manager = get_memory_manager(
                session_id=request.session_id,
                user_id=current_user.id
            )
            # Add user message to memory
            user_msg = request.messages[-1]
            if user_msg.role == "user":
                await memory_manager.add_message(
                    content=user_msg.content,
                    role="user"
                )
        
        # Generate response
        response = await llm.generate(messages)
        
        # Save assistant response to memory
        if request.session_id:
            await memory_manager.add_message(
                content=response.content,
                role="assistant"
            )
        
        return ChatResponse(
            content=response.content,
            model=response.model,
            provider=llm.get_provider_name(),
            usage=response.usage,
            finish_reason=response.finish_reason
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/completions/stream")
async def chat_completion_stream(
    request: ChatRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Generate streaming chat completion."""
    try:
        llm = get_llm(
            provider=request.provider,
            model_name=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        messages = [
            Message(role=m.role, content=m.content)
            for m in request.messages
        ]
        
        async def generate():
            full_response = ""
            async for chunk in llm.stream_generate(messages):
                full_response += chunk
                yield f"data: {json.dumps({'content': chunk, 'done': False})}\n\n"
            
            # Save to memory if session_id provided
            if request.session_id:
                memory_manager = get_memory_manager(
                    session_id=request.session_id,
                    user_id=current_user.id
                )
                user_msg = request.messages[-1]
                if user_msg.role == "user":
                    await memory_manager.add_message(
                        content=user_msg.content,
                        role="user"
                    )
                await memory_manager.add_message(
                    content=full_response,
                    role="assistant"
                )
            
            yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models", response_model=ModelListResponse)
async def list_models(
    current_user: UserResponse = Depends(get_current_user)
):
    """List available models and providers."""
    models_by_provider = {}
    
    for model, provider in LLMFactory.list_models().items():
        if provider not in models_by_provider:
            models_by_provider[provider] = []
        models_by_provider[provider].append(model)
    
    providers = [
        ProviderInfo(
            name=provider,
            models=models,
            description=f"{provider.upper()} language models"
        )
        for provider, models in models_by_provider.items()
    ]
    
    return ModelListResponse(providers=providers)


@router.post("/route")
async def route_prompt(
    message: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Route a message to the appropriate prompt template."""
    router = get_prompt_router()
    template = await router.route(message)
    
    return {
        "template_name": template.name,
        "template": template.template,
        "category": template.category,
        "variables": template.variables
    }
