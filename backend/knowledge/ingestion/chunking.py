"""
Document ingestion and chunking

Extracted from Local-LLM project (backend/local_llm_staging/backend/rag/ingest.py).

This module provides text chunking utilities for RAG document processing.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple


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


def chunk_text(text: str, chunk_size: int = 1500, chunk_overlap: int = 300) -> List[str]:
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
            # Look for sentence endings within last 200 chars
            for i in range(max(start, end - 200), end):
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


def _parse_markdown_sections(text: str) -> List[Dict[str, Any]]:
    """
    Parse markdown into heading-aware sections.

    Returns list of:
      { "heading_stack": [(level:int, title:str), ...], "content": str }
    """
    lines = (text or "").splitlines()
    sections: List[Dict[str, Any]] = []

    heading_stack: List[Tuple[int, str]] = []
    current_lines: List[str] = []

    def flush():
        if not current_lines and not heading_stack:
            return
        sections.append(
            {
                "heading_stack": list(heading_stack),
                "content": "\n".join(current_lines).strip(),
            }
        )

    for line in lines:
        m = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if m:
            flush()
            current_lines = []
            level = len(m.group(1))
            title = m.group(2).strip()
            # Pop to parent level
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()
            heading_stack.append((level, title))
        else:
            current_lines.append(line)

    flush()

    # If a file has no headings, treat as one section
    if not sections:
        return [{"heading_stack": [], "content": (text or "").strip()}]
    return sections


def _heading_prefix(heading_stack: List[Tuple[int, str]]) -> str:
    if not heading_stack:
        return ""
    # Recreate markdown headings for context.
    return "\n".join([("#" * lvl) + " " + title for (lvl, title) in heading_stack]).strip()


def _section_path(heading_stack: List[Tuple[int, str]]) -> str:
    if not heading_stack:
        return "introduction"
    return ">".join([t.strip() for (_lvl, t) in heading_stack if t and t.strip()]) or "introduction"


def process_file(file_path: str, chunk_size: int = 1500, chunk_overlap: int = 300) -> List[Dict[str, Any]]:
    """
    Process a file and return heading-aware chunks.
    
    Extracted from Local-LLM project. Loads a file and chunks its content.
    
    Args:
        file_path: Path to file
        chunk_size: Size of each chunk
        chunk_overlap: Overlap between chunks
        
    Returns:
        List of dicts: { "text": str, "section_path": str }
    """
    content = load_document(file_path)
    sections = _parse_markdown_sections(content)

    chunk_items: List[Dict[str, Any]] = []
    for sec in sections:
        hs = sec.get("heading_stack") or []
        body = (sec.get("content") or "").strip()
        if not body and not hs:
            continue
        prefix = _heading_prefix(hs)
        section_path = _section_path(hs)

        section_text = (prefix + "\n\n" + body).strip() if prefix else body
        for c in chunk_text(section_text, chunk_size, chunk_overlap):
            chunk_items.append({"text": c, "section_path": section_path})

    return chunk_items
