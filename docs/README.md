# Agent_X - Agentic AI Platform

Transform your business workflows with autonomous AI agents powered by GPT-4, Claude, and open-source models.

## 🎯 What is Agent_X?

Agent_X is a production-ready agentic AI platform featuring:

- **Functional Agents + Assistants** for Site Scan, Market Research, Blog, Sales (partial), plus Fintech/General/Code chat assistants
- **Multi-LLM Support** - OpenAI, Anthropic Claude, or Ollama (local/free)
- **Go + Python Architecture** - High-performance Go backend (Gin framework) with Python AI agents
- **CLI-Based Execution** - Agents run as CLI tools, spawned directly by the Go backend as subprocesses
- **Beautiful Dashboard** - React + TypeScript UI for managing and monitoring agents
- **Hybrid Concurrency Control** - Global and per-tool limits for resource management

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
  - RESTful endpoints for agents, tasks, monitoring, and MCC (Merchant Category Codes)
  - CLI tool executor with hybrid concurrency control (global + per-tool limits)
  - PostgreSQL database with 9 agents pre-configured
  - Real-time system metrics and health monitoring
  - Task pagination support
  - Graceful shutdown handling
  
- ✅ **Agent Framework** (Python + LangChain)
  - Base agent class with ReAct pattern
  - Multi-LLM support (OpenAI/Anthropic/Ollama)
  - CLI interface for subprocess execution
  - Tool system, memory, and logging
  - Standardized JSON input/output contract
  
- ✅ **Site Scan Agent** - Production-grade
  - Comprehensive site scanning (V2 modular engine)
  - Content risk detection and business details extraction
  - SEO analysis and tech stack detection
  - Page caching for efficient re-scans
  - Change detection and compliance monitoring
  - KYC site scan decisioning
  
- ✅ **Market Research Agent** - LLM-based research
  - Web search via DuckDuckGo (free)
  - Competitor and trend analysis
  - Lightweight crawl via `monitor_url`
  
- ✅ **Blog Agent** - Document workflow
  - Outline and draft generation
  - Brand style normalization
  
- ✅ **Assistants (Chat)** - Fintech, General, Code
  - RAG-enabled fintech assistant via knowledge base
  
- ⚠️ **Sales Agent** - Partial scaffold
  - Email generation with context awareness
  - Lead qualification
  - Calendar integration support
  
- ✅ **Frontend-Backend Integration**
  - Dashboard with real-time metrics
  - Agent execution and monitoring
  - Activity logs with live data and pagination
  - Task tracking and history
  - 9 agent pages (UI ready, 7 agents pending implementation)
  
- ✅ **Docker Deployment**
  - One-command setup with docker-compose
  - PostgreSQL 16 and Redis 7 infrastructure
  - Automatic schema initialization

### 🔄 Planned Features

- [ ] Remaining 7 agents implementation (Support, HR, Legal, Finance, Marketing, Intelligence, Lead Sourcing)
- [ ] WebSocket for real-time updates
- [ ] Expanded RAG coverage (more knowledge bases)
- [ ] Workflow automation
- [ ] Enhanced error recovery and retry mechanisms

## 🏗️ Architecture

```
Frontend (React + TypeScript + Vite)
     ↓ HTTP REST API
Go Backend (Gin Framework)
     ↓ os/exec subprocess spawn
Python CLI Agents (LangChain)
     ↓ HTTP API calls
OpenAI / Claude / Ollama
     ↓
PostgreSQL Database (Task storage, agent config)
```

### CLI-Based Agent Execution

Unlike queue-based systems, Agent_X runs Python agents as CLI tools:

1. **Frontend** sends HTTP request to Go backend (`POST /api/agents/:name/execute`)
2. **Go backend** creates task record in PostgreSQL (status: "pending")
3. **Go backend** spawns Python subprocess: `python3 backend/agents/{agent}/cli.py --input '{...}'`
4. **Python agent** executes (may call LLM APIs, web scraping, etc.)
5. **Python agent** returns JSON to stdout: `{"status": "completed", "output": {...}}`
6. **Go backend** captures stdout, parses JSON, and updates task in database
7. **Frontend** polls task status or receives result

This provides:
- **Simpler architecture** - No Redis workers or message queues needed
- **Better observability** - Direct stdout/stderr logging captured by Go
- **Easy debugging** - Run agents standalone: `python cli.py --input '...'`
- **Hybrid concurrency** - Global limit (10) + per-tool limit (5) prevents resource exhaustion
- **Isolation** - Each agent runs in separate process, failures don't crash backend

