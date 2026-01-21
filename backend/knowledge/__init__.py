"""
Knowledge Module for AgentX

Extracted from Local-LLM project. Provides RAG (Retrieval-Augmented Generation)
capabilities including vector storage, document ingestion, and retrieval.

This module is independent of AgentX agents and can be used by assistants
or other components that need knowledge base access.
"""

from .vector_store import ChromaDBStore, OllamaEmbeddingClient
from .ingestion import chunk_text, process_file
from .retrieval import RAGRetriever, KnowledgePipeline

__all__ = [
    "ChromaDBStore",
    "OllamaEmbeddingClient",
    "chunk_text",
    "process_file",
    "RAGRetriever",
    "KnowledgePipeline",
]
