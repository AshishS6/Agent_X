# Knowledge Base Ingestion Guide

## Quick Start

Ingest markdown files into a ChromaDB knowledge base for RAG:

```bash
python backend/knowledge/ingest.py \
  --kb fintech \
  --path knowledge_base/
```

## Prerequisites

1. **Ollama running with embedding model:**
   ```bash
   ollama serve
   ollama pull nomic-embed-text  # If not already installed
   ```

2. **Knowledge base directory structure:**
   ```
   knowledge_base/
   ├── zwitch/
   │   ├── api/
   │   ├── concepts/
   │   └── states/
   └── openmoney/
       ├── modules/
       └── concepts/
   ```

## Usage Examples

### Basic Ingestion

```bash
# From project root
python backend/knowledge/ingest.py \
  --kb fintech \
  --path knowledge_base/
```

### Custom Chunking

```bash
# Larger chunks, more overlap
python backend/knowledge/ingest.py \
  --kb fintech \
  --path knowledge_base/ \
  --chunk-size 1500 \
  --chunk-overlap 300
```

### Faster Processing

```bash
# Larger batch size for parallel embedding
python backend/knowledge/ingest.py \
  --kb fintech \
  --path knowledge_base/ \
  --batch-size 20
```

## What It Does

1. **Finds all `.md` files** recursively in the directory
2. **Chunks each file** (default: 1000 chars with 200 char overlap)
3. **Generates embeddings** using Ollama's `nomic-embed-text` model
4. **Extracts metadata** from file paths:
   - `vendor`: First directory level (e.g., "zwitch", "openmoney")
   - `layer`: Second directory level (e.g., "api", "concepts", "states")
   - `source_path`: Relative path from knowledge base root
5. **Stores in ChromaDB** as collection named after `--kb` argument

## Verification

After ingestion, test with the assistant endpoint:

```bash
curl -X POST http://localhost:3001/api/assistants/fintech/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How do I integrate Zwitch payment gateway?",
    "knowledge_base": "fintech",
    "assistant": "fintech"
  }'
```

You should see:
- Non-empty `"answer"` with context-specific information
- `"rag_used": true` in metadata
- Citations with public URLs (if available)

## Troubleshooting

### Error: "No markdown files found"

- Check the `--path` is correct (use absolute path if needed)
- Verify `.md` files exist in subdirectories

### Error: "Failed to connect to Ollama"

- Ensure Ollama is running: `ollama serve`
- Check `OLLAMA_BASE_URL` environment variable
- Verify embedding model exists: `ollama list | grep nomic-embed`

### Slow Ingestion

- Increase `--batch-size` for parallel embedding (default: 10)
- Reduce `--chunk-size` if files are very large
- Process smaller directories at a time

### ChromaDB Errors

- Check disk space in `backend/data/chromadb/`
- Verify write permissions
- Clear and re-ingest if collection is corrupted

## Metadata Structure

The ingestion tool automatically creates metadata from file paths:

| File Path | vendor | layer | source_path |
|-----------|--------|-------|-------------|
| `zwitch/api/07_transfers.md` | zwitch | api | zwitch/api/07_transfers.md |
| `openmoney/modules/receivables.md` | openmoney | modules | openmoney/modules/receivables.md |
| `zwitch/products_overview.md` | zwitch | (none) | zwitch/products_overview.md |

This metadata enables:
- Vendor filtering (e.g., only Zwitch docs)
- Layer filtering (e.g., only API docs)
- Source citations in responses

## Next Steps

After successful ingestion:

1. **Test RAG retrieval:**
   ```bash
   curl -X POST http://localhost:3001/api/assistants/fintech/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "What are Zwitch products?", "knowledge_base": "fintech", "assistant": "fintech"}'
   ```

2. **Verify context is used:**
   - Check `"rag_used": true` in response metadata
   - Answer should reference specific documentation

3. **Check citations:**
   - Response should include public URLs in `"citations"` array
   - No internal file paths should appear
