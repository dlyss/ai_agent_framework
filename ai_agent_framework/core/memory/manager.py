"""Memory Manager - Unified interface for short and long-term memory."""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from core.memory.base import MemoryItem
from core.memory.short_term import ShortTermMemory
from core.memory.long_term import LongTermMemory
from core.llm.base import BaseLLM, Message


class MemoryManager:
    """Unified memory manager combining short and long-term memory."""
    
    def __init__(
        self,
        short_term: ShortTermMemory,
        long_term: LongTermMemory,
        llm: Optional[BaseLLM] = None,
        auto_archive: bool = True,
        archive_threshold: float = 0.6
    ):
        self.short_term = short_term
        self.long_term = long_term
        self.llm = llm
        self.auto_archive = auto_archive
        self.archive_threshold = archive_threshold
    
    async def add_message(
        self,
        content: str,
        role: str = "user",
        importance: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a message to memory.
        
        Args:
            content: Message content
            role: Message role (user/assistant/system)
            importance: Importance score (0-1)
            metadata: Optional metadata
            
        Returns:
            Memory item ID
        """
        item = MemoryItem(
            content=content,
            role=role,
            importance=importance,
            metadata=metadata or {}
        )
        
        # Add to short-term memory
        item_id = await self.short_term.add(item)
        
        # Archive to long-term if importance is high
        if self.auto_archive and importance >= self.archive_threshold:
            await self.long_term.add(item)
        
        return item_id
    
    async def add_conversation_turn(
        self,
        user_message: str,
        assistant_message: str,
        user_metadata: Optional[Dict] = None,
        assistant_metadata: Optional[Dict] = None
    ) -> tuple:
        """Add a conversation turn (user + assistant).
        
        Args:
            user_message: User's message
            assistant_message: Assistant's response
            user_metadata: Optional user message metadata
            assistant_metadata: Optional assistant message metadata
            
        Returns:
            Tuple of (user_id, assistant_id)
        """
        user_id = await self.add_message(
            user_message,
            role="user",
            metadata=user_metadata
        )
        assistant_id = await self.add_message(
            assistant_message,
            role="assistant",
            metadata=assistant_metadata
        )
        return user_id, assistant_id
    
    async def get_conversation_history(
        self,
        max_turns: Optional[int] = None,
        max_tokens: int = 4000
    ) -> List[Message]:
        """Get conversation history for LLM context.
        
        Args:
            max_turns: Maximum conversation turns
            max_tokens: Maximum token budget
            
        Returns:
            List of Message objects
        """
        items = await self.short_term.get_context_window(max_tokens)
        
        if max_turns:
            # Ensure we get complete turns
            items = items[-(max_turns * 2):]
        
        return [Message(role=item.role, content=item.content) for item in items]
    
    async def search_all(
        self,
        query: str,
        limit: int = 10,
        include_short_term: bool = True,
        include_long_term: bool = True
    ) -> List[MemoryItem]:
        """Search across all memory stores.
        
        Args:
            query: Search query
            limit: Max results
            include_short_term: Include short-term results
            include_long_term: Include long-term results
            
        Returns:
            Combined search results
        """
        results = []
        
        if include_short_term:
            short_results = await self.short_term.search(query, limit=limit)
            results.extend(short_results)
        
        if include_long_term:
            long_results = await self.long_term.search(query, limit=limit)
            # Avoid duplicates
            existing_ids = {r.id for r in results}
            for item in long_results:
                if item.id not in existing_ids:
                    results.append(item)
        
        # Sort by timestamp and limit
        results.sort(key=lambda x: x.timestamp, reverse=True)
        return results[:limit]
    
    async def get_relevant_context(
        self,
        query: str,
        short_term_count: int = 5,
        long_term_count: int = 3
    ) -> Dict[str, List[MemoryItem]]:
        """Get relevant context from both memory types.
        
        Args:
            query: Query for semantic search
            short_term_count: Max short-term items
            long_term_count: Max long-term items
            
        Returns:
            Dict with 'short_term' and 'long_term' lists
        """
        short_results = await self.short_term.get_recent(short_term_count)
        long_results = await self.long_term.search(query, limit=long_term_count)
        
        return {
            "short_term": short_results,
            "long_term": long_results
        }
    
    async def archive_to_long_term(
        self,
        item_ids: Optional[List[str]] = None,
        importance_threshold: float = 0.5
    ) -> int:
        """Archive short-term memories to long-term.
        
        Args:
            item_ids: Specific IDs to archive, or None for all
            importance_threshold: Minimum importance for auto-archive
            
        Returns:
            Number of items archived
        """
        items = await self.short_term.get_all()
        archived = 0
        
        for item in items:
            if item_ids and item.id not in item_ids:
                continue
            if item.importance >= importance_threshold:
                await self.long_term.add(item)
                archived += 1
        
        return archived
    
    async def summarize_and_archive(
        self,
        max_items: int = 10
    ) -> Optional[str]:
        """Summarize recent conversation and archive.
        
        Args:
            max_items: Max items to summarize
            
        Returns:
            Summary memory ID or None
        """
        if not self.llm:
            return None
        
        items = await self.short_term.get_recent(max_items)
        if not items:
            return None
        
        # Build conversation text
        conversation = "\n".join([
            f"{item.role}: {item.content}"
            for item in items
        ])
        
        # Generate summary
        messages = [
            Message(
                role="system",
                content="Summarize the following conversation concisely, capturing key points and decisions."
            ),
            Message(role="user", content=conversation)
        ]
        
        response = await self.llm.generate(messages, max_tokens=500)
        
        # Archive summary
        summary_item = MemoryItem(
            content=response.content,
            role="system",
            importance=0.8,
            metadata={
                "type": "summary",
                "source_count": len(items),
                "source_ids": [item.id for item in items]
            }
        )
        
        return await self.long_term.add(summary_item)
    
    async def clear_short_term(self) -> bool:
        """Clear short-term memory."""
        return await self.short_term.clear()
    
    async def clear_all(self) -> bool:
        """Clear all memory."""
        await self.short_term.clear()
        await self.long_term.clear()
        return True
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics.
        
        Returns:
            Dict with memory stats
        """
        return {
            "short_term_count": await self.short_term.count(),
            "long_term_count": await self.long_term.count(),
            "short_term_max_size": self.short_term.max_size,
        }
