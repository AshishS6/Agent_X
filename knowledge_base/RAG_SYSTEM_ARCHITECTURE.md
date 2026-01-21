# RAG System Architecture Documentation

## Overview

This document explains how the RAG (Retrieval-Augmented Generation) system works in this project, including the architecture, data flow, and implementation details.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React/TypeScript)               │
│  - User asks question via chat interface                    │
│  - Selects "fintech" assistant                               │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP POST /api/chat
                       │ { assistant_id: "fintech", messages: [...] }
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Backend API (FastAPI - main.py)                 │
│  1. Receives chat request                                    │
│  2. Identifies assistant config (FintechAssistant)           │
│  3. Checks if RAG is enabled (use_rag=True)                  │
│  4. Extracts last user message                               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ If RAG enabled
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              RAG Pipeline (rag/pipeline.py)                  │
│  1. Takes user query                                         │
│  2. Calls Retriever to find relevant context                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│            Retriever (rag/retrieve.py)                       │
│  1. Generates query embedding using EmbeddingClient         │
│  2. Queries VectorStore for similar chunks                   │
│  3. Returns top N (default: 5) relevant chunks               │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
┌──────────────────┐        ┌──────────────────┐
│ EmbeddingClient   │        │  VectorStore      │
│ (rag/embed.py)    │        │  (rag/store.py)   │
│                   │        │                   │
│ - Uses Ollama     │        │ - Uses ChromaDB   │
│ - Model:          │        │ - Collection:     │
│   nomic-embed-text│        │   "fintech"       │
│ - Generates       │        │ - Stores:         │
│   embeddings      │        │   embeddings +    │
│                   │        │   text chunks +   │
│                   │        │   metadata        │
└──────────────────┘        └──────────────────┘
        │                             │
        │                             │
        └──────────────┬──────────────┘
                       │
                       │ Returns context chunks
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              RAG Pipeline (continued)                         │
│  3. Formats context + user query into enhanced prompt       │
│  4. Returns: "Context: ... Question: {user_query}"           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Enhanced prompt
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Backend API (main.py - continued)                │
│  5. Adds system prompt from assistant config                 │
│  6. Sends enhanced message to OllamaClient                   │
│  7. Streams response back to frontend                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Streaming response
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (continued)                      │
│  - Displays streaming response to user                       │
└─────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. Assistant Configuration (`backend/assistants/`)

**Purpose:** Defines different AI assistants with specific configurations.

**Files:**
- `base.py` - Base `AssistantConfig` class
- `fintech.py` - Fintech assistant configuration
- `general.py` - General assistant
- `code.py` - Code assistant

**Fintech Assistant Config:**
```python
AssistantConfig(
    name="fintech",
    model="qwen2.5:7b",
    use_rag=True,                    # RAG enabled
    knowledge_base="fintech",        # ChromaDB collection name
    system_prompt="You are a financial technology expert..."
)
```

### 2. RAG Pipeline (`backend/rag/pipeline.py`)

**Purpose:** Orchestrates the RAG process end-to-end.

**Key Method:**
```python
async def query(
    user_query: str,
    knowledge_base: str,
    n_results: int = 5
) -> str
```

**Process:**
1. Calls `Retriever.retrieve()` to get relevant chunks
2. Combines chunks into context string
3. Formats final prompt: `"Context: {chunks}\n\nQuestion: {query}"`
4. Returns enhanced prompt

### 3. Retriever (`backend/rag/retrieve.py`)

**Purpose:** Finds relevant documents for a query.

**Key Method:**
```python
async def retrieve(
    query: str,
    knowledge_base: str,
    n_results: int = 5
) -> List[str]
```

**Process:**
1. Generates embedding for user query using `EmbeddingClient`
2. Queries `VectorStore` with query embedding
3. Returns top N most similar text chunks

### 4. Embedding Client (`backend/rag/embed.py`)

**Purpose:** Generates vector embeddings for text.

**Technology:**
- Uses Ollama API
- Model: `nomic-embed-text`
- Endpoint: `POST /api/embeddings`

**Key Methods:**
- `embed(text: str)` - Single text embedding
- `embed_batch(texts: List[str])` - Batch embeddings (parallel)

**Embedding Process:**
1. Sends text to Ollama embedding API
2. Receives vector representation (list of floats)
3. Returns embedding vector

### 5. Vector Store (`backend/rag/store.py`)

**Purpose:** Stores and retrieves document embeddings.

**Technology:**
- Uses ChromaDB (persistent SQLite database)
- Location: `backend/data/chromadb/`
- Collection name: `"fintech"` (matches assistant config)

**Key Methods:**
- `get_collection(knowledge_base: str)` - Get or create collection
- `add_documents(...)` - Add documents with embeddings
- `query(...)` - Search for similar documents

