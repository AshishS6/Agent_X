# 🚀 Agent_X - Quick Start Guide

Get your agentic AI platform running in 5 minutes!

## Prerequisites

- **Docker Desktop** installed and running
- **Go 1.21+** installed
- **Python 3.11+** installed
- **LLM API Key** (OpenAI, Anthropic, or Ollama locally)

## Step 1: Configure API Keys

```bash
# Backend environment
cd backend
cp .env.example .env

# Edit backend/.env and add your API key:
# OPENAI_API_KEY=sk-your-key-here
# OR
# ANTHROPIC_API_KEY=sk-ant-your-key-here
# Also set: LLM_PROVIDER=openai (or anthropic)
```

## Step 2: Start Infrastructure

```bash
# From Agent_X root directory
docker-compose up -d

# Wait ~30 seconds for services to initialize
# Check status:
docker-compose ps
```

You should see:
- ✅ `agentx-postgres` - running (PostgreSQL 16)
- ✅ `agentx-redis` - running (Redis 7, for future features)

**Note**: The database schema (`database/schema.sql`) is automatically applied on first startup. This creates all tables (agents, tasks, conversations, etc.) and seeds the 9 agents.

## Step 3: Install Python Dependencies

```bash
cd backend/agents
pip install -r requirements.txt
```

> **Note**: Agents require:
> - `duckduckgo-search` (web search)
> - `beautifulsoup4` (web scraping)
> - `langchain`, `langchain-openai`, `langchain-anthropic`
> - `python-whois` (domain analysis)

## Step 4: Start the Go Backend

```bash
cd backend
make dev
```

**Note**: If `air` (hot reload tool) is not installed, it will fall back to `go run ./cmd/server`.

You should see:
```
✅ Database connected
📁 Project root: /path/to/Agent_X
⚡ Executor initialized (global: 10, per-tool default: 5)
🚀 Server starting on port 3001
```

The Go backend:
- Exposes REST API on port 3001
- Spawns Python CLI agents as subprocesses (`os/exec`)
- Manages hybrid concurrency (global limit: 10, per-tool limit: 5)
- Automatically initializes MCC (Merchant Category Codes) tables
- Graceful shutdown on SIGINT/SIGTERM

## Step 5: Verify System

```bash
# Health check
curl http://localhost:3001/api/monitoring/health

# Expected response:
# {"success":true,"data":{"status":"healthy","services":{"database":true}}}

# List all agents
curl http://localhost:3001/api/agents

# List available CLI tools
curl http://localhost:3001/api/tools

# Get system metrics
curl http://localhost:3001/api/monitoring/metrics
```

## Step 6: Test Agent Execution

### Market Research Agent - Site Scan

```bash
curl -X POST http://localhost:3001/api/agents/market_research/execute \
  -H "Content-Type: application/json" \
  -d '{
    "action": "comprehensive_site_scan",
    "input": {
      "topic": "https://example.com",
      "business_name": "Example Inc"
    }
  }'
```

Response will include a task ID. Check the result:

```bash
curl http://localhost:3001/api/tasks/{task-id}
```

### Sales Agent - Email Generation

```bash
curl -X POST http://localhost:3001/api/agents/sales/execute \
  -H "Content-Type: application/json" \
  -d '{
    "action": "generate_email",
    "input": {
      "recipientName": "John Doe",
      "context": "Follow up after product demo"
    }
  }'
```

### Direct CLI Testing (No Backend)

You can test agents directly without the backend running:

```bash
# Market Research Agent
cd backend/agents/market_research_agent
python cli.py --input '{"action": "site_scan", "url": "https://example.com"}'

# Sales Agent
cd backend/agents/sales_agent
python cli.py --input '{"action": "generate_email", "recipientName": "Jane", "context": "Demo follow-up"}'

# Dry run (validate input without executing) - if supported
python cli.py --input '{"action": "site_scan", "url": "https://example.com"}' --dry-run
```

**Note**: Agents require environment variables (API keys) to be set. They will look for `.env` files in multiple locations:
- `backend/agents/<agent_name>/.env`
- `backend/agents/.env`
- `backend/.env`

