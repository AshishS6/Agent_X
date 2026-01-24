"""
Code-focused assistant

Extracted from Local-LLM project (backend/local_llm_staging/backend/assistants/code.py).

This assistant is configured for code-related questions without RAG support.
"""

import os
from typing import Optional

from .base_assistant import AssistantConfig


class CodeAssistant:
    """
    Code-focused assistant configuration
    
    Extracted from Local-LLM project. Provides configuration for a code
    assistant without RAG support.
    """
    
    @staticmethod
    def get_config(model: Optional[str] = None) -> AssistantConfig:
        """Model defaults to LLM_LOCAL_MODEL env var or qwen2.5:7b-instruct."""
        if model is None:
            model = os.getenv("LLM_LOCAL_MODEL", "qwen2.5:7b-instruct")
        return AssistantConfig(
            name="code",
            model=model,
            use_rag=False,
            knowledge_base=None,
            system_prompt="""You are an expert software engineer and coding assistant. You help users with:
- Writing, debugging, and optimizing code
- Explaining programming concepts
- Code reviews and best practices
- Architecture and design patterns
- Troubleshooting technical issues

Provide clear, well-structured code examples and explanations. Always consider best practices, performance, and maintainability."""
        )
