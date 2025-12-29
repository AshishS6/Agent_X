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
- ✅ `agentx-postgres` - running
- ✅ `agentx-redis` - running

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

You should see:
```
[GIN-debug] Listening and serving HTTP on :3001
```

The Go backend:
- Exposes REST API on port 3001
- Spawns Python CLI agents as subprocesses
- Manages hybrid concurrency (global + per-tool limits)

## Step 5: Verify System

```bash
# Health check
curl http://localhost:3001/api/monitoring/health

# Expected response:
# {"success":true,"data":{"status":"healthy","services":{"database":true}}}

# List available tools
curl http://localhost:3001/api/tools
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

You can test agents directly:

```bash
# Market Research Agent
cd backend/agents/market_research_agent
python cli.py --input '{"action": "site_scan", "url": "https://example.com"}'

# Sales Agent
cd backend/agents/sales_agent
python cli.py --input '{"action": "generate_email", "recipientName": "Jane", "context": "Demo follow-up"}'

# Dry run (validate input without executing)
python cli.py --input '{"action": "site_scan", "url": "https://example.com"}' --dry-run
```

## Step 7: Start the Frontend

```bash
# In Agent_X root directory (new terminal)
npm install  # First time only
npm run dev
```

Dashboard opens at http://localhost:5173

**Active Pages:**
- ✅ Dashboard Home - Real-time system metrics
- ✅ Market Research Agent - Site scan with V2 engine
- ✅ Sales Agent - Email generation and lead qualification
- ✅ Activity Logs - Live task execution history

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
```

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

**Key Insight**: No Redis workers! The Go backend spawns Python agents directly as subprocesses, capturing stdout as JSON output.

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
| POST | `/api/agents/:name/execute` | Execute agent (e.g., `market_research`, `sales`) |
| GET | `/api/tasks/:id` | Get task result |
| GET | `/api/tools` | List available CLI tools |
| GET | `/api/monitoring/health` | Health check |

---

**Ready to build intelligent agents!** 🤖
