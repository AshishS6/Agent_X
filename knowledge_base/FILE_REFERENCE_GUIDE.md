# File Reference Guide

This document provides a detailed explanation of each file in the project, organized by folder structure.

## Backend Files

### Main Application

#### `backend/main.py`
**Purpose:** FastAPI application entry point

**Key Components:**
- FastAPI app initialization
- CORS middleware configuration
- Assistant registry (general, code, fintech)
- RAG pipeline initialization
- Chat endpoint (`/api/chat`) with streaming
- Document ingestion endpoint (`/api/ingest`)
- Health check endpoint (`/api/health`)
- Models endpoint (`/api/models`)
- Assistants endpoint (`/api/assistants`)

**Key Functions:**
- `lifespan()` - Startup/shutdown lifecycle
- `chat()` - Main chat endpoint with RAG integration
- `ingest_document()` - File upload and ingestion

**RAG Integration:**
- Checks if assistant has `use_rag=True`
- Calls `rag_pipeline.query()` with user query
- Retrieves 5 chunks (configurable)
- Enhances user message with context
- Sends to Ollama for generation

---

### Assistant Configurations

#### `backend/assistants/base.py`
**Purpose:** Base configuration class for assistants

**Class:** `AssistantConfig`
- `name: str` - Assistant identifier
- `model: str` - Ollama model to use
- `use_rag: bool` - Whether to use RAG
- `knowledge_base: Optional[str]` - ChromaDB collection name
- `system_prompt: str` - System prompt for LLM

**Usage:** Base class for all assistant configurations

---

#### `backend/assistants/fintech.py`
**Purpose:** Fintech assistant configuration

**Configuration:**
- Name: "fintech"
- Model: "qwen2.5:7b" (default)
- RAG: Enabled
- Knowledge Base: "fintech"
- System Prompt: Generic fintech expert prompt

**Current Issues:**
- System prompt is too generic
- No specific instructions for KB usage
- No guidance on citing sources

**Improvement Needed:**
- Add KB hierarchy awareness
- Add source citation instructions
- Add product-specific guidance

---

#### `backend/assistants/general.py`
**Purpose:** General-purpose assistant

**Configuration:**
- RAG: Disabled
- General-purpose system prompt

---

#### `backend/assistants/code.py`
**Purpose:** Code-focused assistant

**Configuration:**
- RAG: Disabled
- Code-focused system prompt

---

### RAG System Files

#### `backend/rag/pipeline.py`
**Purpose:** End-to-end RAG pipeline orchestration

**Class:** `RAGPipeline`

**Key Method:**
```python
async def query(
    user_query: str,
    knowledge_base: str,
    n_results: int = 5
) -> str
```

**Process:**
1. Calls `Retriever.retrieve()` to get context chunks
2. Combines chunks into context string
3. Formats prompt: `"Context: {chunks}\n\nQuestion: {query}"`
4. Returns enhanced prompt

**Current Limitations:**
- Simple context formatting
- No source citation
- No context quality check
- Fixed n_results=5

---

#### `backend/rag/retrieve.py`
**Purpose:** Document retrieval from vector store

**Class:** `Retriever`

**Key Method:**
```python
async def retrieve(
    query: str,
    knowledge_base: str,
    n_results: int = 5
) -> List[str]
```

**Process:**
1. Generates query embedding using `EmbeddingClient`
2. Queries `VectorStore` with embedding
3. Returns top N most similar chunks

**Current Limitations:**
- No re-ranking
- No metadata filtering
- No query expansion
- Simple cosine similarity only

---

#### `backend/rag/embed.py`
**Purpose:** Embedding generation using Ollama

**Class:** `EmbeddingClient`

**Configuration:**
- Model: "nomic-embed-text"
- Base URL: `http://localhost:11434` (Ollama)
- Timeout: 60 seconds

**Key Methods:**
- `embed(text: str)` - Single text embedding
- `embed_batch(texts: List[str])` - Batch embeddings (parallel, batch_size=10)
- `close()` - Close HTTP client

**Process:**
1. Sends text to Ollama `/api/embeddings` endpoint
2. Receives vector representation (list of floats)
3. Returns embedding vector

