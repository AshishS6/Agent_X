#!/usr/bin/env python3
"""
Ad-hoc RAG evaluation harness (baseline + regression).

Goals:
- Run the same questions N times
- Capture retrieval metadata + final assistant answers
- Compute quantitative signals:
  - answer stability
  - vendor purity
  - layer purity
  - unsupported-claim proxy (ungrounded sentence rate)
  - explicit uncertainty rate
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


_BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))


def _now_ts() -> str:
    return time.strftime("%Y%m%d-%H%M%S")


def _normalize_text(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def _split_sentences(text: str) -> List[str]:
    # Lightweight splitter for our proxy metrics (good enough for dashboards).
    text = (text or "").strip()
    if not text:
        return []
    # Split on newlines and sentence punctuation.
    parts = re.split(r"(?:\n+|(?<=[\.\!\?])\s+)", text)
    return [p.strip() for p in parts if p and p.strip()]


_UNCERTAINTY_PATTERNS = [
    r"\b(i don'?t know)\b",
    r"\b(not sure)\b",
    r"\b(unclear)\b",
    r"\b(insufficient)\b",
    r"\b(not available in (the )?knowledge base)\b",
    r"\b(not in (the )?knowledge base)\b",
    r"\b(kb is (inconsistent|conflicting))\b",
    r"\b(conflict(?:ing)? information)\b",
]


def _has_explicit_uncertainty(answer: str) -> bool:
    a = (answer or "").lower()
    return any(re.search(p, a) for p in _UNCERTAINTY_PATTERNS)


def _tokenize_for_grounding(text: str) -> List[str]:
    # Keep only alphabetic tokens (avoid counting numbers as grounded).
    toks = re.findall(r"[A-Za-z][A-Za-z\-]{2,}", text or "")
    return [t.lower() for t in toks]


def _unsupported_sentence_count(answer: str, context: str) -> Tuple[int, int]:
    """
    Proxy: count sentences with *no* token overlap against context.
    This is not perfect, but it reliably flags "free-form" drift.
    """
    ctx = (context or "").lower()
    sentences = _split_sentences(answer)
    if not sentences:
        return (0, 0)

    unsupported = 0
    for s in sentences:
        toks = _tokenize_for_grounding(s)
        if not toks:
            # Short/empty sentence: ignore.
            continue
        if not any(t in ctx for t in toks[:20]):  # cap per sentence for speed
            unsupported += 1
    return (unsupported, len(sentences))


def _majority_fraction(items: List[str]) -> float:
    if not items:
        return 0.0
    counts: Dict[str, int] = {}
    for it in items:
        counts[it] = counts.get(it, 0) + 1
    return max(counts.values()) / len(items)


@dataclass
class Case:
    id: str
    query: str
    expected_vendor: str = "unknown"
    expected_layers: Optional[List[str]] = None


async def _retrieve_debug(
    query: str,
    knowledge_base: str,
    n_results: int,
    assistant: str,
) -> List[Dict[str, Any]]:
    # Import lazily so the harness can be used as a standalone script.
    from knowledge.vector_store import ChromaDBStore, OllamaEmbeddingClient
    from knowledge.retrieval.retriever import RAGRetriever

    embedding_client = OllamaEmbeddingClient()
    vector_store = ChromaDBStore()
    retriever = RAGRetriever(embedding_client, vector_store)

    vendor = None
    layer = None
    boost_layers = None
    effective_n_results = n_results

    # Mirror the assistant's retrieval discipline (important for vendor/layer purity metrics).
    if assistant == "fintech":
        try:
            from assistants.runner import _classify_fintech_query

            cls = _classify_fintech_query(query)
            vendor = cls.get("vendor")
            layer = cls.get("layer")
            boost_layers = cls.get("boost_layers")
            effective_n_results = int(cls.get("n_results", n_results))
        except Exception:
            # If classification import fails, fall back to raw retrieval.
            pass

    try:
        return await retriever.retrieve(
            query=query,
            knowledge_base=knowledge_base,
            n_results=effective_n_results,
            include_metadata=True,
            vendor=vendor,
            layer=layer,
            boost_layers=boost_layers,
            expand_query=True,
        )
    finally:
        await embedding_client.close()


async def _run_assistant_once(query: str, assistant: str, knowledge_base: str) -> Dict[str, Any]:
    from assistants.runner import run_assistant

    return await run_assistant(
        message=query,
        assistant_name=assistant,
        knowledge_base=knowledge_base,
    )


async def evaluate(
    cases: List[Case],
    assistant: str,
    knowledge_base: str,
    runs: int,
    n_results: int,
    out_dir: Path,
    retrieval_only: bool,
) -> Dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_path = out_dir / f"raw_{_now_ts()}.jsonl"

    report: Dict[str, Any] = {
        "meta": {
            "assistant": assistant,
            "knowledge_base": knowledge_base,
            "runs": runs,
            "n_results": n_results,
            "retrieval_only": retrieval_only,
            "ts": _now_ts(),
        },
        "cases": [],
    }

    with raw_path.open("w", encoding="utf-8") as raw_f:
        for case in cases:
            answers_norm: List[str] = []
            vendor_purity_runs: List[float] = []
            layer_purity_runs: List[float] = []
            unsupported_rates: List[float] = []
            uncertainty_flags: List[int] = []

            for i in range(runs):
                retrieval = await _retrieve_debug(case.query, knowledge_base, n_results, assistant)
                retrieved_context = "\n\n".join([r.get("text", "") for r in retrieval])

                # Vendor/layer purity from metadata (retrieval stage).
                vendors = [((r.get("metadata") or {}).get("vendor") or "").lower() for r in retrieval]
                layers = [((r.get("metadata") or {}).get("layer") or "").lower() for r in retrieval]

                if case.expected_vendor and case.expected_vendor != "unknown":
                    denom = max(1, len(vendors))
                    vendor_purity = sum(1 for v in vendors if v == case.expected_vendor) / denom
                else:
                    vendor_purity = 1.0  # not applicable

                if case.expected_layers:
                    expected = {l.lower() for l in case.expected_layers}
                    denom = max(1, len(layers))
                    layer_purity = sum(1 for l in layers if l in expected) / denom
                else:
                    layer_purity = 1.0  # not applicable

                vendor_purity_runs.append(vendor_purity)
                layer_purity_runs.append(layer_purity)

                if retrieval_only:
                    answer = ""
                    citations: List[str] = []
                else:
                    resp = await _run_assistant_once(case.query, assistant, knowledge_base)
                    answer = resp.get("answer", "") or ""
                    citations = resp.get("citations", []) or []

                answers_norm.append(_normalize_text(answer))

                # Unsupported claims proxy.
                unsupported, total_sents = _unsupported_sentence_count(answer, retrieved_context)
                unsupported_rate = (unsupported / total_sents) if total_sents else 0.0
                unsupported_rates.append(unsupported_rate)

                uncertainty_flags.append(1 if _has_explicit_uncertainty(answer) else 0)

                raw_f.write(
                    json.dumps(
                        {
                            "case_id": case.id,
                            "run": i,
                            "query": case.query,
                            "expected_vendor": case.expected_vendor,
                            "expected_layers": case.expected_layers,
                            "retrieval": [
                                {
                                    "distance": r.get("distance"),
                                    "metadata": r.get("metadata"),
                                }
                                for r in retrieval
                            ],
                            "answer": answer,
                            "citations": citations,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )

            case_summary = {
                "id": case.id,
                "query": case.query,
                "expected_vendor": case.expected_vendor,
                "expected_layers": case.expected_layers,
                "answer_stability": _majority_fraction(answers_norm),
                "vendor_purity_mean": statistics.mean(vendor_purity_runs) if vendor_purity_runs else None,
                "layer_purity_mean": statistics.mean(layer_purity_runs) if layer_purity_runs else None,
                "unsupported_rate_mean": statistics.mean(unsupported_rates) if unsupported_rates else None,
                "uncertainty_rate": (sum(uncertainty_flags) / runs) if runs else None,
            }
            report["cases"].append(case_summary)

    # Aggregate overview.
    report["aggregate"] = {
        "avg_answer_stability": statistics.mean([c["answer_stability"] for c in report["cases"]]) if report["cases"] else None,
        "avg_vendor_purity_mean": statistics.mean([c["vendor_purity_mean"] for c in report["cases"] if c["vendor_purity_mean"] is not None]) if report["cases"] else None,
        "avg_layer_purity_mean": statistics.mean([c["layer_purity_mean"] for c in report["cases"] if c["layer_purity_mean"] is not None]) if report["cases"] else None,
        "avg_unsupported_rate_mean": statistics.mean([c["unsupported_rate_mean"] for c in report["cases"] if c["unsupported_rate_mean"] is not None]) if report["cases"] else None,
        "avg_uncertainty_rate": statistics.mean([c["uncertainty_rate"] for c in report["cases"] if c["uncertainty_rate"] is not None]) if report["cases"] else None,
        "raw_jsonl": str(raw_path),
    }

    return report


def _load_cases(path: Path) -> List[Case]:
    data = json.loads(path.read_text(encoding="utf-8"))
    cases: List[Case] = []
    for item in data:
        cases.append(
            Case(
                id=item["id"],
                query=item["query"],
                expected_vendor=item.get("expected_vendor", "unknown"),
                expected_layers=item.get("expected_layers"),
            )
        )
    return cases


def main() -> None:
    parser = argparse.ArgumentParser(description="Ad-hoc KB evaluation harness")
    parser.add_argument("--cases", default="backend/knowledge/eval_cases.json", help="Path to eval cases JSON")
    parser.add_argument("--assistant", default="fintech", help="Assistant name (default: fintech)")
    parser.add_argument("--kb", default="fintech", help="Knowledge base collection (default: fintech)")
    parser.add_argument("--runs", type=int, default=5, help="Runs per case (default: 5)")
    parser.add_argument("--n-results", type=int, default=10, help="Retrieved chunks per run (default: 10)")
    parser.add_argument("--out-dir", default="backend/knowledge/eval_reports", help="Output directory")
    parser.add_argument("--retrieval-only", action="store_true", help="Skip LLM answers; only measure retrieval")
    args = parser.parse_args()

    cases = _load_cases(Path(args.cases))
    out_dir = Path(args.out_dir)

    report = asyncio.run(
        evaluate(
            cases=cases,
            assistant=args.assistant,
            knowledge_base=args.kb,
            runs=args.runs,
            n_results=args.n_results,
            out_dir=out_dir,
            retrieval_only=args.retrieval_only,
        )
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / f"report_{_now_ts()}.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps({"report": str(report_path), "raw_jsonl": report["aggregate"]["raw_jsonl"]}, indent=2))


if __name__ == "__main__":
    main()

