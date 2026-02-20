#!/usr/bin/env python3
"""
Assistant Runner - CLI entry point for assistants

This is a minimal CLI tool that:
1. Loads assistant config
2. Calls KnowledgePipeline for RAG
3. Builds prompt using prompt_builder
4. Calls LLM Router for LLM response (local-first with cloud fallback)
5. Streams structured JSON (NDJSON)

Usage:
    python runner.py --input '{"message": "...", "assistant": "fintech", "knowledge_base": "fintech"}'

All LLM calls go through the centralized LLM Router which handles:
- Local-first provider selection
- Automatic fallback to cloud if local unavailable
- Usage tracking (tokens, costs, latency)
"""

import sys
import json
import argparse
import logging
import asyncio
import re
from typing import Dict, Any, List, Optional, Tuple

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("Assistant.Runner")

# Import assistant modules
from assistants.fintech_assistant import FintechAssistant
from assistants.code_assistant import CodeAssistant
from assistants.general_assistant import GeneralAssistant
from assistants.prompt_builder import (
    build_fintech_prompt,
    build_generic_prompt,
    maybe_build_fintech_api_samples_answer,
)

# Import knowledge and LLM modules
from knowledge.vector_store import ChromaDBStore, get_embedding_client
from knowledge.retrieval import KnowledgePipeline
from llm.router import LLMRouter, Intent, get_router


# Assistant registry
ASSISTANTS = {
    "fintech": FintechAssistant,
    "code": CodeAssistant,
    "general": GeneralAssistant,
}


def _classify_fintech_query(message: str) -> Dict[str, Any]:
    """
    Rule-based query classification for retrieval discipline.

    Returns:
      - vendor: "openmoney" | "zwitch" | None (None means mixed/unknown)
      - intent: "explanatory" | "procedural" | "api" | "comparison"
      - layer: Optional[str] (hard filter when confidence is high)
      - boost_layers: List[str]
      - n_results: int
    """
    q = (message or "").strip()
    ql = q.lower()

    # Intent
    if any(k in ql for k in [" vs ", " versus ", "compare", "difference between", "difference b/w"]):
        intent = "comparison"
    elif any(k in ql for k in [" api", "endpoint", "webhook", "sdk", "curl", "post ", "get ", "/v1/"]):
        intent = "api"
    elif any(k in ql for k in ["how do i", "how to", "steps", "setup", "configure", "integrate", "implementation", "guide"]):
        intent = "procedural"
    else:
        intent = "explanatory"

    # Vendor
    mentions_open = ("open money" in ql) or ("openmoney" in ql) or ("open.money" in ql)
    mentions_zwitch = ("zwitch" in ql) or ("developers.zwitch" in ql) or ("zwitch.io" in ql)
    mentions_open_platform = bool(re.search(r"\bin\s+open\b", ql)) and not bool(
        re.search(r"\b(openai|open-source|open source|openapi)\b", ql)
    )

    # Strong hints: API-like queries almost always map to Zwitch in this KB.
    looks_like_api = intent == "api" or bool(re.search(r"\b(post|get|put|delete|patch)\b", ql)) or ("/v1/" in ql)

    vendor: Optional[str]
    if (mentions_open or mentions_open_platform) and not mentions_zwitch:
        vendor = "openmoney"
    elif mentions_zwitch and not mentions_open:
        vendor = "zwitch"
    elif looks_like_api and not mentions_open:
        vendor = "zwitch"
    else:
        vendor = None  # mixed/unknown

    # Layer inference (soft by default; hard-filter only for high-confidence cases).
    hard_layer: Optional[str] = None
    boost_layers: List[str] = []

    if vendor == "zwitch":
        # Default Zwitch hierarchy boost.
        boost_layers = ["states", "flows", "api", "concepts", "company", "faq", "best_practices"]
        if intent == "api":
            hard_layer = "api"
            boost_layers = ["api", "states", "flows", "best_practices"]
        elif any(k in ql for k in ["status", "lifecycle", "state"]):
            hard_layer = "states"
            boost_layers = ["states", "flows", "api", "concepts"]
        elif any(k in ql for k in ["webhook", "happy path", "failure", "flow"]):
            hard_layer = "flows"
            boost_layers = ["flows", "states", "api", "concepts"]

    elif vendor == "openmoney":
        # Default Open Money hierarchy boost.
        boost_layers = ["principles", "states", "workflows", "concepts", "modules", "products", "company", "faq", "risks", "data_semantics"]
        if any(k in ql for k in ["status", "success", "failed", "pending", "settlement"]):
            boost_layers = ["states", "principles", "risks", "workflows", "concepts", "faq"]
        elif any(k in ql for k in ["reconcile", "reconciliation", "sync", "accounting", "tally", "zoho"]):
            boost_layers = ["workflows", "principles", "modules", "concepts", "faq"]
        elif any(k in ql for k in ["product", "products", "modules", "features", "offerings"]):
            boost_layers = ["products", "modules", "concepts", "faq", "company"]
        elif any(k in ql for k in ["invoice", "payment link", "collect", "receivable", "payable", "bill", "vendor payment"]):
            boost_layers = ["workflows", "modules", "products", "concepts", "faq", "principles"]

        # Never hard-filter to "api" for openmoney (KB should not treat it as API provider).
        if looks_like_api:
            boost_layers = ["concepts", "principles", "faq"]

    else:
        # Mixed/unknown: keep broad and boost overview-ish layers.
        boost_layers = ["concepts", "products", "company", "faq", "principles", "states", "workflows", "api"]

    # Retrieval size: larger for comparison and "what is" identity questions.
    if intent == "comparison":
        n_results = 14
    elif any(k in ql for k in ["what is zwitch", "whats zwitch", "what's zwitch"]):
        n_results = 24
    elif any(k in ql for k in ["what is", "whats", "what's"]):
        n_results = 16
    else:
        n_results = 10

    return {
        "vendor": vendor,
        "intent": intent,
        "layer": hard_layer,
        "boost_layers": boost_layers,
        "n_results": n_results,
    }


