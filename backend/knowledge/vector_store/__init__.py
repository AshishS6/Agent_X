"""
Vector Store Module

Provides ChromaDB-based vector storage and embedding generation.
Supports both Ollama (local) and OpenAI (cloud) embeddings via a smart factory.
"""

from .chromadb_store import ChromaDBStore
from .embedding_client import OllamaEmbeddingClient
from .openai_embedding_client import OpenAIEmbeddingClient
from .embedding_factory import get_embedding_client

__all__ = [
    "ChromaDBStore",
    "OllamaEmbeddingClient",
    "OpenAIEmbeddingClient",
    "get_embedding_client",
]
