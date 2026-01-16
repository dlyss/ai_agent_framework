"""Milvus Vector Store implementation."""

import uuid
from typing import List, Dict, Any, Optional
from pymilvus import (
    connections,
    utility,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
)

from core.vector_store.base import BaseVectorStore, Document, SearchResult
from app.config import get_settings


class MilvusVectorStore(BaseVectorStore):
    """Milvus vector store implementation."""
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        db_name: Optional[str] = None,
        alias: str = "default"
    ):
        settings = get_settings()
        self.host = host or settings.milvus_host
        self.port = port or settings.milvus_port
        self.user = user or settings.milvus_user
        self.password = password or settings.milvus_password
        self.db_name = db_name or settings.milvus_db_name
        self.alias = alias
        self._connected = False
    
    async def connect(self):
        """Connect to Milvus server."""
        if not self._connected:
            connections.connect(
                alias=self.alias,
                host=self.host,
                port=self.port,
                user=self.user if self.user else None,
                password=self.password if self.password else None,
                db_name=self.db_name,
            )
            self._connected = True
    
    async def disconnect(self):
        """Disconnect from Milvus server."""
        if self._connected:
            connections.disconnect(self.alias)
            self._connected = False
    
    async def create_collection(
        self,
        collection_name: str,
        dimension: int,
        description: str = "",
        index_type: str = "IVF_FLAT",
        metric_type: str = "COSINE",
        nlist: int = 1024,
        **kwargs
    ) -> bool:
        """Create a new collection with index."""
        await self.connect()
        
        if utility.has_collection(collection_name, using=self.alias):
            return True
        
        # Define schema
        fields = [
            FieldSchema(
                name="id",
                dtype=DataType.VARCHAR,
                is_primary=True,
                max_length=64
            ),
            FieldSchema(
                name="content",
                dtype=DataType.VARCHAR,
                max_length=65535
            ),
            FieldSchema(
                name="metadata",
                dtype=DataType.JSON
            ),
            FieldSchema(
                name="embedding",
                dtype=DataType.FLOAT_VECTOR,
                dim=dimension
            ),
        ]
        
        schema = CollectionSchema(
            fields=fields,
            description=description
        )
        
        # Create collection
        collection = Collection(
            name=collection_name,
            schema=schema,
            using=self.alias
        )
        
        # Create index
        index_params = {
            "index_type": index_type,
            "metric_type": metric_type,
            "params": {"nlist": nlist}
        }
        collection.create_index(
            field_name="embedding",
            index_params=index_params
        )
        
        # Load collection
        collection.load()
        
        return True
    
    async def drop_collection(self, collection_name: str) -> bool:
        """Drop a collection."""
        await self.connect()
        
        if utility.has_collection(collection_name, using=self.alias):
            utility.drop_collection(collection_name, using=self.alias)
        return True
    
    async def collection_exists(self, collection_name: str) -> bool:
        """Check if collection exists."""
        await self.connect()
        return utility.has_collection(collection_name, using=self.alias)
    
    async def insert(
        self,
        collection_name: str,
        documents: List[Document]
    ) -> List[str]:
        """Insert documents into collection."""
        await self.connect()
        
        collection = Collection(collection_name, using=self.alias)
        
        # Prepare data
        ids = []
        contents = []
        metadatas = []
        embeddings = []
        
        for doc in documents:
            doc_id = doc.id or str(uuid.uuid4())
            ids.append(doc_id)
            contents.append(doc.content[:65535])  # Truncate if needed
            metadatas.append(doc.metadata)
            embeddings.append(doc.embedding)
        
        # Insert
        collection.insert([ids, contents, metadatas, embeddings])
        collection.flush()
        
        return ids
    
    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search for similar documents."""
        await self.connect()
        
        collection = Collection(collection_name, using=self.alias)
        collection.load()
        
        # Build filter expression
        expr = None
        if filters:
            conditions = []
            for key, value in filters.items():
                if isinstance(value, str):
                    conditions.append(f'metadata["{key}"] == "{value}"')
                else:
                    conditions.append(f'metadata["{key}"] == {value}')
            expr = " and ".join(conditions) if conditions else None
        
        # Search
        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 10}
        }
        
        results = collection.search(
            data=[query_vector],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            expr=expr,
            output_fields=["id", "content", "metadata"]
        )
        
        # Parse results
        search_results = []
        for hits in results:
            for hit in hits:
                search_results.append(SearchResult(
                    id=hit.entity.get("id"),
                    content=hit.entity.get("content"),
                    metadata=hit.entity.get("metadata", {}),
                    score=hit.distance
                ))
        
        return search_results
    
    async def delete(
        self,
        collection_name: str,
        ids: List[str]
    ) -> bool:
        """Delete documents by IDs."""
        await self.connect()
        
        collection = Collection(collection_name, using=self.alias)
        
        # Build expression
        ids_str = ", ".join([f'"{id}"' for id in ids])
        expr = f"id in [{ids_str}]"
        
        collection.delete(expr)
        return True
    
    async def get_by_ids(
        self,
        collection_name: str,
        ids: List[str]
    ) -> List[Document]:
        """Get documents by IDs."""
        await self.connect()
        
        collection = Collection(collection_name, using=self.alias)
        collection.load()
        
        # Build expression
        ids_str = ", ".join([f'"{id}"' for id in ids])
        expr = f"id in [{ids_str}]"
        
        results = collection.query(
            expr=expr,
            output_fields=["id", "content", "metadata", "embedding"]
        )
        
        documents = []
        for item in results:
            documents.append(Document(
                id=item.get("id"),
                content=item.get("content"),
                metadata=item.get("metadata", {}),
                embedding=item.get("embedding")
            ))
        
        return documents
    
    async def count(self, collection_name: str) -> int:
        """Get document count in collection."""
        await self.connect()
        
        collection = Collection(collection_name, using=self.alias)
        return collection.num_entities
