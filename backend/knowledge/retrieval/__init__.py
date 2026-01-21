"""
Retrieval Module

Provides RAG retrieval, pipeline, and URL mapping for knowledge base queries.
Extracted from Local-LLM project.
"""

from .retriever import RAGRetriever
from .pipeline import KnowledgePipeline
from .prompts import get_rag_prompt, get_direct_prompt
from .url_mapping import URLMapper

__all__ = [
    "RAGRetriever",
    "KnowledgePipeline",
    "get_rag_prompt",
    "get_direct_prompt",
    "URLMapper",
]
