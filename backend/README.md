# Go Backend for Agent_X

A Go-based backend server that executes Python CLI tools with hybrid concurrency control.

## Quick Start

```bash
# Install dependencies
go mod download

# Copy environment file
cp .env.example .env

# Edit .env with your database and API keys
vim .env

# Run the server
make dev
```

## Architecture

```
Frontend → Go Backend → CLI Tool (Python subprocess) → Result
                ↓
           PostgreSQL Database
```

### Hybrid Concurrency Control

- **Global Limit (10)**: Maximum concurrent tool executions across all tools
- **Per-Tool Limit (5)**: Maximum concurrent executions per tool type

This prevents any single tool from monopolizing resources while ensuring predictable memory usage.

## API Endpoints

### Agents (Backward Compatible)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/agents` | List all agents |
| GET | `/api/agents/:id` | Get agent by ID |
| POST | `/api/agents/:id/execute` | Execute agent task |
| PUT | `/api/agents/:id` | Update agent |
| GET | `/api/agents/:id/metrics` | Get agent metrics |

### Tasks
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tasks` | List all tasks |
| GET | `/api/tasks/:id` | Get task by ID |
| GET | `/api/tasks/status/counts` | Get task status counts |

### Tools (New)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tools` | List available tools |
| GET | `/api/tools/:name` | Get tool configuration |

### Monitoring
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/monitoring/health` | Health check |
| GET | `/api/monitoring/metrics` | System metrics |
| GET | `/api/monitoring/activity` | Recent activity |
| GET | `/api/monitoring/system` | System info |

## Adding New Tools

1. Create CLI tool in `agents/<tool_name>/cli.py`
2. Register in `internal/tools/registry.go`:

```go
"my-tool": {
    Name:             "My Tool",
    Description:      "Description of what it does",
    Command:          "python",
    Args:             []string{"agents/my_tool_agent/cli.py"},
    Timeout:          3 * time.Minute,
    WorkingDir:       ".",
    ConcurrencyLimit: 5,
    AgentType:        "my-tool",
},
```

3. Seed agent in database (optional, for backward compat)

## CLI Tool Contract

All Python CLI tools must follow this contract:

**Input**: `--input '{"action": "...", "key": "value"}'`

**Output** (JSON to stdout):
```json
{
  "status": "completed" | "failed",
  "output": { ... },
  "error": "string if failed",
  "metadata": { ... }
}
```

**Logs**: Write to stderr (not stdout)

**Exit Code**: 0 = success, non-zero = failure

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| PORT | 3001 | Server port |
| GIN_MODE | debug | Gin mode (debug/release) |
| DATABASE_URL | postgres://... | PostgreSQL connection string |
| GLOBAL_CONCURRENCY_LIMIT | 10 | Max total concurrent executions |
| DEFAULT_TOOL_CONCURRENCY_LIMIT | 5 | Default per-tool limit |
| CORS_ORIGINS | localhost:5173 | Allowed CORS origins |
| LLM_PROVIDER | openai | LLM provider for tools |
| OPENAI_API_KEY | - | OpenAI API key |

## Development

```bash
# Format code
make fmt

# Run tests
make test

# Build binary
make build

# Clean
make clean
```
