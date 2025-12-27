# 🚀 Agent_X - Quick Start Guide

Get your agentic AI platform running in 5 minutes!

## Prerequisites

- **Docker Desktop** installed and running
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

# Agent environment
cd ../agents  
cp .env.example .env

# Edit agents/.env and add the same API key
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
- ✅ `agentx-backend` - running

## Step 3: Verify Backend

```bash
# Test health check
curl http://localhost:3001/api/monitoring/health

# Expected response:
# {"success":true,"data":{"status":"healthy","services":{"database":true,"redis":true}}}
```

## Step 4: Start Agent Worker

You can run either or both agents depending on your needs.

### Option A: Sales Agent

```bash
# In a new terminal window
cd agents/sales_agent
python worker.py
```

You should see:
```
Sales Agent Worker started, listening on tasks:sales
Using LLM provider: openai
```

### Option B: Market Research Agent

```bash
# In a new terminal window
cd agents/market_research_agent
python worker.py
```

You should see:
```
Market Research Agent Worker started, listening on tasks:market_research
Using LLM provider: openai
```

> **Note**: Market Research Agent requires additional dependencies:
> - `duckduckgo-search` (web search)
> - `beautifulsoup4` (web scraping)
> - `python-whois` (domain analysis)
> 
> These are included in `agents/requirements.txt`

## Step 5: Test the System

### Option A: Direct Agent Test (No Backend)

**Sales Agent:**
```bash
cd agents/sales_agent
python test_agent.py
```

**Market Research Agent:**
```bash
cd agents/market_research_agent
python test_agent.py
```

These will test the agents directly using the LLM.

### Option B: Full Stack Test (API → Queue → Agent)

**Test Sales Agent:**

```bash
# 1. Get Sales Agent ID
curl http://localhost:3001/api/agents | jq '.data[] | select(.type=="sales") | .id'

# 2. Execute email generation task (replace {agent-id})
curl -X POST http://localhost:3001/api/agents/{agent-id}/execute \
  -H "Content-Type: application/json" \
  -d '{
    "action": "generate_email",
    "input": {
      "recipientName": "John Doe",
      "context": "Follow up after demo"
    },
    "priority": "high"
  }'

# 3. Check task result (replace {task-id} from response)
curl http://localhost:3001/api/tasks/{task-id}
```

**Test Market Research Agent:**

```bash
# 1. Get Market Research Agent ID
curl http://localhost:3001/api/agents | jq '.data[] | select(.type=="market_research") | .id'

# 2. Execute site scan (replace {agent-id})
curl -X POST http://localhost:3001/api/agents/{agent-id}/execute \
  -H "Content-Type: application/json" \
  -d '{
    "action": "comprehensive_site_scan",
    "input": {
      "url": "https://example.com",
      "business_name": "Example Inc"
    },
    "priority": "high"
  }'

# 3. Execute web search (replace {agent-id})
curl -X POST http://localhost:3001/api/agents/{agent-id}/execute \
  -H "Content-Type: application/json" \
  -d '{
    "action": "search_web",
    "input": {
      "query": "artificial intelligence trends 2024",
      "max_results": 5
    }
  }'

# 4. Check task result
curl http://localhost:3001/api/tasks/{task-id}
```

SELECT id, type, name, status FROM agents;

# View recent tasks
SELECT id, action, status, created_at FROM tasks ORDER BY created_at DESC LIMIT 5;

# Exit
\q
```

## Step 6: Access the Frontend

```bash
# In Agent_X root directory (new terminal)
npm install  # First time only
npm run dev
```

Dashboard will open at http://localhost:5173

**Active Pages:**
- ✅ Dashboard Home - Real-time system metrics
- ✅ Market Research Agent - Full functionality with site scan, crawler, search
- ✅ Sales Agent - Email generation and lead qualification
- ✅ Activity Logs - Live task execution history
- ✅ Integrations - Integration management
- 🔄 Other agent pages - UI only (backend not implemented)

---

## Troubleshooting

### Backend won't start
```bash
docker-compose logs backend
# Look for database connection errors
# Make sure DATABASE_URL in backend/.env matches docker-compose.yml
```

### Worker can't find modules
```bash
cd agents
pip install -r requirements.txt
# Make sure you're in a Python 3.11+ environment
```

### "API key not set" error
```bash
# Backend needs: backend/.env
# Agents need: agents/.env
# Make sure both have OPENAI_API_KEY or ANTHROPIC_API_KEY
```

### Database not initialized
```bash
docker-compose down -v  # Remove volumes
docker-compose up -d    # Restart (will re-run schema.sql)
```

---

## What's Working

✅ Backend API with 9 agents configured  
✅ PostgreSQL database with schema  
✅ Redis message queue  
✅ **Sales Agent** with LLM integration  
✅ **Market Research Agent** with web search, crawling, site scanning  
✅ Task processing pipeline  
✅ **Frontend-Backend Integration** for dashboard, agents, tasks  
✅ Real-time monitoring and metrics  
✅ Activity logs with live data  
✅ Integration management  

## What's Next

After verifying the system works:

1. **Implement Remaining Agents** - Support, HR, Legal, Finance, Marketing, Intelligence, Lead Sourcing
2. **WebSocket Integration** - Add real-time updates for task status
3. **Advanced Features** - RAG, workflows, analytics

---

## Quick Reference

| Service | URL | Credentials |
|---------|-----|-------------|
| Backend API | http://localhost:3001 | - |
| PostgreSQL | localhost:5432 | postgres / dev_password |
| Redis | localhost:6379 | - |
| Frontend | http://localhost:5173 | - |

## Support

- 📖 Backend docs: `backend/README.md`
- 🐍 Agent docs: `agents/README.md`
- 🎯 Implementation plan: See artifact
- 🚶 Walkthrough: See artifact

---

**Ready to build intelligent agents!** 🤖
