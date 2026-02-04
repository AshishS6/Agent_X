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
import hashlib
from datetime import datetime
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
        else:
            # Root-level vendor docs (e.g., zwitch/products_overview.md)
            metadata["layer"] = "overview"

    # Normalize special folders
    if metadata.get("layer") == "_meta":
        metadata["layer"] = "meta"

    # Heuristic doc_type/confidence guardrails (can be refined/overridden later).
    filename_lower = metadata.get("filename", "").lower()
    layer_lower = metadata.get("layer", "").lower()
    if filename_lower in {"company_overview.md", "products_overview.md", "faq.md"}:
        metadata["doc_type"] = "source_of_truth"
        metadata["confidence"] = "high"
    elif layer_lower in {"states", "principles", "api"}:
        metadata["doc_type"] = "source_of_truth"
        metadata["confidence"] = "high"
    elif layer_lower == "meta":
        metadata["doc_type"] = "derived"
        metadata["confidence"] = "low"
    else:
        metadata["doc_type"] = "derived"
        metadata["confidence"] = "medium"
    
    return metadata


async def ingest_directory(
    knowledge_base: str,
    directory_path: str,
    chunk_size: int = 1500,
    chunk_overlap: int = 300,
    batch_size: int = 10,
    incremental: bool = True,
    delete_missing: bool = False,
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

        collection = vector_store.get_collection(knowledge_base)
        current_source_paths = set()
        
        # Process each file
        for file_path in md_files:
            try:
                logger.info(f"Processing: {file_path}")
                
                # Process file into chunks
                chunk_items = process_file(str(file_path), chunk_size, chunk_overlap)
                if not chunk_items:
                    logger.warning(f"No content extracted from {file_path}")
                    continue

                # Support both legacy and structured chunking outputs
                if isinstance(chunk_items[0], dict):
                    texts = [c.get("text", "") for c in chunk_items]
                else:
                    texts = chunk_items  # type: ignore[assignment]
                    chunk_items = [{"text": t, "section_path": "introduction"} for t in texts]
                
                # Extract metadata from path
                metadata_list = []
                file_metadata = extract_metadata_from_path(str(file_path), str(directory))

                # Provenance metadata
                source_path = file_metadata.get("source_path", "")
                current_source_paths.add(source_path)
                stat = file_path.stat()
                file_bytes = file_path.read_bytes()
                file_hash = hashlib.sha256(file_bytes).hexdigest()
                file_metadata.update(
                    {
                        "file_hash": file_hash,
                        "file_mtime": str(int(stat.st_mtime)),
                        "file_size": str(int(stat.st_size)),
                        "ingested_at": datetime.utcnow().isoformat() + "Z",
                    }
                )

                # Incremental mode: if this source_path already exists and hash matches, skip.
                if incremental and source_path:
                    existing = collection.get(
                        where={"source_path": source_path},
                        include=["metadatas"],
                    )
                    if existing and existing.get("ids"):
                        existing_mds = existing.get("metadatas") or []
                        existing_hash = None
                        if existing_mds and isinstance(existing_mds, list):
                            # Chroma returns list[dict] for metadatas
                            existing_hash = (existing_mds[0] or {}).get("file_hash")
                        if existing_hash and existing_hash == file_hash:
                            logger.info(f"✓ Skipping unchanged file (hash match): {source_path}")
                            continue
                        # File changed: delete old chunks for this file
                        try:
                            collection.delete(where={"source_path": source_path})
                            logger.info(f"Deleted old chunks for changed file: {source_path}")
                        except Exception as e:
                            logger.warning(f"Failed deleting old chunks for {source_path}: {e}")
                
                for i in range(len(texts)):
                    chunk_metadata = file_metadata.copy()
                    chunk_metadata["chunk_index"] = i
                    chunk_metadata["total_chunks"] = len(texts)
                    chunk_metadata["section_path"] = (chunk_items[i] or {}).get("section_path", "introduction")
                    metadata_list.append(chunk_metadata)
                
                # Generate embeddings in batches
                logger.info(f"Generating embeddings for {len(texts)} chunks...")
                embeddings = await embedding_client.embed_batch(texts, batch_size=batch_size)
                
                # Store in vector database
                vector_store.add_documents(
                    knowledge_base=knowledge_base,
                    texts=texts,
                    embeddings=embeddings,
                    metadatas=metadata_list
                )
                
                total_chunks += len(texts)
                total_files += 1
                logger.info(f"✓ Ingested {len(texts)} chunks from {file_path.name}")
                
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}", exc_info=True)
                continue

        # Optionally delete chunks for missing files.
        if delete_missing:
            try:
                all_docs = collection.get(include=["metadatas"])
                metadatas = all_docs.get("metadatas") or []
                missing_source_paths = set()
                for md in metadatas:
                    sp = (md or {}).get("source_path")
                    if sp and sp not in current_source_paths:
                        missing_source_paths.add(sp)
                for sp in sorted(missing_source_paths):
                    try:
                        collection.delete(where={"source_path": sp})
                        logger.info(f"Deleted chunks for missing file: {sp}")
                    except Exception as e:
                        logger.warning(f"Failed deleting chunks for missing file {sp}: {e}")
            except Exception as e:
                logger.warning(f"Failed delete-missing pass: {e}")
        
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
        default=1500,
        help="Size of each chunk in characters (default: 1500)"
    )
    
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=300,
        help="Overlap between chunks in characters (default: 300)"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of chunks to process embeddings in parallel (default: 10)"
    )

    parser.add_argument(
        "--no-incremental",
        action="store_true",
        help="Disable incremental ingestion (always re-embed and upsert all files)"
    )

    parser.add_argument(
        "--delete-missing",
        action="store_true",
        help="Delete chunks for files that no longer exist on disk (best-effort)"
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
            batch_size=args.batch_size,
            incremental=(not args.no_incremental),
            delete_missing=bool(args.delete_missing),
        ))
        sys.exit(0)
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