**Current Limitations:**
- Fixed model (no selection)
- No embedding caching
- No error retry logic

---

#### `backend/rag/store.py`
**Purpose:** ChromaDB vector store management

**Class:** `VectorStore`

**Configuration:**
- Persist directory: `backend/data/chromadb/`
- Uses ChromaDB PersistentClient
- Collection metadata: `{"hnsw:space": "cosine"}`

**Key Methods:**
- `get_collection(knowledge_base: str)` - Get or create collection
- `add_documents(...)` - Add documents with embeddings and metadata
- `query(...)` - Search for similar documents
- `list_collections()` - List all collections
- `delete_collection(...)` - Delete a collection
- `delete_all_collections()` - Delete all collections

**Storage:**
- Location: `backend/data/chromadb/`
- Format: ChromaDB SQLite database
- Collections: Named by `knowledge_base` parameter

**Metadata Stored:**
- `vendor`: "zwitch" or "openmoney"
- `layer`: "states", "flows", "api", "concepts", etc.
- `source_path`: Relative path to source file
- `is_meta`: Whether file is in `_meta/` folder
- `chunk_index`: Chunk number within file
- `total_chunks`: Total chunks in file

**Current Limitations:**
- Metadata stored but not used for filtering
- No hybrid search (keyword + semantic)
- No result boosting by layer/vendor

---

#### `backend/rag/ingest.py`
**Purpose:** Document chunking and processing

**Key Functions:**
- `load_document(file_path: str)` - Load file content
- `chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200)` - Split text into chunks
- `process_file(file_path: str)` - Process file and return chunks

**Chunking Strategy:**
- Chunk size: 1000 characters (default)
- Overlap: 200 characters (default)
- Tries to break at sentence boundaries (`.!?\n`)
- Looks for sentence endings within last 100 chars

**Current Limitations:**
- Fixed chunk size (1000 chars)
- Fixed overlap (200 chars)
- No semantic chunking
- May split important context
- Simple sentence boundary detection

---

#### `backend/rag/reingest_knowledge_base.py`
**Purpose:** Batch re-ingestion script for knowledge base

**Key Functions:**
- `determine_vendor(file_path: str)` - Extract vendor (zwitch/openmoney)
- `determine_layer(file_path: str)` - Extract layer (states/flows/api/etc.)
- `is_meta_file(file_path: str)` - Check if file is in `_meta/`
- `get_source_path(file_path: str, knowledge_base_root: str)` - Get relative path
- `reset_vector_store(vector_store: VectorStore)` - Delete all collections
- `find_markdown_files(knowledge_base_root: str)` - Find all .md files
- `ingest_file(...)` - Process single file with metadata
- `reingest_knowledge_base(...)` - Main re-ingestion function

**Process:**
1. Resets vector store (deletes all collections)
2. Finds all `.md` files in `knowledge_base/`
3. Processes each file:
   - Chunks the file
   - Generates metadata (vendor, layer, source_path)
   - Creates embeddings
   - Stores in ChromaDB
4. Provides summary statistics

**Usage:**
```bash
cd backend
python3 -m rag.reingest_knowledge_base
```

**Current Limitations:**
- No incremental updates (always deletes all)
- No validation of ingested content
- No dry-run mode

---

#### `backend/rag/prompts.py`
**Purpose:** Prompt templates for RAG

**Functions:**
- `get_rag_prompt(query: str, context: str, system_prompt: str)` - RAG prompt with context
- `get_direct_prompt(query: str, system_prompt: str)` - Direct prompt without RAG

**Current Usage:**
- Not actively used (prompting done inline in `pipeline.py`)

---

### Other Backend Files

#### `backend/models.py`
**Purpose:** Pydantic models for API requests/responses

**Models:**
- `ChatRequest` - Chat request model
- `ChatChunk` - Streaming response chunk
- `HealthResponse` - Health check response
- `ModelInfo` - Model information
- `AssistantInfo` - Assistant information
- `IngestRequest` - Ingestion request
- `IngestResponse` - Ingestion response

---

#### `backend/ollama_client.py`
**Purpose:** Ollama API client

**Class:** `OllamaClient`