async def run_assistant(message: str, assistant_name: str, knowledge_base: str):
    """
    Run an assistant with RAG and LLM, data to stdout (NDJSON).
    """
    # Load assistant config
    if assistant_name not in ASSISTANTS:
        raise ValueError(f"Unknown assistant: {assistant_name}")
    
    assistant_class = ASSISTANTS[assistant_name]
    config = assistant_class.get_config()
    
    logger.info(f"Running assistant: {assistant_name} with model preference: {config.model}")
    
    # Initialize components
    embedding_client = get_embedding_client()
    vector_store = ChromaDBStore()
    knowledge_pipeline = KnowledgePipeline(embedding_client, vector_store)
    
    # Initialize LLM Router (handles provider selection and fallback)
    router = get_router()
    
    try:
        # Step 1: Get RAG context if enabled
        context_text = ""
        public_urls = []
        cls: Dict[str, Any] = {}
        
        if config.use_rag and config.knowledge_base:
            logger.info(f"Retrieving context from knowledge base: {config.knowledge_base}")
            vendor = None
            layer = None
            boost_layers = None
            n_results = 10
            

            if assistant_name == "fintech":
                cls = _classify_fintech_query(message)
                vendor = cls.get("vendor")
                layer = cls.get("layer")
                boost_layers = cls.get("boost_layers")
                n_results = int(cls.get("n_results", 10))

            rag_result = await knowledge_pipeline.query(
                user_query=message,
                knowledge_base=config.knowledge_base,
                n_results=n_results,
                vendor=vendor,
                layer=layer,
                boost_layers=boost_layers,
            )
            context_text = rag_result.get("context", "")
            public_urls = rag_result.get("public_urls", [])
            logger.info(f"Retrieved context length: {len(context_text)} chars, URLs: {len(public_urls)}")
        else:
            logger.info("RAG disabled for this assistant")
            
        # Emit initial metadata
        print(json.dumps({
            "type": "meta",
            "assistant": assistant_name,
            "citations": sorted(public_urls) if public_urls else [],
            "rag_used": config.use_rag and bool(context_text),
            "kb": config.knowledge_base if (config.use_rag and bool(context_text)) else ""
        }), flush=True)

        # Step 2: Build the user prompt body (system prompt is always applied separately)
        # Special-case: if the user asks for API sample request/response bodies, extract them
        # deterministically from retrieved context to prevent schema hallucination/reformatting.
        if assistant_name == "fintech" and config.use_rag and context_text:
            extracted = maybe_build_fintech_api_samples_answer(
                context=context_text,
                user_query=message,
                vendor=cls.get("vendor"),
            )
            if extracted:
                # Direct answer extraction (no LLM)
                print(json.dumps({
                    "type": "content",
                    "content": extracted
                }), flush=True)
                
                # Emit dummy usage for compatibility
                print(json.dumps({
                    "type": "control",
                    "event": "usage",
                    "data": {
                         "provider": "kb_extract",
                         "model_id": "kb_extract",
                         "input_tokens": 0,
                         "output_tokens": 0,
                         "latency_ms": 0,
                         "cost": 0
                    }
                }), flush=True)
                return

        if config.use_rag and context_text:
            if assistant_name == "fintech":
                prompt_body = build_fintech_prompt({
                    "context": context_text,
                    "public_urls": public_urls,
                    "query": message,
                    "vendor": cls.get("vendor") if assistant_name == "fintech" else None,
                    "intent": cls.get("intent") if assistant_name == "fintech" else None,
                    "layer": cls.get("layer") if assistant_name == "fintech" else None,
                })
            else:
                prompt_body = build_generic_prompt({
                    "context": context_text,
                    "public_urls": public_urls,
                    "query": message
                })
        else:
            # No RAG - just ask the question.
            prompt_body = f"Question: {message}\n\nAnswer:"
        
        # Step 3: Call LLM Router (local-first with cloud fallback)
        # Router will:
        # 1. Try Ollama first (local)
        # 2. Fallback to OpenAI/Anthropic if Ollama unavailable
        # 3. Track usage (tokens, costs, latency)
        
        # Determine intent based on assistant type
        intent = Intent.CHAT
        if assistant_name == "code":
            intent = Intent.CODE
        elif assistant_name == "fintech":
            intent = Intent.ANALYSIS
        
        logger.info(f"Calling LLM Router - Assistant: {assistant_name}, Intent: {intent.value}, Model preference: {config.model}")
        
        # Build full prompt (CRITICAL): system prompt must always be applied.
        full_prompt = f"{config.system_prompt}\n\n{prompt_body}"
        
        # Stream response
        async for chunk in router.stream_completion(
            caller=assistant_name,
            prompt=full_prompt,
            model_preference=config.model,  # Router will try to use this model
            intent=intent
        ):
            print(json.dumps(chunk), flush=True)
            
    finally:
        # Cleanup
        await embedding_client.close()


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description="Assistant Runner")
    parser.add_argument("--input", required=True, help="JSON input string")
    
    args = parser.parse_args()
    
    try:
        # Parse input
        input_data = json.loads(args.input)
        message = input_data.get("message")
        assistant_name = input_data.get("assistant", "general")
        knowledge_base = input_data.get("knowledge_base", assistant_name)
        
        if not message:
            raise ValueError("Missing required field: message")
        
        # Run assistant
        asyncio.run(run_assistant(message, assistant_name, knowledge_base))
        sys.exit(0)
    
    except Exception as e:
        logger.error(f"Error running assistant: {e}", exc_info=True)
        error_result = {
            "type": "error",
            "error": str(e)
        }
        # Output error JSON to stdout (ONLY JSON, no logs)
        print(json.dumps(error_result), flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
