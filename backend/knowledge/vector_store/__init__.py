"""
Vector Store Module

Provides ChromaDB-based vector storage and Ollama-based embedding generation.
Extracted from Local-LLM project.
"""

from .chromadb_store import ChromaDBStore
from .embedding_client import OllamaEmbeddingClient

__all__ = ["ChromaDBStore", "OllamaEmbeddingClient"]
