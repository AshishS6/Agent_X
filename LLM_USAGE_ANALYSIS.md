# Complete LLM Usage Analysis for AgentX

## Executive Summary

This document provides a comprehensive analysis of all LLM (Large Language Model) usage across the AgentX project, including configuration locations, usage patterns, and environment variables.

## 1. LLM Configuration Overview

### 1.1 Environment Variables

**Location**: `backend/.env`

Current configuration:
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your-openai-api-key
```

**Missing Configuration**:
- No `OLLAMA_BASE_URL` configured (defaults to `http://localhost:11434`)
- No `LLM_MODEL` configured (used when `LLM_PROVIDER=ollama`)
- No `ANTHROPIC_API_KEY` configured (needed for Anthropic provider)

### 1.2 Go Backend Configuration

**Location**: `backend/internal/config/config.go`

The Go backend reads LLM configuration from environment variables:
- `LLM_PROVIDER` (default: "openai")
- `OPENAI_API_KEY` (default: "")
- These are passed to Python agents via environment variables in `executor.go`

**Key Code**:
```go
LLMProvider:  getEnv("LLM_PROVIDER", "openai"),
OpenAIAPIKey: getEnv("OPENAI_API_KEY", ""),
```

### 1.3 Python Agents Configuration

**Location**: `backend/agents/shared/base_agent.py`

The `BaseAgent` class supports three LLM providers:
1. **OpenAI**: Uses `langchain_openai.ChatOpenAI`
   - Requires: `OPENAI_API_KEY` environment variable
   - Default model: `gpt-4-turbo-preview`

2. **Anthropic**: Uses `langchain_anthropic.ChatAnthropic`
   - Requires: `ANTHROPIC_API_KEY` environment variable
   - Default model: `claude-3-sonnet-20240229`

3. **Ollama** (Local LLM): Uses `langchain_community.chat_models.ChatOllama`
   - Requires: `OLLAMA_BASE_URL` environment variable (default: `http://localhost:11434`)
   - Model: Read from `LLM_MODEL` environment variable or defaults to model specified in agent factory

**Key Code**:
```python
def _create_llm(self):
    provider = self.config.llm_provider.lower()
    
    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=self.config.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            api_key=os.getenv("OPENAI_API_KEY")
        )
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=self.config.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
    elif provider == "ollama":
        from langchain_community.chat_models import ChatOllama
        return ChatOllama(
            model=self.config.model,
            temperature=self.config.temperature,
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        )
```

## 2. LLM Usage by Component

### 2.1 Agents (Task-Based, Stateless)

Agents use LLM through the `BaseAgent` class. They are executed as CLI tools by the Go backend.

#### 2.1.1 Blog Agent ✅ **USES LLM**

**Location**: `backend/agents/blog_agent/main.py`

**LLM Usage**:
- **Purpose**: Generate blog outlines and full blog posts
- **Provider Selection**: Reads from `LLM_PROVIDER` environment variable
- **Model Selection**:
  - OpenAI: `gpt-4-turbo-preview`
  - Anthropic: `claude-3-sonnet-20240229`
  - Ollama: `LLM_MODEL` env var or defaults to `deepseek-r1:7b`

**LLM Calls**:
1. `_generate_outline()` - Line 160: `response = self.llm.invoke(messages)`
   - Generates structured JSON outline with title and sections
   
2. `_generate_post_from_outline()` - Line 274: `response = self.llm.invoke(messages)`
   - Generates full blog post from outline
   - Returns JSON with title, content, meta_description, word_count

**Configuration**:
```python
def create_blog_agent(llm_provider: str = "openai") -> BlogAgent:
    if llm_provider == "openai":
        model = "gpt-4-turbo-preview"
    elif llm_provider == "anthropic":
        model = "claude-3-sonnet-20240229"
    elif llm_provider == "ollama":
        model = os.getenv("LLM_MODEL", "deepseek-r1:7b")
    
    config = AgentConfig(
        agent_type="blog",
        name="Blog Agent",
        llm_provider=llm_provider,
        model=model,
        temperature=0.7,
        max_tokens=4000,  # Higher for blog generation
    )
```

