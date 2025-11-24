# Agent_X Python Agents

AI agent services for the Agent_X platform. Each agent is an autonomous worker that processes tasks using LLMs (OpenAI, Anthropic Claude, or Ollama).

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

### 3. Run Sales Agent Worker

```bash
# Make sure backend and Redis are running first
cd sales_agent
python worker.py
```

The worker will listen for tasks on the `tasks:sales` Redis queue and processenthem automatically.

## Architecture

```
agents/
├── shared/               # Shared utilities
│   ├── base_agent.py    # Base agent class
│   ├── db_utils.py      # Database helpers
│   └── tools/           # Reusable tools
├── sales_agent/         # Sales agent implementation
│   ├── main.py          # Agent logic
│   └── worker.py        # Queue worker
└── requirements.txt     # Python dependencies
```

## Base Agent Framework

All agents extend the `BaseAgent` class which provides:

- **LLM Integration**: Supports OpenAI, Anthropic Claude, and Ollama
- **Tool System**: Register and use tools (functions the LLM can call)
- **Conversation Management**: Tracks conversation history
- **Error Handling**: Robust error handling and logging
- **Database Integration**: Automatic task status updates

### Example: Creating a Custom Agent

```python
from shared.base_agent import BaseAgent, AgentConfig, TaskInput

class MyAgent(BaseAgent):
    def _register_tools(self):
        """Register agent-specific tools"""
        @tool
        def my_custom_tool(input: str) -> str:
            return f"Processed: {input}"
        
        self.add_tool(my_custom_tool)
    
    def _get_system_prompt(self) -> str:
        """Define agent personality and capabilities"""
        return "You are a helpful AI assistant specialized in..."

# Create instance
config = AgentConfig(
    agent_type="my-agent",
    name="My Custom Agent",
    llm_provider="openai",
    model="gpt-4-turbo-preview"
)
agent = MyAgent(config)

# Execute task
task = TaskInput(
    task_id="123",
    action="do_something",
    input_data={"key": "value"}
)
result = agent.execute_task(task)
```

## Sales Agent

The Sales Agent handles:
- Lead qualification
- Email generation
- Meeting scheduling
- CRM analysis

### Example: Generate Email

```python
from sales_agent.main import create_sales_agent
from shared.base_agent import TaskInput

agent = create_sales_agent(llm_provider="openai")

task = TaskInput(
    task_id="test-123",
    action="generate_email",
    input_data={
        "recipientName": "John Doe",
        "companyName": "Acme Corp",
        "context": "Follow up after product demo",
        "keyPoints": "Highlight ROI and implementation timeline"
    }
)

result = agent.execute_task(task)
print(result.output["email"]["body"])
```

### Example: Qualify Lead

```python
task = TaskInput(
    task_id="test-456",
    action="qualify_lead",
    input_data={
        "companyName": "TechStart Inc",
        "industry": "SaaS",
        "size": "50-200 employees",
        "budget": "$50k-$100k",
        "painPoints": "Manual data entry, slow processes"
    }
)

result = agent.execute_task(task)
print(f"Score: {result.output['qualification']['score']}/10")
print(f"Recommendation: {result.output['qualification']['recommendation']}")
```

## Worker Pattern

Each agent has a `worker.py` that:
1. Listens to Redis queue for new tasks
2. Processes tasks using the agent
3. Updates task status in database
4. Saves conversation history

### Running Workers

```bash
# Sales Agent
cd sales_agent && python worker.py

# Support Agent (when implemented)
cd support_agent && python worker.py
```

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

You can test agents directly without the backend running:

```python
import os
os.environ["DATABASE_URL"] = "postgresql://..."  # Your DB
os.environ["OPENAI_API_KEY"] = "sk-..."

from sales_agent.main import create_sales_agent
from shared.base_agent import TaskInput

agent = create_sales_agent()
task = TaskInput(task_id="test", action="generate_email", input_data={...})
result = agent.execute_task(task)
print(result)
```

## Next Steps

Phase 2 implementation will add:
- Support Agent
- HR Agent
- Legal Agent
- Finance Agent
- Market Research Agent
- Marketing Agent
- Lead Sourcing Agent
- Intelligence Agent

Each will follow the same pattern using the base agent framework.
