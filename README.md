# Agent_X - Agentic AI Platform

Transform your business workflows with autonomous AI agents powered by GPT-4, Claude, and open-source models.

## 🎯 What is Agent_X?

Agent_X is a production-ready agentic AI platform featuring:

- **9 Specialized AI Agents** for Sales, Support, HR, Legal, Finance, and more
- **Multi-LLM Support** - OpenAI, Anthropic Claude, or Ollama (local/free)
- **Microservices Architecture** - Scalable backend with message queuing
- **Beautiful Dashboard** - React UI for managing and monitoring agents
- **Real Agent Execution** - Not just a demo, actual LLM-powered agents that work

## 🚀 Quick Start

```bash
# 1. Clone and configure
git clone <your-repo>
cd Agent_X
cp backend/.env.example backend/.env  # Add your OpenAI/Anthropic API key
cp agents/.env.example agents/.env

# 2. Start infrastructure
docker-compose up -d

# 3. Run agent worker
cd agents && pip install -r requirements.txt
cd sales_agent && python worker.py

# 4. Test it!
python test_agent.py
```

See [QUICKSTART.md](./QUICKSTART.md) for detailed setup.

## 📦 What's Included

### Phase 1: Core Infrastructure ✅ COMPLETE

- ✅ **Backend API** (Node.js/TypeScript + Express)
  - RESTful endpoints for agents, tasks, monitoring
  - PostgreSQL database with 9 agents pre-configured
  - Redis queue for async task processing
  
- ✅ **Agent Framework** (Python + LangChain)
  - Base agent class with ReAct pattern
  - Multi-LLM support (OpenAI/Anthropic/Ollama)
  - Tool system, memory, logging
  
- ✅ **Sales Agent** - Fully functional!
  - Email generation
  - Lead qualification
  - Queue worker for autonomous processing
  
- ✅ **Docker Deployment**
  - One-command setup with docker-compose
  - PostgreSQL, Redis, Backend API
  
- ✅ **Frontend Dashboard** (React + TypeScript)
  - Beautiful dark theme UI
  - Agent management pages
  - System monitoring (currently with mock data)

### Coming in Phase 2-4

- [ ] Frontend-backend integration
- [ ] Remaining 8 agents implementation
- [ ] WebSocket for real-time updates
- [ ] RAG with vector database
- [ ] Workflow automation
- [ ] Production deployment to cloud

## 🏗️ Architecture

```
Frontend (React)
     ↓ HTTP
Backend API (Node.js)
     ↓ Redis Queue
Agent Workers (Python)
     ↓ LLM Calls
OpenAI / Claude / Ollama
```

- **Backend**: Express.js REST API
- **Database**: PostgreSQL with JSONB
- **Queue**: Redis Streams
- **Agents**: Python + LangChain
- **LLMs**: Multi-provider support

## 📚 Documentation

- [Quick Start Guide](./QUICKSTART.md) - Get running in 5 minutes
- [Backend README](./backend/README.md) - API documentation
- [Agents README](./agents/README.md) - Agent development guide
- [Implementation Plan](./docs/implementation_plan.md) - Full roadmap
- [Walkthrough](./docs/walkthrough.md) - What we've built

## 🎬 Demo

**Sales Agent Email Generation:**
```python
# Input
task = {
  "action": "generate_email",
  "input": {
    "recipientName": "Jane Smith",
    "context": "Follow up after demo"
  }
}

# Output (from GPT-4)
{
  "email": {
    "subject": "Following Up on Our Demo",
    "body": "Hi Jane,\n\nGreat connecting with you yesterday..."
  }
}
```

**Lead Qualification:**
```python
# Input: Company info, pain points, budget
# Output: Score (1-10), recommendation, reasoning
```

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | React, TypeScript, Vite, TailwindCSS |
| Backend API | Node.js, Express, TypeScript |
| Database | PostgreSQL 16 |
| Queue | Redis 7 |
| Agents | Python 3.11+, LangChain |
| LLMs | OpenAI GPT-4, Anthropic Claude, Ollama |
| Deployment | Docker Compose |

## 📈 Roadmap

**Phase 1: Core Infrastructure** ✅ COMPLETE (Week 1-2)  
Backend API, Database, Redis, Sales Agent, Docker setup

**Phase 2: Multi-Agent System** 🚧 NEXT (Week 3-4)  
Implement remaining 8 agents, tool integrations, frontend integration

**Phase 3: Advanced Features** (Week 5-6)  
RAG, persistent memory, workflows, real-time monitoring

**Phase 4: Production** (Week 7-8)  
Security, performance, cloud deployment, CI/CD

## 🤝 Contributing

Agents are designed to be easy to extend:

```python
class MyAgent(BaseAgent):
    def _register_tools(self):
        # Add custom tools
        
    def _get_system_prompt(self):
        return "You are a helpful..."
        
# That's it! Framework handles the rest.
```

## 📄 License

MIT

## 🙋 Support

- **Issues**: GitHub Issues
- **Docs**: See `docs/` directory
- **Questions**: Open a discussion

---

Built with ❤️ using OpenAI, LangChain, and modern web technologies
