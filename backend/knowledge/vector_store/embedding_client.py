"""
Embedding generation using Ollama

Extracted from Local-LLM project (backend/local_llm_staging/backend/rag/embed.py).
Renamed from EmbeddingClient to OllamaEmbeddingClient for clarity.

This module provides async embedding generation via Ollama API.
"""

import httpx
import os
import logging
from typing import List
import asyncio

logger = logging.getLogger(__name__)


class OllamaEmbeddingClient:
    """
    Client for generating embeddings via Ollama
    
    Extracted from Local-LLM project. Provides async embedding generation
    for RAG applications.
    """
    
    def __init__(self, base_url: str = None, model: str = "nomic-embed-text"):
        """
        Initialize embedding client
        
        Args:
            base_url: Ollama base URL (defaults to OLLAMA_BASE_URL env var or http://localhost:11434)
            model: Embedding model name (defaults to nomic-embed-text)
        """
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = model
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def embed(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.model,
                    "prompt": text
                }
            )
            response.raise_for_status()
            data = response.json()
            return data.get("embedding", [])
        except Exception as e:
            logger.error(f"Error generating embedding: {e}", exc_info=True)
            raise
    
    async def embed_batch(self, texts: List[str], batch_size: int = 10) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process in parallel
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = await asyncio.gather(*[self.embed(text) for text in batch])
            embeddings.extend(batch_embeddings)
        
        return embeddings
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
