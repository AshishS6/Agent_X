"""
OpenAI Embedding Client

Cloud-based embedding generation using the OpenAI Embeddings API.
Used when LLM_MODE=cloud_only or EMBEDDING_PROVIDER=openai.

Model: text-embedding-3-small (default)
  - 1536 dimensions
  - ~$0.02 per 1M tokens (very cheap)
  - Fast, no local GPU required
"""

import os
import logging
from typing import List
import asyncio

logger = logging.getLogger(__name__)


class OpenAIEmbeddingClient:
    """
    Client for generating embeddings via the OpenAI Embeddings API.

    Drop-in replacement for OllamaEmbeddingClient when running in cloud mode.
    Uses the same async interface so the rest of the pipeline is unchanged.
    """

    def __init__(
        self,
        api_key: str = None,
        model: str = None,
    ):
        """
        Initialize OpenAI embedding client.

        Args:
            api_key: OpenAI API key. Defaults to OPENAI_API_KEY env var.
            model:   Embedding model name. Defaults to OPENAI_EMBEDDING_MODEL
                     env var, or 'text-embedding-3-small'.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY environment variable."
            )

        self.model = (
            model
            or os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        )

        # Import openai lazily so the module is optional (won't break if not installed)
        try:
            import openai as _openai
            self._client = _openai.AsyncOpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError(
                "openai package is required for OpenAI embeddings. "
                "Run: pip install openai"
            )

        logger.info(
            f"OpenAIEmbeddingClient initialized - model: {self.model}"
        )

    async def embed(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed.

        Returns:
            Embedding vector (list of floats).
        """
        try:
            response = await self._client.embeddings.create(
                model=self.model,
                input=text,
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating OpenAI embedding: {e}", exc_info=True)
            raise

    async def embed_batch(
        self, texts: List[str], batch_size: int = 20
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in parallel batches.

        OpenAI supports up to 2048 inputs per request; we batch conservatively
        to avoid rate-limit issues while still being fast.

        Args:
            texts:      List of texts to embed.
            batch_size: Number of texts per API call (default: 20).

        Returns:
            List of embedding vectors.
        """
        embeddings: List[List[float]] = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            try:
                response = await self._client.embeddings.create(
                    model=self.model,
                    input=batch,
                )
                # Results are ordered by index
                batch_embeddings = [item.embedding for item in sorted(response.data, key=lambda x: x.index)]
                embeddings.extend(batch_embeddings)
                logger.debug(
                    f"Embedded batch {i // batch_size + 1}: {len(batch)} texts"
                )
            except Exception as e:
                logger.error(
                    f"Error generating OpenAI embeddings for batch {i}-{i+batch_size}: {e}",
                    exc_info=True,
                )
                raise

        return embeddings

    async def close(self):
        """Close the async HTTP client (no-op for openai SDK, but keeps interface consistent)."""
        try:
            await self._client.close()
        except Exception:
            pass