**Methods:**
- `health_check()` - Check Ollama connection
- `get_models()` - Get available models
- `chat_stream(model: str, messages: List[Dict])` - Stream chat responses

---

#### `backend/response_filter.py`
**Purpose:** Filter thinking content from reasoning models

**Functions:**
- `filter_thinking_content(content: str)` - Remove thinking tags
- `extract_final_answer(content: str, model: str)` - Extract final answer

**Usage:** Filters output from reasoning models (like deepseek-r1) to show only final answers

---

## Knowledge Base Files

### Root Level

#### `knowledge_base/README.md`
**Purpose:** Main KB overview and usage guide

**Contents:**
- Current KB contents summary
- How to use KB in frontend
- Testing questions
- Methods for adding documents
- File structure overview

**Status:** ⚠️ Outdated (mentions only 8 chunks, should be updated)

---

#### `knowledge_base/KNOWLEDGE_BASE_EXPLAINED.md`
**Purpose:** Explains distinction between KB folder and RAG system

**Key Points:**
- `knowledge_base/` folder is just organizational
- RAG uses ChromaDB collections, not folder structure
- Files must be uploaded via API to be ingested
- Collection name is `"fintech"`, not folder name

**Status:** ✅ Accurate and helpful

---

#### `knowledge_base/COMPLETE_KB_SUMMARY.md`
**Purpose:** Comprehensive summary of entire KB

**Contents:**
- Complete overview of all files
- Open Money section (40 files)
- Zwitch section (46 files)
- Hierarchy explanations
- Usage guidelines

**Status:** ✅ Comprehensive (824 lines)

---

### Open Money Files

#### `knowledge_base/openmoney/README.md`
**Purpose:** Hierarchy and precedence rules for Open Money KB

**Key Content:**
- Authority hierarchy (principles > states > workflows > ...)
- Conflict resolution rules
- Usage guidelines
- Absolute principles

**Status:** ✅ Well documented

---

#### `knowledge_base/openmoney/company_overview.md`
**Purpose:** Company identity and positioning

**Contents:**
- Company identity
- Core focus areas
- Target customers
- Primary capabilities
- What Open Money is NOT
- Operating geography
- Regulatory context

**Status:** ✅ Good, but may need updates with latest website info

---

#### `knowledge_base/openmoney/concepts/`
**Purpose:** High-level explanations (lowest authority)

**Files:**
- `what_is_open_money.md` - Open Money identity
- `open_money_vs_bank.md` - Platform comparison
- `open_money_vs_accounting_software.md` - Software comparison
- `open_money_product_philosophy.md` - Product philosophy
- `data_ownership_and_limitations.md` - Data boundaries

**Status:** ✅ Well documented

---

#### `knowledge_base/openmoney/principles/`
**Purpose:** Foundational rules (highest authority)

**Files:**
- `backend_authority.md` - Backend owns critical decisions
- `reconciliation_is_not_optional.md` - Reconciliation is mandatory
- `financial_finality_rules.md` - When money movement is final

**Status:** ✅ Critical principles well documented

---

#### `knowledge_base/openmoney/states/`
**Purpose:** State machines (source of truth for finality)

**Files:**
- `invoice_state_lifecycle.md` - Invoice state machine
- `bill_state_lifecycle.md` - Bill state machine
- `payment_link_state_lifecycle.md` - Payment link state machine
- `payout_state_lifecycle.md` - Payout state machine
- `bank_account_states.md` - Bank account connection states

**Status:** ✅ Complete state machines

---

#### `knowledge_base/openmoney/workflows/`
**Purpose:** End-to-end system behavior

**Files:**
- `invoice_to_collection.md` - Invoice collection flow
- `bill_to_payout.md` - Bill payout flow
- `payment_link_to_settlement.md` - Payment link settlement
- `bulk_collection_flow.md` - Bulk collection process
- `reconciliation_flow.md` - Reconciliation process
- `gst_compliance_flow.md` - GST compliance process

**Status:** ✅ Complete workflows

---

#### `knowledge_base/openmoney/data_semantics/`
**Purpose:** Data meaning and limitations

