"""
ChromaDB storage for embeddings

Extracted from Local-LLM project (backend/local_llm_staging/backend/rag/store.py).
Renamed from VectorStore to ChromaDBStore for clarity.

This module provides persistent vector storage using ChromaDB for RAG applications.
"""

import chromadb
from chromadb.config import Settings
import os
import logging
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ChromaDBStore:
    """
    ChromaDB-based vector store for knowledge bases
    
    Extracted from Local-LLM project. Provides persistent vector storage
    with collection-based organization for different knowledge bases.
    """
    
    def __init__(self, persist_directory: str = None):
        """
        Initialize ChromaDB client
        
        Args:
            persist_directory: Directory to persist ChromaDB data.
                              Defaults to backend/data/chromadb/
        """
        if persist_directory is None:
            # Default to backend/data/chromadb/ relative to this file
            backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            persist_directory = os.path.join(backend_dir, "data", "chromadb")
        
        # Ensure directory exists
        Path(persist_directory).mkdir(parents=True, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
    
    def get_collection(self, knowledge_base: str):
        """
        Get or create a collection for a knowledge base
        
        Args:
            knowledge_base: Name of the knowledge base
            
        Returns:
            ChromaDB collection
        """
        try:
            return self.client.get_or_create_collection(
                name=knowledge_base,
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            logger.error(f"Error getting/creating collection '{knowledge_base}': {e}", exc_info=True)
            raise
    
    def add_documents(
        self,
        knowledge_base: str,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict]] = None
    ):
        """
        Add documents to a knowledge base
        
        Args:
            knowledge_base: Name of the knowledge base
            texts: List of text chunks
            embeddings: List of embedding vectors
            metadatas: Optional metadata for each document
        """
        collection = self.get_collection(knowledge_base)
        
        # Generate IDs
        # Note: Python hash() is not stable across runs, but collision risk is low
        # For production, consider using UUIDs or content-hash (sha256) for stability
        ids = [f"doc_{i}_{hash(text[:50])}" for i, text in enumerate(texts)]
        
        # Prepare metadatas - ChromaDB requires at least one key-value pair
        if metadatas is None:
            metadatas = [{"chunk_index": i} for i in range(len(texts))]
        else:
            # Ensure each metadata dict has at least one key
            metadatas = [md if md else {"chunk_index": i} for i, md in enumerate(metadatas)]
        
        collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
    
    def query(
        self,
        knowledge_base: str,
        query_embedding: List[float],
        n_results: int = 5,
        include_metadata: bool = False
    ):
        """
        Query a knowledge base
        
        Args:
            knowledge_base: Name of the knowledge base
            query_embedding: Query embedding vector
            n_results: Number of results to return
            include_metadata: If True, return dicts with text and metadata. If False, return list of strings.
            
        Returns:
            If include_metadata=False: List of retrieved text chunks
            If include_metadata=True: List of dicts with 'text' and 'metadata' keys
        """
        collection = self.get_collection(knowledge_base)
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=['documents', 'metadatas', 'distances']
        )
        
        # Extract documents from results
        if results['documents'] and len(results['documents']) > 0:
            documents = results['documents'][0]
            metadatas = results.get('metadatas', [[]])[0] if results.get('metadatas') else []
            distances = results.get('distances', [[]])[0] if results.get('distances') else []
            
            if include_metadata:
                # Return list of dicts with text, metadata, and distance
                result_list = []
                for i, doc in enumerate(documents):
                    metadata = metadatas[i] if i < len(metadatas) else {}
                    distance = distances[i] if i < len(distances) else None
                    result_list.append({
                        'text': doc,
                        'metadata': metadata,
                        'distance': distance
                    })
                return result_list
            else:
                # Return list of strings (backward compatible)
                return documents
        return []
    
    def list_collections(self):
        """
        List all collections in the vector store
        
        Returns:
            List of collection names
        """
        try:
            collections = self.client.list_collections()
            return [col.name for col in collections]
        except Exception as e:
            logger.error(f"Error listing collections: {e}", exc_info=True)
            return []
    
    def delete_collection(self, knowledge_base: str):
        """
        Delete a knowledge base collection
        
        Args:
            knowledge_base: Name of the knowledge base
        """
        try:
            self.client.delete_collection(name=knowledge_base)
        except Exception as e:
            logger.error(f"Error deleting collection {knowledge_base}: {e}", exc_info=True)
    
    def delete_all_collections(self):
        """
        Delete all collections in the vector store
        
        Returns:
            Number of collections deleted
        """
        collections = self.list_collections()
        deleted = 0
        for collection_name in collections:
            try:
                self.delete_collection(collection_name)
                deleted += 1
            except Exception as e:
                logger.error(f"Error deleting collection {collection_name}: {e}", exc_info=True)
        return deleted
