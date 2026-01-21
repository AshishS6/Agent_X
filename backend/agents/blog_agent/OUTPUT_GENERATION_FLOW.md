# Blog Agent Output Generation Flow

## Overview
The Blog Agent uses **LLM (Large Language Model)** to generate blog outlines and drafts. Based on your logs, it's currently using **Ollama with deepseek-r1:7b model**.

## Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Frontend Request (BlogAgent.tsx)                            │
│    - User fills form: topic, brand, audience, intent            │
│    - POST /api/agents/blog/execute                              │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Go Backend Handler (agents.go)                               │
│    - Creates task in database                                   │
│    - Spawns async goroutine                                     │
│    - Calls Python CLI via executor                             │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Python CLI (cli.py)                                          │
│    - Parses JSON input                                          │
│    - Reads LLM_PROVIDER from env (ollama/openai/anthropic)      │
│    - Creates BlogAgent instance                                 │
│    - Calls agent.execute_task()                                  │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. BlogAgent (main.py)                                          │
│    - Inherits from BaseAgent                                    │
│    - Routes to specific method based on action:                 │
│      • generate_outline → _generate_outline()                   │
│      • generate_post_from_outline → _generate_post_from_outline()│
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. Prompt Construction                                          │
│    For generate_outline:                                        │
│    - Builds detailed prompt with:                                │
│      • Brand guidance (OPEN/Zwitch)                              │
│      • Audience guidance (SME/Developer/Founder/Enterprise)      │
│      • Intent guidance (education/product/announcement)          │
│      • Topic from user input                                    │
│    - Includes JSON structure template                           │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. LLM Invocation (BaseAgent._create_llm)                       │
│    - Creates LLM instance based on provider:                     │
│      • OpenAI: ChatOpenAI (gpt-4-turbo-preview)                 │
│      • Anthropic: ChatAnthropic (claude-3-sonnet)                │
│      • Ollama: ChatOllama (deepseek-r1:7b) ← CURRENT           │
│    - Sends SystemMessage + HumanMessage                         │
│    - System prompt: Blog agent instructions                      │
│    - User prompt: Generated prompt with specs                   │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. LLM Response Processing                                      │
│    - Receives LLM response (JSON string)                        │
│    - Extracts JSON from markdown code blocks if present          │
│    - Parses JSON to Python dict                                  │
│    - Validates structure (title, outline, etc.)                 │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. Output Formatting                                            │
│    - Wraps in standardized format:                               │
│      {                                                           │
│        "action": "generate_outline",                            │
│        "response": {                                            │
│          "title": "...",                                        │
│          "outline": [...],                                      │
│          "brand": "OPEN",                                       │
│          "topic": "AI in marketing",                            │
│          "target_audience": "SME",                              │
│          "intent": "education"                                 │
│        }                                                        │
│      }                                                           │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ 9. Return to CLI                                                │
│    - CLI formats as TaskResult                                  │
│    - Outputs JSON to stdout                                      │
│    - Go backend captures stdout                                 │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ 10. Database Storage                                            │
│     - Go backend parses JSON output                             │
│     - Updates task in database:                                 │
│       • status = "completed"                                    │
│       • output = JSON from LLM                                  │
│       • completed_at = NOW()                                     │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ 11. Frontend Display                                            │
│     - Frontend polls /api/tasks every 5 seconds                 │
│     - Conversations tab displays output                          │
│     - Renders outline structure with title, sections, intents    │
└─────────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. LLM Provider Selection
- **Environment Variable**: `LLM_PROVIDER` (ollama/openai/anthropic)
- **Current Setting**: `ollama` (from your logs)
- **Model**: `deepseek-r1:7b` (default for Ollama)

### 2. System Prompt
The agent uses a comprehensive system prompt that instructs the LLM to:
- Generate structured, actionable blog outlines
- Maintain brand voice consistency
- Target specific audiences effectively
- Follow content intent (education/product/announcement)

### 3. User Prompt Construction
For `generate_outline`, the prompt includes:
- Brand guidance (technical vs friendly)
- Audience guidance (SME/Developer/Founder/Enterprise)
- Intent guidance (education/product/announcement)
- Topic from user input
- JSON structure template

### 4. LLM Response Format
The LLM is instructed to return JSON:
```json
{
  "title": "Blog Title Here",
  "outline": [
    {
      "heading": "Section Title (H2)",
      "intent": "What this section covers",
      "subsections": [
        {
          "heading": "Subsection Title (H3)",
          "intent": "What this subsection covers"
        }
      ]
    }
  ]
}
```

### 5. Response Parsing
- Extracts JSON from markdown code blocks if present
- Falls back to regex extraction if needed
- Validates JSON structure
- Raises error if parsing fails

## Current Configuration

Based on your logs:
- **LLM Provider**: Ollama
- **Model**: deepseek-r1:7b
- **Temperature**: 0.7 (default)
- **Max Tokens**: 4000 (for blog generation)

## Verification

The output IS being generated by the LLM as designed:
1. ✅ LLM is invoked (line 160 in main.py: `response = self.llm.invoke(messages)`)
2. ✅ Response is parsed from JSON (lines 175-180)
3. ✅ Output is structured correctly (lines 182-192)
4. ✅ Task completed successfully (your logs show "completed" status)

## Code References

- **LLM Initialization**: `backend/agents/shared/base_agent.py:84-112`
- **Blog Agent Logic**: `backend/agents/blog_agent/main.py:75-192`
- **Prompt Construction**: `backend/agents/blog_agent/main.py:120-151`
- **LLM Invocation**: `backend/agents/blog_agent/main.py:154-160`
- **Response Parsing**: `backend/agents/blog_agent/main.py:162-180`