**Files:**
- `derived_vs_actual_balances.md` - Balance interpretation
- `reconciliation_logic.md` - Reconciliation meaning
- `cashflow_calculation.md` - Cashflow derivation
- `overdue_calculation_logic.md` - Overdue computation
- `sample_data_vs_real_data.md` - Sample data isolation

**Status:** ✅ Well documented

---

#### `knowledge_base/openmoney/risks/`
**Purpose:** Safety warnings

**Files:**
- `dashboard_misinterpretation.md` - Dashboard limitations
- `stale_bank_data.md` - Bank sync delays
- `reconciliation_gaps.md` - Reconciliation failures
- `gst_compliance_risks.md` - Compliance risks

**Status:** ✅ Comprehensive risk documentation

---

#### `knowledge_base/openmoney/decisions/`
**Purpose:** Opinionated trade-offs

**Files:**
- `invoice_vs_payment_link.md` - When to use each
- `single_vs_bulk_payments.md` - Bulk payment guidance
- `when_to_reconcile.md` - Reconciliation timing
- `handling_failed_payouts.md` - Payout failure handling

**Status:** ✅ Good guidance

---

#### `knowledge_base/openmoney/modules/`
**Purpose:** Product surface documentation

**Files:**
- `receivables.md` - Receivables module
- `payables.md` - Payables module
- `banking.md` - Banking module
- `cashflow_analytics.md` - Cashflow module
- `payments_and_payouts.md` - Payments module
- `compliance.md` - Compliance module

**Status:** ✅ Product modules documented

---

### Zwitch Files

#### `knowledge_base/zwitch/README.md`
**Purpose:** Hierarchy and precedence rules for Zwitch KB

**Key Content:**
- Authority hierarchy (states > flows > api > ...)
- Conflict resolution rules
- Usage guidelines

**Status:** ✅ Well documented

---

#### `knowledge_base/zwitch/company_overview.md`
**Purpose:** Company identity and positioning

**Contents:**
- Company identity
- Core focus areas
- Target customers
- Primary capabilities
- Product categories (4 main categories)
- What Zwitch is NOT
- Operating geography
- Regulatory context

**Status:** ✅ Good, but may need updates with latest website info

---

#### `knowledge_base/zwitch/FAQ.md`
**Purpose:** Frequently asked questions

**Contents:**
- Does Zwitch offer Payment Gateway? (YES)
- Payment Gateway features
- Integration methods
- Key statistics
- Getting started guide

**Status:** ✅ Helpful, but could be expanded

---

#### `knowledge_base/zwitch/PAYMENT_GATEWAY.md`
**Purpose:** Direct confirmation of Payment Gateway services

**Contents:**
- Direct answer: YES
- Quick facts
- Direct quote from website
- Integration options
- Conclusion

**Status:** ✅ Clear and direct

---

#### `knowledge_base/zwitch/api/`
**Purpose:** Exact API interfaces and endpoints (factual reference)

**Files (16 files, numbered 00-15):**
- `00_introduction.md` - API overview, base URL, authentication
- `01_authentication.md` - Bearer token authentication
- `02_error_codes.md` - Error response format
- `03_accounts.md` - Account management APIs
- `04_account_balance_statement.md` - Balance and statements
- `05_payments.md` - Payment collection APIs
- `06_beneficiaries.md` - Beneficiary management
- `07_transfers.md` - Transfer/payout APIs
- `08_verification.md` - Verification APIs
- `09_bharat_connect.md` - Zwitch Bill Connect APIs
- `10_webhooks.md` - Webhook setup and configuration
- `11_api_constants.md` - API constants and enums
- `12_connected_banking.md` - Connected Banking APIs
- `13_examples_node.md` - Node.js code examples
- `14_examples_python.md` - Python code examples
- `15_layer_js.md` - Layer.js integration guide

**Status:** ✅ Comprehensive API documentation

---

#### `knowledge_base/zwitch/states/`
**Purpose:** State machines (source of truth for finality)

**Files:**
- `payment_status_lifecycle.md` - Payment state machine
- `transfer_status_lifecycle.md` - Transfer state machine
- `verification_states.md` - Verification state machine

**Status:** ✅ Complete state machines

---

#### `knowledge_base/zwitch/flows/`
**Purpose:** End-to-end system behavior