**Environment Variables Passed**:
- `LLM_PROVIDER` (from Go backend `.env`)
- `OPENAI_API_KEY` (from Go backend `.env`)
- `ANTHROPIC_API_KEY` (from Go backend `.env`)
- `OLLAMA_BASE_URL` (not explicitly passed, uses default or system env)
- `LLM_MODEL` (not explicitly passed, uses default or system env)

#### 2.1.2 Market Research Agent ✅ **USES LLM**

**Location**: `backend/agents/market_research_agent/main.py`

**LLM Usage**:
- **Purpose**: ReAct agent for competitor analysis, trend tracking, and report generation
- **Provider Selection**: Reads from `LLM_PROVIDER` environment variable
- **Model Selection**:
  - OpenAI: `gpt-4-turbo-preview`
  - Anthropic: `claude-3-sonnet-20240229`
  - Ollama: `LLM_MODEL` env var or defaults to `deepseek-r1:7b`

**LLM Calls**:
- Uses LangChain ReAct agent pattern (Line 1239: `create_react_agent`)
- LLM is invoked through `AgentExecutor` for tool-based reasoning
- For `site_scan` action: **BYPASSES LLM** - directly executes tools (Line 1098-1121)
- For other actions: Uses LLM with ReAct pattern for tool orchestration

**Configuration**:
```python
def create_market_research_agent(llm_provider: str = "openai") -> MarketResearchAgent:
    if llm_provider == "openai":
        model = "gpt-4-turbo-preview"
    elif llm_provider == "anthropic":
        model = "claude-3-sonnet-20240229"
    elif llm_provider == "ollama":
        model = os.getenv("LLM_MODEL", "deepseek-r1:7b")
    
    config = AgentConfig(
        agent_type="market_research",
        name="Market Research Agent",
        llm_provider=llm_provider,
        model=model,
        temperature=0.5,  # Lower for more deterministic analysis
    )
```

**Note**: Site scans use V2 modular engine (deterministic, no LLM). Other actions use LLM.

#### 2.1.3 Sales Agent ✅ **USES LLM**

**Location**: `backend/agents/sales_agent/main.py`

**LLM Usage**:
- **Purpose**: Lead qualification, email generation
- **Provider Selection**: Reads from `LLM_PROVIDER` environment variable
- **Model Selection**:
  - OpenAI: `gpt-4-turbo-preview`
  - Anthropic: `claude-3-sonnet-20240229`
  - Ollama: `LLM_MODEL` env var or defaults to `deepseek-r1:7b`

**Configuration**:
```python
def create_sales_agent(llm_provider: str = "openai") -> SalesAgent:
    if llm_provider == "openai":
        model = "gpt-4-turbo-preview"
    elif llm_provider == "anthropic":
        model = "claude-3-sonnet-20240229"
    elif llm_provider == "ollama":
        model = os.getenv("LLM_MODEL", "deepseek-r1:7b")
```

### 2.2 Assistants (Conversational, Stateful) ✅ **USES LLM**

Assistants use a **different LLM client** - they use `OllamaClient` directly, NOT LangChain.

**Location**: `backend/assistants/runner.py`

#### 2.2.1 Assistant LLM Configuration

**Key Difference**: Assistants **ALWAYS use Ollama** (local LLM), not OpenAI/Anthropic.

**LLM Client**: `backend/llm/providers/ollama_client.py`
- Uses `/api/generate` endpoint (works with all Ollama models)
- NOT using LangChain - direct HTTP calls to Ollama

**Configuration**:
```python
# In runner.py
ollama_client = OllamaClient()  # Uses OLLAMA_BASE_URL env var or defaults to http://localhost:11434

# Model selection per assistant:
# - FintechAssistant: "qwen2.5:7b-instruct" (default)
# - CodeAssistant: "qwen2.5:7b-instruct" (default)
# - GeneralAssistant: "qwen2.5:7b-instruct" (default)
```

**Assistant Configurations**:

1. **Fintech Assistant** (`backend/assistants/fintech_assistant.py`):
   - Model: `qwen2.5:7b-instruct` (default)
   - Uses RAG: ✅ Yes (knowledge base: "fintech")
   - System prompt: Extensive fintech-specific instructions

