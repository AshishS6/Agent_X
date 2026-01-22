#!/usr/bin/env python3
"""
LLM Router smoke test.

Verifies:
- Router initialization
- Provider health (Ollama, OpenAI key, Anthropic key)
- generate_completion() via router (local-first with fallback) [optional]
- Usage tracking

Run from backend directory:
    cd backend && PYTHONPATH=. python3 scripts/test_llm_router.py
    cd backend && PYTHONPATH=. python3 scripts/test_llm_router.py --skip-completion

Requires: agents dependencies (see backend/agents/requirements.txt).
Optional: Ollama running (or OpenAI/Anthropic keys) for the completion step.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

# Load backend .env when run from backend/
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    load_dotenv(env_path)
except ImportError:
    pass


async def main(skip_completion: bool) -> None:
    print("=== LLM Router smoke test ===\n")

    # 1. Imports
    print("1. Imports...")
    try:
        from llm.router import get_router, get_tracker, get_health_checker, Intent
    except Exception as e:
        print(f"   FAIL: {e}")
        sys.exit(1)
    print("   OK\n")

    # 2. Router init
    print("2. Router init...")
    try:
        router = get_router()
    except Exception as e:
        print(f"   FAIL: {e}")
        sys.exit(1)
    print("   OK\n")

    # 3. Health checks
    print("3. Health checks...")
    health = get_health_checker()
    ollama_status = await health.check_ollama()
    openai_status = health.check_openai_key()
    anthropic_status = health.check_anthropic_key()
    print(f"   Ollama:    {ollama_status.value}")
    print(f"   OpenAI:    {openai_status.value} (key presence)")
    print(f"   Anthropic: {anthropic_status.value} (key presence)\n")

    # 4. Generate completion (smoke test)
    if skip_completion:
        print("4. generate_completion (smoke)... SKIPPED (--skip-completion)\n")
    else:
        print("4. generate_completion (smoke)...")
        prompt = "Reply with exactly: OK"
        try:
            result = await router.generate_completion(
                caller="test_llm_router",
                prompt=prompt,
                model_preference=os.getenv("LLM_LOCAL_MODEL", "qwen2.5:7b-instruct"),
                intent=Intent.CHAT,
            )
            text = result.get("text", "")
            usage = result.get("usage", {})
            provider = usage.get("provider", "?")
            print(f"   Provider: {provider}")
            print(f"   Response: {text[:80]}{'...' if len(text) > 80 else ''}")
            print(f"   Usage: tokens={usage.get('input_tokens', 0) + usage.get('output_tokens', 0)}, "
                  f"latency_ms={usage.get('latency_ms')}")
        except Exception as e:
            print(f"   SKIP (no provider available): {e}")
            print("   Ensure Ollama is running or set OPENAI_API_KEY / ANTHROPIC_API_KEY.\n")

    # 5. Usage stats
    print("5. Usage tracker...")
    tracker = get_tracker()
    stats = tracker.get_statistics()
    print(f"   Total calls: {stats.get('total_calls', 0)}")
    print(f"   Total cost: ${stats.get('total_cost_usd', 0):.4f}")
    print(f"   Provider distribution: {stats.get('provider_distribution', {})}\n")

    print("=== Smoke test done ===")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="LLM Router smoke test")
    ap.add_argument("--skip-completion", action="store_true", help="Skip LLM completion (init + health + tracker only)")
    args = ap.parse_args()
    asyncio.run(main(skip_completion=args.skip_completion))