**Files:**
- `payin_happy_path.md` - Successful payment flow
- `payin_failure_path.md` - Payment failure handling
- `refund_flow.md` - Refund process
- `settlement_flow.md` - Settlement process

**Status:** ✅ Complete flows

---

#### `knowledge_base/zwitch/best_practices/`
**Purpose:** Production recommendations

**Files:**
- `recommended_db_schema.md` - Database design recommendations
- `production_checklist.md` - Pre-launch checklist
- `logging_and_audits.md` - Logging requirements

**Status:** ✅ Good production guidance

---

#### `knowledge_base/zwitch/decisions/`
**Purpose:** Opinionated trade-offs

**Files:**
- `polling_vs_webhooks.md` - Webhooks primary, polling fallback
- `frontend_vs_backend_calls.md` - Backend authority
- `retries_and_idempotency.md` - Retry strategies

**Status:** ✅ Good architectural guidance

---

#### `knowledge_base/zwitch/risks/`
**Purpose:** Safety warnings

**Files:**
- `double_credit_risk.md` - Preventing duplicate processing
- `webhook_signature_verification.md` - Security requirement
- `reconciliation_failures.md` - Handling discrepancies
- `compliance_boundaries.md` - Legal responsibilities

**Status:** ✅ Comprehensive risk documentation

---

#### `knowledge_base/zwitch/principles/`
**Purpose:** Foundational rules

**Files:**
- `source_of_truth.md` - Webhooks are primary source
- `backend_authority.md` - Backend owns critical decisions
- `idempotency.md` - Idempotency is mandatory

**Status:** ✅ Critical principles well documented

---

#### `knowledge_base/zwitch/concepts/`
**Purpose:** High-level explanations

**Files:**
- `payin_vs_payout.md` - Money flow explanation
- `payment_token_vs_order.md` - Conceptual distinction
- `merchant_vs_platform.md` - Business model distinction
- `zwitch_vs_open_money.md` - Platform comparison

**Status:** ✅ Good conceptual explanations

---

#### `knowledge_base/zwitch/_meta/`
**Purpose:** Metadata and analysis

**Files:**
- `API_FACT_CHECK_ANALYSIS.md` - Fact check analysis
- `UPDATE_SUMMARY.md` - Summary of updates

**Status:** ✅ Helpful metadata

---

## Documentation Files (New)

#### `knowledge_base/RAG_SYSTEM_ARCHITECTURE.md`
**Purpose:** Complete RAG system architecture documentation

**Contents:**
- System architecture diagram
- Key components explanation
- Data flow diagrams
- Configuration details
- Current status and limitations

**Status:** ✅ Comprehensive documentation

---

#### `knowledge_base/KB_STRUCTURE_AND_CONTENT.md`
**Purpose:** KB structure and content analysis

**Contents:**
- Folder structure
- Content statistics
- Knowledge hierarchy
- Content coverage analysis
- Accuracy comparison with websites
- Content quality assessment

**Status:** ✅ Detailed analysis

---

#### `knowledge_base/CURRENT_PHASE_ANALYSIS.md`
**Purpose:** Current phase and status analysis

**Contents:**
- What's working
- Current issues
- Detailed file analysis
- RAG query flow analysis
- Data ingestion status
- Performance metrics
- Identified gaps

**Status:** ✅ Comprehensive status report

---

#### `knowledge_base/IMPROVEMENT_PLAN.md`
**Purpose:** Comprehensive improvement plan

**Contents:**
- Current issues summary
- Phase 1-5 improvement plans
- Implementation priorities
- Success metrics
- Timeline

**Status:** ✅ Detailed improvement roadmap

---

#### `knowledge_base/FILE_REFERENCE_GUIDE.md`
**Purpose:** This file - detailed file-by-file reference

**Status:** ✅ Complete reference guide

---

## Summary

### Backend Files: 15 files
- Main application: 1 file
- Assistants: 4 files
- RAG system: 7 files
- Other: 3 files

### Knowledge Base Files: ~91 files
- Root level: 10 files (including new docs)
- Open Money: ~40 files
- Zwitch: ~46 files

### Total: ~106 files

All files are documented and organized with clear purposes and responsibilities.
