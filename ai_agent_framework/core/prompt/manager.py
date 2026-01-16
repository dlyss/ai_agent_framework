"""Prompt Template Manager."""

import json
import os
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from pathlib import Path


class PromptTemplate(BaseModel):
    """Prompt template model."""
    name: str
    template: str
    description: str = ""
    variables: List[str] = []
    category: str = "general"
    version: str = "1.0"
    metadata: Dict[str, Any] = {}
    
    def format(self, **kwargs) -> str:
        """Format the template with variables.
        
        Args:
            **kwargs: Variable values
            
        Returns:
            Formatted prompt string
        """
        return self.template.format(**kwargs)
    
    def validate_variables(self, **kwargs) -> bool:
        """Validate that all required variables are provided.
        
        Args:
            **kwargs: Variable values
            
        Returns:
            True if all variables are provided
        """
        provided = set(kwargs.keys())
        required = set(self.variables)
        return required.issubset(provided)


class PromptManager:
    """Manages prompt templates with CRUD operations."""
    
    def __init__(self, templates_dir: Optional[str] = None):
        self.templates: Dict[str, PromptTemplate] = {}
        self.templates_dir = templates_dir
        
        # Load templates from directory if provided
        if templates_dir and os.path.exists(templates_dir):
            self._load_from_directory(templates_dir)
        
        # Register default templates
        self._register_defaults()
    
    def _load_from_directory(self, directory: str):
        """Load templates from JSON files in directory."""
        path = Path(directory)
        for file_path in path.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            template = PromptTemplate(**item)
                            self.templates[template.name] = template
                    else:
                        template = PromptTemplate(**data)
                        self.templates[template.name] = template
            except Exception as e:
                print(f"Error loading template from {file_path}: {e}")
    
    def _register_defaults(self):
        """Register default prompt templates."""
        defaults = [
            PromptTemplate(
                name="chat_default",
                template="You are a helpful AI assistant. Respond to the user's message thoughtfully and accurately.",
                description="Default chat system prompt",
                category="chat",
                variables=[]
            ),
            PromptTemplate(
                name="rag_default",
                template="""Based on the following context, answer the user's question.
If the context doesn't contain relevant information, say so.

Context:
{context}

Question: {question}

Answer:""",
                description="Default RAG prompt template",
                category="rag",
                variables=["context", "question"]
            ),
            PromptTemplate(
                name="summarize",
                template="""Please summarize the following text concisely:

{text}

Summary:""",
                description="Text summarization prompt",
                category="summarize",
                variables=["text"]
            ),
            PromptTemplate(
                name="translate",
                template="""Translate the following text from {source_lang} to {target_lang}:

{text}

Translation:""",
                description="Translation prompt",
                category="translate",
                variables=["source_lang", "target_lang", "text"]
            ),
            PromptTemplate(
                name="code_review",
                template="""Please review the following code and provide feedback on:
1. Code quality
2. Potential bugs
3. Performance issues
4. Suggestions for improvement

Code:
```{language}
{code}
```

Review:""",
                description="Code review prompt",
                category="code",
                variables=["language", "code"]
            ),
            PromptTemplate(
                name="qa_extraction",
                template="""Extract question-answer pairs from the following text for training purposes.
Format each pair as JSON: {{"question": "...", "answer": "..."}}

Text:
{text}

QA Pairs:""",
                description="QA extraction for fine-tuning data",
                category="finetune",
                variables=["text"]
            ),
        ]
        
        for template in defaults:
            if template.name not in self.templates:
                self.templates[template.name] = template
    
    def register(self, template: PromptTemplate) -> bool:
        """Register a new template.
        
        Args:
            template: PromptTemplate to register
            
        Returns:
            True if successful
        """
        self.templates[template.name] = template
        return True
    
    def get(self, name: str) -> Optional[PromptTemplate]:
        """Get a template by name.
        
        Args:
            name: Template name
            
        Returns:
            PromptTemplate or None
        """
        return self.templates.get(name)
    
    def delete(self, name: str) -> bool:
        """Delete a template.
        
        Args:
            name: Template name
            
        Returns:
            True if deleted
        """
        if name in self.templates:
            del self.templates[name]
            return True
        return False
    
    def list_templates(self, category: Optional[str] = None) -> List[PromptTemplate]:
        """List all templates, optionally filtered by category.
        
        Args:
            category: Optional category filter
            
        Returns:
            List of templates
        """
        templates = list(self.templates.values())
        if category:
            templates = [t for t in templates if t.category == category]
        return templates
    
    def list_categories(self) -> List[str]:
        """List all unique categories.
        
        Returns:
            List of category names
        """
        return list(set(t.category for t in self.templates.values()))
    
    def format_template(self, name: str, **kwargs) -> str:
        """Get and format a template.
        
        Args:
            name: Template name
            **kwargs: Template variables
            
        Returns:
            Formatted prompt string
            
        Raises:
            ValueError: If template not found
        """
        template = self.get(name)
        if not template:
            raise ValueError(f"Template not found: {name}")
        return template.format(**kwargs)
    
    def save_to_file(self, filepath: str):
        """Save all templates to a JSON file.
        
        Args:
            filepath: Output file path
        """
        data = [t.model_dump() for t in self.templates.values()]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_from_file(self, filepath: str):
        """Load templates from a JSON file.
        
        Args:
            filepath: Input file path
        """
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    template = PromptTemplate(**item)
                    self.templates[template.name] = template
            else:
                template = PromptTemplate(**data)
                self.templates[template.name] = template
