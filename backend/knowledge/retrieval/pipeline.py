"""
End-to-end RAG pipeline

Extracted from Local-LLM project (backend/local_llm_staging/backend/rag/pipeline.py).
Renamed from RAGPipeline to KnowledgePipeline for clarity.

This module provides the complete RAG pipeline for querying knowledge bases.
It is generic and domain-agnostic - it retrieves context and returns structured data.
Domain-specific prompt composition should be handled by the assistant layer.
"""

import logging
from typing import List, Optional, Set, Dict, Any
from .retriever import RAGRetriever
from ..vector_store.embedding_client import OllamaEmbeddingClient
from ..vector_store.chromadb_store import ChromaDBStore
from .url_mapping import URLMapper

logger = logging.getLogger(__name__)


class KnowledgePipeline:
    """
    End-to-end RAG pipeline for knowledge base queries
    
    Extracted from Local-LLM project. Provides context-enhanced query processing
    with public URL citation support.
    """
    
    def __init__(self, embedding_client: OllamaEmbeddingClient, vector_store: ChromaDBStore):
        """
        Initialize RAG pipeline
        
        Args:
            embedding_client: Client for generating embeddings
            vector_store: Vector store for similarity search
        """
        self.retriever = RAGRetriever(embedding_client, vector_store)
    
    async def query(
        self,
        user_query: str,
        knowledge_base: str,
        n_results: int = 5,
        vendor: Optional[str] = None,
        layer: Optional[str] = None,
        boost_layers: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Process a RAG query and return structured context data
        
        This is a generic, domain-agnostic method that retrieves context and
        extracts public URLs. Domain-specific prompt composition should be
        handled by the assistant layer.
        
        Args:
            user_query: User's query
            knowledge_base: Knowledge base to search
            n_results: Number of context chunks to retrieve
            vendor: Optional vendor filter (e.g., 'zwitch', 'openmoney')
            layer: Optional layer filter (e.g., 'states', 'api', 'concepts')
            boost_layers: Optional list of layers to boost (e.g., ['states', 'principles'])
            
        Returns:
            Dictionary with:
            - "context": str - Retrieved context text (empty string if no results)
            - "public_urls": List[str] - Validated public URLs for citation
            - "query": str - Original user query
        """
        # Retrieve relevant context with metadata
        try:
            context_results = await self.retriever.retrieve(
                query=user_query,
                knowledge_base=knowledge_base,
                n_results=n_results,
                include_metadata=True,
                vendor=vendor,
                layer=layer,
                boost_layers=boost_layers
            )
        except Exception as e:
            # Log error but don't fail completely - return empty context
            logger.error(f"Error retrieving context: {e}", exc_info=True)
            context_results = []
        
        # Format context - NO internal source citations
        # Extract public URLs from context and source paths for citation
        if context_results:
            # Combine text without internal source citations
            context = "\n\n".join([r.get('text', '') for r in context_results])
            
            # Get source paths from metadata
            source_paths = [r.get('metadata', {}).get('source_path', '') for r in context_results if r.get('metadata', {}).get('source_path')]
            
            # Extract and validate public URLs using URLMapper
            public_urls = list(URLMapper.extract_and_validate_urls(context, source_paths))
        else:
            context = ""
            public_urls = []
        
        return {
            "context": context,
            "public_urls": public_urls,
            "query": user_query
        }
