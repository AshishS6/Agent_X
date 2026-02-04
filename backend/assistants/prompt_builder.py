"""
Prompt builder utilities for assistants

Provides domain-specific prompt composition for assistants using RAG context.
This module handles the business logic that was previously in KnowledgePipeline.
"""

import re
from typing import Dict, List, Optional, Any, Tuple


_API_SAMPLE_PATTERNS = [
    "sample request",
    "sample response",
    "request body",
    "response body",
    "example request",
    "example response",
    "request/response",
    "request response",
    "request and response",
    "request & response",
]


def maybe_build_fintech_api_samples_answer(
    *,
    context: str,
    user_query: str,
    vendor: Optional[str],
) -> Optional[str]:
    """
    Deterministically extract example request/response blocks from retrieved context.

    This is used to prevent the LLM from reformatting or hallucinating API schemas when
    the user explicitly asks for sample request/response bodies.
    """
    ql = (user_query or "").lower()
    if not any(p in ql for p in _API_SAMPLE_PATTERNS):
        return None

    # Open Money is platform-first; do not synthesize API samples.
    if (vendor or "").lower() == "openmoney":
        return (
            "The retrieved context does not confirm an Open Money developer API surface (endpoints, webhooks, or request/response schemas). "
            "If you need workflow guidance, I can describe the dashboard/mobile app steps based on what’s in the KB."
        )

    ctx = context or ""
    ctxl = ctx.lower()
    if not ctx.strip():
        return "KB insufficient: no retrieved context available to extract sample request/response."

    wants_balance = any(k in ql for k in ["/balance", "account balance", "get account balance"])
    wants_statement = any(k in ql for k in ["/statement", "account statement", "get account statement"])

    # Extract fenced code blocks.
    blocks: List[Tuple[str, str]] = []
    for m in re.finditer(r"```([a-zA-Z0-9_+-]+)\n([\s\S]*?)\n```", ctx):
        lang = (m.group(1) or "").strip().lower()
        body = m.group(2) or ""
        blocks.append((lang, body))

    json_blocks = [(lang, body) for (lang, body) in blocks if lang == "json"]
    req_blocks = [(lang, body) for (lang, body) in blocks if lang in {"js", "javascript", "python"}]

    # Prefer request examples that actually call the endpoint mentioned.
    if wants_balance:
        req_blocks = [b for b in req_blocks if "/balance" in b[1].lower()] or req_blocks
        json_blocks = [b for b in json_blocks if "balance" in b[1].lower()] or json_blocks
    if wants_statement:
        req_blocks = [b for b in req_blocks if "/statement" in b[1].lower()] or req_blocks
        json_blocks = [b for b in json_blocks if "transactions" in b[1].lower()] or json_blocks

    req = req_blocks[0] if req_blocks else None
    resp = json_blocks[0] if json_blocks else None

    if not req and not resp:
        return "KB insufficient: the retrieved context does not include a sample request or a response body to copy verbatim."

    parts: List[str] = []
    if req:
        parts.append("### Sample Request\n\n```" + req[0] + "\n" + req[1] + "\n```")
    else:
        parts.append("### Sample Request\n\nKB insufficient: request example not provided in the retrieved context.")

    if resp:
        parts.append("### Sample Response\n\n```json\n" + resp[1] + "\n```")
    else:
        parts.append("### Sample Response\n\nKB insufficient: response body example not provided in the retrieved context.")

    return "\n\n".join(parts)


