# Improvement Plan for RAG System and Knowledge Base

## Executive Summary

This document outlines a comprehensive improvement plan to enhance the accuracy and quality of responses from the fintech assistant. The plan addresses both technical RAG improvements and knowledge base content updates.

## Current Issues Summary

1. **Answer Quality:** Responses may be inaccurate or incomplete
2. **Retrieval Limitations:** Only 5 chunks, no re-ranking, simple search
3. **Chunking Strategy:** Fixed size, may split context
4. **Content Gaps:** Some product info outdated, missing details

## Phase 1: Immediate Fixes (Week 1)

### 1.1 Improve System Prompt

**File:** `backend/assistants/fintech.py`

**Current:**
```python
system_prompt="You are a financial technology expert assistant..."
```

**Improvement:**
```python
system_prompt="""You are a financial technology expert assistant specializing in Zwitch and Open Money platforms.

KNOWLEDGE BASE USAGE:
- Use the provided context from the knowledge base as the primary source
- If context contains relevant information, cite it directly
- If context is incomplete, clearly state what information is missing
- Follow the knowledge hierarchy: states > flows > api > concepts

RESPONSE GUIDELINES:
- Be accurate and specific
- Cite sources when referencing KB content
- If unsure, say so rather than guessing
- For product questions, list all products/categories mentioned in context
- Use exact terminology from the knowledge base

ZWITCH PRODUCTS:
- Payment Gateway (150+ payment methods, payment links, refunds, recurring payments)
- Payouts (Connected Banking, instant transfers, 150+ banks)
- Zwitch Bill Connect (1000+ ERPs, Bharat Connect Network)
- Verification Suite (verification, compliance, onboarding APIs)

OPEN MONEY PRODUCTS:
- Connected Banking (ICICI, SBI, Axis, Yes Bank)
- Pay Vendors (bill management, payouts)
- Get Paid (invoices, payment links)
- Auto-Reconciliation (accounting software sync)
- GST Compliance (invoicing, tax filing)

Always prioritize accuracy over completeness."""
```

**Impact:** Better guidance for LLM to use KB correctly

### 1.2 Increase Retrieval Count

**File:** `backend/main.py`

**Current:**
```python
enhanced_content = await rag_pipeline.query(
    user_query=last_user_message,
    knowledge_base=assistant_config.knowledge_base,
    n_results=5
)
```

**Improvement:**
```python
enhanced_content = await rag_pipeline.query(
    user_query=last_user_message,
    knowledge_base=assistant_config.knowledge_base,
    n_results=10  # Increased from 5
)
```

**Impact:** More context available, better chance of complete answers

### 1.3 Add Source Citation

**File:** `backend/rag/pipeline.py`

**Current:** Returns plain context string

**Improvement:**
```python
async def query(
    self,
    user_query: str,
    knowledge_base: str,
    n_results: int = 10
) -> str:
    context_chunks = await self.retriever.retrieve(
        query=user_query,
        knowledge_base=knowledge_base,
        n_results=n_results
    )
    
    # Get metadata for citation
    context_with_sources = []
    for i, chunk in enumerate(context_chunks):
        # Extract source from metadata if available
        source = f"Source {i+1}"  # TODO: Get actual source_path from metadata
        context_with_sources.append(f"[{source}]\n{chunk}")
    
    context = "\n\n".join(context_with_sources) if context_with_sources else ""
    
    if context:
        return f"""Use the following context from the knowledge base to answer the question. Cite sources when referencing specific information.

Context:
{context}

Question: {user_query}

When answering, cite sources like [Source 1], [Source 2], etc."""
    else:
        return user_query
```

**Impact:** Users can verify sources, better transparency

### 1.4 Update KB Content

**Priority Files to Update:**

1. **`knowledge_base/zwitch/company_overview.md`**
   - Verify all 4 product categories are clearly listed
   - Add statistics (4M+ businesses, $35B+ transactions)
   - Add missing features (corporate cards, anchor financing)

