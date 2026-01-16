"""Short-term memory implementation using in-memory storage."""

from typing import List, Optional, Dict
from collections import deque
from datetime import datetime

from core.memory.base import BaseMemory, MemoryItem
from app.config import get_settings


class ShortTermMemory(BaseMemory):
    """Short-term memory using deque for sliding window."""
    
    def __init__(
        self,
        max_size: Optional[int] = None,
        session_id: Optional[str] = None
    ):
        settings = get_settings()
        self.max_size = max_size or settings.short_term_memory_size
        self.session_id = session_id
        self._memory: deque[MemoryItem] = deque(maxlen=self.max_size)
        self._index: Dict[str, MemoryItem] = {}
    
    async def add(self, item: MemoryItem) -> str:
        """Add item to short-term memory."""
        # Add session_id to metadata
        if self.session_id:
            item.metadata["session_id"] = self.session_id
        
        # Remove from index if it will be evicted
        if len(self._memory) >= self.max_size:
            evicted = self._memory[0]
            self._index.pop(evicted.id, None)
        
        self._memory.append(item)
        self._index[item.id] = item
        return item.id
    
    async def get(self, item_id: str) -> Optional[MemoryItem]:
        """Get item by ID."""
        return self._index.get(item_id)
    
    async def search(
        self,
        query: str,
        limit: int = 5,
        **kwargs
    ) -> List[MemoryItem]:
        """Search memory by content (simple substring match)."""
        query_lower = query.lower()
        results = []
        
        for item in reversed(list(self._memory)):
            if query_lower in item.content.lower():
                results.append(item)
                if len(results) >= limit:
                    break
        
        return results
    
    async def delete(self, item_id: str) -> bool:
        """Delete item by ID."""
        if item_id in self._index:
            item = self._index.pop(item_id)
            # Rebuild deque without the item
            self._memory = deque(
                [m for m in self._memory if m.id != item_id],
                maxlen=self.max_size
            )
            return True
        return False
    
    async def clear(self) -> bool:
        """Clear all memory."""
        self._memory.clear()
        self._index.clear()
        return True
    
    async def get_recent(self, limit: int = 10) -> List[MemoryItem]:
        """Get recent items (most recent first)."""
        items = list(self._memory)
        items.reverse()
        return items[:limit]
    
    async def count(self) -> int:
        """Get memory count."""
        return len(self._memory)
    
    async def get_all(self) -> List[MemoryItem]:
        """Get all items in chronological order."""
        return list(self._memory)
    
    def to_messages(self) -> List[Dict[str, str]]:
        """Convert memory to message format for LLM.
        
        Returns:
            List of message dicts with role and content
        """
        return [
            {"role": item.role, "content": item.content}
            for item in self._memory
        ]
    
    async def add_user_message(self, content: str) -> str:
        """Convenience method to add user message."""
        item = MemoryItem(content=content, role="user")
        return await self.add(item)
    
    async def add_assistant_message(self, content: str) -> str:
        """Convenience method to add assistant message."""
        item = MemoryItem(content=content, role="assistant")
        return await self.add(item)
    
    async def get_context_window(self, max_tokens: int = 4000) -> List[MemoryItem]:
        """Get items that fit within token limit (approximate).
        
        Args:
            max_tokens: Maximum tokens to include
            
        Returns:
            List of items within token budget
        """
        items = []
        total_chars = 0
        char_limit = max_tokens * 4  # Rough estimate
        
        for item in reversed(list(self._memory)):
            if total_chars + len(item.content) > char_limit:
                break
            items.insert(0, item)
            total_chars += len(item.content)
        
        return items
