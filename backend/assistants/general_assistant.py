"""
General purpose assistant

Extracted from Local-LLM project (backend/local_llm_staging/backend/assistants/general.py).

This assistant is configured for general-purpose questions without RAG support.
"""

from .base_assistant import AssistantConfig


class GeneralAssistant:
    """
    General purpose assistant configuration
    
    Extracted from Local-LLM project. Provides configuration for a general
    assistant without RAG support.
    """
    
    @staticmethod
    def get_config(model: str = "qwen2.5:7b") -> AssistantConfig:
        """
        Get general assistant configuration
        
        Args:
            model: Model to use (defaults to qwen2.5:7b)
            
        Returns:
            AssistantConfig instance
        """
        return AssistantConfig(
            name="General Assistant",
            model=model,
            use_rag=False,
            knowledge_base=None,
            system_prompt="You are a helpful AI assistant. Provide clear, accurate, and helpful responses to user questions."
        )
