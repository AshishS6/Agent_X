# Agent_X Python Agents

AI agent services for the Agent_X platform. Each agent is a standalone CLI tool that processes tasks.

## Quick Start

### 1. Install Dependencies

```bash
cd agents
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env

# Edit .env and add your API keys:
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Run Agent (CLI Mode)

Agents are executed as CLI tools. You can run them manually for testing:

```bash
# Market Research Agent
cd market_research_agent
python cli.py --input '{"action": "site_scan", "url": "https://example.com"}'

# Sales Agent
cd sales_agent
python cli.py --input '{"action": "generate_email", "recipientName": "John"}'
```

## Architecture

```
agents/
├── shared/               # Shared utilities
│   ├── base_agent.py    # Base agent logic
│   └── tools/           # Reusable tools
├── market_research_agent/
│   ├── cli.py           # CLI entry point
│   └── main.py          # Agent logic
└── requirements.txt     # Python dependencies
```

## Base Agent Framework

All agents extend the `BaseAgent` class which provides:

- **LLM Integration**: Supports OpenAI, Anthropic Claude, and Ollama
- **Tool System**: Register and use tools (functions the LLM can call)
- **JSON Input/Output**: Standardized I/O via stdout for CLI integration

### Example: Creating a Custom Agent

```python
# cli.py
from shared.base_agent import BaseAgent

def run_agent(action, input_data):
    # logic here...
    return {"status": "completed", "output": result}

if __name__ == "__main__":
    # parse args and call run_agent
    pass
```

## Worker Pattern (Legacy Note)

*Note: Previous versions used Redis workers (`worker.py`). The current architecture uses the Go backend to spawn `cli.py` subprocesses directly. There are no long-running Python worker processes.*

## LLM Provider Configuration

### OpenAI (Default)

```bash
DEFAULT_LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
```

### Anthropic Claude

```bash
DEFAULT_LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### Ollama (Local, Free)

```bash
# Install Ollama first: https://ollama.ai
# Pull a model: ollama pull llama3

DEFAULT_LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
```

## Testing Without Full Stack

You can test agents directly via CLI without the backend running, as long as `.env` is configured.
