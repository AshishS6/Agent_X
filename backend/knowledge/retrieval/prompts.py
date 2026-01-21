"""
Prompt templates for RAG system

Extracted from Local-LLM project (backend/local_llm_staging/backend/rag/prompts.py).

This module provides prompt templates for RAG-enhanced queries.
"""


def get_rag_prompt(query: str, context: str, system_prompt: str) -> str:
    """
    Construct RAG prompt with context and system prompt
    
    Args:
        query: User query
        context: Retrieved context from knowledge base
        system_prompt: Assistant-specific system prompt
        
    Returns:
        Formatted prompt string
    """
    return f"""{system_prompt}

Use the following context from the knowledge base to answer the question. If the context doesn't contain relevant information, use your general knowledge to provide a helpful response.

Context:
{context}

Question: {query}

Answer:"""


def get_direct_prompt(query: str, system_prompt: str) -> str:
    """
    Construct direct prompt without RAG context
    
    Args:
        query: User query
        system_prompt: Assistant-specific system prompt
        
    Returns:
        Formatted prompt string
    """
    return f"""{system_prompt}

Question: {query}

Answer:"""
