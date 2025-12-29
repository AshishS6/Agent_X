# Agent_X - Agentic AI Platform

Transform your business workflows with autonomous AI agents powered by GPT-4, Claude, and open-source models.

## 🎯 What is Agent_X?

Agent_X is a production-ready agentic AI platform featuring:

- **9 Specialized AI Agents** for Sales, Support, HR, Legal, Finance, and more
- **Multi-LLM Support** - OpenAI, Anthropic Claude, or Ollama (local/free)
- **Go + Python Architecture** - High-performance Go backend with Python AI agents
- **CLI-Based Execution** - Agents run as CLI tools, spawned directly by the backend
- **Beautiful Dashboard** - React UI for managing and monitoring agents

## 🚀 Quick Start

```bash
# 1. Clone and configure
git clone <your-repo>
cd Agent_X
cp backend/.env.example backend/.env  # Add your OpenAI/Anthropic API key

# 2. Start infrastructure (PostgreSQL & Redis)
docker-compose up -d

# 3. Install Python dependencies
cd backend/agents && pip install -r requirements.txt

# 4. Start the Go backend
cd backend && make dev

# 5. Start the frontend
cd .. && npm run dev
```

See [QUICKSTART.md](./QUICKSTART.md) for detailed setup.

## 📦 What's Included

### ✅ Active Features

- ✅ **Go Backend API** (Gin + PostgreSQL)
  - RESTful endpoints for agents, tasks, monitoring
  - CLI tool executor with hybrid concurrency control
  - PostgreSQL database with 9 agents pre-configured
  - Real-time system metrics and health monitoring
  
- ✅ **Agent Framework** (Python + LangChain)
  - Base agent class with ReAct pattern
  - Multi-LLM support (OpenAI/Anthropic/Ollama)
  - CLI interface for subprocess execution
  - Tool system, memory, and logging
  
- ✅ **Market Research Agent** - Fully functional!
  - Web search via DuckDuckGo (free)
  - Advanced web crawler with keyword tracking
  - Comprehensive site scanning (V2 modular engine)
  - Content risk detection and business details extraction
  - SEO analysis and tech stack detection
  
- ✅ **Sales Agent** - Fully functional!
  - Email generation
  - Lead qualification
  - Calendar integration
  
- ✅ **Frontend-Backend Integration**
  - Dashboard with real-time metrics
  - Agent execution and monitoring
  - Activity logs with live data
  - Task tracking and history
  
- ✅ **Docker Deployment**
  - One-command setup with docker-compose
  - PostgreSQL, Redis infrastructure

### 🔄 Planned Features

- [ ] Remaining 7 agents (Support, HR, Legal, Finance, Marketing, Intelligence, Lead Sourcing)
- [ ] WebSocket for real-time updates
- [ ] RAG with vector database
- [ ] Workflow automation

## 🏗️ Architecture

```
Frontend (React)
     ↓ HTTP
Go Backend (Gin)
     ↓ subprocess spawn
Python CLI Agents
     ↓ LLM API
OpenAI / Claude / Ollama
```

### CLI-Based Agent Execution

Unlike queue-based systems, Agent_X runs Python agents as CLI tools:

1. **Frontend** sends request to Go backend
2. **Go backend** spawns `python3 cli.py --input '{...}'`
3. **Python agent** executes and returns JSON to stdout
4. **Go backend** parses output and updates database

This provides:
- **Simpler architecture** - No Redis workers needed
- **Better observability** - Direct stdout/stderr logging
- **Easy debugging** - Run agents standalone
- **Hybrid concurrency** - Global + per-tool limits

## 📚 Documentation

- [Quick Start Guide](./QUICKSTART.md) - Get running in 5 minutes
- [Go Backend README](./backend/README.md) - API documentation
- [Agents README](./backend/agents/README.md) - Agent development guide

## 🎬 Demo

**Market Research Agent - Site Scan (V2 Engine):**
```bash
# Execute via API
curl -X POST http://localhost:3001/api/agents/market_research/execute \
  -H "Content-Type: application/json" \
  -d '{
    "action": "comprehensive_site_scan",
    "input": {"topic": "https://example.com", "business_name": "Example Inc"}
  }'

# Or run CLI directly
python cli.py --input '{"action": "site_scan", "url": "https://example.com"}'
```

**Sales Agent - Email Generation:**
```bash
curl -X POST http://localhost:3001/api/agents/sales/execute \
  -H "Content-Type: application/json" \
  -d '{
    "action": "generate_email",
    "input": {"recipientName": "Jane Smith", "context": "Follow up after demo"}
  }'
```

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | React, TypeScript, Vite, TailwindCSS |
| Backend API | **Go 1.21+, Gin** |
| Database | PostgreSQL 16 |
| Agents | Python 3.11+, LangChain |
| LLMs | OpenAI GPT-4, Anthropic Claude, Ollama |
| Web Search | DuckDuckGo Search API (Free) |
| Web Scraping | BeautifulSoup4, Requests |
| Deployment | Docker Compose |

## 📈 Roadmap

**Phase 1: Core Infrastructure** ✅ COMPLETE  
Go Backend, Database, Agent CLI Framework, Frontend Integration

**Phase 2: V2 Engine** ✅ COMPLETE  
Modular scan engine, SEO analysis, tech stack detection

**Phase 3: Multi-Agent System** 🚧 IN PROGRESS  
Implement remaining 7 agents, advanced tool integrations

**Phase 4: Production**  
Security hardening, performance optimization, cloud deployment

## 🤝 Adding New Agents

1. Create CLI tool in `backend/agents/<agent_name>/cli.py`
2. Register in `backend/internal/tools/registry.go`:

```go
"my_agent": {
    Name:        "My Agent",
    Command:     "python3",
    Args:        []string{"agents/my_agent/cli.py"},
    Timeout:     3 * time.Minute,
    AgentType:   "my_agent",
},
```

3. Seed agent in database (optional)

## 📄 License

MIT

## 🙋 Support

- **Issues**: GitHub Issues
- **Docs**: See documentation above

---

Built with ❤️ using Go, Python, LangChain, and OpenAI
