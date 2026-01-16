"""Embedding model for RAG."""

from typing import List, Optional
from sentence_transformers import SentenceTransformer
import numpy as np

from app.config import get_settings


class EmbeddingModel:
    """Embedding model wrapper using SentenceTransformers."""
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
        normalize: bool = True
    ):
        settings = get_settings()
        self.model_name = model_name or settings.embedding_model
        self.device = device or settings.embedding_device
        self.normalize = normalize
        
        self.model = SentenceTransformer(
            self.model_name,
            device=self.device
        )
        self._dimension = None
    
    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        if self._dimension is None:
            test_embedding = self.model.encode(["test"])
            self._dimension = len(test_embedding[0])
        return self._dimension
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Embed texts to vectors.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=self.normalize,
            show_progress_bar=False
        )
        return embeddings.tolist()
    
    def embed_query(self, query: str) -> List[float]:
        """Embed a single query.
        
        Args:
            query: Query text
            
        Returns:
            Embedding vector
        """
        return self.embed([query])[0]
    
    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """Embed multiple documents.
        
        Args:
            documents: List of document texts
            
        Returns:
            List of embedding vectors
        """
        return self.embed(documents)
    
    def similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity score
        """
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))
