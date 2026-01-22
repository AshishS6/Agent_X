#!/usr/bin/env python3
"""
Assistant Runner - CLI entry point for assistants

This is a minimal CLI tool that:
1. Loads assistant config
2. Calls KnowledgePipeline for RAG
3. Builds prompt using prompt_builder
4. Calls LLM Router for LLM response (local-first with cloud fallback)
5. Returns structured JSON

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
from typing import Dict, Any

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
from assistants.prompt_builder import build_fintech_prompt, build_generic_prompt

# Import knowledge and LLM modules
from knowledge.vector_store import ChromaDBStore, OllamaEmbeddingClient
from knowledge.retrieval import KnowledgePipeline
from llm.router import LLMRouter, Intent, get_router


# Assistant registry
ASSISTANTS = {
    "fintech": FintechAssistant,
    "code": CodeAssistant,
    "general": GeneralAssistant,
}


async def run_assistant(message: str, assistant_name: str, knowledge_base: str) -> Dict[str, Any]:
    """
    Run an assistant with RAG and LLM
    
    Args:
        message: User message
        assistant_name: Name of assistant (e.g., "fintech")
        knowledge_base: Knowledge base name (e.g., "fintech")
    
    Returns:
        Dictionary with answer, citations, and metadata
    """
    # Load assistant config
    if assistant_name not in ASSISTANTS:
        raise ValueError(f"Unknown assistant: {assistant_name}")
    
    assistant_class = ASSISTANTS[assistant_name]
    config = assistant_class.get_config()
    
    logger.info(f"Running assistant: {assistant_name} with model preference: {config.model}")
    
    # Initialize components
    embedding_client = OllamaEmbeddingClient()
    vector_store = ChromaDBStore()
    knowledge_pipeline = KnowledgePipeline(embedding_client, vector_store)
    
    # Initialize LLM Router (handles provider selection and fallback)
    router = get_router()
    
    try:
        # Step 1: Get RAG context if enabled
        context_text = ""
        public_urls = []
        
        if config.use_rag and config.knowledge_base:
            logger.info(f"Retrieving context from knowledge base: {config.knowledge_base}")
            rag_result = await knowledge_pipeline.query(
                user_query=message,
                knowledge_base=config.knowledge_base,
                n_results=10
            )
            context_text = rag_result.get("context", "")
            public_urls = rag_result.get("public_urls", [])
            logger.info(f"Retrieved context length: {len(context_text)} chars, URLs: {len(public_urls)}")
        else:
            logger.info("RAG disabled for this assistant")
        
        # Step 2: Build prompt
        if config.use_rag and context_text:
            if assistant_name == "fintech":
                prompt = build_fintech_prompt({
                    "context": context_text,
                    "public_urls": public_urls,
                    "query": message
                })
            else:
                prompt = build_generic_prompt({
                    "context": context_text,
                    "public_urls": public_urls,
                    "query": message
                })
        else:
            # No RAG - use direct prompt
            prompt = f"{config.system_prompt}\n\nQuestion: {message}\n\nAnswer:"
        
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
        
        # Build full prompt
        if config.use_rag and context_text:
            # RAG prompt already includes system instructions
            full_prompt = prompt
        else:
            # No RAG - combine system prompt and user message
            full_prompt = f"{config.system_prompt}\n\nQuestion: {message}\n\nAnswer:"
        
        # Generate completion through router
        try:
            result = await router.generate_completion(
                caller=assistant_name,
                prompt=full_prompt,
                model_preference=config.model,  # Router will try to use this model
                intent=intent
            )
            
            response_text = result["text"]
            usage = result["usage"]
            provider = result["provider"]
            model_id = result["model_id"]
            
            logger.info(
                f"✅ LLM Response - Provider: {provider}, Model: {model_id}, "
                f"Response length: {len(response_text)} chars, "
                f"Tokens: {usage.get('input_tokens', 0)}+{usage.get('output_tokens', 0)}, "
                f"Cost: ${usage.get('estimated_cost_usd', 0):.6f}, "
                f"Latency: {usage.get('latency_ms', 0):.0f}ms"
            )
            
        except Exception as e:
            logger.error(f"LLM Router generate failed: {e}", exc_info=True)
            raise
        
        # Step 4: Return structured response (LOCKED CONTRACT)
        # This contract must match ChatResponse in Go handler
        return {
            "assistant": assistant_name,
            "answer": response_text,  # Required: markdown-formatted answer
            "citations": sorted(public_urls) if public_urls else [],  # Required: array (never null)
            "metadata": {
                "model": model_id.split(":", 1)[1] if ":" in model_id else model_id,  # Just model name for compatibility
                "provider": provider,
                "rag_used": config.use_rag and bool(context_text),
                "kb": config.knowledge_base if (config.use_rag and bool(context_text)) else "",
                "usage": usage  # Include usage metadata
            }
        }
    
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
        result = asyncio.run(run_assistant(message, assistant_name, knowledge_base))
        
        # Output JSON to stdout (ONLY JSON, no logs)
        # Ensure nothing else prints to stdout before this
        json_output = json.dumps(result, indent=2)
        print(json_output, flush=True)
        sys.exit(0)
    
    except Exception as e:
        logger.error(f"Error running assistant: {e}", exc_info=True)
        error_result = {
            "assistant": input_data.get("assistant", "unknown"),
            "answer": f"Error: {str(e)}",  # Always provide answer (even if error)
            "citations": [],  # Required: array (never null)
            "metadata": {
                "model": "",
                "provider": "ollama",
                "rag_used": False,
                "kb": "",
                "error": str(e)
            }
        }
        # Output error JSON to stdout (ONLY JSON, no logs)
        json_output = json.dumps(error_result, indent=2)
        print(json_output, flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
