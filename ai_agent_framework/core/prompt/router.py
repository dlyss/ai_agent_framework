"""Prompt Router - Dynamic prompt selection based on intent."""

from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from pydantic import BaseModel
import re

from core.prompt.manager import PromptManager, PromptTemplate
from core.llm.base import BaseLLM, Message


class RouterStrategy(str, Enum):
    """Routing strategy types."""
    KEYWORD = "keyword"      # Simple keyword matching
    REGEX = "regex"          # Regex pattern matching
    LLM = "llm"              # LLM-based intent classification
    SEMANTIC = "semantic"    # Embedding-based similarity
    CUSTOM = "custom"        # Custom function


class RouteRule(BaseModel):
    """Route rule definition."""
    name: str
    template_name: str
    strategy: RouterStrategy
    pattern: Optional[str] = None  # For keyword/regex
    keywords: List[str] = []       # For keyword strategy
    priority: int = 0              # Higher = more priority
    description: str = ""


class PromptRouter:
    """Routes user input to appropriate prompt templates."""
    
    def __init__(
        self,
        prompt_manager: PromptManager,
        default_template: str = "chat_default",
        llm: Optional[BaseLLM] = None
    ):
        self.prompt_manager = prompt_manager
        self.default_template = default_template
        self.llm = llm
        self.rules: List[RouteRule] = []
        self.custom_handlers: Dict[str, Callable] = {}
        
        # Register default routes
        self._register_defaults()
    
    def _register_defaults(self):
        """Register default routing rules."""
        defaults = [
            RouteRule(
                name="summarize",
                template_name="summarize",
                strategy=RouterStrategy.KEYWORD,
                keywords=["summarize", "summary", "总结", "概括", "摘要"],
                priority=10,
                description="Route to summarization template"
            ),
            RouteRule(
                name="translate",
                template_name="translate",
                strategy=RouterStrategy.KEYWORD,
                keywords=["translate", "翻译", "translation"],
                priority=10,
                description="Route to translation template"
            ),
            RouteRule(
                name="code_review",
                template_name="code_review",
                strategy=RouterStrategy.KEYWORD,
                keywords=["review code", "代码审查", "code review", "审查代码"],
                priority=10,
                description="Route to code review template"
            ),
            RouteRule(
                name="rag_query",
                template_name="rag_default",
                strategy=RouterStrategy.KEYWORD,
                keywords=["search", "find", "查找", "搜索", "根据文档"],
                priority=5,
                description="Route to RAG template"
            ),
        ]
        
        for rule in defaults:
            self.add_rule(rule)
    
    def add_rule(self, rule: RouteRule):
        """Add a routing rule.
        
        Args:
            rule: RouteRule to add
        """
        self.rules.append(rule)
        # Sort by priority (descending)
        self.rules.sort(key=lambda r: r.priority, reverse=True)
    
    def remove_rule(self, name: str) -> bool:
        """Remove a routing rule by name.
        
        Args:
            name: Rule name
            
        Returns:
            True if removed
        """
        original_len = len(self.rules)
        self.rules = [r for r in self.rules if r.name != name]
        return len(self.rules) < original_len
    
    def register_custom_handler(
        self,
        name: str,
        handler: Callable[[str], Optional[str]]
    ):
        """Register a custom routing handler.
        
        Args:
            name: Handler name
            handler: Function that takes input and returns template name or None
        """
        self.custom_handlers[name] = handler
    
    def _match_keyword(self, text: str, keywords: List[str]) -> bool:
        """Match text against keywords."""
        text_lower = text.lower()
        return any(kw.lower() in text_lower for kw in keywords)
    
    def _match_regex(self, text: str, pattern: str) -> bool:
        """Match text against regex pattern."""
        return bool(re.search(pattern, text, re.IGNORECASE))
    
    async def _match_llm(self, text: str) -> Optional[str]:
        """Use LLM to classify intent and select template."""
        if not self.llm:
            return None
        
        # Build classification prompt
        template_options = "\n".join([
            f"- {t.name}: {t.description}"
            for t in self.prompt_manager.list_templates()
        ])
        
        messages = [
            Message(
                role="system",
                content=f"""You are an intent classifier. Based on the user's input, 
select the most appropriate template from the following options:

{template_options}

Respond with ONLY the template name, nothing else."""
            ),
            Message(role="user", content=text)
        ]
        
        response = await self.llm.generate(messages, max_tokens=50)
        template_name = response.content.strip()
        
        # Validate template exists
        if self.prompt_manager.get(template_name):
            return template_name
        return None
    
    async def route(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> PromptTemplate:
        """Route user input to appropriate template.
        
        Args:
            user_input: User's input text
            context: Optional context for routing decisions
            
        Returns:
            Selected PromptTemplate
        """
        context = context or {}
        
        # Try each rule in priority order
        for rule in self.rules:
            matched = False
            
            if rule.strategy == RouterStrategy.KEYWORD:
                matched = self._match_keyword(user_input, rule.keywords)
            
            elif rule.strategy == RouterStrategy.REGEX:
                if rule.pattern:
                    matched = self._match_regex(user_input, rule.pattern)
            
            elif rule.strategy == RouterStrategy.CUSTOM:
                if rule.name in self.custom_handlers:
                    result = self.custom_handlers[rule.name](user_input)
                    if result:
                        template = self.prompt_manager.get(result)
                        if template:
                            return template
            
            elif rule.strategy == RouterStrategy.LLM:
                template_name = await self._match_llm(user_input)
                if template_name:
                    template = self.prompt_manager.get(template_name)
                    if template:
                        return template
            
            if matched:
                template = self.prompt_manager.get(rule.template_name)
                if template:
                    return template
        
        # Return default template
        return self.prompt_manager.get(self.default_template) or PromptTemplate(
            name="fallback",
            template="{input}",
            variables=["input"]
        )
    
    def list_rules(self) -> List[RouteRule]:
        """List all routing rules.
        
        Returns:
            List of RouteRule
        """
        return self.rules.copy()
    
    def get_rule(self, name: str) -> Optional[RouteRule]:
        """Get a rule by name.
        
        Args:
            name: Rule name
            
        Returns:
            RouteRule or None
        """
        for rule in self.rules:
            if rule.name == name:
                return rule
        return None
