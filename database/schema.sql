-- Agent_X Database Schema
-- PostgreSQL 16+

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Agents table
CREATE TABLE IF NOT EXISTS agents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  type VARCHAR(50) NOT NULL UNIQUE,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'paused', 'error')),
  config JSONB DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index on agent type for fast lookups
CREATE INDEX IF NOT EXISTS idx_agents_type ON agents(type);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);

-- Tasks table
CREATE TABLE IF NOT EXISTS tasks (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
  user_id VARCHAR(255),
  action VARCHAR(100) NOT NULL,
  input JSONB NOT NULL DEFAULT '{}',
  output JSONB,
  status VARCHAR(20) NOT NULL DEFAULT 'pending' 
    CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
  priority VARCHAR(10) DEFAULT 'medium' 
    CHECK (priority IN ('high', 'medium', 'low')),
  error TEXT,
  started_at TIMESTAMP WITH TIME ZONE,
  completed_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for task queries
CREATE INDEX IF NOT EXISTS idx_tasks_agent_id ON tasks(agent_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id);

-- Conversations table (for agent conversation history)
CREATE TABLE IF NOT EXISTS conversations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
  task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
  role VARCHAR(20) NOT NULL CHECK (role IN ('system', 'user', 'assistant', 'tool')),
  content TEXT NOT NULL,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conversations_agent_id ON conversations(agent_id);
CREATE INDEX IF NOT EXISTS idx_conversations_task_id ON conversations(task_id);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at DESC);