**Storage Structure:**
```
backend/data/chromadb/
├── chroma.sqlite3              # ChromaDB database
└── [collection_id]/            # Collection data
    ├── *.bin                   # Embedding vectors
    └── metadata
```

**Metadata Stored:**
- `vendor`: "zwitch" or "openmoney"
- `layer`: "states", "flows", "api", "concepts", etc.
- `source_path`: Relative path to source file
- `is_meta`: Whether file is in `_meta/` folder
- `chunk_index`: Chunk number within file
- `total_chunks`: Total chunks in file

### 6. Document Ingestion (`backend/rag/ingest.py`)

**Purpose:** Processes files into chunks for storage.

**Chunking Strategy:**
- Chunk size: 1000 characters (default)
- Overlap: 200 characters (default)
- Tries to break at sentence boundaries

**Process:**
1. Loads file content
2. Splits into overlapping chunks
3. Returns list of text chunks

**Re-ingestion Script:**
- `backend/rag/reingest_knowledge_base.py`
- Processes all `.md` files in `knowledge_base/`
- Adds metadata (vendor, layer, source_path)
- Stores in ChromaDB collection `"fintech"`

## Data Flow

### Query Flow (User Question → Answer)

1. **User asks question** → Frontend sends to `/api/chat`
2. **Backend identifies assistant** → Gets `FintechAssistant` config
3. **RAG enabled?** → Yes, `use_rag=True`
4. **Generate query embedding** → `EmbeddingClient.embed(user_query)`
5. **Search vector store** → `VectorStore.query(query_embedding, n_results=5)`
6. **Retrieve top chunks** → Returns 5 most similar text chunks
7. **Format prompt** → `"Context: {chunks}\n\nQuestion: {query}"`
8. **Send to LLM** → Ollama with system prompt + enhanced message
9. **Stream response** → Back to frontend

### Ingestion Flow (File → Vector Store)

1. **File in `knowledge_base/`** → Markdown file
2. **Re-ingestion script** → `python -m rag.reingest_knowledge_base`
3. **Find all `.md` files** → Recursively searches `knowledge_base/`
4. **Process each file** → `process_file()` splits into chunks
5. **Generate metadata** → Vendor, layer, source_path, etc.
6. **Generate embeddings** → `EmbeddingClient.embed_batch(chunks)`
7. **Store in ChromaDB** → `VectorStore.add_documents(...)`
8. **Ready for queries** → Chunks are searchable

## Knowledge Base vs Vector Store

### Important Distinction

**`knowledge_base/` folder:**
- Just organizational structure
- Source files (markdown)
- NOT used directly by RAG
- For version control and documentation

**`knowledge_base` parameter (ChromaDB collection):**
- Actual RAG storage
- Vector embeddings + text chunks
- Used by RAG for retrieval
- Stored in `backend/data/chromadb/`

**Current Setup:**
- Folder: `knowledge_base/` (organizational)
- Collection: `"fintech"` (ChromaDB)
- Assistant config: `knowledge_base="fintech"` (matches collection)

## Configuration

### Assistant Registration (`backend/main.py`)

```python
ASSISTANTS["fintech"] = FintechAssistant.get_config()
```

### RAG Initialization (`backend/main.py`)

```python
embedding_client = EmbeddingClient()
vector_store = VectorStore()
rag_pipeline = RAGPipeline(embedding_client, vector_store)
```

### RAG Usage in Chat Endpoint

```python
if assistant_config.use_rag and assistant_config.knowledge_base:
    enhanced_content = await rag_pipeline.query(
        user_query=last_user_message,
        knowledge_base=assistant_config.knowledge_base,
        n_results=5
    )
```

## Current Status

### What's Working
- ✅ RAG pipeline is functional
- ✅ ChromaDB storage is working
- ✅ Embeddings are generated via Ollama
- ✅ Document ingestion script exists
- ✅ Metadata is attached to chunks
- ✅ Fintech assistant uses RAG

### Current Limitations
- ⚠️ Only 5 chunks retrieved per query (may miss relevant info)
- ⚠️ Simple chunking strategy (no semantic chunking)
- ⚠️ No re-ranking of results
- ⚠️ No query expansion or reformulation
- ⚠️ No hybrid search (keyword + semantic)
- ⚠️ Chunk size fixed at 1000 chars (may split important context)

## Performance Considerations

### Embedding Generation
- Uses Ollama API (local or remote)
- Batch processing for multiple chunks
- Default batch size: 10 chunks in parallel

### Vector Search
- ChromaDB uses cosine similarity
- HNSW index for fast approximate search
- Query time: ~10-50ms for 5 results

### Overall Latency
- Query embedding: ~100-500ms
- Vector search: ~10-50ms
- LLM generation: Variable (depends on model)
- Total RAG overhead: ~200-600ms

## Future Improvements

See `IMPROVEMENT_PLAN.md` for detailed improvement recommendations.
