"""
Document ingestion and chunking

Extracted from Local-LLM project (backend/local_llm_staging/backend/rag/ingest.py).

This module provides text chunking utilities for RAG document processing.
"""

from typing import List


def load_document(file_path: str) -> str:
    """
    Load document content from file
    
    Args:
        file_path: Path to document file
        
    Returns:
        Document content as string
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks
    
    Extracted from Local-LLM project. Splits text into chunks with overlap
    to preserve context across boundaries.
    
    Args:
        text: Text to chunk
        chunk_size: Size of each chunk in characters
        chunk_overlap: Overlap between chunks in characters
        
    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence endings within last 100 chars
            for i in range(max(start, end - 100), end):
                if text[i] in '.!?\n':
                    end = i + 1
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move start forward with overlap
        start = end - chunk_overlap
        if start >= len(text):
            break
    
    return chunks


def process_file(file_path: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """
    Process a file and return chunks
    
    Extracted from Local-LLM project. Loads a file and chunks its content.
    
    Args:
        file_path: Path to file
        chunk_size: Size of each chunk
        chunk_overlap: Overlap between chunks
        
    Returns:
        List of text chunks
    """
    content = load_document(file_path)
    return chunk_text(content, chunk_size, chunk_overlap)
