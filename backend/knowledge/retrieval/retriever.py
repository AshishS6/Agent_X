"""
Retrieval logic for RAG

Extracted from Local-LLM project (backend/local_llm_staging/backend/rag/retrieve.py).
Renamed from Retriever to RAGRetriever for clarity.

This module provides semantic retrieval with filtering and boosting capabilities.
"""

import re
from typing import List, Dict, Optional, Any
from ..vector_store.embedding_client import OllamaEmbeddingClient
from ..vector_store.chromadb_store import ChromaDBStore


class RAGRetriever:
    """
    Retriever for RAG queries
    
    Extracted from Local-LLM project. Provides semantic search with
    metadata filtering and layer boosting.
    """
    
    def __init__(self, embedding_client: OllamaEmbeddingClient, vector_store: ChromaDBStore):
        """
        Initialize retriever
        
        Args:
            embedding_client: Client for generating embeddings
            vector_store: Vector store for similarity search
        """
        self.embedding_client = embedding_client
        self.vector_store = vector_store
    
    async def retrieve(
        self,
        query: str,
        knowledge_base: str,
        n_results: int = 5,
        include_metadata: bool = False,
        vendor: Optional[str] = None,
        layer: Optional[str] = None,
        boost_layers: Optional[List[str]] = None,
        expand_query: bool = True
    ):
        """
        Retrieve relevant documents for a query
        
        Args:
            query: User query
            knowledge_base: Knowledge base to search
            n_results: Number of results to return
            include_metadata: If True, return dicts with text and metadata
            vendor: Optional vendor filter (e.g., 'zwitch', 'openmoney')
            layer: Optional layer filter (e.g., 'states', 'api', 'concepts')
            boost_layers: Optional list of layers to boost (e.g., ['states', 'principles'])
            expand_query: If True, expand query with synonyms and related terms
            
        Returns:
            If include_metadata=False: List of retrieved text chunks
            If include_metadata=True: List of dicts with 'text', 'metadata', and 'distance' keys
        """
        # Expand query if enabled
        if expand_query:
            expanded_terms = self._expand_query(query)
            # Use original query + expansions to improve matching (keyword + semantic).
            # Keep it deterministic and bounded.
            expanded_terms = list(dict.fromkeys([t.strip() for t in expanded_terms if t and t.strip()]))[:12]
            search_query = (query + " " + " ".join(expanded_terms)).strip()
        else:
            search_query = query
        
        # Generate query embedding
        query_lower = search_query.lower()

        # Multi-query retrieval for better recall on common intents.
        # This helps when a short user query semantically matches the wrong doc (e.g., "payout api" → Layer.js).
        queries = [search_query]
        if any(k in query_lower for k in ["what is zwitch", "whats zwitch", "what's zwitch"]):
            queries.append("Zwitch products Payment Gateway Payouts Zwitch Bill Connect Verification Suite")
        if any(k in query_lower for k in ["payout", "payouts", "transfer", "transfers", "disburse", "beneficiary"]):
            queries.append("transfers payouts beneficiary POST /v1/transfers POST /v1/transfers/bulk")
        if any(k in query_lower for k in ["payment gateway", "layer.js", "layer js", "payment token", "checkout"]):
            queries.append("payment gateway layer.js payment token POST /v1/pg/payment_token")
        if any(k in query_lower for k in ["balance", "/balance", "statement", "/statement", "account balance"]):
            queries.append("GET /v1/accounts/{id}/balance GET /v1/accounts/{id}/statement balance statement")

        # Keep bounded and deterministic
        queries = list(dict.fromkeys([q.strip() for q in queries if q and q.strip()]))[:3]
        query_embeddings = [await self.embedding_client.embed(q) for q in queries]
        
        # Query with more results if filtering is needed
        if vendor or layer or boost_layers:
            # We filter/boost after retrieval; ask Chroma for more so the right doc is in the candidate set.
            query_n_results = max(n_results * 8, 40)
        else:
            query_n_results = n_results
        
        # Query vector store with metadata (possibly multiple times) then merge for recall.
        merged: List[Dict[str, Any]] = []
        best_by_sig: Dict[Any, Dict[str, Any]] = {}
        for emb in query_embeddings:
            partial = self.vector_store.query(
                knowledge_base=knowledge_base,
                query_embedding=emb,
                n_results=query_n_results,
                include_metadata=True,
            )
            for r in partial:
                md = r.get("metadata") or {}
                sig = (
                    (md.get("source_path") or ""),
                    md.get("chunk_index"),
                    (r.get("text") or "")[:120],
                )
                prev = best_by_sig.get(sig)
                if prev is None or (r.get("distance") is not None and r.get("distance") < prev.get("distance", float("inf"))):
                    best_by_sig[sig] = r
        merged = list(best_by_sig.values())
        results = merged
        
        # Apply metadata filtering and boosting
        if vendor or layer or boost_layers:
            results = self._filter_and_boost_results(
                results, query=search_query, vendor=vendor, layer=layer, boost_layers=boost_layers
            )
            # For API-like queries, expand to include adjacent chunks from the same file.
            # This reduces "partial schema" failures where the endpoint header is retrieved
            # but the example request/response JSON lives in neighboring chunks.
            if self._should_expand_neighbors(query=search_query, layer=layer, boost_layers=boost_layers):
                results = self._expand_with_neighbor_chunks(
                    results=results,
                    knowledge_base=knowledge_base,
                    query=search_query,
                    vendor=vendor,
                    layer=layer,
                    window=6,
                    max_sources=4,
                )

            # Limit to n_results after filtering/expansion
            results = results[:n_results]
        
        if include_metadata:
            return results
        else:
            # Return just the text for backward compatibility
            return [r['text'] for r in results]

    def _should_expand_neighbors(
        self,
        query: str,
        layer: Optional[str] = None,
        boost_layers: Optional[List[str]] = None,
    ) -> bool:
        ql = (query or "").lower()
        boost_set = {b.lower() for b in boost_layers} if boost_layers else set()
        looks_like_api = any(k in ql for k in [" api", "endpoint", "webhook", "sdk", "curl", "/v1/"]) or bool(
            re.search(r"\b(post|get|put|delete|patch)\b", ql)
        )
        asks_for_examples = any(k in ql for k in ["sample request", "sample response", "request body", "response body", "example request", "example response"])
        return (layer or "").lower() == "api" or ("api" in boost_set and (looks_like_api or asks_for_examples)) or asks_for_examples

    def _expand_with_neighbor_chunks(
        self,
        results: List[Dict[str, Any]],
        knowledge_base: str,
        query: str,
        vendor: Optional[str] = None,
        layer: Optional[str] = None,
        window: int = 2,
        max_sources: int = 4,
    ) -> List[Dict[str, Any]]:
        """
        Expand top results by including +/- window chunks from the same source_path.
        Deterministic: stable ordering and stable distance assignment.
        """
        if not results:
            return results

        collection = self.vector_store.get_collection(knowledge_base)
        global_best_distance = min(
            (float(r.get("distance")) for r in results if r.get("distance") is not None),
            default=0.5,
        )

        # Only expand a bounded number of source files (highest-ranked first).
        seen_sources: List[str] = []
        for r in results:
            sp = ((r.get("metadata") or {}).get("source_path") or "").strip()
            if sp and sp not in seen_sources:
                seen_sources.append(sp)
            if len(seen_sources) >= max_sources:
                break

        existing = set()
        for r in results:
            md = r.get("metadata") or {}
            existing.add(((md.get("source_path") or ""), md.get("chunk_index")))

        expanded: List[Dict[str, Any]] = list(results)

        # Build quick lookups from existing results for distance anchoring.
        best_distance_by_sig: Dict[Any, float] = {}
        for r in results:
            md = r.get("metadata") or {}
            sig = ((md.get("source_path") or ""), md.get("chunk_index"))
            d = r.get("distance")
            if d is None:
                continue
            prev = best_distance_by_sig.get(sig)
            if prev is None or d < prev:
                best_distance_by_sig[sig] = float(d)

        for sp in seen_sources:
            try:
                got = collection.get(where={"source_path": sp}, include=["documents", "metadatas"])
            except Exception:
                continue

            docs = got.get("documents") or []
            mds = got.get("metadatas") or []
            if not docs or not mds:
                continue

            # Map chunk_index -> (doc, md) for deterministic neighbor selection.
            by_idx: Dict[int, Dict[str, Any]] = {}
            for doc, md in zip(docs, mds):
                if not isinstance(md, dict):
                    continue
                ci = md.get("chunk_index")
                if ci is None:
                    continue
                try:
                    ci_int = int(ci)
                except Exception:
                    continue
                by_idx[ci_int] = {"text": doc, "metadata": md}

            ql = (query or "").lower()
            wants_balance = any(k in ql for k in ["/balance", "account balance", "get account balance"])
            wants_statement = any(k in ql for k in ["/statement", "account statement", "get account statement"])

            # Expand around any chunk_index already present from this source.
            indices_in_results = sorted(
                [int(md.get("chunk_index")) for md in (r.get("metadata") or {} for r in results) if (md.get("source_path") or "") == sp and md.get("chunk_index") is not None]
            )
            if not indices_in_results:
                continue

            for ci in indices_in_results:
                anchor_dist = best_distance_by_sig.get((sp, ci), None)
                if anchor_dist is None:
                    # Fall back to "best known" for this source
                    anchor_dist = min(
                        (best_distance_by_sig.get((sp, i)) for i in indices_in_results if best_distance_by_sig.get((sp, i)) is not None),
                        default=0.5,
                    )

                for delta in range(-window, window + 1):
                    ni = ci + delta
                    if (sp, ni) in existing:
                        continue
                    item = by_idx.get(ni)
                    if not item:
                        continue

                    md = item.get("metadata") or {}
                    # Enforce same vendor/layer constraints (best-effort).
                    if vendor and (md.get("vendor", "").lower() != vendor.lower()):
                        continue
                    if layer and (md.get("layer", "").lower() != layer.lower()):
                        continue

                    # Assign a deterministic "slightly worse" distance than the anchor.
                    dist = float(anchor_dist) * 1.01 + (abs(delta) * 1e-4)
                    expanded.append({"text": item.get("text", ""), "metadata": md, "distance": dist})
                    existing.add((sp, ni))

            # Priority: pull in explicit response-schema chunks for the asked endpoint.
            # This reduces failures where we retrieve the endpoint header and examples, but miss the JSON response block.
            def _is_priority_response_chunk(text: str) -> bool:
                tl = (text or "").lower()
                if "```json" not in tl and "### response" not in tl:
                    return False
                if wants_balance and ("/balance" in tl or "get account balance" in tl):
                    return True
                if wants_statement and ("/statement" in tl or "get account statement" in tl):
                    return True
                return False

            priority_indices = [i for i, item in by_idx.items() if _is_priority_response_chunk(item.get("text", ""))]
            if priority_indices:
                best_anchor = min(
                    (best_distance_by_sig.get((sp, i)) for i in indices_in_results if best_distance_by_sig.get((sp, i)) is not None),
                    default=0.5,
                )
                for pi in sorted(set(priority_indices)):
                    if (sp, pi) in existing:
                        continue
                    item = by_idx.get(pi)
                    if not item:
                        continue
                    md = item.get("metadata") or {}
                    if vendor and (md.get("vendor", "").lower() != vendor.lower()):
                        continue
                    if layer and (md.get("layer", "").lower() != layer.lower()):
                        continue
                    # Make these slightly *better* than the anchor so they survive top-k slicing.
                    dist = min(float(best_anchor) * 0.95, float(global_best_distance) * 0.98)
                    expanded.append({"text": item.get("text", ""), "metadata": md, "distance": dist})
                    existing.add((sp, pi))

        # Deterministic sort consistent with _filter_and_boost_results.
        def _sort_key(x: Dict[str, Any]):
            md = x.get("metadata") or {}
            return (
                x.get("distance", float("inf")),
                (md.get("source_path") or ""),
                md.get("chunk_index", -1),
            )

        expanded.sort(key=_sort_key)
        return expanded
    
    def _filter_and_boost_results(
        self,
        results: List[Dict[str, Any]],
        query: str,
        vendor: Optional[str] = None,
        layer: Optional[str] = None,
        boost_layers: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter and boost results based on metadata
        
        Args:
            results: List of result dicts with 'text', 'metadata', 'distance'
            vendor: Optional vendor filter
            layer: Optional layer filter
            boost_layers: Optional list of layers to boost
            
        Returns:
            Filtered and boosted results
        """
        filtered_results: List[Dict[str, Any]] = []
        boost_set = {b.lower() for b in boost_layers} if boost_layers else set()
        ql = (query or "").lower()
        
        for result in results:
            metadata = result.get('metadata', {})
            section_path = (metadata.get("section_path") or "").lower()
            
            # Apply vendor filter
            if vendor and metadata.get('vendor', '').lower() != vendor.lower():
                continue
            
            # Apply layer filter
            if layer and metadata.get('layer', '').lower() != layer.lower():
                continue
            
            # Apply layer boosting
            result_layer = (metadata.get('layer', '') or '').lower()
            if boost_set and result_layer in boost_set:
                # Boost by reducing distance (lower distance = higher relevance)
                if result.get('distance') is not None:
                    result['distance'] = result['distance'] * 0.7  # Boost by 30%
            
            # Boost products_overview files for product questions
            source_path = metadata.get('source_path', '').lower()
            if 'products_overview' in source_path or 'products-overview' in source_path:
                # Strong boost for products overview files
                if result.get('distance') is not None:
                    result['distance'] = result['distance'] * 0.5  # Boost by 50%

            # Heuristic source boosts for common Zwitch/Open Money misses.
            if result.get("distance") is not None:
                # Zwitch payouts/transfers: strongly prefer transfers + beneficiaries docs.
                if any(k in ql for k in ["payout", "payouts", "transfer", "transfers", "disburse", "beneficiary"]):
                    if "zwitch/api/07_transfers" in source_path or "/api/07_transfers" in source_path or "07_transfers" in source_path:
                        result["distance"] = result["distance"] * 0.35
                    elif "zwitch/api/06_beneficiaries" in source_path or "06_beneficiaries" in source_path:
                        result["distance"] = result["distance"] * 0.5
                    elif "15_layer_js" in source_path:
                        # Penalize payment-gateway-only docs for payout questions.
                        result["distance"] = result["distance"] * 1.25

                # Zwitch account balance / statement: prefer the dedicated balance+statement doc.
                if any(k in ql for k in ["balance", "/balance", "statement", "/statement", "account balance"]):
                    if "zwitch/api/04_account_balance_statement" in source_path or "04_account_balance_statement" in source_path:
                        result["distance"] = result["distance"] * 0.35

                # If user asks for samples/bodies, strongly prefer the explicit Response sub-sections.
                if any(k in ql for k in ["sample", "example", "request body", "response body", "request/response", "request response"]):
                    if any(k in ql for k in ["balance", "/balance"]) and "get account balance>response" in section_path:
                        result["distance"] = result["distance"] * 0.25
                    if any(k in ql for k in ["statement", "/statement"]) and "get account statement>response" in section_path:
                        result["distance"] = result["distance"] * 0.25

                # Zwitch "what is zwitch": prefer overview/company docs over API intro.
                if any(k in ql for k in ["what is zwitch", "whats zwitch", "what's zwitch"]):
                    if "zwitch/products_overview" in source_path or "zwitch/company_overview" in source_path or "zwitch/faq" in source_path:
                        result["distance"] = result["distance"] * 0.35
                    elif "/api/" in source_path:
                        result["distance"] = result["distance"] * 1.2
            
            filtered_results.append(result)

        # De-duplicate obvious repeats (common when re-ingesting without stable IDs).
        deduped: List[Dict[str, Any]] = []
        seen = set()
        for r in filtered_results:
            md = r.get("metadata") or {}
            sig = (
                (md.get("source_path") or ""),
                md.get("chunk_index"),
                (r.get("text") or "")[:120],
            )
            if sig in seen:
                continue
            seen.add(sig)
            deduped.append(r)

        def _sort_key(x: Dict[str, Any]):
            md = x.get("metadata") or {}
            return (
                x.get("distance", float("inf")),
                (md.get("source_path") or ""),
                md.get("chunk_index", -1),
            )

        # Deterministic ordering (important when distances tie).
        deduped.sort(key=_sort_key)
        return deduped
    
    def _expand_query(self, query: str) -> List[str]:
        """
        Expand query with synonyms and related terms
        
        Args:
            query: Original query
            
        Returns:
            List of expanded terms
        """
        expansions = []
        query_lower = query.lower()
        
        # Product-related expansions
        product_expansions = {
            'products': ['product categories', 'services', 'offerings', 'solutions', 'features'],
            'payment gateway': ['pg', 'payment processing', 'checkout', 'payment collection'],
            'payouts': ['transfers', 'disbursements', 'payments out', 'money transfer'],
            'verification': ['kyc', 'identity verification', 'compliance', 'onboarding'],
            'connected banking': ['bank integration', 'bank account', 'banking'],
            'reconciliation': ['reconcile', 'matching', 'matching payments', 'payment matching'],
            'invoice': ['invoicing', 'bills', 'billing'],
            'api': ['apis', 'api integration', 'developer api', 'rest api'],
            'integration': ['integrate', 'connect', 'setup', 'configure'],
            'how to': ['how do i', 'how can i', 'steps to', 'guide to'],
            'what is': ['what are', 'explain', 'describe', 'tell me about'],
            'difference': ['compare', 'vs', 'versus', 'different from']
        }
        
        # Check for matches and add expansions
        for key, synonyms in product_expansions.items():
            if key in query_lower:
                expansions.extend(synonyms)
        
        # Platform-specific expansions
        if 'zwitch' in query_lower:
            expansions.extend(['zwitch api', 'zwitch platform', 'zwitch services'])
        if 'open money' in query_lower or 'openmoney' in query_lower:
            expansions.extend(['open money platform', 'open money dashboard', 'open money app'])
        
        return expansions
