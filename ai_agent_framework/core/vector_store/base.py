"""Base Vector Store interface."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class Document(BaseModel):
    """Document model for vector store."""
    id: Optional[str] = None
    content: str
    metadata: Dict[str, Any] = {}
    embedding: Optional[List[float]] = None


class SearchResult(BaseModel):
    """Search result model."""
    id: str
    content: str
    metadata: Dict[str, Any] = {}
    score: float


class BaseVectorStore(ABC):
    """Abstract base class for vector stores."""
    
    @abstractmethod
    async def create_collection(
        self,
        collection_name: str,
        dimension: int,
        **kwargs
    ) -> bool:
        """Create a new collection.
        
        Args:
            collection_name: Name of the collection
            dimension: Vector dimension
            **kwargs: Additional parameters
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    async def drop_collection(self, collection_name: str) -> bool:
        """Drop a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    async def collection_exists(self, collection_name: str) -> bool:
        """Check if collection exists.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            True if exists
        """
        pass
    
    @abstractmethod
    async def insert(
        self,
        collection_name: str,
        documents: List[Document]
    ) -> List[str]:
        """Insert documents into collection.
        
        Args:
            collection_name: Name of the collection
            documents: List of documents with embeddings
            
        Returns:
            List of inserted document IDs
        """
        pass
    
    @abstractmethod
    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search for similar documents.
        
        Args:
            collection_name: Name of the collection
            query_vector: Query embedding vector
            top_k: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            List of search results
        """
        pass
    
    @abstractmethod
    async def delete(
        self,
        collection_name: str,
        ids: List[str]
    ) -> bool:
        """Delete documents by IDs.
        
        Args:
            collection_name: Name of the collection
            ids: List of document IDs to delete
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    async def get_by_ids(
        self,
        collection_name: str,
        ids: List[str]
    ) -> List[Document]:
        """Get documents by IDs.
        
        Args:
            collection_name: Name of the collection
            ids: List of document IDs
            
        Returns:
            List of documents
        """
        pass
