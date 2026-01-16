"""LangChain 1.x LCEL-based RAG Chain implementation."""

from typing import List, Optional, Dict, Any, AsyncIterator
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from core.rag.retriever import Retriever
from core.vector_store.base import SearchResult
from app.config import get_settings


class LangChainRAGChain:
    """RAG Chain using LangChain 1.x LCEL (LangChain Expression Language).
    
    This implementation uses the modern LangChain 1.x API with:
    - LCEL pipe syntax (|)
    - ChatPromptTemplate
    - RunnablePassthrough for context injection
    - Async invoke/ainvoke methods
    """
    
    DEFAULT_SYSTEM_PROMPT = """You are a helpful assistant that answers questions based on the provided context.
If the context doesn't contain relevant information to answer the question, say so clearly.
Always cite the source when using information from the context."""

    DEFAULT_USER_TEMPLATE = """Context:
{context}

Question: {question}

Please provide a comprehensive answer based on the context above."""

    def __init__(
        self,
        retriever: Retriever,
        model_name: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        system_prompt: Optional[str] = None,
        include_sources: bool = True,
        max_context_length: int = 4000
    ):
        """Initialize LangChain RAG Chain.
        
        Args:
            retriever: Document retriever instance
            model_name: OpenAI model name
            temperature: Generation temperature
            max_tokens: Maximum tokens for response
            api_key: OpenAI API key (optional, uses env if not provided)
            api_base: OpenAI API base URL (optional)
            system_prompt: Custom system prompt
            include_sources: Whether to include sources in response
            max_context_length: Maximum context length in characters
        """
        settings = get_settings()
        
        self.retriever = retriever
        self.include_sources = include_sources
        self.max_context_length = max_context_length
        
        # Initialize LangChain ChatOpenAI (1.x API)
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key or settings.openai_api_key,
            base_url=api_base or settings.openai_api_base,
        )
        
        # Build prompt template using LCEL
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt or self.DEFAULT_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", self.DEFAULT_USER_TEMPLATE),
        ])
        
        # Build LCEL chain
        self.chain = self.prompt | self.llm | StrOutputParser()
    
    def _format_context(self, results: List[SearchResult]) -> str:
        """Format retrieved results into context string."""
        context_parts = []
        total_length = 0
        
        for i, result in enumerate(results):
            content = result.content
            if total_length + len(content) > self.max_context_length:
                remaining = self.max_context_length - total_length
                if remaining > 100:
                    content = content[:remaining] + "..."
                else:
                    break
            
            source_info = f"[Source {i+1}]"
            if result.metadata:
                source_name = result.metadata.get("source", result.metadata.get("file", ""))
                if source_name:
                    source_info = f"[Source {i+1}: {source_name}]"
            
            context_parts.append(f"{source_info}\n{content}")
            total_length += len(content)
        
        return "\n\n".join(context_parts)
    
    def _format_chat_history(self, history: Optional[List[Dict[str, str]]]) -> List:
        """Convert chat history to LangChain message format."""
        if not history:
            return []
        
        messages = []
        for msg in history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
            elif role == "system":
                messages.append(SystemMessage(content=content))
        
        return messages
    
    async def ainvoke(
        self,
        question: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """Async invoke the RAG chain.
        
        Args:
            question: User's question
            top_k: Number of documents to retrieve
            filters: Metadata filters for retrieval
            chat_history: Optional conversation history
            
        Returns:
            Dict containing answer and optionally sources
        """
        # Retrieve relevant documents
        results = await self.retriever.retrieve(
            query=question,
            top_k=top_k,
            filters=filters
        )
        
        # Format context and history
        context = self._format_context(results)
        history_messages = self._format_chat_history(chat_history)
        
        # Invoke chain using LCEL (LangChain 1.x)
        answer = await self.chain.ainvoke({
            "context": context,
            "question": question,
            "chat_history": history_messages,
        })
        
        # Build response
        response = {"answer": answer}
        
        if self.include_sources:
            response["sources"] = [
                {
                    "id": r.id,
                    "content": r.content[:200] + "..." if len(r.content) > 200 else r.content,
                    "score": r.score,
                    "metadata": r.metadata
                }
                for r in results
            ]
        
        return response
    
    async def astream(
        self,
        question: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> AsyncIterator[str]:
        """Async stream the RAG chain response.
        
        Args:
            question: User's question
            top_k: Number of documents to retrieve
            filters: Metadata filters for retrieval
            chat_history: Optional conversation history
            
        Yields:
            Response chunks as strings
        """
        # Retrieve relevant documents
        results = await self.retriever.retrieve(
            query=question,
            top_k=top_k,
            filters=filters
        )
        
        # Format context and history
        context = self._format_context(results)
        history_messages = self._format_chat_history(chat_history)
        
        # Stream using LCEL (LangChain 1.x)
        async for chunk in self.chain.astream({
            "context": context,
            "question": question,
            "chat_history": history_messages,
        }):
            yield chunk
    
    def invoke(
        self,
        question: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """Sync invoke the RAG chain (for non-async contexts).
        
        Note: This method retrieves documents synchronously.
        For async operations, use ainvoke().
        """
        import asyncio
        return asyncio.run(self.ainvoke(question, top_k, filters, chat_history))


class LangChainConversationChain:
    """Simple conversation chain using LangChain 1.x LCEL.
    
    For direct LLM conversations without RAG.
    """
    
    DEFAULT_SYSTEM_PROMPT = "You are a helpful AI assistant."
    
    def __init__(
        self,
        model_name: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ):
        settings = get_settings()
        
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key or settings.openai_api_key,
            base_url=api_base or settings.openai_api_base,
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt or self.DEFAULT_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
        ])
        
        self.chain = self.prompt | self.llm | StrOutputParser()
    
    async def ainvoke(
        self,
        user_input: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """Async invoke conversation."""
        history_messages = []
        if chat_history:
            for msg in chat_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    history_messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    history_messages.append(AIMessage(content=content))
        
        return await self.chain.ainvoke({
            "input": user_input,
            "chat_history": history_messages,
        })
    
    async def astream(
        self,
        user_input: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> AsyncIterator[str]:
        """Async stream conversation."""
        history_messages = []
        if chat_history:
            for msg in chat_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    history_messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    history_messages.append(AIMessage(content=content))
        
        async for chunk in self.chain.astream({
            "input": user_input,
            "chat_history": history_messages,
        }):
            yield chunk
