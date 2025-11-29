# Agent_X Project Documentation

## 1. Project Overview
Agent_X is a modular, agent-based business automation platform. It allows users to deploy specialized AI agents (Market Research, Sales, etc.) to perform complex tasks autonomously. The system is built with a microservices-inspired architecture, separating the frontend dashboard, backend API, and independent agent workers.

## 2. Architecture
The system consists of four main components:

1.  **Frontend (Dashboard)**: A React/TypeScript application for managing agents, viewing tasks, and monitoring system status.
2.  **Backend (API)**: A Node.js/Express server that handles API requests, manages the database, and pushes tasks to the Redis queue.
3.  **Message Queue (Redis)**: Acts as the communication bridge between the backend and the agent workers.
4.  **Agent Workers**: Independent Python processes that consume tasks from Redis, execute them using LLMs (Ollama/OpenAI), and update the database.
5.  **Database (PostgreSQL)**: Stores all persistent data, including agent configurations, tasks, logs, and metrics.

### System Diagram
```mermaid
graph TD
    User[User] -->|HTTP| Frontend[Frontend (React)]
    Frontend -->|REST API| Backend[Backend (Node.js)]
    Backend -->|SQL| DB[(PostgreSQL)]
    Backend -->|Push Task| Redis[(Redis Queue)]
    
    subgraph Agents
        Worker1[Market Research Agent]
        Worker2[Sales Agent]
    end
    
    Redis -->|Consume Task| Worker1
    Redis -->|Consume Task| Worker2
    
    Worker1 -->|Update Status| DB
    Worker2 -->|Update Status| DB
    
    Worker1 -.->|LLM Calls| Ollama[Ollama / OpenAI]
    Worker2 -.->|LLM Calls| Ollama
```

## 3. Key Components

### 3.1 Frontend (`/src`)
-   **Framework**: React 19, Vite, TypeScript, Tailwind CSS.
-   **Key Pages**:
    -   `Dashboard.tsx`: System overview.
    -   `MarketResearchAgent.tsx`: Interface for the Market Research Agent.
    -   `SalesAgent.tsx`: Interface for the Sales Agent.
-   **Services**: `api.ts` handles all backend communication.

### 3.2 Backend (`/backend`)
-   **Framework**: Node.js, Express.
-   **Database**: PostgreSQL (via `pg` library).
-   **Key Routes**:
    -   `/agents`: Manage agent configurations.
    -   `/tasks`: Create and retrieve tasks (supports pagination).
    -   `/integrations`: Manage external tool connections.
-   **Queue Producer**: Pushes tasks to Redis streams (`tasks:market_research`, `tasks:sales`).

### 3.3 Agents (`/agents`)
-   **Framework**: Python, LangChain (ReAct pattern).
-   **Shared Logic** (`/agents/shared`):
    -   `base_agent.py`: Common agent functionality (LLM initialization, task execution loop).
    -   `db_utils.py`: Database interaction helpers.
-   **Market Research Agent**:
    -   **Tools**: Web Search, URL Monitor, Comprehensive Site Scan.
    -   **Worker**: Listens on `tasks:market_research`.
-   **Sales Agent**:
    -   **Tools**: Lead Qualification, Email Generation.
    -   **Worker**: Listens on `tasks:sales`.

## 4. Data Flow
1.  **Task Creation**: User submits a request via the Frontend.
2.  **API Handling**: Backend receives the request, creates a `Task` record in Postgres (status: `pending`), and pushes a message to Redis.
3.  **Task Processing**: The appropriate Agent Worker picks up the message from Redis.
4.  **Execution**: The Agent uses its LLM and Tools to execute the task.
    -   Updates status to `processing`.
    -   On completion/failure, updates status to `completed` or `failed` in Postgres.
5.  **Result Display**: Frontend polls the API (or receives WebSocket updates) to display the result.

## 5. Setup & Deployment

### Prerequisites
-   Docker & Docker Compose
-   Node.js 18+
-   Python 3.10+
-   Ollama (for local LLM)

### Running the System
1.  **Start Infrastructure**:
    ```bash
    docker-compose up -d postgres redis
    ```
2.  **Start Backend**:
    ```bash
    cd backend && npm run dev
    ```
3.  **Start Frontend**:
    ```bash
    npm run dev
    ```
4.  **Start Agents**:
    ```bash
    # Terminal 1
    cd agents/market_research_agent && python3 worker.py
    
    # Terminal 2
    cd agents/sales_agent && python3 worker.py
    ```

## 6. API Reference (Brief)
-   `GET /api/agents`: List all agents.
-   `POST /api/agents/:id/execute`: Execute a task for an agent.
-   `GET /api/tasks`: List tasks (supports `limit`, `offset`, `agentId`).
-   `GET /api/tasks/:id`: Get task details.

## 7. Troubleshooting
-   **Agent Stuck**: Check Redis connection and ensure `worker.py` is running.
-   **Parsing Errors**: Ensure the LLM model is capable of following ReAct formatting (recommended: `mistral` or `llama3.1`).
-   **Database Issues**: Check `docker-compose logs postgres`.

## 8. Documentation Maintenance
-   **Trigger**: Whenever code changes are made to architecture, API endpoints, or agent logic.
-   **Responsibility**: The developer/agent making the change must update this document.
-   **Key Files to Update**:
    -   `docs/project_documentation.md`: High-level changes.
    -   `docs/task.md`: Current progress.
    -   `docs/implementation_plan.md`: Planning new features.

