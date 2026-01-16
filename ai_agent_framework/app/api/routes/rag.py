"""RAG routes."""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
import json

from app.api.auth import get_current_user
from app.api.deps import get_rag_chain, get_retriever, get_vector_store, get_embedding_model
from schemas.auth import UserResponse
from schemas.rag import (
    DocumentInput,
    DocumentsUploadRequest,
    DocumentsUploadResponse,
    RAGQueryRequest,
    RAGQueryResponse,
    SourceDocument,
    CollectionInfo,
    CollectionListResponse,
    CollectionCreateRequest,
)


router = APIRouter(prefix="/rag", tags=["RAG"])


@router.post("/collections", response_model=dict)
async def create_collection(
    request: CollectionCreateRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Create a new vector collection."""
    try:
        vector_store = get_vector_store()
        embedding_model = get_embedding_model()
        
        await vector_store.create_collection(
            collection_name=request.name,
            dimension=request.dimension or embedding_model.dimension,
            description=request.description
        )
        
        return {
            "success": True,
            "collection_name": request.name,
            "dimension": request.dimension or embedding_model.dimension
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/collections/{collection_name}")
async def delete_collection(
    collection_name: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Delete a vector collection."""
    try:
        vector_store = get_vector_store()
        await vector_store.drop_collection(collection_name)
        return {"success": True, "message": f"Collection {collection_name} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents", response_model=DocumentsUploadResponse)
async def upload_documents(
    request: DocumentsUploadRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Upload documents to RAG system."""
    try:
        collection_name = request.collection_name or "default_collection"
        retriever = get_retriever(collection_name=collection_name)
        
        documents = [
            {
                "id": doc.id,
                "content": doc.content,
                "metadata": {
                    **doc.metadata,
                    "uploaded_by": current_user.id
                }
            }
            for doc in request.documents
        ]
        
        ids = await retriever.add_documents(documents)
        
        return DocumentsUploadResponse(
            ids=ids,
            count=len(ids),
            collection_name=collection_name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=RAGQueryResponse)
async def query_rag(
    request: RAGQueryRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Query the RAG system."""
    try:
        collection_name = request.collection_name or "default_collection"
        rag_chain = get_rag_chain(collection_name=collection_name)
        
        result = await rag_chain.query(
            question=request.question,
            top_k=request.top_k,
            filters=request.filters
        )
        
        sources = None
        if request.include_sources and "sources" in result:
            sources = [
                SourceDocument(
                    id=s["id"],
                    content=s["content"],
                    score=s["score"],
                    metadata=s.get("metadata", {})
                )
                for s in result["sources"]
            ]
        
        return RAGQueryResponse(
            answer=result["answer"],
            sources=sources,
            model=result.get("model", ""),
            usage=result.get("usage")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/stream")
async def query_rag_stream(
    request: RAGQueryRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Stream query the RAG system."""
    try:
        collection_name = request.collection_name or "default_collection"
        rag_chain = get_rag_chain(collection_name=collection_name)
        
        async def generate():
            async for chunk in rag_chain.stream_query(
                question=request.question,
                top_k=request.top_k,
                filters=request.filters
            ):
                yield f"data: {json.dumps({'content': chunk, 'done': False})}\n\n"
            yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_documents(
    query: str,
    collection_name: Optional[str] = None,
    top_k: int = 5,
    current_user: UserResponse = Depends(get_current_user)
):
    """Search documents without generation."""
    try:
        collection = collection_name or "default_collection"
        retriever = get_retriever(collection_name=collection, top_k=top_k)
        
        results = await retriever.retrieve(query)
        
        return {
            "query": query,
            "results": [
                {
                    "id": r.id,
                    "content": r.content,
                    "score": r.score,
                    "metadata": r.metadata
                }
                for r in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{collection_name}/{document_id}")
async def delete_document(
    collection_name: str,
    document_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Delete a document from collection."""
    try:
        retriever = get_retriever(collection_name=collection_name)
        await retriever.delete_documents([document_id])
        return {"success": True, "message": f"Document {document_id} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
