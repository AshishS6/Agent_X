# Local-LLM to AgentX Migration Plan

**Date:** 2025-01-XX  
**Status:** Analysis Complete, Migration In Progress

---

## PART 1: LOCAL-LLM CAPABILITY ANALYSIS

### Component Classification

#### 1. RAG / Knowledge Components
**Location:** `backend/local_llm_staging/backend/rag/`

| File | Purpose | Classification |
|------|---------|----------------|
| `store.py` | ChromaDB vector store wrapper | **RAG / Knowledge** → `backend/knowledge/vector_store/` |
| `embed.py` | Ollama embedding client | **RAG / Knowledge** → `backend/knowledge/vector_store/` |
| `ingest.py` | Document chunking and processing | **RAG / Knowledge** → `backend/knowledge/ingestion/` |
| `retrieve.py` | Retrieval logic with filtering/boosting | **RAG / Knowledge** → `backend/knowledge/retrieval/` |
| `pipeline.py` | End-to-end RAG pipeline | **RAG / Knowledge** → `backend/knowledge/retrieval/` |
| `prompts.py` | RAG prompt templates | **RAG / Knowledge** → `backend/knowledge/retrieval/` |
| `url_mapping.py` | Public URL citation mapping | **RAG / Knowledge** → `backend/knowledge/retrieval/` |
| `__init__.py` | Module exports | **RAG / Knowledge** → `backend/knowledge/` |

**Knowledge Base Data:**
- `knowledge_base/` directory (57 markdown files)
- **Action:** Keep as-is, reference from new knowledge module

#### 2. Assistant Logic
**Location:** `backend/local_llm_staging/backend/assistants/`

| File | Purpose | Classification |
|------|---------|----------------|
| `base.py` | AssistantConfig Pydantic model | **Assistant Logic** → `backend/assistants/base_assistant.py` |
| `fintech.py` | Fintech assistant config | **Assistant Logic** → `backend/assistants/fintech_assistant.py` |
| `code.py` | Code assistant config | **Assistant Logic** → `backend/assistants/code_assistant.py` |
| `general.py` | General assistant config | **Assistant Logic** → `backend/assistants/general_assistant.py` (optional) |

**Note:** These are configuration classes, not execution classes. They define system prompts and RAG settings.

#### 3. LLM Provider / Infrastructure
**Location:** `backend/local_llm_staging/backend/`

| File | Purpose | Classification |
|------|---------|----------------|
| `ollama_client.py` | Ollama HTTP client for chat/embeddings | **LLM Provider** → `backend/llm/providers/ollama_client.py` |
| `models.py` | Pydantic models for API | **UI/Server Glue** → **DISCARD** (FastAPI-specific) |
| `response_filter.py` | Response filtering for reasoning models | **LLM Provider** → `backend/llm/prompts/response_filter.py` |

#### 4. UI / Server Glue (TO BE DISCARDED)
**Location:** `backend/local_llm_staging/backend/`

| File | Purpose | Classification |
|------|---------|----------------|
| `main.py` | FastAPI server with chat endpoints | **UI/Server Glue** → **DISCARD** |
| `models.py` | FastAPI Pydantic models | **UI/Server Glue** → **DISCARD** |

**Frontend:**
- `src/` directory (React/TypeScript UI)
- **Action:** **DISCARD** (AgentX has its own frontend)

#### 5. Test / Experimental
**Location:** `backend/local_llm_staging/backend/`

| File | Purpose | Classification |
|------|---------|----------------|
| `test_rag.py` | RAG testing script | **Test** → **DISCARD** (can recreate if needed) |
| `test_rag.sh` | Test script | **Test** → **DISCARD** |
| `reingest_knowledge_base.py` | Reingestion script | **Test/Utility** → **DISCARD** (can recreate) |
| `view_fintech_data.py` | Debug script | **Test** → **DISCARD** |
| `analyze_kb.py` | Analysis script | **Test** → **DISCARD** |

---

## PART 2: TARGET ARCHITECTURE

### Directory Structure

