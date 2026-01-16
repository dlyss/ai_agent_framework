"""Long-term memory implementation using vector store."""

from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from core.memory.base import BaseMemory, MemoryItem
from core.vector_store.base import BaseVectorStore, Document
from core.rag.embeddings import EmbeddingModel
from app.config import get_settings


class LongTermMemory(BaseMemory):
    """Long-term memory using vector store for semantic search."""
    
    def __init__(
        self,
        vector_store: BaseVectorStore,
        embedding_model: EmbeddingModel,
        collection_name: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        settings = get_settings()
        self.vector_store = vector_store
        self.embedding_model = embedding_model
        self.collection_name = collection_name or settings.long_term_memory_collection
        self.user_id = user_id
        self._initialized = False
    
    async def _ensure_collection(self):
        """Ensure collection exists."""
        if not self._initialized:
            exists = await self.vector_store.collection_exists(self.collection_name)
            if not exists:
                await self.vector_store.create_collection(
                    self.collection_name,
                    dimension=self.embedding_model.dimension
                )
            self._initialized = True
    
    def _item_to_document(self, item: MemoryItem) -> Document:
        """Convert MemoryItem to Document."""
        # Create searchable content
        content = item.content
        
        # Build metadata
        metadata = {
            "role": item.role,
            "timestamp": item.timestamp.isoformat(),
            "importance": item.importance,
            **item.metadata
        }
        if self.user_id:
            metadata["user_id"] = self.user_id
        
        # Generate embedding
        embedding = self.embedding_model.embed_query(content)
        
        return Document(
            id=item.id,
            content=content,
            metadata=metadata,
            embedding=embedding
        )
    
    def _document_to_item(self, doc: Document) -> MemoryItem:
        """Convert Document to MemoryItem."""
        metadata = doc.metadata.copy()
        
        return MemoryItem(
            id=doc.id,
            content=doc.content,
            role=metadata.pop("role", "user"),
            timestamp=datetime.fromisoformat(metadata.pop("timestamp", datetime.now().isoformat())),
            importance=metadata.pop("importance", 0.5),
            metadata=metadata
        )
    
    async def add(self, item: MemoryItem) -> str:
        """Add item to long-term memory."""
        await self._ensure_collection()
        
        doc = self._item_to_document(item)
        ids = await self.vector_store.insert(self.collection_name, [doc])
        return ids[0]
    
    async def add_batch(self, items: List[MemoryItem]) -> List[str]:
        """Add multiple items to memory.
        
        Args:
            items: List of MemoryItems
            
        Returns:
            List of item IDs
        """
        await self._ensure_collection()
        
        docs = [self._item_to_document(item) for item in items]
        return await self.vector_store.insert(self.collection_name, docs)
    
    async def get(self, item_id: str) -> Optional[MemoryItem]:
        """Get item by ID."""
        await self._ensure_collection()
        
        docs = await self.vector_store.get_by_ids(self.collection_name, [item_id])
        if docs:
            return self._document_to_item(docs[0])
        return None
    
    async def search(
        self,
        query: str,
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        min_score: float = 0.0,
        **kwargs
    ) -> List[MemoryItem]:
        """Semantic search in memory."""
        await self._ensure_collection()
        
        # Add user filter if user_id is set
        if self.user_id:
            filters = filters or {}
            filters["user_id"] = self.user_id
        
        # Embed query
        query_vector = self.embedding_model.embed_query(query)
        
        # Search
        results = await self.vector_store.search(
            self.collection_name,
            query_vector=query_vector,
            top_k=limit,
            filters=filters
        )
        
        # Filter by score and convert to MemoryItems
        items = []
        for result in results:
            if result.score >= min_score:
                items.append(MemoryItem(
                    id=result.id,
                    content=result.content,
                    role=result.metadata.get("role", "user"),
                    timestamp=datetime.fromisoformat(
                        result.metadata.get("timestamp", datetime.now().isoformat())
                    ),
                    importance=result.metadata.get("importance", 0.5),
                    metadata={
                        k: v for k, v in result.metadata.items()
                        if k not in ["role", "timestamp", "importance"]
                    }
                ))
        
        return items
    
    async def delete(self, item_id: str) -> bool:
        """Delete item by ID."""
        await self._ensure_collection()
        return await self.vector_store.delete(self.collection_name, [item_id])
    
    async def clear(self) -> bool:
        """Clear all memory (drops and recreates collection)."""
        await self.vector_store.drop_collection(self.collection_name)
        self._initialized = False
        await self._ensure_collection()
        return True
    
    async def get_recent(self, limit: int = 10) -> List[MemoryItem]:
        """Get recent items (requires querying all and sorting)."""
        await self._ensure_collection()
        
        # Use a generic query to get items
        results = await self.search("", limit=limit * 2)
        
        # Sort by timestamp
        results.sort(key=lambda x: x.timestamp, reverse=True)
        return results[:limit]
    
    async def count(self) -> int:
        """Get memory count."""
        await self._ensure_collection()
        
        # This is a rough count from the vector store
        from pymilvus import Collection
        try:
            collection = Collection(self.collection_name)
            return collection.num_entities
        except Exception:
            return 0
    
    async def get_by_importance(
        self,
        min_importance: float = 0.7,
        limit: int = 10
    ) -> List[MemoryItem]:
        """Get high-importance memories.
        
        Args:
            min_importance: Minimum importance threshold
            limit: Max items to return
            
        Returns:
            List of important memories
        """
        await self._ensure_collection()
        
        # Search with importance filter
        results = await self.search(
            "",
            limit=limit,
            filters={"importance": {"$gte": min_importance}}
        )
        
        return results
    
    async def consolidate_memories(
        self,
        items: List[MemoryItem],
        summary: str
    ) -> str:
        """Consolidate multiple memories into a summary.
        
        Args:
            items: Items to consolidate
            summary: Summary text
            
        Returns:
            New consolidated memory ID
        """
        # Create consolidated memory
        consolidated = MemoryItem(
            content=summary,
            role="system",
            importance=0.8,
            metadata={
                "type": "consolidated",
                "source_ids": [item.id for item in items]
            }
        )
        
        # Add consolidated memory
        new_id = await self.add(consolidated)
        
        # Optionally delete original items
        for item in items:
            await self.delete(item.id)
        
        return new_id
