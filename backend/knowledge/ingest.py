#!/usr/bin/env python3
"""
Knowledge Base Ingestion CLI

Ingests markdown files from a directory into a ChromaDB knowledge base.
Processes files, chunks content, generates embeddings, and stores in vector DB.

Usage:
    python backend/knowledge/ingest.py --kb fintech --path knowledge_base/

Or from project root:
    python backend/knowledge/ingest.py --kb fintech --path ./knowledge_base
"""

import sys
import os
import argparse
import logging
import asyncio
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urlparse

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge.ingestion.chunking import process_file
from knowledge.vector_store import ChromaDBStore, OllamaEmbeddingClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr  # Logs to stderr, not stdout
)
logger = logging.getLogger("Knowledge.Ingest")


def extract_metadata_from_path(file_path: str, kb_root: str) -> Dict[str, str]:
    """
    Extract metadata from file path structure
    
    Examples:
        knowledge_base/zwitch/api/07_transfers.md
        -> vendor: zwitch, layer: api, source_path: zwitch/api/07_transfers.md
        
        knowledge_base/openmoney/modules/receivables.md
        -> vendor: openmoney, layer: modules, source_path: openmoney/modules/receivables.md
    
    Args:
        file_path: Full path to file
        kb_root: Root directory of knowledge base
    
    Returns:
        Metadata dictionary
    """
    # Get relative path from knowledge base root
    rel_path = os.path.relpath(file_path, kb_root)
    rel_path_clean = rel_path.replace('\\', '/')  # Normalize path separators
    
    # Split path components
    parts = rel_path_clean.split('/')
    
    metadata = {
        "source_path": rel_path_clean,
        "filename": os.path.basename(file_path)
    }
    
    # Detect vendor (first directory level)
    if len(parts) > 1:
        vendor = parts[0]
        metadata["vendor"] = vendor.lower()
        
        # Detect layer (second directory level)
        if len(parts) > 2:
            layer = parts[1]
            metadata["layer"] = layer.lower()
    
    return metadata


async def ingest_directory(
    knowledge_base: str,
    directory_path: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    batch_size: int = 10
):
    """
    Ingest all markdown files from a directory into a knowledge base
    
    Args:
        knowledge_base: Name of the knowledge base (ChromaDB collection name)
        directory_path: Path to directory containing markdown files
        chunk_size: Size of each chunk in characters
        chunk_overlap: Overlap between chunks
        batch_size: Number of chunks to process embeddings in parallel
    """
    directory = Path(directory_path)
    if not directory.exists():
        raise ValueError(f"Directory does not exist: {directory_path}")
    
    if not directory.is_dir():
        raise ValueError(f"Path is not a directory: {directory_path}")
    
    # Find all markdown files
    md_files = list(directory.rglob("*.md"))
    if not md_files:
        logger.warning(f"No markdown files found in {directory_path}")
        return
    
    logger.info(f"Found {len(md_files)} markdown files to ingest")
    
    # Initialize components
    embedding_client = OllamaEmbeddingClient()
    vector_store = ChromaDBStore()
    
    try:
        total_chunks = 0
        total_files = 0
        
        # Process each file
        for file_path in md_files:
            try:
                logger.info(f"Processing: {file_path}")
                
                # Process file into chunks
                chunks = process_file(str(file_path), chunk_size, chunk_overlap)
                if not chunks:
                    logger.warning(f"No content extracted from {file_path}")
                    continue
                
                # Extract metadata from path
                metadata_list = []
                file_metadata = extract_metadata_from_path(str(file_path), str(directory))
                
                for i in range(len(chunks)):
                    chunk_metadata = file_metadata.copy()
                    chunk_metadata["chunk_index"] = i
                    metadata_list.append(chunk_metadata)
                
                # Generate embeddings in batches
                logger.info(f"Generating embeddings for {len(chunks)} chunks...")
                embeddings = await embedding_client.embed_batch(chunks, batch_size=batch_size)
                
                # Store in vector database
                vector_store.add_documents(
                    knowledge_base=knowledge_base,
                    texts=chunks,
                    embeddings=embeddings,
                    metadatas=metadata_list
                )
                
                total_chunks += len(chunks)
                total_files += 1
                logger.info(f"✓ Ingested {len(chunks)} chunks from {file_path.name}")
                
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}", exc_info=True)
                continue
        
        logger.info(f"✅ Ingestion complete: {total_files} files, {total_chunks} chunks stored in '{knowledge_base}'")
        
    finally:
        await embedding_client.close()


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Ingest markdown files into a knowledge base",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ingest fintech knowledge base
  python backend/knowledge/ingest.py --kb fintech --path knowledge_base/
  
  # Custom chunk size
  python backend/knowledge/ingest.py --kb fintech --path knowledge_base/ --chunk-size 1500
  
  # Ingest from absolute path
  python backend/knowledge/ingest.py --kb fintech --path /path/to/knowledge_base
        """
    )
    
    parser.add_argument(
        "--kb",
        "--knowledge-base",
        dest="knowledge_base",
        required=True,
        help="Knowledge base name (ChromaDB collection name)"
    )
    
    parser.add_argument(
        "--path",
        required=True,
        help="Path to directory containing markdown files"
    )
    
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        help="Size of each chunk in characters (default: 1000)"
    )
    
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=200,
        help="Overlap between chunks in characters (default: 200)"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of chunks to process embeddings in parallel (default: 10)"
    )
    
    args = parser.parse_args()
    
    # Convert path to absolute
    path = os.path.abspath(args.path)
    
    # Run ingestion
    try:
        asyncio.run(ingest_directory(
            knowledge_base=args.knowledge_base,
            directory_path=path,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            batch_size=args.batch_size
        ))
        sys.exit(0)
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
