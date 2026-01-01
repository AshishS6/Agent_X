# Architecture & Setup Guide

This document provides detailed instructions for cloning, setting up, and understanding the architecture of the **Agent_X** project.

## 1. Cloning & Setup Logic

To get this project running on a new machine, follow these steps.

### Prerequisites
- **Git**
- **Docker Desktop** (for PostgreSQL & Redis)
- **Go 1.21+** (for the Backend API)
- **Python 3.11+** (for AI Agents)
- **Node.js 18+** (for the Frontend Dashboard)

### Step-by-Step Installation

#### 1. Clone the Repository
```bash
git clone <repository_url>
cd Agent_X
```

#### 2. Environment Configuration
The project uses environment variables for configuration. You need to set these up for both the backend and agents.

**Backend Configuration:**
```bash
cd backend
cp .env.example .env
```
Open `backend/.env` and update the following:
- `OPENAI_API_KEY`: Your OpenAI key (required for agents).
- `DATABASE_URL`: Default is set for Docker (`postgres://postgres:dev_password@localhost:5432/agentx?sslmode=disable`). Change only if using external DB.

#### 3. Database & Infrastructure
The database schema is defined in `database/schema.sql`. This file is **automatically applied** when you start the Docker containers.

```bash
# Return to root directory
cd .. 
docker-compose up -d
```
*This command starts PostgreSQL 16 and Redis 7. Postgres will automatically execute `database/schema.sql` on first startup to create all tables (agents, tasks, conversations, agent_metrics, integrations, crawl_page_cache, site_scan_snapshots) and seed the 9 agents.*

**Note**: Redis is included for future features (WebSocket, real-time updates). Currently, the system uses direct subprocess execution without message queues.

#### 4. Python Agent Dependencies
The agents run as subprocesses and need their dependencies installed in the system or a virtual environment.

```bash
cd backend/agents
pip install -r requirements.txt
```
*Note: We recommend using a virtual environment (`python -m venv venv && source venv/bin/activate`) before installing.*

#### 5. Start the Go Backend
The backend listens for API requests and spawns Python agents as subprocesses.

```bash
cd backend
make dev
```
*Port: 3001*

**Note**: The `make dev` command uses `air` for hot reload if installed, otherwise falls back to `go run ./cmd/server`. The actual entry point is `cmd/server/main.go`, not `main.go` in the backend root.

#### 6. Start the Frontend
The frontend is a React + TypeScript dashboard to visualize agent activities.

```bash
cd ..  # Return to project root
npm install  # First time only
npm run dev
```
*Port: 5173 (Vite dev server)*

The frontend uses:
- React 19 with TypeScript
- Vite 7 for build tooling
- TailwindCSS 4 for styling
- React Router 7 for navigation
- Axios for API calls

---

## 2. Architecture & Internals

### High-Level Overview
```
┌─────────────────────────────────┐
│  Frontend (React + TypeScript)  │
│  localhost:5173                 │
└────────────┬────────────────────┘
             │ HTTP REST API
             ↓
┌─────────────────────────────────┐
│  Go Backend (Gin Framework)     │
│  localhost:3001                 │
│  - Handlers (agents, tasks)     │
│  - Executor (subprocess spawn)   │
│  - Concurrency control          │
└────────────┬────────────────────┘
             │ os/exec subprocess
             ↓
┌─────────────────────────────────┐
│  Python CLI Agents              │
│  - Market Research Agent        │
│  - Sales Agent                  │
│  - (7 more pending)             │
└────────────┬────────────────────┘
             │ HTTP API calls
             ↓
┌─────────────────────────────────┐
│  External Services              │
│  - OpenAI / Anthropic / Ollama  │
│  - DuckDuckGo Search            │
│  - Web scraping targets         │
└─────────────────────────────────┘
             │
             ↓
┌─────────────────────────────────┐
│  PostgreSQL Database            │
│  - Tasks, Agents, Metrics      │
│  - Conversations, Integrations  │
└─────────────────────────────────┘
```

### Key Design Decisions
1.  **CLI-First Agents**: Agents are not microservices or long-running processes. They are CLI tools executed on-demand. This simplifies deployment and debugging. You can run `python cli.py --input '...'` manually to debug.
2.  **Hybrid Concurrency**: The Go backend manages concurrency using semaphores:
    - **Global Limit**: Maximum 10 concurrent tool executions across all tools
    - **Per-Tool Limit**: Maximum 5 concurrent executions per tool type
    - Prevents resource exhaustion while allowing parallel execution