2. **`knowledge_base/openmoney/company_overview.md`**
   - Update with latest statistics (3.5M+ businesses)
   - Add bank partnerships (ICICI, SBI, Axis, Yes Bank)
   - Add accounting software integrations

3. **Create:** `knowledge_base/zwitch/products_overview.md`
   - Comprehensive product overview
   - All 4 categories with features
   - Use cases and examples

4. **Create:** `knowledge_base/openmoney/products_overview.md`
   - Comprehensive product overview
   - All features and capabilities
   - Integration details

**Impact:** More accurate and complete product information

## Phase 2: Enhanced Retrieval (Week 2)

### 2.1 Implement Metadata Filtering

**File:** `backend/rag/retrieve.py`

**Enhancement:**
```python
async def retrieve(
    self,
    query: str,
    knowledge_base: str,
    n_results: int = 10,
    vendor: Optional[str] = None,
    layer: Optional[str] = None,
    boost_layers: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve with metadata filtering and boosting
    
    Returns:
        List of dicts with 'text' and 'metadata' keys
    """
    query_embedding = await self.embedding_client.embed(query)
    
    # Query with more results for filtering
    results = self.vector_store.query(
        knowledge_base=knowledge_base,
        query_embedding=query_embedding,
        n_results=n_results * 2  # Get more for filtering
    )
    
    # Filter and boost by metadata
    filtered_results = []
    for result in results:
        # Apply filters
        if vendor and result.metadata.get('vendor') != vendor:
            continue
        if layer and result.metadata.get('layer') != layer:
            continue
        
        # Boost authoritative layers
        result_layer = result.metadata.get('layer', '')
        if boost_layers and result_layer in boost_layers:
            result.score *= 1.5  # Boost authoritative layers
        
        filtered_results.append(result)
    
    # Sort by score and return top N
    filtered_results.sort(key=lambda x: x.score, reverse=True)
    return filtered_results[:n_results]
```

**Impact:** Better retrieval of authoritative sources

### 2.2 Add Query Expansion

**File:** `backend/rag/retrieve.py`

**Enhancement:**
```python
def expand_query(self, query: str) -> List[str]:
    """
    Expand query with synonyms and related terms
    """
    expansions = []
    
    # Product-related expansions
    product_expansions = {
        'products': ['product categories', 'services', 'offerings', 'solutions'],
        'payment gateway': ['pg', 'payment processing', 'checkout'],
        'payouts': ['transfers', 'disbursements', 'payments out'],
        'verification': ['kyc', 'identity verification', 'compliance'],
    }
    
    query_lower = query.lower()
    for key, synonyms in product_expansions.items():
        if key in query_lower:
            expansions.extend(synonyms)
    
    return expansions

async def retrieve(self, ...):
    # Expand query
    expanded_terms = self.expand_query(query)
    
    # Generate embeddings for original and expanded
    embeddings = [await self.embedding_client.embed(query)]
    for term in expanded_terms:
        embeddings.append(await self.embedding_client.embed(term))
    
    # Query with multiple embeddings (average or use best)
    # ... implementation
```

**Impact:** Better matching for product-related queries

### 2.3 Implement Re-ranking

**File:** `backend/rag/retrieve.py`

**Enhancement:**
```python
async def rerank_results(
    self,
    query: str,
    results: List[Dict],
    n_results: int = 10
) -> List[Dict]:
    """
    Re-rank results using cross-encoder or rule-based scoring
    """
    # Rule-based re-ranking
    for result in results:
        score = result.get('score', 0.0)
        metadata = result.get('metadata', {})
        
        # Boost authoritative layers
        layer = metadata.get('layer', '')
        layer_boost = {
            'states': 1.3,
            'principles': 1.3,
            'flows': 1.2,
            'api': 1.1,
            'concepts': 0.9
        }
        score *= layer_boost.get(layer, 1.0)
        
        # Boost exact matches in title/heading
        text = result.get('text', '')
        if query.lower() in text.lower()[:200]:  # First 200 chars
            score *= 1.2
        
        # Boost company overview files
        source = metadata.get('source_path', '')
        if 'company_overview' in source or 'FAQ' in source:
            score *= 1.15
        
        result['score'] = score
    
    # Sort by new score
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:n_results]
```