```
backend/
├── knowledge/                    # NEW: RAG capabilities
│   ├── __init__.py
│   ├── vector_store/
│   │   ├── __init__.py
│   │   ├── chromadb_store.py     # Extracted from rag/store.py
│   │   └── embedding_client.py   # Extracted from rag/embed.py
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── chunking.py           # Extracted from rag/ingest.py
│   │   └── file_processor.py     # Extracted from rag/ingest.py
│   └── retrieval/
│       ├── __init__.py
│       ├── retriever.py          # Extracted from rag/retrieve.py
│       ├── pipeline.py           # Extracted from rag/pipeline.py
│       ├── prompts.py            # Extracted from rag/prompts.py
│       └── url_mapping.py         # Extracted from rag/url_mapping.py
│
├── assistants/                    # NEW: Conversational assistants
│   ├── __init__.py
│   ├── base_assistant.py         # Extracted from assistants/base.py
│   ├── fintech_assistant.py      # Extracted from assistants/fintech.py
│   ├── code_assistant.py         # Extracted from assistants/code.py
│   └── general_assistant.py     # Extracted from assistants/general.py (optional)
│
├── llm/                           # NEW: LLM provider abstractions
│   ├── __init__.py
│   ├── providers/
│   │   ├── __init__.py
│   │   └── ollama_client.py      # Extracted from ollama_client.py
│   └── prompts/
│       ├── __init__.py
│       └── response_filter.py    # Extracted from response_filter.py
│
└── agents/                        # EXISTING: Task-based agents (unchanged)
    └── ... (no changes)
```

---

## PART 3: FILE MAPPING & MIGRATION STRATEGY

### Knowledge Module (`backend/knowledge/`)

| Source File | Target File | Changes Required |
|-------------|-------------|------------------|
| `rag/store.py` | `knowledge/vector_store/chromadb_store.py` | Rename class `VectorStore` → `ChromaDBStore`, remove FastAPI dependencies |
| `rag/embed.py` | `knowledge/vector_store/embedding_client.py` | Rename class `EmbeddingClient` → `OllamaEmbeddingClient`, keep async interface |
| `rag/ingest.py` | `knowledge/ingestion/chunking.py` | Extract `chunk_text()` and `process_file()` functions, remove file I/O assumptions |
| `rag/retrieve.py` | `knowledge/retrieval/retriever.py` | Rename class `Retriever` → `RAGRetriever`, keep filtering/boosting logic |
| `rag/pipeline.py` | `knowledge/retrieval/pipeline.py` | Rename class `RAGPipeline` → `KnowledgePipeline`, remove FastAPI dependencies |
| `rag/prompts.py` | `knowledge/retrieval/prompts.py` | Keep as-is, simple utility functions |
| `rag/url_mapping.py` | `knowledge/retrieval/url_mapping.py` | Keep as-is, pure utility class |

### Assistants Module (`backend/assistants/`)

| Source File | Target File | Changes Required |
|-------------|-------------|------------------|
| `assistants/base.py` | `assistants/base_assistant.py` | Keep `AssistantConfig` model, add docstring about extraction |
| `assistants/fintech.py` | `assistants/fintech_assistant.py` | Keep `FintechAssistant` class, add docstring |
| `assistants/code.py` | `assistants/code_assistant.py` | Keep `CodeAssistant` class, add docstring |
| `assistants/general.py` | `assistants/general_assistant.py` | Keep `GeneralAssistant` class, add docstring |

**Note:** Assistants are configuration-only. They don't execute tasks. They define:
- System prompts
- Model preferences
- RAG knowledge base mappings
- RAG enablement flags

### LLM Module (`backend/llm/`)

| Source File | Target File | Changes Required |
|-------------|-------------|------------------|
| `ollama_client.py` | `llm/providers/ollama_client.py` | Keep as-is, pure HTTP client |
| `response_filter.py` | `llm/prompts/response_filter.py` | Keep as-is, pure utility functions |

---

## PART 4: FUNCTIONALITY TO BE LOST (INTENTIONAL)

### Discarded Components

1. **FastAPI Server (`main.py`)**
   - Chat streaming endpoints
   - Document ingestion endpoints
   - Health check endpoints
   - **Reason:** AgentX uses Go backend, not FastAPI

