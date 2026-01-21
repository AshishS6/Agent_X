"""
LLM Module for AgentX

Extracted from Local-LLM project. Provides LLM provider abstractions and
prompt utilities.

This module is independent and can be used by both agents and assistants.
"""

from .providers.ollama_client import OllamaClient
from .prompts.response_filter import filter_thinking_content, extract_final_answer

__all__ = [
    "OllamaClient",
    "filter_thinking_content",
    "extract_final_answer",
]