**Impact:** Better ordering of results by relevance and authority

## Phase 3: Improved Chunking (Week 3)

### 3.1 Implement Semantic Chunking

**File:** `backend/rag/ingest.py`

**Enhancement:**
```python
def semantic_chunk_text(
    text: str,
    min_chunk_size: int = 500,
    max_chunk_size: int = 1500,
    overlap: int = 200
) -> List[str]:
    """
    Chunk text semantically, trying to preserve meaning
    """
    chunks = []
    
    # Split by headings first (markdown)
    sections = re.split(r'\n#{1,3}\s+', text)
    
    for section in sections:
        if len(section) <= max_chunk_size:
            chunks.append(section.strip())
        else:
            # Further split by paragraphs
            paragraphs = section.split('\n\n')
            current_chunk = ""
            
            for para in paragraphs:
                if len(current_chunk) + len(para) <= max_chunk_size:
                    current_chunk += para + "\n\n"
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = para + "\n\n"
            
            if current_chunk:
                chunks.append(current_chunk.strip())
    
    return chunks
```

**Impact:** Better preservation of context and meaning

### 3.2 Add Chunk Metadata

**Enhancement:**
```python
def process_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Process file and return chunks with metadata
    """
    content = load_document(file_path)
    chunks = semantic_chunk_text(content)
    
    chunk_objects = []
    for i, chunk in enumerate(chunks):
        chunk_obj = {
            'text': chunk,
            'chunk_index': i,
            'total_chunks': len(chunks),
            'has_heading': bool(re.search(r'^#{1,3}\s+', chunk, re.MULTILINE)),
            'word_count': len(chunk.split()),
            'char_count': len(chunk)
        }
        chunk_objects.append(chunk_obj)
    
    return chunk_objects
```

**Impact:** Better chunk selection and filtering

## Phase 4: Content Updates (Week 4)

### 4.1 Create Product Overview Files

**New Files:**

1. **`knowledge_base/zwitch/products_overview.md`**
   ```markdown
   # Zwitch Products Overview
   
   ## Main Product Categories
   
   Zwitch offers four main product categories:
   
   ### 1. Payment Gateway
   - 150+ payment methods
   - Payment links
   - Instant refunds
   - Recurring payments
   - Native SDKs (Android, iOS, Flutter)
   - Layer.js for web
   
   ### 2. Payouts
   - Connected Banking with 150+ banks
   - Instant account-to-account transfers
   - NEFT/RTGS/IMPS/UPI
   - Escrow payments
   - Payouts API
   
   ### 3. Zwitch Bill Connect
   - Connected with 1000+ ERPs and Banks
   - 150+ Connected Payment Methods
   - Instant Bill Discounting API
   - API Marketplace
   - NPCI Bharat Connect Network
   
   ### 4. Verification Suite
   - Verification APIs (VPA, Bank Account, PAN, Name)
   - Compliance APIs
   - Onboarding APIs
   
   ## Statistics
   - 4 Million+ businesses powered
   - 150+ payment methods
   - $35 Billion+ transactions processed
   ```

2. **`knowledge_base/openmoney/products_overview.md`**
   ```markdown
   # Open Money Products Overview
   
   ## Main Features
   
   ### Connected Banking
   - ICICI Connected Banking
   - SBI Connected Banking
   - Axis Bank Connected Banking
   - Yes Bank Connected Banking
   
   ### Pay Vendors
   - Bill management
   - Direct account-to-account payments
   - Auto-sync with accounting software
   
   ### Get Paid
   - GST-compliant invoices
   - Payment links
   - Multiple payment modes (net banking, UPI, cards)
   - Instant settlement
   
   ### Auto-Reconciliation
   - Two-way sync with accounting software
   - Tally integration
   - Zoho Books integration
   - Oracle NetSuite integration
   - Microsoft Dynamics integration
   
   ## Statistics
   - 3.5 Million+ businesses
   - $35 Billion+ transactions annually
   - 65k+ tax practitioners
   - 15/20 top banks use Open
   ```

