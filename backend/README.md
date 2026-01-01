# Go Backend for Agent_X

A Go-based backend server (Gin framework) that executes Python CLI tools with hybrid concurrency control.

## Quick Start

```bash
# Install dependencies
go mod download

# Copy environment file (if .env.example exists)
cp .env.example .env

# Edit .env with your database and API keys
# Required variables:
# - DATABASE_URL (default: postgres://postgres:dev_password@localhost:5432/agentx?sslmode=disable)
# - LLM_PROVIDER (openai, anthropic, or ollama)
# - OPENAI_API_KEY or ANTHROPIC_API_KEY (if using those providers)

# Run the server
make dev
```

**Note**: The actual entry point is `cmd/server/main.go`, not `main.go` in the backend root.

## Architecture

```
Frontend (React)
     ↓ HTTP REST API
Go Backend (Gin)
     ↓ os/exec subprocess spawn
Python CLI Agents
     ↓ HTTP API calls
LLM Providers / External APIs
     ↓
PostgreSQL Database (Task storage)
```

### Hybrid Concurrency Control

The executor (`internal/tools/executor.go`) uses semaphores to manage concurrency:

- **Global Limit (default: 10)**: Maximum concurrent tool executions across all tools
- **Per-Tool Limit (default: 5)**: Maximum concurrent executions per tool type

This prevents any single tool from monopolizing resources while ensuring predictable memory usage. Limits are configurable via environment variables:
- `GLOBAL_CONCURRENCY_LIMIT` (default: 10)
- `DEFAULT_TOOL_CONCURRENCY_LIMIT` (default: 5)

## API Endpoints

### Agents
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/agents` | List all agents |
| GET | `/api/agents/:id` | Get agent by ID (UUID) |
| POST | `/api/agents/:name/execute` | Execute agent by type (e.g., `market_research`, `sales`) |
| PUT | `/api/agents/:id` | Update agent configuration |
| GET | `/api/agents/:id/metrics` | Get agent metrics and statistics |

**Execute Request Body**:
```json
{
  "action": "site_scan",
  "input": {"url": "https://example.com"},
  "priority": "medium",
  "userId": "optional-user-id"
}
```

### Tasks
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tasks` | List tasks (supports `?agentId=`, `?status=`, `?limit=`, `?offset=`) |
| GET | `/api/tasks/:id` | Get task by ID |
| GET | `/api/tasks/status/counts` | Get task status counts (supports `?agentId=`) |
| POST | `/api/tasks/:id/mcc` | Save final MCC (Merchant Category Code) for a task |

**Task Response**:
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "agent_id": "uuid",
      "action": "site_scan",
      "input": {...},
      "output": {...},
      "status": "completed|failed|processing|pending",
      "priority": "high|medium|low",
      "error": null,
      "created_at": "2025-01-01T00:00:00Z",
      "completed_at": "2025-01-01T00:00:10Z"
    }
  ],
  "total": 100
}
```

### Tools
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tools` | List available CLI tools |
| GET | `/api/tools/:name` | Get tool configuration by name |

### Monitoring
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/monitoring/health` | Health check (database connectivity) |
| GET | `/api/monitoring/metrics` | System metrics (active agents, task counts, etc.) |
| GET | `/api/monitoring/activity` | Recent activity (supports `?limit=`) |
| GET | `/api/monitoring/system` | System information |
| GET | `/api/monitoring/proxy` | Proxy endpoint (for future use) |

### MCC (Merchant Category Codes)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/mccs` | Get Merchant Category Codes |

## Adding New Tools

1. Create CLI tool in `backend/agents/<tool_name>/cli.py` following the CLI contract (see below)

2. Register in `internal/tools/registry.go`:

```go
"my-tool": {
    Name:             "My Tool",
    Description:      "Description of what it does",
    Command:          "python3",
    Args:             []string{"backend/agents/my_tool_agent/cli.py"},
    Timeout:          3 * time.Minute,
    WorkingDir:       ".",
    ConcurrencyLimit: 5,
    AgentType:        "my-tool",
},
```

3. Agent is automatically seeded in database via `database/schema.sql` (or add manually to `agents` table)

4. The tool name in the registry maps to the API endpoint: `POST /api/agents/my-tool/execute`

## CLI Tool Contract

All Python CLI tools must follow this standardized contract:

### Input
Command-line argument: `--input '{"action": "...", "key": "value", "task_id": "uuid"}'`

The `task_id` is automatically injected by the Go backend for database tracking.

### Output (to stdout)
Must be valid JSON:
```json
{
  "status": "completed" | "failed",
  "output": { ... },
  "error": "string if failed",
  "metadata": { ... }  // optional
}
```

### Logs (to stderr)
All logging, debug messages, and progress updates should go to `stderr`, not `stdout`. This allows the Go backend to capture logs separately from the JSON output.

### Exit Code
- `0` = success
- Non-zero = failure

### Example Implementation
See `backend/agents/market_research_agent/cli.py` or `backend/agents/sales_agent/cli.py` for reference implementations.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| PORT | 3001 | Server port |
| GIN_MODE | debug | Gin mode (debug/release/test) |
| DATABASE_URL | postgres://postgres:dev_password@localhost:5432/agentx?sslmode=disable | PostgreSQL connection string |
| GLOBAL_CONCURRENCY_LIMIT | 10 | Max total concurrent tool executions |
| DEFAULT_TOOL_CONCURRENCY_LIMIT | 5 | Default per-tool concurrency limit |
| CORS_ORIGINS | localhost:5173 | Comma-separated list of allowed CORS origins |
| LLM_PROVIDER | openai | LLM provider (openai/anthropic/ollama) |
| OPENAI_API_KEY | - | OpenAI API key (if using OpenAI) |
| ANTHROPIC_API_KEY | - | Anthropic API key (if using Anthropic) |
| OLLAMA_BASE_URL | http://localhost:11434 | Ollama base URL (if using Ollama) |

**Note**: LLM provider configuration is primarily for agents, not the backend itself. The backend just spawns Python processes that read their own environment variables.

## Development

```bash
# Format code
make fmt

# Run tests
make test

# Build binary (outputs to bin/server)
make build

# Run built binary
make run

# Clean build artifacts
make clean

# Install dev tools (air for hot reload)
make dev-tools

# Install dependencies
make deps
```

### Project Structure

```
backend/
├── cmd/
│   └── server/
│       └── main.go          # Entry point
├── internal/
│   ├── config/              # Configuration loading
│   ├── database/            # PostgreSQL connection
│   ├── handlers/            # HTTP handlers (agents, tasks, monitoring, tools, mcc)
│   ├── middleware/          # CORS, logging middleware
│   ├── models/              # Database models and repositories
│   ├── seed/                # Database seeding (MCC codes)
│   └── tools/               # Tool executor and registry
├── go.mod                   # Go dependencies
├── Makefile                 # Build commands
└── .env                     # Environment variables (not committed)
```

### Key Components

- **Executor** (`internal/tools/executor.go`): Manages subprocess execution with concurrency limits
- **Registry** (`internal/tools/registry.go`): Maps agent types to CLI tool configurations
- **Handlers** (`internal/handlers/`): HTTP request handlers for all endpoints
- **Models** (`internal/models/`): Database repositories for agents, tasks, etc.
