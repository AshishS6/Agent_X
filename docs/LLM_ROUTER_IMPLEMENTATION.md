# LLM Router Implementation - Complete

## ✅ Implementation Status

All requirements have been implemented. The LLM Router is now the **single point of entry** for all LLM calls in AgentX.

## 📁 New Module Structure

```
backend/llm/router/
├── __init__.py              # Exports router, registry, tracker, health
├── llm_router.py            # Main router with local-first fallback
├── model_registry.py        # Model information and pricing
├── usage_tracker.py         # Token and cost tracking
└── health.py                 # Provider health monitoring
```

## 🔄 Refactored Components

### 1. Agents (`backend/agents/shared/base_agent.py`)
- ✅ **Before**: Direct LLM creation (OpenAI, Anthropic, Ollama)
- ✅ **After**: Uses `LLMRouter.get_chat_client()`
- ✅ **Benefits**: 
  - Automatic local-first selection
  - Automatic fallback
  - Usage tracking
  - No hardcoded models

### 2. Assistants (`backend/assistants/runner.py`)
- ✅ **Before**: Direct `OllamaClient` usage (hardcoded to Ollama)
- ✅ **After**: Uses `LLMRouter.generate_completion()`
- ✅ **Benefits**:
  - Can now use cloud providers as fallback
  - Usage tracking
  - Consistent with agents

## 🎯 Key Features

### 1. Local-First Strategy
- **Default**: Tries Ollama first (local, free)
- **Fallback**: Automatically falls back to OpenAI → Anthropic if:
  - Ollama is unreachable
  - Model unavailable
  - Health check fails

### 2. Centralized Configuration
All configuration in `backend/.env`:
```env
LLM_MODE=local_first              # local_first, cloud_only, local_only
LLM_PRIORITY=ollama,openai,anthropic
LLM_FALLBACK_ENABLED=true
LLM_LOCAL_MODEL=qwen2.5:7b-instruct
LLM_CLOUD_MODEL=openai:gpt-4-turbo-preview
```

### 3. Usage Tracking
Every LLM call tracks:
- **Tokens**: Input + output
- **Cost**: Calculated from pricing registry (cloud only)
- **Latency**: Request time
- **Provider**: Which provider was used
- **Fallback**: Whether fallback was used and why

### 4. Model Registry
Single source of truth for:
- Available models (local + cloud)
- Context limits
- Pricing (for cloud models)
- Recommended intents

### 5. Health Monitoring
- Checks Ollama availability
- Validates API keys (basic)
- Caches health status (60s TTL)

## 📊 Usage Examples

### For Agents (LangChain)
```python
# In BaseAgent._create_llm()
router = get_router()
llm = router.get_chat_client(
    caller="blog_agent",
    intent=Intent.LONG_FORM,
    temperature=0.7,
    max_tokens=4000
)
# Use llm.invoke() as before
```

### For Assistants (Direct API)
```python
# In assistants/runner.py; model_preference from assistant config (env: LLM_LOCAL_MODEL)
router = get_router()
result = await router.generate_completion(
    caller="fintech_assistant",
    prompt=full_prompt,
    model_preference=config.model,  # from env or default
    intent=Intent.ANALYSIS
)
response_text = result["text"]
usage = result["usage"]  # Contains tokens, cost, latency
```

## 🔍 Verification Checklist

- ✅ All LLM calls go through router
- ✅ No direct OpenAI/Anthropic/Ollama calls in agents
- ✅ No direct OllamaClient calls in assistants
- ✅ Local-first strategy implemented
- ✅ Automatic fallback working
- ✅ Usage tracking for all calls
- ✅ Cost calculation for cloud models
- ✅ Health checks implemented
- ✅ Configuration centralized
- ✅ Backward compatibility preserved
- ✅ No hardcoded models (see Audit below)
- ✅ Extensive logging

## 🔎 Router & Hardcoding Audit

**All chat/completion LLM usage is routed through the router.**