## 📚 Documentation

- [Quick Start Guide](./QUICKSTART.md) - Get running in 5 minutes
- [Architecture Guide](./ARCHITECTURE.md) - Deep dive into system design and internals
- [Go Backend README](../backend/README.md) - Backend API documentation and development guide
- [Agents README](../backend/agents/README.md) - Agent development guide and CLI contract
- [Site Scan Agent Docs](../backend/agents/site_scan_agent/docs/) - Site scan engine documentation

## 🎬 Demo

**Site Scan Agent - Site Scan (V2 Engine):**
```bash
# Execute via API
curl -X POST http://localhost:3001/api/agents/site_scan/execute \
  -H "Content-Type: application/json" \
  -d '{
    "action": "comprehensive_site_scan",
    "input": {"topic": "https://example.com", "business_name": "Example Inc"}
  }'

# Response includes task ID - poll for results:
curl http://localhost:3001/api/tasks/{task-id}

# Or run CLI directly (for testing)
cd backend/agents/site_scan_agent
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

**Assistants - Chat (Fintech):**
```bash
curl -X POST http://localhost:3001/api/assistants/fintech/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How do I integrate Zwitch payment gateway?",
    "knowledge_base": "fintech",
    "assistant": "fintech"
  }'
```

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | React 19, TypeScript, Vite 7, TailwindCSS 4, React Router 7 |
| Backend API | **Go 1.21+, Gin Framework** |
| Database | PostgreSQL 16 (with Redis 7 for future features) |
| Agents | Python 3.11+, LangChain, LangChain-OpenAI, LangChain-Anthropic |
| LLMs | OpenAI GPT-4, Anthropic Claude, Ollama (local) |
| Web Search | DuckDuckGo Search API (Free) |
| Web Scraping | BeautifulSoup4, Requests, python-whois |
| Deployment | Docker Compose |
| Concurrency | Go goroutines with semaphore-based limits |

## 📈 Roadmap

**Phase 1: Core Infrastructure** ✅ COMPLETE  
Go Backend, Database, Agent CLI Framework, Frontend Integration, Hybrid Concurrency Control

**Phase 2: V2 Engine** ✅ COMPLETE  
Modular scan engine, SEO analysis, tech stack detection, page caching, change detection

**Phase 3: Multi-Agent System** 🚧 IN PROGRESS  
- ✅ Site Scan Agent (fully functional)
- ✅ Market Research Agent (LLM-based research)
- ✅ Blog Agent (document workflow)
- ✅ Assistants (fintech, general, code)
- ⚠️ Sales Agent (partial scaffold)
- 🔄 Support Agent (UI ready, implementation pending)
- 🔄 HR Agent (UI ready, implementation pending)
- 🔄 Legal Agent (UI ready, implementation pending)
- 🔄 Finance Agent (UI ready, implementation pending)
- 🔄 Marketing Agent (UI ready, implementation pending)
- 🔄 Intelligence Agent (UI ready, implementation pending)
- 🔄 Lead Sourcing Agent (UI ready, implementation pending)

**Phase 4: Production**  
Security hardening, performance optimization, cloud deployment, WebSocket real-time updates, RAG integration

## 🤝 Adding New Agents

1. Create CLI tool in `backend/agents/<agent_name>/cli.py` following the CLI contract:
   - Accept `--input` JSON argument
   - Output JSON to stdout: `{"status": "completed|failed", "output": {...}, "error": "..."}`
   - Write logs to stderr
   - Exit code: 0 = success, non-zero = failure

2. Register in `backend/internal/tools/registry.go`:

```go
"my_agent": {
    Name:             "My Agent",
    Description:      "What this agent does",
    Command:          "python3",
    Args:             []string{"backend/agents/my_agent/cli.py"},
    Timeout:          3 * time.Minute,
    WorkingDir:       ".",
    ConcurrencyLimit: 5,
    AgentType:        "my_agent",
},
```

3. Agent is automatically seeded in database via `database/schema.sql` (or add manually)

4. Frontend page already exists at `src/pages/MyAgent.tsx` (update as needed)

See [backend/agents/README.md](../backend/agents/README.md) for detailed agent development guide.

## 📄 License

MIT

## 🙋 Support

- **Issues**: GitHub Issues
- **Docs**: See documentation above

---

Built with ❤️ using Go, Python, LangChain, and OpenAI
