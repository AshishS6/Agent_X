# Agent_X Backend Setup Guide

## Quick Start (Docker)

### Prerequisites
- Docker Desktop installed
- Node.js 20+ (for local development without Docker)
- PostgreSQL client tools (optional, for direct database access)

### 1. Start All Services

```bash
# From the Agent_X directory
docker-compose up -d
```

This will start:
- **PostgreSQL** on port 5432
- **Redis** on port 6379
- **Backend API** on port 3001

### 2. Verify Services

```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f backend

# Test API health
curl http://localhost:3001/api/monitoring/health
```

### 3. Access the API

- **API Root**: http://localhost:3001
- **Health Check**: http://localhost:3001/api/monitoring/health
- **Agents List**: http://localhost:3001/api/agents
- **System Metrics**: http://localhost:3001/api/monitoring/metrics

---

##Local Development (Without Docker)

### 1. Install Dependencies

```bash
cd backend
npm install
```

### 2. Set Up PostgreSQL

```bash
# Install PostgreSQL (macOS with Homebrew)
brew install postgresql@16
brew services start postgresql@16

# Create database
createdb agentx

# Run schema
psql agentx < ../database/schema.sql
```

### 3. Set Up Redis

```bash
# Install Redis (macOS with Homebrew)
brew install redis
brew services start redis
```

### 4. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your API keys:
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
```

### 5. Start Backend

```bash
npm run dev
```

---

## API Documentation

### Agents

**GET /api/agents** - List all agents
```bash
curl http://localhost:3001/api/agents
```

**GET /api/agents/:id** - Get agent by ID
```bash
curl http://localhost:3001/api/agents/{agent-id}
```

**POST /api/agents/:id/execute** - Execute agent with task
```bash
curl -X POST http://localhost:3001/api/agents/{agent-id}/execute \
  -H "Content-Type: application/json" \
  -d '{
    "action": "generate_email",
    "input": {
      "recipientName": "John Doe",
      "context": "Follow up on demo call"
    },
    "priority": "high"
  }'
```

**PUT /api/agents/:id** - Update agent
```bash
curl -X PUT http://localhost:3001/api/agents/{agent-id} \
  -H "Content-Type: application/json" \
  -d '{"status": "paused"}'
```

**GET /api/agents/:id/metrics** - Get agent metrics
```bash
curl http://localhost:3001/api/agents/{agent-id}/metrics
```

### Tasks

**GET /api/tasks** - List tasks with filters
```bash
# All tasks
curl http://localhost:3001/api/tasks

# Filtered by agent
curl "http://localhost:3001/api/tasks?agentId={agent-id}&status=completed&limit=10"
```

**GET /api/tasks/:id** - Get task details
```bash
curl http://localhost:3001/api/tasks/{task-id}
```

### Monitoring

**GET /api/monitoring/health** - Health check
```bash
curl http://localhost:3001/api/monitoring/health
```

**GET /api/monitoring/metrics** - System metrics
```bash
curl http://localhost:3001/api/monitoring/metrics
```

**GET /api/monitoring/activity** - Recent activity
```bash
curl http://localhost:3001/api/monitoring/activity?limit=20
```

---

## Database Access

```bash
# Connect to database (Docker)
docker-compose exec postgres psql -U postgres -d agentx

# Connect to database (local)
psql agentx

# Useful queries:
SELECT * FROM agents;
SELECT * FROM tasks ORDER BY created_at DESC LIMIT 10;
SELECT * FROM agent_statistics;
```

---

## Troubleshooting

### Database connection failed
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# View logs
docker-compose logs postgres

# Restart service
docker-compose restart postgres
```

### Redis connection failed
```bash
# Check Redis is running
docker-compose ps redis

# Test connection
docker-compose exec redis redis-cli ping

# Should return: PONG
```

### Backend not starting
```bash
# Check logs
docker-compose logs backend

# Rebuild container
docker-compose build backend
docker-compose up -d backend
```

---

## Development Commands

```bash
# Install dependencies
cd backend && npm install

# Run in development mode
npm run dev

# Build for production
npm run build

# Run production build
npm start

# Lint code
npm run lint

# Run tests
npm test
```

---

## Next Steps

1. **Frontend Integration** - Update React frontend to call these APIs
2. **Agent Services** - Implement Python agent workers
3. **WebSocket** - Add real-time updates for dashboard
4. **Authentication** - Add JWT auth for production

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PORT` | No | 3001 | API server port |
| `NODE_ENV` | No | development | Environment mode |
| `DATABASE_URL` | Yes | - | PostgreSQL connection string |
| `REDIS_URL` | Yes | - | Redis connection string |
| `OPENAI_API_KEY` | No | - | OpenAI API key for LLM |
| `ANTHROPIC_API_KEY` | No | - | Anthropic Claude API key |
| `FRONTEND_URL` | No | http://localhost:5173 | Frontend URL for CORS |
| `LOG_LEVEL` | No | info | Logging level |
