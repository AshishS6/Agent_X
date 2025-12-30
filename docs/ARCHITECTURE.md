# Setup & Architecture Guide

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

#### 3. Database & Infrastructure (The "Migration")
The database schema is defined in `database/schema.sql`. This file is **automatically applied** when you start the Docker containers.

```bash
# Return to root directory
cd .. 
docker-compose up -d
```
*This command starts PostgreSQL and Redis. Postgres will automatically execute `database/schema.sql` on first startup to create all tables (agents, tasks, etc.).*

#### 4. Python Agent Dependencies
The agents run as subprocesses and need their dependencies installed in the system or a virtual environment.

```bash
cd backend/agents
pip install -r requirements.txt
```
*Note: We recommend using a virtual environment (`python -m venv venv && source venv/bin/activate`) before installing.*

#### 5. Start the Go Backend
The backend listens for API requests and spawns Python agents.

```bash
cd backend
make dev
```
*Port: 3001*

#### 6. Start the Frontend
The frontend is a React dashboard to visualize agent activities.

```bash
cd ../  # or 'cd frontend' if it's in a subfolder, looking at root based on package.json being there
npm install
npm run dev
```
*Port: 5173*

---

## 2. Architecture & Internals

### High-Level Overview
```
[Frontend (React)] 
      ↓ HTTP JSON
[Go Backend (Gin)] 
      ↓ os/exec (Subprocess)
[Python CLI Agents]
      ↓ HTTP
[External APIs (OpenAI, Search, etc.)]
```

### Key Design Decisions
1.  **CLI-First Agents**: Agents are not microservices. They are CLI tools. This simplifies deployment and debugging. You can run `python cli.py` manually to debug.
2.  **Hybrid Concurrency**: The Go backend manages concurrency. It limits how many agent subprocesses run simultaneously (Global Limit + Per-Tool Limit).
3.  **No Queue Worker**: There is no separate Celery/Redis worker process. The Go backend *is* the worker manager.

### Deep Dive: How Agents Work

All agents follow a strict contract:
- **Input**: JSON string via `--input` argument.
- **Output**: JSON object to `stdout`.
- **Logs**: Text logs to `stderr`.

#### 1. Market Research Agent
- **Location**: `backend/agents/market_research_agent`
- **Entry Point**: `cli.py`
- **Core Logic**:
    - **Site Scan**: When `action` is `site_scan` or `comprehensive_site_scan`, it bypasses the generic LangChain agent and uses a specialized `ModularScanEngine` (V2 Engine).
    - **V2 Engine**: Located in `scan_engine.py`. It performs:
        - **Crawling**: Fetches page HTML (using `requests` or headless browser if configured).
        - **Extraction**: Uses `BeautifulSoup` to parse metadata, text, and links.
        - **Tech Stack Detection**: Analyzes HTML/headers to find technologies (React, WordPress, etc.).
        - **SEO Analysis**: Checks meta tags, headings structure, and load times.
    - **General Research**: For other actions (e.g., "Find competitors for X"), it initializes a LangChain ReAct agent (`main.py`) with tools like `DuckDuckGoSearch` to browse the web and synthesize answers using an LLM.

#### 2. Sales Agent
- **Location**: `backend/agents/sales_agent`
- **Entry Point**: `cli.py`
- **Core Logic**:
    - **Email Generation**: `generate_email` action.
    - **Lead Qualification**: `qualify_lead` action.
    - **Implementation**: Uses `main.create_sales_agent` to build a LangChain agent.
    - **Process**:
        1. Receives input context (prospect name, company).
        2. Queries LLM (e.g., GPT-4) with prompt templates designed for sales copy.
        3. Returns structured JSON with the generated email draft or qualification score.

### API Internal Flow
When you call `POST /api/agents/market_research/execute`:
1.  **Backend**: `internal/api/handlers.go` receives the request.
2.  **Dispatcher**: `pkg/dispatcher` checks concurrency limits.
3.  **Executor**: `internal/tools/executor.go` constructs the command:
    ```bash
    python3 backend/agents/market_research_agent/cli.py --input '{"action": "...", "task_id": "..."}'
    ```
4.  **Execution**: The Python process runs. It does its work (scraping, LLM calls).
5.  **Capture**: Go captures `stdout`.
6.  **Storage**: The result is saved to the `tasks` table in Postgres.
7.  **Response**: The Task ID is returned to the user immediately (async) or the result is returned (sync wait).
