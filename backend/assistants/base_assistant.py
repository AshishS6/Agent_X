"""
Base assistant configuration

Extracted from Local-LLM project (backend/local_llm_staging/backend/assistants/base.py).

This module defines the base configuration model for assistants.
Assistants are conversational, stateful components that can use RAG.
They are distinct from agents, which are task-based and stateless.
"""

from pydantic import BaseModel
from typing import Optional


class AssistantConfig(BaseModel):
    """
    Configuration for an assistant
    
    Extracted from Local-LLM project. Defines system prompts, model preferences,
    and RAG settings for conversational assistants.
    
    Note: This is a configuration class only. It does not execute tasks.
    Assistants are separate from agents - agents execute tasks, assistants
    provide conversational interfaces with optional RAG support.
    """
    name: str
    model: str
    use_rag: bool
    knowledge_base: Optional[str] = None
    system_prompt: str
    
    class Config:
        frozen = True  # Make configs immutable
