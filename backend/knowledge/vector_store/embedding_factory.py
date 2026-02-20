"""
Embedding Client Factory

Auto-selects the right embedding backend based on environment config:
  - EMBEDDING_PROVIDER=openai  → OpenAIEmbeddingClient
  - EMBEDDING_PROVIDER=ollama  → OllamaEmbeddingClient
  - (default) LLM_MODE=cloud_only → OpenAIEmbeddingClient
  - (default) everything else  → OllamaEmbeddingClient
"""

import os
import logging
from typing import Union

from .embedding_client import OllamaEmbeddingClient
from .openai_embedding_client import OpenAIEmbeddingClient

logger = logging.getLogger(__name__)

EmbeddingClient = Union[OllamaEmbeddingClient, OpenAIEmbeddingClient]


def get_embedding_client() -> EmbeddingClient:
    """
    Factory: returns the best embedding client for the current config.

    Decision order:
      1. EMBEDDING_PROVIDER env var (explicit override, 'openai' or 'ollama')
      2. LLM_MODE=cloud_only  → OpenAI embeddings
      3. LLM_MODE=local_only  → Ollama embeddings
      4. Default              → Ollama embeddings (local-first)

    Returns:
        An embedding client with .embed() and .embed_batch() async methods.
    """
    embedding_provider = (os.getenv("EMBEDDING_PROVIDER", "") or "").strip().lower()
    llm_mode = (os.getenv("LLM_MODE", "") or "").strip().lower()

    # Explicit override wins
    if embedding_provider == "openai":
        logger.info("Embedding provider: OpenAI (EMBEDDING_PROVIDER=openai)")
        return OpenAIEmbeddingClient()

    if embedding_provider == "ollama":
        logger.info("Embedding provider: Ollama (EMBEDDING_PROVIDER=ollama)")
        return OllamaEmbeddingClient()

    # Infer from LLM_MODE
    if llm_mode == "cloud_only":
        logger.info(
            "Embedding provider: OpenAI (inferred from LLM_MODE=cloud_only)"
        )
        return OpenAIEmbeddingClient()

    if llm_mode == "local_only":
        logger.info(
            "Embedding provider: Ollama (inferred from LLM_MODE=local_only)"
        )
        return OllamaEmbeddingClient()

    # Default: local-first (Ollama)
    logger.info("Embedding provider: Ollama (default, local-first)")
    return OllamaEmbeddingClient()
