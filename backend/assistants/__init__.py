"""
Assistants Module for AgentX

Extracted from Local-LLM project. Provides assistant configurations for
conversational AI assistants (distinct from task-based agents).

Assistants are stateful, conversational, and can use RAG for knowledge retrieval.
Agents are stateless, task-based, and execute specific actions.

This module contains configuration classes only - they define system prompts,
model preferences, and RAG settings. Execution logic is separate.
"""

from .base_assistant import AssistantConfig
from .fintech_assistant import FintechAssistant
from .code_assistant import CodeAssistant
from .general_assistant import GeneralAssistant
from .prompt_builder import build_fintech_prompt, build_generic_prompt

__all__ = [
    "AssistantConfig",
    "FintechAssistant",
    "CodeAssistant",
    "GeneralAssistant",
    "build_fintech_prompt",
    "build_generic_prompt",
]
