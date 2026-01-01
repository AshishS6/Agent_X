# Agent_X Python Agents

AI agent services for the Agent_X platform. Each agent is a standalone CLI tool that processes tasks.

## Quick Start

### 1. Install Dependencies

```bash
cd backend/agents
pip install -r requirements.txt
```

**Recommended**: Use a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Agents look for `.env` files in multiple locations (in order):
1. `backend/agents/<agent_name>/.env`
2. `backend/agents/.env`
3. `backend/.env`

Create a `.env` file in one of these locations:

```bash
# Example: backend/agents/.env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...

# OR for Anthropic:
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...

# OR for Ollama (local):
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
```

### 3. Run Agent (CLI Mode)

Agents are executed as CLI tools. You can run them manually for testing:

```bash
# Market Research Agent
cd backend/agents/market_research_agent
python cli.py --input '{"action": "site_scan", "url": "https://example.com"}'

# Sales Agent
cd backend/agents/sales_agent
python cli.py --input '{"action": "generate_email", "recipientName": "John", "context": "Follow up"}'
```

## Architecture

```
backend/agents/
├── shared/                      # Shared utilities
│   ├── base_agent.py           # Base agent class with LLM integration
│   ├── db_utils.py             # Database connection utilities
│   └── tools/                  # Reusable tools (if any)
├── market_research_agent/      # ✅ Fully functional
│   ├── cli.py                  # CLI entry point
│   ├── main.py                 # LangChain ReAct agent
│   ├── scan_engine.py          # V2 Modular Scan Engine
│   ├── scanners/               # Site scanning modules
│   ├── analyzers/             # Content analysis modules
│   ├── crawlers/              # Web crawling modules
│   └── docs/                  # Agent-specific documentation
├── sales_agent/                # ✅ Fully functional
│   ├── cli.py                 # CLI entry point
│   ├── main.py                # LangChain ReAct agent
│   └── worker.py              # Legacy worker (not used in current architecture)
├── cleanup_tasks.py            # Utility script for stuck tasks
└── requirements.txt            # Python dependencies
```

## Base Agent Framework

All agents use the `BaseAgent` class from `shared/base_agent.py` which provides:

- **LLM Integration**: Supports OpenAI, Anthropic Claude, and Ollama
- **Tool System**: Register and use tools (functions the LLM can call)
- **JSON Input/Output**: Standardized I/O via stdout for CLI integration
- **Database Integration**: Optional database connection via `db_utils.py`
- **Logging**: Structured logging to stderr

### CLI Contract

All agents must follow this contract:

**Input**: `--input '{"action": "...", "key": "value", "task_id": "uuid"}'`

**Output** (to stdout, JSON):
```json
{
  "status": "completed" | "failed",
  "output": { ... },
  "error": "string if failed"
}
```

**Logs**: Write to `stderr` (not `stdout`)

**Exit Code**: `0` = success, non-zero = failure

### Example: Creating a Custom Agent

```python
#!/usr/bin/env python3
# cli.py
import sys
import json
import argparse
import logging
from typing import Dict, Any

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("MyAgent.CLI")

def run_agent(action: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        # Your agent logic here
        if action == "my_action":
            result = {"message": "Success"}
            return {"status": "completed", "output": result}
        else:
            return {"status": "failed", "error": f"Unknown action: {action}"}
    except Exception as e:
        logger.error(f"Agent execution failed: {e}", exc_info=True)
        return {"status": "failed", "error": str(e)}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="JSON input string")
    args = parser.parse_args()
    
    input_data = json.loads(args.input)
    action = input_data.pop("action", None)
    
    if not action:
        print(json.dumps({"status": "failed", "error": "Missing 'action' field"}))
        sys.exit(1)
    
    result = run_agent(action, input_data)
    print(json.dumps(result))
    sys.exit(0 if result["status"] == "completed" else 1)
```

## Agent Execution Model

**Current Architecture**: The Go backend spawns Python agents as subprocesses on-demand. There are no long-running Python worker processes.

**Legacy Note**: Previous versions used Redis workers (`worker.py`). The `worker.py` files may still exist in some agents but are not used by the current architecture. Agents are executed via `cli.py` only.

## LLM Provider Configuration

Agents read LLM configuration from environment variables. The `BaseAgent` class automatically detects the provider.

### OpenAI (Default)

```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
```

### Anthropic Claude

```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### Ollama (Local, Free)

```bash
# Install Ollama first: https://ollama.ai
# Pull a model: ollama pull llama3

LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3  # or mistral, qwen2.5, etc.
```

**Note**: The environment variable name is `LLM_PROVIDER` (not `DEFAULT_LLM_PROVIDER`). Agents check multiple `.env` file locations automatically.

## Testing Without Full Stack

You can test agents directly via CLI without the backend running, as long as `.env` is configured:

```bash
cd backend/agents/market_research_agent
python cli.py --input '{"action": "site_scan", "url": "https://example.com"}'
```

This is useful for:
- **Development**: Testing agent logic without running the full stack
- **Debugging**: Isolating agent issues from backend problems
- **CI/CD**: Running agent tests independently

## Available Agents

### ✅ Market Research Agent
- **Status**: Fully functional
- **Location**: `backend/agents/market_research_agent/`
- **Actions**: `site_scan`, `comprehensive_site_scan`, general research queries
- **Features**: V2 Modular Scan Engine, SEO analysis, tech stack detection, compliance monitoring
- **Documentation**: See `backend/agents/market_research_agent/docs/`

### ✅ Sales Agent
- **Status**: Fully functional
- **Location**: `backend/agents/sales_agent/`
- **Actions**: `generate_email`, `qualify_lead`
- **Features**: Email generation, lead qualification

### 🔄 Other Agents (UI Ready, Implementation Pending)
- Support Agent
- HR Agent
- Legal Agent
- Finance Agent
- Marketing Agent
- Intelligence Agent
- Lead Sourcing Agent

## Dependencies

Key Python packages (see `requirements.txt`):
- `langchain` - Agent framework
- `langchain-openai` - OpenAI integration
- `langchain-anthropic` - Anthropic integration
- `duckduckgo-search` - Web search
- `beautifulsoup4` - HTML parsing
- `requests` - HTTP client
- `python-whois` - Domain information
- `python-dotenv` - Environment variable loading
