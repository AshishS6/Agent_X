"""
Prompt builder utilities for assistants

Provides domain-specific prompt composition for assistants using RAG context.
This module handles the business logic that was previously in KnowledgePipeline.
"""

from typing import Dict, List, Optional, Any


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
    
    # Build citation instruction
    if public_urls:
        url_list = "\n".join([f"- {url}" for url in sorted(public_urls)])
        citation_instruction = f"\n\nWhen providing information, you may cite these public resources if relevant:\n{url_list}\n\nIMPORTANT: Do NOT cite internal file references, source numbers, or markdown file paths. Only cite the public URLs listed above (websites, documentation, dashboards) when relevant."
    else:
        citation_instruction = "\n\nIMPORTANT: Do NOT cite internal file references, source numbers, or markdown file paths. Only cite public URLs (websites, documentation, dashboards) if they are mentioned in the context and relevant to the answer."
    
    # If no context, return query as-is
    if not context:
        return user_query
    
    # Detect question type and add specific instructions (domain-specific logic)
    query_lower = user_query.lower()
    
    # Detect question type
    is_payment_gateway_question = any(phrase in query_lower for phrase in [
        'payment gateway', 'pg integration', 'layer.js', 'layer js', 
        'integrate payment', 'payment integration', 'checkout', 'payment page'
    ])
    
    is_payout_question = any(phrase in query_lower for phrase in [
        'payout', 'payout api', 'transfer api', 'send money', 'disburse',
        'beneficiary', 'transfer money', 'payout integration'
    ])
    
    is_zwitch_product_question = any(phrase in query_lower for phrase in [
        'what products', 'what are the products', 'list products', 
        'products does', 'products offered', 'products available'
    ]) and 'zwitch' in query_lower
    
    # Add specific instructions based on question type
    specific_instruction = ""
    
    if is_payment_gateway_question:
        specific_instruction = "\n\nCRITICAL: This question is about PAYMENT GATEWAY integration (collecting payments from customers). Focus ONLY on:\n- Layer.js integration\n- Create Payment Token API (POST /v1/pg/payment_token)\n- Payment collection, not payouts\n- Do NOT mention payout/transfer APIs unless specifically asked\n- Use the Layer.js documentation in the context"
    
    elif is_payout_question:
        specific_instruction = "\n\nCRITICAL: This question is about PAYOUT/TRANSFER API (sending money to beneficiaries). Focus ONLY on:\n- Transfers API (POST /v1/transfers)\n- Beneficiary management\n- Payouts, not payment collection\n- Do NOT mention payment gateway, Layer.js, or payment tokens unless specifically asked\n- Use the Transfers API documentation in the context"
    
    elif is_zwitch_product_question:
        specific_instruction = "\n\nIMPORTANT: This is a question about Zwitch products. You MUST list ALL 4 products: 1. Payment Gateway, 2. Payouts, 3. Zwitch Bill Connect, 4. Verification Suite. Do not mention only one product. Always provide the complete list of all 4 products."
    
    # Add instruction to focus on current question only
    focus_instruction = "\n\nIMPORTANT: Answer ONLY the current question asked. Do NOT mix concepts from previous questions in the conversation. If the question is about Payment Gateway, answer only about Payment Gateway. If the question is about Payouts/Transfers, answer only about Payouts/Transfers. Keep your answer focused and relevant to the specific question asked."
    
    return f"""Use the following context from the knowledge base to answer the CURRENT question. Answer ONLY what is asked - do not mix different concepts or APIs unless the question specifically asks for comparison.

Context:
{context}

Current Question: {user_query}{specific_instruction}{focus_instruction}{citation_instruction}"""


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
    
    # If no context, return query as-is
    if not context:
        return user_query
    
    return f"""Use the following context from the knowledge base to answer the question.

Context:
{context}

Question: {user_query}{citation_instruction}"""
