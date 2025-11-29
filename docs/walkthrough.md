# Market Research Agent - Status Update Fix

## Problems Identified

### Problem 1: Agent Still Using Markdown Format
The agent continues to generate markdown-formatted responses despite the code changes because **old worker processes are still running** with the outdated code.

### Problem 2: Tasks Stuck in "Processing" Status
Tasks remain in "Processing" status in the frontend even though the agent produces output in the terminal. This happens because:

1. **The agent hits `max_iterations` (10 attempts)** due to repeated parsing errors
2. **The agent returns "completed" with an error message** instead of properly failing
3. **The database never gets updated to "failed"**, so the frontend keeps showing "Processing"

---

## Root Causes

### Markdown Format Issue
**You have 2 duplicate market_research_agent workers running:**
- Worker 1: Running for ~5 minutes (old code)
- Worker 2: Running for ~3 minutes (old code)

Both are processing tasks with the old prompt template, causing the markdown format errors.

### Status Update Issue
**In the original code** ([`main.py:1025-1028`](file:///Users/ashish/Agent_X/agents/market_research_agent/main.py#L1025-L1028)):

```python
except Exception as e:
    self.logger.error(f"Agent execution failed: {e}")
    response_text = f"Error executing agent: {str(e)}"  # Still returns "completed"!
```

This catches the exception but returns a "completed" status with an error message, instead of re-raising the exception to mark the task as "failed".

---

## Changes Made

### 1. Improved ReAct Prompt Template (Lines 951-987)
- Added explicit instructions prohibiting markdown
- Provided concrete examples of correct vs. incorrect formats
- Emphasized JSON formatting for Action Input

### 2. Enhanced Error Handling (Lines 994-1015)
- Custom error handler that gives clear feedback to the LLM
- Max iterations limit (10) to prevent infinite loops
- Execution timeout (5 minutes)

### 3. **Fixed Status Update Logic (Lines 1017-1034)** ✨ **NEW**
```python
# Execute
try:
    result = agent_executor.invoke({"input": full_input})
    response_text = result.get("output", "")
    
    # Check if the result indicates a failure
    if not response_text or "Error executing agent" in response_text or "max iterations" in str(result).lower():
        self.logger.error(f"Agent failed to complete task properly. Result: {result}")
        raise Exception(f"Agent failed: {response_text or 'No output generated'}")
        
except Exception as e:
    # Re-raise to let base class mark task as "failed"
    self.logger.error(f"Agent execution failed: {e}", exc_info=True)
    raise  # This will update DB status to "failed"
```

**Key Change**: Now **raises an exception** instead of returning a completed status with an error message. This ensures the `worker.py` properly updates the database with `status="failed"`.

---

## How to Fix This

### Step 1: Kill ALL Market Research Agent Workers

You have **2 duplicate workers** running. **Stop both of them**:

1. Find the terminal windows running `python3 worker.py` in `/Users/ashish/Agent_X/agents/market_research_agent`
2. Press `Ctrl+C` in **BOTH** terminal windows to stop them
3. Verify they're stopped by checking there are no more parsing error loops

### Step 2: Start ONE Fresh Worker

In a **single** terminal window:

```bash
cd /Users/ashish/Agent_X/agents/market_research_agent
python3 worker.py
```

You should see:
```
Market Research Agent Worker started, listening on tasks:market_research
Using LLM provider: ollama
```

### Step 3: Test the Fix

1. **Submit a new site scan task** from the UI (use a simple URL like `https://example.com`)
2. **Watch the terminal** - you should see:
   - The LLM attempting to use tools
   - If parsing errors occur, the custom error handler providing feedback
   - After 10 failed attempts, the task should be marked as **"failed"** (not "processing")
3. **Check the frontend** - the task should show **"Failed"** status instead of being stuck in "Processing"

---

## What You Should See

### ✅ Success Case (If Format is Followed)
```
Question: Scan https://example.com
Thought: I need to use the comprehensive_site_scan tool
Action: comprehensive_site_scan
Action Input: {"url": "https://example.com", "business_name": ""}
Observation: {... JSON report ...}
Thought: I now know the final answer
Final Answer: {report summary}
```

**Result**: Task marked as **"Completed"** ✅

### ❌ Failure Case (If Format Errors Persist)
```
### Action: comprehensive_site_scan  
**Action Input:** ...
comprehensive_site_scan** is not a valid tool...
ERROR: Invalid format detected. You MUST use the exact format...
(repeats 10 times)
Agent execution failed: Agent failed: max iterations reached
```

**Result**: Task marked as **"Failed"** (NOT stuck in "Processing") ✅

---

## If Parsing Errors Still Persist

The Ollama model might not be good at following structured formats. **Recommended solutions**:

### Option 1: Use a Better Ollama Model

Current model: **Unknown** (not specified in env)

**Better models for tool use**:
- `mistral` - Better instruction following
- `llama3.1` or `llama3.2` - Newer, better for tool use
- `qwen2.5` - Excellent at structured formats

**To check which model you're using:**
```bash
cd /Users/ashish/Agent_X/agents
cat .env
```

**To change the model**, add to [`agents/.env`](file:///Users/ashish/Agent_X/agents/.env):
```bash
OLLAMA_MODEL=mistral
```

Then update [`shared/base_agent.py:107`](file:///Users/ashish/Agent_X/agents/shared/base_agent.py#L107):
```python
return ChatOllama(
    model=os.getenv("OLLAMA_MODEL", "llama2"),  # Read from env
    temperature=self.config.temperature,
    base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
)
```

### Option 2: Switch to OpenAI (If Available)

If you have OpenAI credits, update [`agents/.env`](file:///Users/ashish/Agent_X/agents/.env):
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=your_api_key_here
```

OpenAI models are much better at following the ReAct format.

---

## Summary of Fixes

| Issue | Before | After |
|-------|--------|-------|
| **Parsing errors** | Agent uses markdown format | Explicit prompt with examples (but LLM still needs to cooperate) |
| **Status stuck in "Processing"** | Returns "completed" on failure | Raises exception → marks as "failed" ✅ |
| **Infinite loops** | Could run forever | Max 10 iterations, 5 min timeout ✅ |
| **Duplicate workers** | 2 workers competing | Need to manually kill and restart with 1 worker |

---

## Files Modified

1. [`/Users/ashish/Agent_X/agents/market_research_agent/main.py`](file:///Users/ashish/Agent_X/agents/market_research_agent/main.py)
   - Lines 951-987: Updated ReAct prompt
   - Lines 994-1015: Custom error handler
   - Lines 1017-1034: **Fixed status update logic** ✨

## Next Steps

1. ✅ **Kill the 2 duplicate workers** (Completed)
2. ✅ **Start 1 fresh worker** (Completed)
3. ✅ **Restart Sales Agent** (Completed)
4. **Test with a new site scan task**

### Verification

You can now submit a new task from the UI.
- The Market Research Agent should now properly handle the task.
- If it fails parsing, it will mark the task as "Failed" instead of getting stuck.
- The Sales Agent is also running with corrected configuration.

### Cleanup and Pagination

I have also implemented:
1.  **Stuck Task Cleanup**: A script ran to mark tasks stuck in "processing" for >1 hour as "failed".
2.  **Pagination**: The Market Research Agent history now supports pagination (10 items per page).

**To Verify:**
1.  Check the **Market Research Agent** dashboard.
2.  Scroll down to "Research History".
3.  You should see "Total: X" and "Previous/Next" buttons if you have more than 10 tasks.
4.  Check the **Sales Agent** dashboard to ensure it still loads tasks correctly.