3.  **No Queue Worker**: There is no separate Celery/Redis worker process. The Go backend spawns Python subprocesses directly using `os/exec`, capturing stdout/stderr. Redis is included for future WebSocket features.
4.  **Standardized I/O Contract**: All agents follow the same CLI contract:
    - Input: `--input '{"action": "...", ...}'` (JSON string)
    - Output: JSON to stdout: `{"status": "completed|failed", "output": {...}, "error": "..."}`
    - Logs: Write to stderr (not stdout)
    - Exit code: 0 = success, non-zero = failure
5.  **Async Task Pattern**: Tasks are created immediately with "pending" status, then executed asynchronously in a goroutine. Frontend polls task status.

### Deep Dive: How Agents Work

All agents follow a strict contract:
- **Input**: JSON string via `--input` argument.
- **Output**: JSON object to `stdout`.
- **Logs**: Text logs to `stderr`.

#### 1. Market Research Agent
- **Location**: `backend/agents/market_research_agent`
- **Entry Point**: `cli.py`
- **Status**: ✅ Fully functional
- **Core Logic**:
    - **Site Scan**: When `action` is `site_scan` or `comprehensive_site_scan`, it uses a specialized `ModularScanEngine` (V2 Engine) located in `scan_engine.py`.
    - **V2 Modular Engine** performs:
        - **Crawling**: Fetches page HTML with robots.txt and sitemap support
        - **Page Caching**: Stores crawled pages in `crawl_page_cache` table for efficient re-scans
        - **Extraction**: Uses `BeautifulSoup` to parse metadata, text, and links
        - **Tech Stack Detection**: Analyzes HTML/headers to find technologies (React, WordPress, etc.)
        - **SEO Analysis**: Checks meta tags, headings structure, load times, and provides recommendations
        - **Compliance Monitoring**: Detects privacy policies, terms of service, GDPR compliance
        - **Change Detection**: Tracks changes between scans using page hashes
        - **Business Intelligence**: Extracts business metadata, contact info, social links
    - **General Research**: For other actions (e.g., "Find competitors for X"), it initializes a LangChain ReAct agent (`main.py`) with tools like `DuckDuckGoSearch` to browse the web and synthesize answers using an LLM.
    - **Output Format**: Returns structured JSON matching `v2_output_contract.md` specification

#### 2. Sales Agent
- **Location**: `backend/agents/sales_agent`
- **Entry Point**: `cli.py`
- **Status**: ✅ Fully functional
- **Core Logic**:
    - **Email Generation**: `generate_email` action - creates personalized sales emails
    - **Lead Qualification**: `qualify_lead` action - scores and qualifies leads
    - **Calendar Integration**: Support for meeting scheduling (implementation pending)
    - **Implementation**: Uses `main.create_sales_agent` to build a LangChain ReAct agent
    - **Process**:
        1. Receives input context (prospect name, company, context)
        2. Queries LLM (e.g., GPT-4) with prompt templates designed for sales copy
        3. Returns structured JSON with the generated email draft or qualification score

### API Internal Flow
When you call `POST /api/agents/market_research/execute`:

1.  **Request Handler**: `internal/handlers/agents.go` (`Execute` method) receives the request
2.  **Agent Lookup**: Finds agent by type (`market_research`) in database
3.  **Tool Resolution**: Maps agent type to CLI tool config in `internal/tools/registry.go`
4.  **Task Creation**: Creates task record in PostgreSQL with status "pending"
5.  **Async Execution**: Spawns goroutine to execute tool:
    - Updates task status to "processing"
    - **Concurrency Check**: `internal/tools/executor.go` checks global and per-tool semaphores
    - **Command Construction**: Builds command:
      ```bash
      python3 backend/agents/market_research_agent/cli.py --input '{"action": "...", "task_id": "..."}'
      ```
    - **Subprocess Spawn**: Uses `os/exec` to run Python process with timeout
    - **Output Capture**: Captures stdout (JSON) and stderr (logs)
6.  **Result Processing**: Parses JSON from stdout:
    - If `status: "failed"` → Updates task with error message
    - If `status: "completed"` → Updates task with output JSON
7.  **Response**: Returns Task ID immediately (async pattern)
8.  **Frontend Polling**: Frontend polls `GET /api/tasks/:id` to get result

**Error Handling**:
- Subprocess timeout → Task marked as "failed"
- Non-zero exit code → Task marked as "failed"
- Invalid JSON output → Task marked as "failed" with parse error
- Concurrency limit reached → Task remains "pending" until slot available
