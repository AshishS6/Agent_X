"""
General purpose assistant

Extracted from Local-LLM project (backend/local_llm_staging/backend/assistants/general.py).

This assistant is configured for general-purpose questions without RAG support.
"""

import os
from typing import Optional

from .base_assistant import AssistantConfig


class GeneralAssistant:
    """
    General purpose assistant configuration
    
    Extracted from Local-LLM project. Provides configuration for a general
    assistant without RAG support.
    """
    
    @staticmethod
    def get_config(model: Optional[str] = None) -> AssistantConfig:
        """Model defaults to LLM_LOCAL_MODEL env var or qwen2.5:7b-instruct."""
        if model is None:
            model = os.getenv("LLM_LOCAL_MODEL", "qwen2.5:7b-instruct")
        return AssistantConfig(
            name="General Assistant",
            model=model,
            use_rag=False,
            knowledge_base=None,
            system_prompt="You are a helpful AI assistant. Provide clear, accurate, and helpful responses to user questions."
        )
