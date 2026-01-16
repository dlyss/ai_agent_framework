"""Memory routes."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException

from app.api.auth import get_current_user
from app.api.deps import get_memory_manager, clear_memory_manager
from core.memory.base import MemoryItem
from schemas.auth import UserResponse
from schemas.memory import (
    MemoryItemInput,
    MemoryItemResponse,
    MemorySearchRequest,
    MemorySearchResponse,
    ConversationHistoryRequest,
    ConversationHistoryResponse,
    MemoryStatsResponse,
    MemoryClearRequest,
)


router = APIRouter(prefix="/memory", tags=["Memory"])


@router.post("/items", response_model=MemoryItemResponse)
async def add_memory_item(
    session_id: str,
    item: MemoryItemInput,
    current_user: UserResponse = Depends(get_current_user)
):
    """Add a memory item."""
    try:
        memory_manager = get_memory_manager(
            session_id=session_id,
            user_id=current_user.id
        )
        
        item_id = await memory_manager.add_message(
            content=item.content,
            role=item.role,
            importance=item.importance,
            metadata=item.metadata
        )
        
        # Get the added item
        memory_item = await memory_manager.short_term.get(item_id)
        
        return MemoryItemResponse(
            id=memory_item.id,
            content=memory_item.content,
            role=memory_item.role,
            importance=memory_item.importance,
            timestamp=memory_item.timestamp,
            metadata=memory_item.metadata
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=MemorySearchResponse)
async def search_memory(
    session_id: str,
    request: MemorySearchRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Search memory."""
    try:
        memory_manager = get_memory_manager(
            session_id=session_id,
            user_id=current_user.id
        )
        
        results = await memory_manager.search_all(
            query=request.query,
            limit=request.limit,
            include_short_term=request.include_short_term,
            include_long_term=request.include_long_term
        )
        
        items = [
            MemoryItemResponse(
                id=item.id,
                content=item.content,
                role=item.role,
                importance=item.importance,
                timestamp=item.timestamp,
                metadata=item.metadata
            )
            for item in results
        ]
        
        return MemorySearchResponse(items=items, total=len(items))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/history", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    request: ConversationHistoryRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get conversation history for a session."""
    try:
        memory_manager = get_memory_manager(
            session_id=request.session_id,
            user_id=current_user.id
        )
        
        messages = await memory_manager.get_conversation_history(
            max_turns=request.max_turns,
            max_tokens=request.max_tokens
        )
        
        return ConversationHistoryResponse(
            messages=[{"role": m.role, "content": m.content} for m in messages],
            total_items=len(messages)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/{session_id}", response_model=MemoryStatsResponse)
async def get_memory_stats(
    session_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get memory statistics."""
    try:
        memory_manager = get_memory_manager(
            session_id=session_id,
            user_id=current_user.id
        )
        
        stats = await memory_manager.get_stats()
        
        return MemoryStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear")
async def clear_memory(
    request: MemoryClearRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Clear memory."""
    try:
        if request.session_id:
            memory_manager = get_memory_manager(
                session_id=request.session_id,
                user_id=current_user.id
            )
            
            if request.clear_short_term:
                await memory_manager.clear_short_term()
            if request.clear_long_term:
                await memory_manager.long_term.clear()
            
            if request.clear_short_term and request.clear_long_term:
                clear_memory_manager(request.session_id, current_user.id)
        
        return {
            "success": True,
            "message": "Memory cleared",
            "cleared_short_term": request.clear_short_term,
            "cleared_long_term": request.clear_long_term
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/archive/{session_id}")
async def archive_to_long_term(
    session_id: str,
    importance_threshold: float = 0.5,
    current_user: UserResponse = Depends(get_current_user)
):
    """Archive short-term memory to long-term."""
    try:
        memory_manager = get_memory_manager(
            session_id=session_id,
            user_id=current_user.id
        )
        
        archived_count = await memory_manager.archive_to_long_term(
            importance_threshold=importance_threshold
        )
        
        return {
            "success": True,
            "archived_count": archived_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/summarize/{session_id}")
async def summarize_conversation(
    session_id: str,
    max_items: int = 10,
    current_user: UserResponse = Depends(get_current_user)
):
    """Summarize and archive conversation."""
    try:
        memory_manager = get_memory_manager(
            session_id=session_id,
            user_id=current_user.id
        )
        
        summary_id = await memory_manager.summarize_and_archive(max_items=max_items)
        
        if summary_id:
            return {
                "success": True,
                "summary_id": summary_id,
                "message": "Conversation summarized and archived"
            }
        else:
            return {
                "success": False,
                "message": "No items to summarize or LLM not configured"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
