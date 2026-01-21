# Assistant Chat Endpoint - Setup & Testing Guide

## ✅ Implementation Complete

### Files Created

1. **Python Runner** (`backend/assistants/runner.py`)
   - CLI entry point for assistants
   - Loads assistant config
   - Calls KnowledgePipeline for RAG
   - Builds prompt using prompt_builder
   - Calls OllamaClient for LLM response
   - Returns structured JSON

2. **Go Handler** (`backend/internal/handlers/assistants.go`)
   - HTTP handler for `/api/assistants/:name/chat`
   - Parses request
   - Calls Python runner
   - Returns JSON response

3. **Route Added** (`backend/cmd/server/main.go`)
   - Added assistants route group
   - Registered handler

---

## 🧪 Testing Steps

### Step 1: Start Ollama

```bash
# Terminal 1
ollama serve

# Terminal 2 (verify model exists)
ollama list
# If model doesn't exist:
ollama pull qwen2.5:7b
# or
ollama pull deepseek-r1:7b
```

### Step 2: Start AgentX Backend

```bash
cd backend
go run cmd/server/main.go
```

You should see:
```
✅ Database connected
🚀 Server starting on port 3001
📍 API Documentation:
   - Assistants: http://localhost:3001/api/assistants/:name/chat
```

### Step 3: Test from Terminal

```bash
curl -X POST http://localhost:3001/api/assistants/fintech/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How do I integrate Zwitch payment gateway?",
    "knowledge_base": "fintech",
    "assistant": "fintech"
  }'
```

### Expected Response

```json
{
  "assistant": "fintech",
  "answer": "...context-aware answer about payment gateway integration...",
  "citations": [
    "https://developers.zwitch.io/..."
  ],
  "metadata": {
    "model": "qwen2.5:7b",
    "provider": "ollama",
    "rag_used": true
  }
}
```

---

## 🔍 Debug Checklist

### If response is empty or generic:

1. **Check KnowledgePipeline returns context:**
   ```bash
   # Check if ChromaDB has data
   # The knowledge_base="fintech" collection should exist
   ```

2. **Check Python runner logs:**
   - Look for: "Retrieved context length: X chars"
   - If 0, RAG is not finding context

3. **Verify knowledge base exists:**
   - Check `backend/data/chromadb/` directory
   - Verify `fintech` collection exists

### If Ollama not called:

1. **Check Ollama is running:**
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. **Check environment variable:**
   ```bash
   echo $OLLAMA_BASE_URL
   # Should be: http://localhost:11434 (or your Ollama URL)
   ```

3. **Check Python logs:**
   - Look for: "Calling Ollama with model: ..."
   - Check for errors in stderr

### If Go → Python breaks:

1. **Check Python path:**
   ```bash
   which python3
   # Should point to valid Python 3.8+
   ```

2. **Check imports:**
   ```bash
   cd backend
   python3 -c "from assistants.runner import main; print('OK')"
   ```

3. **Check JSON contract:**
   - Verify Python outputs valid JSON to stdout
   - Check Go handler parses JSON correctly

---

## 📋 Success Criteria

✅ Context-aware answer (mentions Zwitch, payment gateway specifics)  
✅ No internal file paths in citations  
✅ Only public URLs cited (developers.zwitch.io, etc.)  
✅ Clear focus (payment gateway, not payouts)  
✅ No stack traces  
✅ Ollama logs show request  
✅ Response time < 30 seconds (for 7B model)

---

## 🚨 Common Issues

### Issue: "ModuleNotFoundError: No module named 'assistants'"

**Fix:** Ensure PYTHONPATH is set:
```bash
export PYTHONPATH=/path/to/Agent_X/backend
```

### Issue: "ChromaDB collection not found"

**Fix:** The knowledge base needs to be ingested first. For now, the endpoint will work but return empty context if the collection doesn't exist.

### Issue: "Ollama connection refused"

**Fix:** 
1. Ensure Ollama is running: `ollama serve`
2. Check OLLAMA_BASE_URL environment variable
3. Verify port 11434 is accessible

---

## 📝 Next Steps (After Basic Test Works)

Once the basic endpoint works:

1. **Add error handling** for missing knowledge bases
2. **Add validation** for assistant names
3. **Add logging** for debugging
4. **Consider streaming** (future enhancement)
5. **Add memory/sessions** (future enhancement)

---

## 🎯 Current Limitations

- ❌ No streaming (waits for full response)
- ❌ No memory (stateless, no conversation history)
- ❌ No session management
- ❌ Single assistant per request
- ❌ No authentication

These are intentional for the minimal implementation.