2. **FastAPI Models (`models.py`)**
   - `ChatRequest`, `ChatChunk`, `HealthResponse`, etc.
   - **Reason:** AgentX has its own API models

3. **Frontend (`src/` directory)**
   - React/TypeScript chat UI
   - **Reason:** AgentX has its own frontend

4. **Test Scripts**
   - `test_rag.py`, `test_rag.sh`
   - **Reason:** Can recreate if needed, not core functionality

5. **Reingestion Scripts**
   - `reingest_knowledge_base.py`
   - **Reason:** Can recreate as CLI tool if needed

### Preserved Components

1. **RAG Core Logic** ✅
   - ChromaDB integration
   - Embedding generation
   - Document chunking
   - Retrieval with filtering/boosting
   - URL mapping for citations

2. **Assistant Configurations** ✅
   - System prompts
   - Knowledge base mappings
   - Model preferences

3. **LLM Provider Abstractions** ✅
   - Ollama client
   - Response filtering

4. **Knowledge Base Data** ✅
   - `knowledge_base/` markdown files
   - **Action:** Keep in place, reference from new module

---

## PART 5: MIGRATION EXECUTION PLAN

### Step 1: Create Directory Structure
```bash
mkdir -p backend/knowledge/{vector_store,ingestion,retrieval}
mkdir -p backend/assistants
mkdir -p backend/llm/{providers,prompts}
```

### Step 2: Extract and Rewrite Knowledge Module
- Copy RAG files to new locations
- Remove FastAPI dependencies
- Update imports
- Add docstrings explaining extraction

### Step 3: Extract Assistants
- Copy assistant configs
- Add docstrings
- Ensure no FastAPI dependencies

### Step 4: Extract LLM Providers
- Copy Ollama client
- Copy response filter
- Ensure no FastAPI dependencies

### Step 5: Verification
- Check no imports reference `local_llm_staging`
- Verify AgentX agents still work
- Test knowledge module independently

### Step 6: Cleanup
- Delete `backend/local_llm_staging/`
- Update any documentation

---

## PART 6: RISKS & MITIGATION

### Risks

1. **ChromaDB Data Location**
   - **Risk:** Local-LLM stores ChromaDB in `backend/data/chromadb/`
   - **Mitigation:** Update `ChromaDBStore` to use configurable path, default to `backend/data/chromadb/`

2. **Knowledge Base Path**
   - **Risk:** Local-LLM references `knowledge_base/` relative to its backend
   - **Mitigation:** Use absolute paths or configurable base path

3. **Ollama Connection**
   - **Risk:** Ollama client hardcodes `localhost:11434`
   - **Mitigation:** Already uses `OLLAMA_BASE_URL` env var, keep as-is

4. **Import Conflicts**
   - **Risk:** AgentX may have conflicting module names
   - **Mitigation:** Use namespaced imports, check for conflicts

### Follow-ups

1. **Integration Testing**
   - Test RAG retrieval independently
   - Test assistant configs
   - Test Ollama client

2. **Documentation**
   - Document new module structure
   - Document how to use knowledge module
   - Document assistant configuration

3. **Future Enhancements**
   - Consider adding knowledge module to AgentX agents (optional)
   - Consider adding assistant API endpoints (separate from agents)

---

## PART 7: VERIFICATION CHECKLIST

- [ ] No imports reference `backend/local_llm_staging/`
- [ ] All new modules have `__init__.py` files
- [ ] All extracted code has docstrings explaining origin
- [ ] ChromaDB path is configurable
- [ ] Knowledge base path is configurable
- [ ] AgentX agents still function (no regressions)
- [ ] Knowledge module can be imported independently
- [ ] Assistants can be imported independently
- [ ] LLM providers can be imported independently
- [ ] `backend/local_llm_staging/` is deleted
- [ ] Git status shows no broken imports

---

## SUMMARY

**Files to Extract:** 12 core files  
**Files to Discard:** ~100 files (FastAPI server, frontend, tests)  
**New Modules:** 3 (`knowledge/`, `assistants/`, `llm/`)  
**Breaking Changes:** None (AgentX agents unchanged)  
**Functionality Lost:** FastAPI chat server, React frontend (intentional)

**Migration Status:** Ready to execute
