"""Retriever for RAG system."""

from typing import List, Optional, Dict, Any
from core.vector_store.base import BaseVectorStore, Document, SearchResult
from core.rag.embeddings import EmbeddingModel


class Retriever:
    """Document retriever for RAG."""
    
    def __init__(
        self,
        vector_store: BaseVectorStore,
        embedding_model: EmbeddingModel,
        collection_name: str,
        top_k: int = 5,
        score_threshold: float = 0.0
    ):
        self.vector_store = vector_store
        self.embedding_model = embedding_model
        self.collection_name = collection_name
        self.top_k = top_k
        self.score_threshold = score_threshold
    
    async def add_documents(
        self,
        documents: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> List[str]:
        """Add documents to the retriever.
        
        Args:
            documents: List of dicts with 'content' and optional 'metadata'
            batch_size: Batch size for processing
            
        Returns:
            List of document IDs
        """
        # Ensure collection exists
        exists = await self.vector_store.collection_exists(self.collection_name)
        if not exists:
            await self.vector_store.create_collection(
                self.collection_name,
                dimension=self.embedding_model.dimension
            )
        
        all_ids = []
        
        # Process in batches
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            # Extract contents and embed
            contents = [doc["content"] for doc in batch]
            embeddings = self.embedding_model.embed_documents(contents)
            
            # Create Document objects
            docs = []
            for j, doc in enumerate(batch):
                docs.append(Document(
                    id=doc.get("id"),
                    content=doc["content"],
                    metadata=doc.get("metadata", {}),
                    embedding=embeddings[j]
                ))
            
            # Insert
            ids = await self.vector_store.insert(self.collection_name, docs)
            all_ids.extend(ids)
        
        return all_ids
    
    async def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Retrieve relevant documents for a query.
        
        Args:
            query: Query text
            top_k: Number of results (default: self.top_k)
            filters: Optional metadata filters
            
        Returns:
            List of search results
        """
        # Embed query
        query_vector = self.embedding_model.embed_query(query)
        
        # Search
        results = await self.vector_store.search(
            self.collection_name,
            query_vector=query_vector,
            top_k=top_k or self.top_k,
            filters=filters
        )
        
        # Filter by score threshold
        if self.score_threshold > 0:
            results = [r for r in results if r.score >= self.score_threshold]
        
        return results
    
    async def delete_documents(self, ids: List[str]) -> bool:
        """Delete documents by IDs.
        
        Args:
            ids: List of document IDs
            
        Returns:
            True if successful
        """
        return await self.vector_store.delete(self.collection_name, ids)
    
    async def get_documents(self, ids: List[str]) -> List[Document]:
        """Get documents by IDs.
        
        Args:
            ids: List of document IDs
            
        Returns:
            List of documents
        """
        return await self.vector_store.get_by_ids(self.collection_name, ids)
