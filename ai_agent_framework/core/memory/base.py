"""Base Memory interface."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class MemoryItem(BaseModel):
    """Memory item model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    role: str = "user"  # user, assistant, system
    metadata: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.now)
    importance: float = 0.5  # 0-1 scale for memory importance
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BaseMemory(ABC):
    """Abstract base class for memory implementations."""
    
    @abstractmethod
    async def add(self, item: MemoryItem) -> str:
        """Add an item to memory.
        
        Args:
            item: MemoryItem to add
            
        Returns:
            Item ID
        """
        pass
    
    @abstractmethod
    async def get(self, item_id: str) -> Optional[MemoryItem]:
        """Get an item by ID.
        
        Args:
            item_id: Item ID
            
        Returns:
            MemoryItem or None
        """
        pass
    
    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int = 5,
        **kwargs
    ) -> List[MemoryItem]:
        """Search memory.
        
        Args:
            query: Search query
            limit: Max results
            **kwargs: Additional parameters
            
        Returns:
            List of matching items
        """
        pass
    
    @abstractmethod
    async def delete(self, item_id: str) -> bool:
        """Delete an item.
        
        Args:
            item_id: Item ID
            
        Returns:
            True if deleted
        """
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """Clear all memory.
        
        Returns:
            True if cleared
        """
        pass
    
    @abstractmethod
    async def get_recent(self, limit: int = 10) -> List[MemoryItem]:
        """Get recent memory items.
        
        Args:
            limit: Max items to return
            
        Returns:
            List of recent items
        """
        pass
    
    @abstractmethod
    async def count(self) -> int:
        """Get total memory count.
        
        Returns:
            Number of items in memory
        """
        pass
