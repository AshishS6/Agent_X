"""
Document Ingestion Module

Provides document chunking and file processing for knowledge base ingestion.
Extracted from Local-LLM project.
"""

from .chunking import chunk_text, process_file

__all__ = ["chunk_text", "process_file"]
