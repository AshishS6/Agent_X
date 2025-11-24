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

```bash
# In a new terminal window
cd agents

# Install Python dependencies (first time only)
pip install -r requirements.txt

# Start Sales Agent worker
cd sales_agent
python worker.py
```

You should see:
```
Sales Agent Worker started, listening on tasks:sales
Using LLM provider: openai
```

## Step 5: Test the System

### Option A: Direct Agent Test (No Backend)

```bash
# In agents/sales_agent directory
python test_agent.py
```

This will generate a sample email and qualify a lead using the AI.

### Option B: Full Stack Test (API → Queue → Agent)

```bash
# 1. Get Sales Agent ID
curl http://localhost:3001/api/agents | jq '.data[] | select(.type=="sales") | .id'

# 2. Execute task (replace {agent-id} with actual ID)
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

# Copy the task ID from response

# 3. Watch worker logs (you should see it processing)

# 4. Check task result (replace {task-id})
curl http://localhost:3001/api/tasks/{task-id}
```

## Step 6: Explore the Database

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres -d agentx

# View agents
SELECT id, type, name, status FROM agents;

# View recent tasks
SELECT id, action, status, created_at FROM tasks ORDER BY created_at DESC LIMIT 5;

# Exit
\q
```

## Step 7: Run Your Frontend

```bash
# In Agent_X root directory
npm run dev
```

Dashboard will open at http://localhost:5173

> 🔴 **Note**: Frontend currently shows mock data. Phase 1 task remaining is to connect it to the backend APIs.

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
✅ Sales Agent with LLM integration  
✅ Task processing pipeline  
✅ Email generation  
✅ Lead qualification  

## What's Next

After verifying the system works:

1. **Frontend Integration** - Connect React dashboard to APIs
2. **WebSocket** - Add real-time updates
3. **Phase 2** - Implement remaining 8 agents

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