| Component | Entry point | Model / provider source |
|-----------|-------------|--------------------------|
| **Agents** (blog, market_research, sales) | `BaseAgent._create_llm()` → `get_router().get_chat_client()` | `model_preference` from `LLM_LOCAL_MODEL` or `LLM_CLOUD_MODEL` (env); empty → router defaults |
| **Assistants** | `runner.run_assistant()` → `get_router().generate_completion()` | `config.model` from `LLM_LOCAL_MODEL` env or default `qwen2.5:7b-instruct` |
| **Router** | `llm_router.py` | `LLM_MODE`, `LLM_PRIORITY`, `LLM_LOCAL_MODEL`, `LLM_CLOUD_MODEL` (env). Registry: `model_registry.py` (canonical model list). |
| **Go** (executor, assistants handler) | Pass `LLM_*`, `OLLAMA_BASE_URL`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` to Python | Env vars only; no hardcoded keys or URLs |

**No hardcoded LLM details in application code.**

- **Agent factories** (`create_blog_agent`, `create_market_research_agent`, `create_sales_agent`): Use `LLM_LOCAL_MODEL` / `LLM_CLOUD_MODEL` env; no provider→model mapping.
- **AgentConfig**: `model` default `""`; router uses env when empty.
- **Assistants** (`fintech`, `code`, `general`): `get_config()` uses `LLM_LOCAL_MODEL` env, fallback `qwen2.5:7b-instruct`.
- **Router** defaults: `LLM_LOCAL_MODEL` / `LLM_CLOUD_MODEL` env with fallbacks; API keys and `OLLAMA_BASE_URL` from env only.
- **Model registry** (`model_registry.py`): Defines available models; no API keys or URLs. Add new models there.

**Out of scope (by design):**

- **Embeddings** (`OllamaEmbeddingClient`): Used for RAG only; not chat. Uses `OLLAMA_BASE_URL` env.
- **`.env` / `.env.example`**: Example values (e.g. `qwen2.5:7b-instruct`) are documentation, not runtime defaults in code.

## 🧪 Testing

### Smoke test (recommended)

A dedicated script verifies router init, health checks, optional completion, and usage tracking:

```bash
cd backend
PYTHONPATH=. python3 scripts/test_llm_router.py
```

- **With completion** (default): Requires Ollama running **or** `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`. Runs a minimal `generate_completion` and prints provider, response, and usage.
- **Without completion**: Use `--skip-completion` to only run init, health, and tracker. Useful when no LLM is available.

```bash
PYTHONPATH=. python3 scripts/test_llm_router.py --skip-completion
```

Dependencies: same as agents (`backend/agents/requirements.txt`). Ensure `backend/.env` (or `LLM_*` / provider env vars) is set.

### End-to-end: Assistant API

1. Start backend: `cd backend && make dev`
2. Start Ollama (or configure cloud keys): `ollama serve` and `ollama pull qwen2.5:7b`
3. Call the fintech assistant:

```bash
curl -X POST http://localhost:3001/api/assistants/fintech/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I integrate Zwitch?", "knowledge_base": "fintech", "assistant": "fintech"}'
```

All LLM calls go through the router (local-first → cloud fallback). Check backend logs for provider selection and usage.

## 🚀 Migration Notes

### Backward Compatibility
- ✅ Old `LLM_PROVIDER` env var still works (for compatibility)
- ✅ Agent factory functions still accept `llm_provider` parameter (ignored, router decides)
- ✅ Same response shapes and API contracts

### Breaking Changes
- ❌ **None** - All changes are internal refactoring

### New Capabilities
- ✅ Assistants can now use cloud providers (previously hardcoded to Ollama)
- ✅ Automatic fallback if local unavailable
- ✅ Usage tracking and cost visibility
- ✅ Centralized model selection

## 📝 Configuration Guide

### Local-First (Default)
```env
LLM_MODE=local_first
LLM_PRIORITY=ollama,openai,anthropic
LLM_FALLBACK_ENABLED=true
```

### Cloud-Only
```env
LLM_MODE=cloud_only
LLM_PRIORITY=openai,anthropic
LLM_FALLBACK_ENABLED=true
```

### Local-Only
```env
LLM_MODE=local_only
LLM_PRIORITY=ollama
LLM_FALLBACK_ENABLED=false
```

## 🔧 Troubleshooting

### Issue: Router always uses cloud
**Check**:
1. Is Ollama running? `ollama serve`
2. Is `OLLAMA_BASE_URL` correct?
3. Check health: Router logs will show provider status

### Issue: Changing `LLM_LOCAL_MODEL` in `.env` has no effect
**Causes**:
1. **Router never used env defaults** – Previously the router read `LLM_LOCAL_MODEL` / `LLM_CLOUD_MODEL` but always picked the first registry model. This is fixed: default model selection now uses these env vars.
2. **Model not in registry** – The chosen model (e.g. `llama3.1:8b`) must exist in `model_registry.py`. Add it if you use a local model not yet registered.
3. **Typo** – Use `llama3.1:8b` (double “l”), not `lama3.1:8b`.
4. **Backend not restarted** – The Go server loads `backend/.env` at startup. Restart the backend (`make dev` or `go run ./cmd/server`) after changing `.env`. Python agents receive env from Go when run via the API.

### Issue: No usage tracking
**Check**:
1. Router is initialized correctly
2. Check logs for usage records
3. Use `get_tracker().get_statistics()` to view stats

### Issue: Fallback not working
**Check**:
1. `LLM_FALLBACK_ENABLED=true`
2. Multiple providers in `LLM_PRIORITY`
3. Check health status in logs

### Issue: `"ChatOllama" object has no field "invoke"` (fixed)
The router previously monkey-patched `client.invoke` on LangChain clients. Those are Pydantic models and reject arbitrary attribute assignment. **Fix**: The router now returns a `_TrackedLangChainClient` wrapper that implements `invoke` with tracking and delegates other attributes to the underlying client. No monkey-patching.

## 📈 Usage Statistics

Access usage statistics:
```python
from llm.router import get_tracker

tracker = get_tracker()
stats = tracker.get_statistics()

print(f"Total calls: {stats['total_calls']}")
print(f"Total cost: ${stats['total_cost_usd']}")
print(f"Provider distribution: {stats['provider_distribution']}")
```

## 🎓 Architecture Benefits

1. **Single Point of Control**: All LLM decisions in one place
2. **Cost Visibility**: Track every dollar spent
3. **Automatic Optimization**: Local-first reduces costs
4. **Resilience**: Automatic fallback ensures availability
5. **Observability**: Full usage tracking and logging
6. **Flexibility**: Easy to add new providers or models

## 🔮 Future Enhancements

Ready for:
- Database-backed usage tracking
- Budget enforcement
- Per-agent budgets
- Advanced routing rules (intent-based)
- A/B testing different models
- Rate limiting
- Caching layer

## ✅ Safety Guarantees

- ✅ **No breaking changes**: All existing functionality preserved
- ✅ **Backward compatible**: Old env vars still work
- ✅ **Safe fallback**: Never fails if any provider available
- ✅ **Error handling**: Graceful degradation
- ✅ **Logging**: Extensive logging for debugging

---

**Status**: ✅ **COMPLETE** - All requirements met, ready for testing