## Step 7: Start the Frontend

```bash
# In Agent_X root directory (new terminal)
npm install  # First time only
npm run dev
```

Dashboard opens at http://localhost:5173

**Active Pages:**
- ✅ Dashboard Home - Real-time system metrics and overview
- ✅ Market Research Agent - Site scan with V2 modular engine, SEO analysis, tech stack detection
- ✅ Sales Agent - Email generation and lead qualification
- ✅ Activity Logs - Live task execution history with pagination
- 🔄 Support Agent - UI ready (implementation pending)
- 🔄 HR Agent - UI ready (implementation pending)
- 🔄 Legal Agent - UI ready (implementation pending)
- 🔄 Finance Agent - UI ready (implementation pending)
- 🔄 Marketing Agent - UI ready (implementation pending)
- 🔄 Intelligence Agent - UI ready (implementation pending)
- 🔄 Lead Sourcing Agent - UI ready (implementation pending)
- 🔄 Workflows, Integrations, Settings - UI ready (implementation pending)

---

## Troubleshooting

### Go backend won't start
```bash
# Check if port 3001 is in use
lsof -i :3001

# Verify database connection
cd backend && make dev

# Check logs for database errors
```

### Python agent errors
```bash
# Verify dependencies
cd backend/agents
pip install -r requirements.txt

# Test CLI directly
cd market_research_agent
python cli.py --input '{"action": "site_scan", "url": "https://google.com"}'
```

### "API key not set" error
```bash
# Ensure backend/.env has:
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here

# OR for Anthropic:
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key-here

# OR for Ollama (local):
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3  # or mistral, qwen2.5, etc.
```

**Note**: Agents read from `.env` files in this order:
1. `backend/agents/<agent_name>/.env`
2. `backend/agents/.env`
3. `backend/.env`

### Database not initialized
```bash
docker-compose down -v  # Remove volumes
docker-compose up -d    # Restart (will re-run init)
```

---

## Architecture Overview

```
┌─────────────────┐
│    Frontend     │ (React + TypeScript)
│  localhost:5173 │
└────────┬────────┘
         │ HTTP
┌────────▼────────┐
│   Go Backend    │ (Gin framework)
│  localhost:3001 │
└────────┬────────┘
         │ subprocess spawn
┌────────▼────────┐
│  Python Agents  │ (CLI tools)
│   cli.py        │
└────────┬────────┘
         │ API calls
┌────────▼────────┐
│  LLM Provider   │
│ OpenAI/Claude   │
└─────────────────┘
```

**Key Insight**: No Redis workers or message queues! The Go backend spawns Python agents directly as subprocesses using `os/exec`, capturing stdout as JSON output. This simplifies architecture and makes debugging easier.

---

## Quick Reference

| Service | URL | Notes |
|---------|-----|-------|
| Go Backend | http://localhost:3001 | Main API |
| PostgreSQL | localhost:5432 | Via Docker |
| Frontend | http://localhost:5173 | Vite dev server |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/agents` | List all agents |
| GET | `/api/agents/:id` | Get agent by ID |
| POST | `/api/agents/:name/execute` | Execute agent by type (e.g., `market_research`, `sales`) |
| PUT | `/api/agents/:id` | Update agent configuration |
| GET | `/api/agents/:id/metrics` | Get agent metrics and statistics |
| GET | `/api/tasks` | List tasks (supports `?agentId=`, `?status=`, `?limit=`, `?offset=`) |
| GET | `/api/tasks/:id` | Get task by ID |
| GET | `/api/tasks/status/counts` | Get task counts by status |
| POST | `/api/tasks/:id/mcc` | Save final MCC for a task |
| GET | `/api/tools` | List available CLI tools |
| GET | `/api/tools/:name` | Get tool configuration |
| GET | `/api/monitoring/health` | Health check |
| GET | `/api/monitoring/metrics` | System metrics |
| GET | `/api/monitoring/activity` | Recent activity |
| GET | `/api/monitoring/system` | System information |
| GET | `/api/mccs` | Get Merchant Category Codes |

---

**Ready to build intelligent agents!** 🤖
