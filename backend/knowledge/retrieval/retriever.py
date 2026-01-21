"""
Retrieval logic for RAG

Extracted from Local-LLM project (backend/local_llm_staging/backend/rag/retrieve.py).
Renamed from Retriever to RAGRetriever for clarity.

This module provides semantic retrieval with filtering and boosting capabilities.
"""

from typing import List, Dict, Optional, Any
from ..vector_store.embedding_client import OllamaEmbeddingClient
from ..vector_store.chromadb_store import ChromaDBStore


class RAGRetriever:
    """
    Retriever for RAG queries
    
    Extracted from Local-LLM project. Provides semantic search with
    metadata filtering and layer boosting.
    """
    
    def __init__(self, embedding_client: OllamaEmbeddingClient, vector_store: ChromaDBStore):
        """
        Initialize retriever
        
        Args:
            embedding_client: Client for generating embeddings
            vector_store: Vector store for similarity search
        """
        self.embedding_client = embedding_client
        self.vector_store = vector_store
    
    async def retrieve(
        self,
        query: str,
        knowledge_base: str,
        n_results: int = 5,
        include_metadata: bool = False,
        vendor: Optional[str] = None,
        layer: Optional[str] = None,
        boost_layers: Optional[List[str]] = None,
        expand_query: bool = True
    ):
        """
        Retrieve relevant documents for a query
        
        Args:
            query: User query
            knowledge_base: Knowledge base to search
            n_results: Number of results to return
            include_metadata: If True, return dicts with text and metadata
            vendor: Optional vendor filter (e.g., 'zwitch', 'openmoney')
            layer: Optional layer filter (e.g., 'states', 'api', 'concepts')
            boost_layers: Optional list of layers to boost (e.g., ['states', 'principles'])
            expand_query: If True, expand query with synonyms and related terms
            
        Returns:
            If include_metadata=False: List of retrieved text chunks
            If include_metadata=True: List of dicts with 'text', 'metadata', and 'distance' keys
        """
        # Expand query if enabled
        if expand_query:
            expanded_terms = self._expand_query(query)
            # Use original query for primary search, but expanded terms help with matching
            # For now, we'll use the original query but the expansion helps with understanding
            search_query = query
        else:
            search_query = query
        
        # Generate query embedding
        query_embedding = await self.embedding_client.embed(search_query)
        
        # Query with more results if filtering is needed
        query_n_results = n_results * 2 if (vendor or layer) else n_results
        
        # Query vector store with metadata
        results = self.vector_store.query(
            knowledge_base=knowledge_base,
            query_embedding=query_embedding,
            n_results=query_n_results,
            include_metadata=True
        )
        
        # Apply metadata filtering and boosting
        if vendor or layer or boost_layers:
            results = self._filter_and_boost_results(
                results, vendor, layer, boost_layers
            )
            # Limit to n_results after filtering
            results = results[:n_results]
        
        if include_metadata:
            return results
        else:
            # Return just the text for backward compatibility
            return [r['text'] for r in results]
    
    def _filter_and_boost_results(
        self,
        results: List[Dict[str, Any]],
        vendor: Optional[str] = None,
        layer: Optional[str] = None,
        boost_layers: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter and boost results based on metadata
        
        Args:
            results: List of result dicts with 'text', 'metadata', 'distance'
            vendor: Optional vendor filter
            layer: Optional layer filter
            boost_layers: Optional list of layers to boost
            
        Returns:
            Filtered and boosted results
        """
        filtered_results = []
        
        for result in results:
            metadata = result.get('metadata', {})
            
            # Apply vendor filter
            if vendor and metadata.get('vendor', '').lower() != vendor.lower():
                continue
            
            # Apply layer filter
            if layer and metadata.get('layer', '').lower() != layer.lower():
                continue
            
            # Apply layer boosting
            result_layer = metadata.get('layer', '')
            if boost_layers and result_layer in boost_layers:
                # Boost by reducing distance (lower distance = higher relevance)
                if result.get('distance') is not None:
                    result['distance'] = result['distance'] * 0.7  # Boost by 30%
            
            # Boost products_overview files for product questions
            source_path = metadata.get('source_path', '').lower()
            if 'products_overview' in source_path or 'products-overview' in source_path:
                # Strong boost for products overview files
                if result.get('distance') is not None:
                    result['distance'] = result['distance'] * 0.5  # Boost by 50%
            
            filtered_results.append(result)
        
        # Sort by distance (lower is better)
        filtered_results.sort(key=lambda x: x.get('distance', float('inf')))
        
        return filtered_results
    
    def _expand_query(self, query: str) -> List[str]:
        """
        Expand query with synonyms and related terms
        
        Args:
            query: Original query
            
        Returns:
            List of expanded terms
        """
        expansions = []
        query_lower = query.lower()
        
        # Product-related expansions
        product_expansions = {
            'products': ['product categories', 'services', 'offerings', 'solutions', 'features'],
            'payment gateway': ['pg', 'payment processing', 'checkout', 'payment collection'],
            'payouts': ['transfers', 'disbursements', 'payments out', 'money transfer'],
            'verification': ['kyc', 'identity verification', 'compliance', 'onboarding'],
            'connected banking': ['bank integration', 'bank account', 'banking'],
            'reconciliation': ['reconcile', 'matching', 'matching payments', 'payment matching'],
            'invoice': ['invoicing', 'bills', 'billing'],
            'api': ['apis', 'api integration', 'developer api', 'rest api'],
            'integration': ['integrate', 'connect', 'setup', 'configure'],
            'how to': ['how do i', 'how can i', 'steps to', 'guide to'],
            'what is': ['what are', 'explain', 'describe', 'tell me about'],
            'difference': ['compare', 'vs', 'versus', 'different from']
        }
        
        # Check for matches and add expansions
        for key, synonyms in product_expansions.items():
            if key in query_lower:
                expansions.extend(synonyms)
        
        # Platform-specific expansions
        if 'zwitch' in query_lower:
            expansions.extend(['zwitch api', 'zwitch platform', 'zwitch services'])
        if 'open money' in query_lower or 'openmoney' in query_lower:
            expansions.extend(['open money platform', 'open money dashboard', 'open money app'])
        
        return expansions