-- Agent metrics table
CREATE TABLE IF NOT EXISTS agent_metrics (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
  metric_type VARCHAR(50) NOT NULL,
  value NUMERIC NOT NULL,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_metrics_agent_id ON agent_metrics(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_metrics_type ON agent_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_agent_metrics_timestamp ON agent_metrics(timestamp DESC);

-- Integrations table
CREATE TABLE IF NOT EXISTS integrations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR(100) NOT NULL,
  type VARCHAR(50) NOT NULL,
  status VARCHAR(20) DEFAULT 'disconnected' 
    CHECK (status IN ('connected', 'error', 'disconnected')),
  config JSONB DEFAULT '{}',
  last_sync TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_integrations_type ON integrations(type);
CREATE INDEX IF NOT EXISTS idx_integrations_status ON integrations(status);

-- Workflows table (orchestration definitions)
CREATE TABLE IF NOT EXISTS workflows (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR(255) NOT NULL,
  description TEXT,
  status VARCHAR(20) NOT NULL DEFAULT 'draft'
    CHECK (status IN ('active', 'paused', 'draft')),
  trigger_type VARCHAR(50) NOT NULL,
  trigger_config JSONB NOT NULL DEFAULT '{}',
  steps JSONB NOT NULL DEFAULT '[]',
  owner_team VARCHAR(100),
  created_by VARCHAR(255),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows(status);
CREATE INDEX IF NOT EXISTS idx_workflows_trigger_type ON workflows(trigger_type);
CREATE INDEX IF NOT EXISTS idx_workflows_owner_team ON workflows(owner_team);

-- Workflow cases table (long-lived ticket/thread state)
CREATE TABLE IF NOT EXISTS workflow_cases (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
  provider VARCHAR(50) NOT NULL, -- e.g. freshdesk
  external_ref_id TEXT NOT NULL, -- e.g. ticket_id
  status VARCHAR(20), -- open|pending|resolved|closed (optional)
  latest_state JSONB NOT NULL DEFAULT '{}', -- last_seen_conversation_id, ticket_summary, etc.
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_workflow_cases_workflow_provider_ref
  ON workflow_cases(workflow_id, provider, external_ref_id);
CREATE INDEX IF NOT EXISTS idx_workflow_cases_workflow_id ON workflow_cases(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_cases_updated_at ON workflow_cases(updated_at DESC);

-- Workflow runs table (executions)
CREATE TABLE IF NOT EXISTS workflow_runs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
  status VARCHAR(20) NOT NULL DEFAULT 'running'
    CHECK (status IN ('running', 'completed', 'failed')),
  case_id UUID REFERENCES workflow_cases(id) ON DELETE SET NULL,
  provider_event_id TEXT,
  idempotency_key TEXT,
  trigger_payload JSONB NOT NULL DEFAULT '{}',
  started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  completed_at TIMESTAMP WITH TIME ZONE,
  error TEXT
);

CREATE INDEX IF NOT EXISTS idx_workflow_runs_workflow_id ON workflow_runs(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_runs_case_id ON workflow_runs(case_id);
CREATE INDEX IF NOT EXISTS idx_workflow_runs_status ON workflow_runs(status);
CREATE INDEX IF NOT EXISTS idx_workflow_runs_started_at ON workflow_runs(started_at DESC);
-- Prevent duplicate runs per workflow for retrying webhooks
CREATE UNIQUE INDEX IF NOT EXISTS uq_workflow_runs_workflow_id_idempotency_key
  ON workflow_runs(workflow_id, idempotency_key)
  WHERE idempotency_key IS NOT NULL;
-- Preferred idempotency: provider event id (if available)
CREATE UNIQUE INDEX IF NOT EXISTS uq_workflow_runs_workflow_id_provider_event_id
  ON workflow_runs(workflow_id, provider_event_id)
  WHERE provider_event_id IS NOT NULL;

-- Backward-compatible alterations (safe to run on existing DB)
ALTER TABLE IF EXISTS workflow_runs
  ADD COLUMN IF NOT EXISTS case_id UUID REFERENCES workflow_cases(id) ON DELETE SET NULL;
ALTER TABLE IF EXISTS workflow_runs
  ADD COLUMN IF NOT EXISTS provider_event_id TEXT;

-- Workflow step runs table (per-step execution record)
CREATE TABLE IF NOT EXISTS workflow_step_runs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  workflow_run_id UUID NOT NULL REFERENCES workflow_runs(id) ON DELETE CASCADE,
  step_index INTEGER NOT NULL,
  step_type VARCHAR(50) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'running'
    CHECK (status IN ('running', 'completed', 'failed', 'skipped')),
  input JSONB NOT NULL DEFAULT '{}',
  output JSONB NOT NULL DEFAULT '{}',
  task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
  error TEXT,
  started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_workflow_step_runs_workflow_run_id ON workflow_step_runs(workflow_run_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_workflow_step_runs_run_step ON workflow_step_runs(workflow_run_id, step_index);

-- Seed initial agents
INSERT INTO agents (type, name, description, status, config) VALUES
  ('sales', 'Sales Agent', 'Automates lead qualification, email outreach, and meeting scheduling.', 'active', '{}'),
  ('support', 'Support Agent', 'Handles customer inquiries, ticket triage, and knowledge base queries.', 'active', '{}'),
  ('support_ticket_triage', 'Support Ticket Triage Agent', 'Classifies support tickets, identifies missing fields, and drafts replies for human review.', 'active', '{}'),
  ('hr', 'HR Agent', 'Screens candidates, answers employee questions, and manages HR workflows.', 'active', '{}'),
  ('market_research', 'Market Research Agent', 'Analyzes market trends, competitor data, and industry reports.', 'active', '{}'),
  ('site_scan', 'Site Scan Agent', 'Runs website scans, compliance checks, and KYC site scans.', 'active', '{}'),
  ('marketing', 'Marketing Agent', 'Creates content, manages campaigns, and optimizes marketing strategies.', 'active', '{}'),
  ('blog', 'Blog Agent', 'Generates structured blog outlines and drafts for marketing teams.', 'active', '{}'),
  ('leads', 'Lead Sourcing Agent', 'Identifies and qualifies potential leads from various sources.', 'active', '{}'),
  ('intelligence', 'Intelligence Agent', 'Gathers and analyzes business intelligence data.', 'active', '{}'),
  ('legal', 'Legal Agent', 'Reviews contracts, conducts due diligence, and analyzes legal documents.', 'active', '{}'),
  ('finance', 'Finance Agent', 'Processes invoices, analyzes financial data, and generates reports.', 'active', '{}')
ON CONFLICT (type) DO NOTHING;

-- Seed sample integrations
INSERT INTO integrations (name, type, status, config, last_sync) VALUES
  ('Salesforce', 'crm', 'connected', '{}', NOW() - INTERVAL '2 minutes'),
  ('Slack', 'communication', 'connected', '{}', NOW()),
  ('Gmail', 'email', 'connected', '{}', NOW() - INTERVAL '5 minutes'),
  ('Notion', 'productivity', 'error', '{}', NOW() - INTERVAL '1 hour')
ON CONFLICT DO NOTHING;

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for agents table
DROP TRIGGER IF EXISTS update_agents_updated_at ON agents;
CREATE TRIGGER update_agents_updated_at
  BEFORE UPDATE ON agents
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Trigger for workflows table
DROP TRIGGER IF EXISTS update_workflows_updated_at ON workflows;
CREATE TRIGGER update_workflows_updated_at
  BEFORE UPDATE ON workflows
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Trigger for workflow_cases table
DROP TRIGGER IF EXISTS update_workflow_cases_updated_at ON workflow_cases;
CREATE TRIGGER update_workflow_cases_updated_at
  BEFORE UPDATE ON workflow_cases
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- View for agent statistics
CREATE OR REPLACE VIEW agent_statistics AS
SELECT 
  a.id,
  a.type,
  a.name,
  a.status,
  COUNT(t.id) FILTER (WHERE t.status = 'completed') as completed_tasks,
  COUNT(t.id) FILTER (WHERE t.status = 'failed') as failed_tasks,
  COUNT(t.id) FILTER (WHERE t.status = 'processing') as processing_tasks,
  COUNT(t.id) FILTER (WHERE t.status = 'pending') as pending_tasks,
  COUNT(t.id) as total_tasks,
  AVG(EXTRACT(EPOCH FROM (t.completed_at - t.started_at))) FILTER (WHERE t.status = 'completed') as avg_completion_time_seconds
FROM agents a
LEFT JOIN tasks t ON a.id = t.agent_id
GROUP BY a.id, a.type, a.name, a.status;

COMMENT ON VIEW agent_statistics IS 'Aggregated statistics for each agent';

-- Crawl Page Cache table (Added from live DB verification)
CREATE TABLE IF NOT EXISTS crawl_page_cache (
  url TEXT PRIMARY KEY,
  canonical_url TEXT,
  page_type TEXT,
  content_hash TEXT,
  html TEXT,
  status INTEGER,
  headers JSONB DEFAULT '{}',
  expires_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_page_cache_expires ON crawl_page_cache(expires_at);

-- Site Scan Snapshots table (Added from live DB verification)
CREATE TABLE IF NOT EXISTS site_scan_snapshots (
  id SERIAL PRIMARY KEY,
  task_id TEXT,
  target_url TEXT NOT NULL,
  scan_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  page_hashes JSONB DEFAULT '{}',
  derived_signals JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_scan_snapshots_url ON site_scan_snapshots(target_url, scan_timestamp DESC);