def build_fintech_prompt(rag_result: Dict[str, Any]) -> str:
    """
    Build a fintech-specific prompt from RAG results
    
    This function applies domain-specific instructions for fintech questions,
    including payment gateway, payout, and product question detection.
    
    Args:
        rag_result: Dictionary from KnowledgePipeline.query() with:
            - "context": str
            - "public_urls": List[str]
            - "query": str
    
    Returns:
        Formatted prompt string with context and domain-specific instructions
    """
    context = rag_result.get("context", "")
    public_urls = rag_result.get("public_urls", [])
    user_query = rag_result.get("query", "")
    vendor = rag_result.get("vendor", None)
    intent = rag_result.get("intent", None)
    
    # Build citation instruction
    if public_urls:
        url_list = "\n".join([f"- {url}" for url in sorted(public_urls)])
        citation_instruction = f"\n\nWhen providing information, you may cite these public resources if relevant:\n{url_list}\n\nIMPORTANT: Do NOT cite internal file references, source numbers, or markdown file paths. Only cite the public URLs listed above (websites, documentation, dashboards) when relevant."
    else:
        citation_instruction = "\n\nIMPORTANT: Do NOT cite internal file references, source numbers, or markdown file paths. Only cite public URLs (websites, documentation, dashboards) if they are mentioned in the context and relevant to the answer."
    
    # If no context, just ask the question (system prompt carries the contract).
    if not context:
        return f"Question: {user_query}\n\nAnswer:"
    
    # Detect question type and add specific instructions (domain-specific logic)
    query_lower = user_query.lower()
    
    # Detect question type
    #
    # IMPORTANT: Do not apply Zwitch-only integration focus to Open Money questions.
    # Open Money is platform-first; "integration" guidance is generally Zwitch API territory.
    is_payment_gateway_question = (vendor in [None, "zwitch"]) and any(phrase in query_lower for phrase in [
        'payment gateway', 'pg integration', 'layer.js', 'layer js',
        'integrate payment', 'payment integration', 'checkout', 'payment page'
    ])

    is_payout_question = (vendor in [None, "zwitch"]) and any(phrase in query_lower for phrase in [
        'payout', 'payout api', 'transfer api', 'send money', 'disburse',
        'beneficiary', 'transfer money', 'payout integration'
    ])
    
    is_zwitch_product_question = any(phrase in query_lower for phrase in [
        'what products', 'what are the products', 'list products', 
        'products does', 'products offered', 'products available'
    ]) and 'zwitch' in query_lower

    is_what_is_zwitch = any(phrase in query_lower for phrase in [
        "what is zwitch", "whats zwitch", "what's zwitch"
    ])
    
    # Add specific instructions based on question type (no hardcoded facts).
    specific_instruction = ""

    if vendor == "openmoney":
        specific_instruction += (
            "\n\nOpen Money (IMPORTANT): Treat Open Money as a dashboard/mobile app platform. "
            "Do NOT mention Open Money APIs/endpoints/webhooks/SDKs or “API documentation” unless the retrieved context explicitly includes them. "
            "If the user asks for API request/response schemas and they are not in the context, say the KB does not confirm an Open Money developer API surface and suggest the platform workflows instead."
        )
    
    if is_payment_gateway_question:
        specific_instruction += "\n\nFocus: PAYMENT GATEWAY integration (collecting payments). Use ONLY what appears in the retrieved context. If the context does not include the exact steps/endpoints, say what’s missing."
    
    elif is_payout_question:
        specific_instruction += "\n\nFocus: PAYOUT/TRANSFER integration (sending money). Use ONLY what appears in the retrieved context. If the context does not include the exact steps/endpoints/fields, say what’s missing."
    
    elif is_zwitch_product_question:
        specific_instruction += "\n\nFocus: Zwitch products. List ONLY the products explicitly present in the retrieved context. If the context is incomplete, say so instead of guessing."

    elif is_what_is_zwitch:
        specific_instruction += "\n\nFocus: Define what Zwitch is (1-2 sentences). If the retrieved context includes Zwitch's main product categories, list them as a short bulleted list. Do not invent categories that are not present in the context."

    # API sample / schema questions: enforce exact copying, no invented JSON.
    is_api_sample_question = any(p in query_lower for p in [
        "sample request", "sample response", "request body", "response body",
        "example request", "example response", "request/response", "request response"
    ]) or (intent == "api")
    if is_api_sample_question:
        specific_instruction += (
            "\n\nAPI EXAMPLES (STRICT): If the retrieved context contains example requests/responses or JSON blocks, copy them exactly as shown. "
            "For “sample response”, provide the HTTP response body (e.g., the JSON object), not client-side parsing/logging code. "
            "Do NOT invent fields, headers, or JSON schemas, and do NOT reformat examples into a different style (e.g., don’t convert fetch() examples into raw HTTP/curl unless curl/HTTP is shown in the context). "
            "Do NOT rename variables, change formatting, or modify example values (copy-paste verbatim). "
            "Do NOT output an ```http``` or ```bash``` example unless the retrieved context contains an example in that same format. "
            "If the context does not include an example request or response body, say which one is missing."
        )
    
    # Add instruction to focus on current question only
    focus_instruction = "\n\nIMPORTANT: Answer ONLY the current question asked. Do NOT mix concepts from previous questions in the conversation. If the question is about Payment Gateway, answer only about Payment Gateway. If the question is about Payouts/Transfers, answer only about Payouts/Transfers. Keep your answer focused and relevant to the specific question asked."
    
    return f"""Use the retrieved context below to answer the CURRENT question.

=== RETRIEVED CONTEXT (verbatim) ===
{context}
=== END RETRIEVED CONTEXT ===

Current Question: {user_query}{specific_instruction}{focus_instruction}{citation_instruction}

Answer:"""


def build_generic_prompt(rag_result: Dict[str, Any]) -> str:
    """
    Build a generic prompt from RAG results (no domain-specific logic)
    
    Args:
        rag_result: Dictionary from KnowledgePipeline.query() with:
            - "context": str
            - "public_urls": List[str]
            - "query": str
    
    Returns:
        Formatted prompt string with context
    """
    context = rag_result.get("context", "")
    public_urls = rag_result.get("public_urls", [])
    user_query = rag_result.get("query", "")
    
    # Build citation instruction
    if public_urls:
        url_list = "\n".join([f"- {url}" for url in sorted(public_urls)])
        citation_instruction = f"\n\nWhen providing information, you may cite these public resources if relevant:\n{url_list}\n\nIMPORTANT: Do NOT cite internal file references, source numbers, or markdown file paths. Only cite the public URLs listed above (websites, documentation, dashboards) when relevant."
    else:
        citation_instruction = "\n\nIMPORTANT: Do NOT cite internal file references, source numbers, or markdown file paths. Only cite public URLs (websites, documentation, dashboards) if they are mentioned in the context and relevant to the answer."
    
    # If no context, just ask the question (system prompt carries the contract).
    if not context:
        return f"Question: {user_query}\n\nAnswer:"
    
    return f"""Use the retrieved context below to answer the question.

=== RETRIEVED CONTEXT (verbatim) ===
{context}
=== END RETRIEVED CONTEXT ===

Question: {user_query}{citation_instruction}

Answer:"""