2. **Code Assistant** (`backend/assistants/code_assistant.py`):
   - Model: `qwen2.5:7b-instruct` (default)
   - Uses RAG: ❌ No
   - System prompt: Code-focused instructions

3. **General Assistant** (`backend/assistants/general_assistant.py`):
   - Model: `qwen2.5:7b-instruct` (default)
   - Uses RAG: ❌ No
   - System prompt: General purpose instructions

**LLM Call** (Line 127 in `runner.py`):
```python
response_text = await ollama_client.generate(
    model=config.model,
    prompt=full_prompt,
    stream=False
)
```

**Environment Variables**:
- `OLLAMA_BASE_URL` - Passed from Go backend (Line 115 in `assistants.go`)
- Model is hardcoded in assistant configs (can be overridden via `get_config(model=...)`)

**Important**: Assistants are **hardcoded to use Ollama only**. They do NOT support OpenAI or Anthropic.

## 3. LLM Module Structure

### 3.1 LLM Providers Module

**Location**: `backend/llm/`

**Structure**:
```
backend/llm/
├── __init__.py              # Exports OllamaClient, response filters
├── providers/
│   ├── __init__.py          # Exports OllamaClient
│   └── ollama_client.py     # Ollama HTTP client
└── prompts/
    ├── __init__.py
    └── response_filter.py   # Utilities for filtering LLM responses
```

**OllamaClient** (`backend/llm/providers/ollama_client.py`):
- **Purpose**: Direct HTTP client for Ollama API
- **Used By**: Assistants only
- **Methods**:
  - `health_check()` - Check Ollama availability
  - `get_models()` - List available models
  - `generate()` - Text completion (used by assistants)
  - `chat_stream()` - Streaming chat (not currently used)

**Configuration**:
- Base URL: `OLLAMA_BASE_URL` env var or `http://localhost:11434`
- Streaming timeout: `OLLAMA_STREAMING_TIMEOUT` env var or 900 seconds

## 4. Environment Variable Flow

### 4.1 Go Backend → Python Agents

**Location**: `backend/internal/tools/executor.go` (Line 127-131)

```go
cmd.Env = append(os.Environ(),
    "LLM_PROVIDER="+os.Getenv("LLM_PROVIDER"),
    "OPENAI_API_KEY="+os.Getenv("OPENAI_API_KEY"),
    "ANTHROPIC_API_KEY="+os.Getenv("ANTHROPIC_API_KEY"),
)
```

**Note**: `OLLAMA_BASE_URL` and `LLM_MODEL` are **NOT explicitly passed** to agents. They rely on system environment variables or defaults.

### 4.2 Go Backend → Python Assistants

**Location**: `backend/internal/handlers/assistants.go` (Line 114-117)

```go
cmd.Env = append(os.Environ(),
    "OLLAMA_BASE_URL="+os.Getenv("OLLAMA_BASE_URL"),
    "PYTHONPATH="+filepath.Join(h.projectRoot, "backend"),
)
```

**Note**: Only `OLLAMA_BASE_URL` is passed. Assistants are hardcoded to use Ollama.

## 5. Configuration Summary

### 5.1 Current State

| Component | LLM Provider | Model | Config Location | Status |
|-----------|--------------|-------|-----------------|--------|
| **Blog Agent** | Configurable (OpenAI/Anthropic/Ollama) | Varies by provider | `backend/.env` → `LLM_PROVIDER` | ✅ Configured (OpenAI, no API key) |
| **Market Research Agent** | Configurable (OpenAI/Anthropic/Ollama) | Varies by provider | `backend/.env` → `LLM_PROVIDER` | ✅ Configured (OpenAI, no API key) |
| **Sales Agent** | Configurable (OpenAI/Anthropic/Ollama) | Varies by provider | `backend/.env` → `LLM_PROVIDER` | ✅ Configured (OpenAI, no API key) |
| **Assistants** | **Ollama ONLY** | `qwen2.5:7b-instruct` | Hardcoded in assistant configs | ✅ Uses local LLM |

### 5.2 Missing Configuration

