"""RAG Chain - Combines retrieval and generation."""

from typing import List, Optional, Dict, Any, AsyncGenerator
from core.llm.base import BaseLLM, Message
from core.rag.retriever import Retriever
from core.vector_store.base import SearchResult


class RAGChain:
    """RAG Chain combining retrieval and LLM generation."""
    
    DEFAULT_TEMPLATE = """Based on the following context, answer the user's question.
If the context doesn't contain relevant information, say so.

Context:
{context}

Question: {question}

Answer:"""

    def __init__(
        self,
        llm: BaseLLM,
        retriever: Retriever,
        template: Optional[str] = None,
        system_message: Optional[str] = None,
        include_sources: bool = True,
        max_context_length: int = 4000
    ):
        self.llm = llm
        self.retriever = retriever
        self.template = template or self.DEFAULT_TEMPLATE
        self.system_message = system_message or "You are a helpful assistant that answers questions based on the provided context."
        self.include_sources = include_sources
        self.max_context_length = max_context_length
    
    def _format_context(self, results: List[SearchResult]) -> str:
        """Format retrieved results into context string."""
        context_parts = []
        total_length = 0
        
        for i, result in enumerate(results):
            content = result.content
            # Truncate if needed
            if total_length + len(content) > self.max_context_length:
                remaining = self.max_context_length - total_length
                if remaining > 100:  # Only add if we can fit meaningful content
                    content = content[:remaining] + "..."
                else:
                    break
            
            context_parts.append(f"[{i+1}] {content}")
            total_length += len(content)
        
        return "\n\n".join(context_parts)
    
    def _build_prompt(
        self,
        question: str,
        context: str
    ) -> str:
        """Build the prompt from template."""
        return self.template.format(
            context=context,
            question=question
        )
    
    async def query(
        self,
        question: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        chat_history: Optional[List[Message]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Query the RAG chain.
        
        Args:
            question: User question
            top_k: Number of documents to retrieve
            filters: Metadata filters for retrieval
            chat_history: Previous conversation history
            **kwargs: Additional LLM parameters
            
        Returns:
            Dict with answer, sources, etc.
        """
        # Retrieve relevant documents
        results = await self.retriever.retrieve(
            query=question,
            top_k=top_k,
            filters=filters
        )
        
        # Format context
        context = self._format_context(results)
        
        # Build messages
        messages = [Message(role="system", content=self.system_message)]
        
        # Add chat history if provided
        if chat_history:
            messages.extend(chat_history)
        
        # Add current question with context
        prompt = self._build_prompt(question, context)
        messages.append(Message(role="user", content=prompt))
        
        # Generate response
        response = await self.llm.generate(messages, **kwargs)
        
        # Build result
        result = {
            "answer": response.content,
            "model": response.model,
            "usage": response.usage,
        }
        
        if self.include_sources:
            result["sources"] = [
                {
                    "id": r.id,
                    "content": r.content[:200] + "..." if len(r.content) > 200 else r.content,
                    "score": r.score,
                    "metadata": r.metadata
                }
                for r in results
            ]
        
        return result
    
    async def stream_query(
        self,
        question: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        chat_history: Optional[List[Message]] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream query the RAG chain.
        
        Args:
            question: User question
            top_k: Number of documents to retrieve
            filters: Metadata filters for retrieval
            chat_history: Previous conversation history
            **kwargs: Additional LLM parameters
            
        Yields:
            Response chunks
        """
        # Retrieve relevant documents
        results = await self.retriever.retrieve(
            query=question,
            top_k=top_k,
            filters=filters
        )
        
        # Format context
        context = self._format_context(results)
        
        # Build messages
        messages = [Message(role="system", content=self.system_message)]
        
        if chat_history:
            messages.extend(chat_history)
        
        prompt = self._build_prompt(question, context)
        messages.append(Message(role="user", content=prompt))
        
        # Stream generate
        async for chunk in self.llm.stream_generate(messages, **kwargs):
            yield chunk
    
    async def add_documents(
        self,
        documents: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> List[str]:
        """Add documents to the RAG system.
        
        Args:
            documents: List of documents
            batch_size: Processing batch size
            
        Returns:
            List of document IDs
        """
        return await self.retriever.add_documents(documents, batch_size)