### 4.2 Update Company Overviews

**Files to Update:**
- `knowledge_base/zwitch/company_overview.md`
- `knowledge_base/openmoney/company_overview.md`

**Add:**
- Latest statistics
- All product categories clearly listed
- Integration partners
- Use cases

### 4.3 Create FAQ Files

**Enhance:**
- `knowledge_base/zwitch/FAQ.md` - Add more common questions
- Create: `knowledge_base/openmoney/FAQ.md` - New FAQ file

**Common Questions to Add:**
- "What products does Zwitch offer?"
- "How do I integrate Zwitch Payment Gateway?"
- "What is the difference between Payment Gateway and UPI Collect?"
- "What banks does Open Money support?"
- "How does Open Money reconciliation work?"

## Phase 5: Evaluation and Testing (Week 5)

### 5.1 Create Test Suite

**New File:** `backend/test_rag_quality.py`

```python
"""
Test suite for RAG quality evaluation
"""

TEST_QUESTIONS = [
    {
        "question": "What all products Zwitch has?",
        "expected_products": [
            "Payment Gateway",
            "Payouts",
            "Zwitch Bill Connect",
            "Verification Suite"
        ],
        "min_score": 0.8
    },
    {
        "question": "Does Zwitch offer Payment Gateway?",
        "expected_answer": "yes",
        "min_score": 0.9
    },
    # ... more test cases
]

async def evaluate_rag():
    """Run evaluation tests"""
    # Implementation
    pass
```

### 5.2 Add Answer Quality Metrics

**Metrics to Track:**
- Answer completeness (all products mentioned?)
- Answer accuracy (correct information?)
- Source citation (sources cited?)
- Response time
- Chunk relevance score

### 5.3 A/B Testing Framework

**Implementation:**
- Compare old vs new retrieval
- Compare different chunking strategies
- Compare different n_results values
- Track user satisfaction

## Implementation Priority

### High Priority (Do First)
1. ✅ Improve system prompt (1.1)
2. ✅ Increase retrieval count (1.2)
3. ✅ Update KB product information (1.4)
4. ✅ Create product overview files (4.1)

### Medium Priority (Do Next)
1. Add source citation (1.3)
2. Implement metadata filtering (2.1)
3. Add query expansion (2.2)
4. Update company overviews (4.2)

### Low Priority (Nice to Have)
1. Implement re-ranking (2.3)
2. Semantic chunking (3.1)
3. Evaluation framework (5.1)
4. A/B testing (5.3)

## Success Metrics

### Answer Quality
- ✅ All 4 Zwitch products mentioned when asked
- ✅ Accurate product descriptions
- ✅ Sources cited in responses
- ✅ No hallucinations

### Performance
- Response time < 3 seconds
- Retrieval time < 500ms
- High chunk relevance scores

### User Satisfaction
- Answers are complete and accurate
- Sources are verifiable
- Responses are helpful

## Timeline

- **Week 1:** Immediate fixes (1.1, 1.2, 1.4, 4.1)
- **Week 2:** Enhanced retrieval (2.1, 2.2)
- **Week 3:** Improved chunking (3.1, 3.2)
- **Week 4:** Content updates (4.2, 4.3)
- **Week 5:** Evaluation and testing (5.1, 5.2, 5.3)

## Next Steps

1. Review and approve this plan
2. Start with Phase 1 (immediate fixes)
3. Test improvements incrementally
4. Gather feedback and iterate
5. Continue with subsequent phases
