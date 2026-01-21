# Knowledge Module - RAG System

This module provides RAG (Retrieval-Augmented Generation) capabilities for AgentX, including vector storage, document ingestion, and retrieval.

## Components

- **Vector Store** (`vector_store/`): ChromaDB integration for persistent vector storage
- **Ingestion** (`ingestion/`): Document chunking and processing utilities
- **Retrieval** (`retrieval/`): RAG pipeline with filtering, boosting, and URL mapping

## Usage

### Ingesting Documents into Knowledge Base

Use the ingestion CLI to populate a knowledge base:

```bash
python backend/knowledge/ingest.py \
  --kb fintech \
  --path knowledge_base/
```

**Arguments:**
- `--kb` / `--knowledge-base`: Name of the knowledge base (ChromaDB collection)
- `--path`: Path to directory containing markdown files
- `--chunk-size`: Size of each chunk in characters (default: 1000)
- `--chunk-overlap`: Overlap between chunks (default: 200)
- `--batch-size`: Number of chunks to embed in parallel (default: 10)

**Example:**
```bash
# Ingest fintech knowledge base
python backend/knowledge/ingest.py --kb fintech --path knowledge_base/

# Custom chunking parameters
python backend/knowledge/ingest.py \
  --kb fintech \
  --path knowledge_base/ \
  --chunk-size 1500 \
  --chunk-overlap 300
```

### Knowledge Base Structure

The ingestion tool automatically extracts metadata from file paths:

```
knowledge_base/
├── zwitch/
│   ├── api/
│   │   └── 07_transfers.md     → vendor: zwitch, layer: api
│   ├── concepts/
│   │   └── payin_vs_payout.md  → vendor: zwitch, layer: concepts
│   └── states/
│       └── payment_status.md   → vendor: zwitch, layer: states
└── openmoney/
    ├── modules/
    │   └── receivables.md      → vendor: openmoney, layer: modules
    └── concepts/
        └── what_is_open_money.md
```

### Using Knowledge Pipeline in Code

```python
from knowledge.vector_store import ChromaDBStore, OllamaEmbeddingClient
from knowledge.retrieval import KnowledgePipeline

# Initialize
embedding_client = OllamaEmbeddingClient()
vector_store = ChromaDBStore()
pipeline = KnowledgePipeline(embedding_client, vector_store)

# Query
result = await pipeline.query(
    user_query="How do I integrate payment gateway?",
    knowledge_base="fintech",
    n_results=10
)

# Result contains:
# {
#   "context": "...",
#   "public_urls": ["https://developers.zwitch.io/..."],
#   "query": "..."
# }
```

## Storage

ChromaDB data is stored in `backend/data/chromadb/` by default. Each knowledge base is a separate collection.

## Environment Variables

- `OLLAMA_BASE_URL`: Ollama API base URL (default: http://localhost:11434)
- Embedding model defaults to `nomic-embed-text` (must be installed in Ollama)

## Dependencies

- `chromadb`: Vector database
- `httpx`: Async HTTP client for Ollama API
- Python 3.8+