1. **OpenAI API Key**: Set in `.env` but value is placeholder (`your-openai-api-key`)
2. **Ollama Configuration** (for agents):
   - `OLLAMA_BASE_URL` - Not in `.env` (uses default: `http://localhost:11434`)
   - `LLM_MODEL` - Not in `.env` (uses default per agent: `deepseek-r1:7b`)
3. **Ollama Configuration** (for assistants):
   - `OLLAMA_BASE_URL` - Not in `.env` (uses default: `http://localhost:11434`)
   - Model is hardcoded in assistant configs

### 5.3 Recommended .env Configuration

```env
# LLM Provider (for agents: openai, anthropic, or ollama)
LLM_PROVIDER=ollama

# OpenAI (if using OpenAI)
OPENAI_API_KEY=sk-your-actual-key-here

# Anthropic (if using Anthropic)
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here

# Ollama (for agents and assistants)
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=deepseek-r1:7b  # or qwen2.5:7b-instruct, llama3, etc.
```

## 6. Key Findings

### 6.1 Two Different LLM Architectures

1. **Agents** (Blog, Market Research, Sales):
   - Use **LangChain** with provider abstraction
   - Support OpenAI, Anthropic, and Ollama
   - Configuration via `LLM_PROVIDER` environment variable
   - LLM initialized in `BaseAgent._create_llm()`

2. **Assistants** (Fintech, Code, General):
   - Use **OllamaClient** directly (no LangChain)
   - **ONLY support Ollama** (local LLM)
   - Model hardcoded in assistant configs
   - LLM called via `ollama_client.generate()`

### 6.2 Configuration Inconsistencies

1. **Ollama for Assistants**: Hardcoded, no environment variable override
2. **Ollama for Agents**: Uses `LLM_MODEL` env var but it's not in `.env`
3. **OLLAMA_BASE_URL**: Not explicitly passed to agents, relies on system env

### 6.3 Current Usage

- **Blog Agent**: ✅ Uses LLM for content generation
- **Market Research Agent**: ✅ Uses LLM for ReAct agent (except site_scan which bypasses LLM)
- **Sales Agent**: ✅ Uses LLM for lead qualification and email generation
- **Assistants**: ✅ Use Ollama for conversational responses with optional RAG

## 7. Recommendations

1. **Add Ollama Configuration to .env**:
   ```env
   OLLAMA_BASE_URL=http://localhost:11434
   LLM_MODEL=deepseek-r1:7b
   ```

2. **Update Go Backend** to pass `OLLAMA_BASE_URL` and `LLM_MODEL` to agents:
   ```go
   cmd.Env = append(os.Environ(),
       "LLM_PROVIDER="+os.Getenv("LLM_PROVIDER"),
       "OPENAI_API_KEY="+os.Getenv("OPENAI_API_KEY"),
       "ANTHROPIC_API_KEY="+os.Getenv("ANTHROPIC_API_KEY"),
       "OLLAMA_BASE_URL="+os.Getenv("OLLAMA_BASE_URL"),  // ADD THIS
       "LLM_MODEL="+os.Getenv("LLM_MODEL"),              // ADD THIS
   )
   ```

3. **Consider Making Assistants Configurable**: Currently hardcoded to Ollama. Could add support for OpenAI/Anthropic if needed.

4. **Document Model Requirements**: Each assistant/agent has different model defaults. Document which models work best for each use case.

## 8. File Reference

### Configuration Files
- `backend/.env` - Main environment configuration
- `backend/internal/config/config.go` - Go backend config loader
- `backend/agents/shared/base_agent.py` - Agent LLM initialization
- `backend/assistants/runner.py` - Assistant LLM execution

### LLM Implementation Files
- `backend/llm/providers/ollama_client.py` - Ollama HTTP client
- `backend/agents/blog_agent/main.py` - Blog agent LLM usage
- `backend/agents/market_research_agent/main.py` - Market research agent LLM usage
- `backend/agents/sales_agent/main.py` - Sales agent LLM usage
- `backend/assistants/fintech_assistant.py` - Fintech assistant config
- `backend/assistants/code_assistant.py` - Code assistant config
- `backend/assistants/general_assistant.py` - General assistant config

### Execution Files
- `backend/internal/tools/executor.go` - Passes env vars to agents
- `backend/internal/handlers/assistants.go` - Passes env vars to assistants
