"""WebSocket routes for streaming."""

import json
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from jose import JWTError

from app.api.auth import decode_token
from app.api.deps import get_llm, get_rag_chain, get_memory_manager
from core.llm.base import Message


router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        self.active_connections: dict = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
    
    async def send_message(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)


manager = ConnectionManager()


async def verify_ws_token(token: str) -> Optional[str]:
    """Verify WebSocket token and return user_id."""
    try:
        token_data = decode_token(token)
        return token_data.user_id
    except Exception:
        return None


@router.websocket("/ws/chat")
async def websocket_chat(
    websocket: WebSocket,
    token: str = Query(...),
    session_id: Optional[str] = Query(None)
):
    """WebSocket endpoint for streaming chat."""
    # Verify token
    user_id = await verify_ws_token(token)
    if not user_id:
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    client_id = f"{user_id}:{session_id or 'default'}"
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            
            action = data.get("action", "chat")
            
            if action == "chat":
                # Get parameters
                messages_data = data.get("messages", [])
                provider = data.get("provider")
                model = data.get("model")
                temperature = data.get("temperature", 0.7)
                max_tokens = data.get("max_tokens", 2048)
                
                # Convert messages
                messages = [
                    Message(role=m["role"], content=m["content"])
                    for m in messages_data
                ]
                
                # Get LLM
                llm = get_llm(
                    provider=provider,
                    model_name=model,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                # Handle memory
                if session_id:
                    memory_manager = get_memory_manager(
                        session_id=session_id,
                        user_id=user_id
                    )
                    # Add user message
                    if messages and messages[-1].role == "user":
                        await memory_manager.add_message(
                            content=messages[-1].content,
                            role="user"
                        )
                
                # Stream response
                full_response = ""
                await websocket.send_json({
                    "type": "start",
                    "model": llm.model_name
                })
                
                async for chunk in llm.stream_generate(messages):
                    full_response += chunk
                    await websocket.send_json({
                        "type": "chunk",
                        "content": chunk
                    })
                
                # Save assistant response
                if session_id:
                    await memory_manager.add_message(
                        content=full_response,
                        role="assistant"
                    )
                
                await websocket.send_json({
                    "type": "end",
                    "content": full_response
                })
            
            elif action == "rag":
                # RAG query
                question = data.get("question", "")
                collection_name = data.get("collection_name", "default_collection")
                top_k = data.get("top_k", 5)
                
                rag_chain = get_rag_chain(collection_name=collection_name)
                
                await websocket.send_json({
                    "type": "start",
                    "action": "rag"
                })
                
                full_response = ""
                async for chunk in rag_chain.stream_query(
                    question=question,
                    top_k=top_k
                ):
                    full_response += chunk
                    await websocket.send_json({
                        "type": "chunk",
                        "content": chunk
                    })
                
                await websocket.send_json({
                    "type": "end",
                    "content": full_response
                })
            
            elif action == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
        manager.disconnect(client_id)


@router.websocket("/ws/rag")
async def websocket_rag(
    websocket: WebSocket,
    token: str = Query(...),
    collection_name: str = Query("default_collection")
):
    """WebSocket endpoint for streaming RAG queries."""
    user_id = await verify_ws_token(token)
    if not user_id:
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    client_id = f"rag:{user_id}"
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            question = data.get("question", "")
            top_k = data.get("top_k", 5)
            filters = data.get("filters")
            
            rag_chain = get_rag_chain(collection_name=collection_name)
            
            await websocket.send_json({
                "type": "start",
                "question": question
            })
            
            full_response = ""
            async for chunk in rag_chain.stream_query(
                question=question,
                top_k=top_k,
                filters=filters
            ):
                full_response += chunk
                await websocket.send_json({
                    "type": "chunk",
                    "content": chunk
                })
            
            await websocket.send_json({
                "type": "end",
                "content": full_response
            })
    
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
        manager.disconnect(client_id)
