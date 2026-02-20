-- Migration 003: Complete Schema - Create all tables required by AgentX application
-- Run this migration to ensure all application features have their required tables.
-- Idempotent: Safe to run multiple times (uses IF NOT EXISTS).
--
-- Prerequisites: Base schema (agents, tasks, conversations, etc.) must exist.
--   Run schema.sql first for fresh installs.
--
-- To run: psql -f database/migrations/003_complete_schema_migration.sql $DATABASE_URL
-- Or: psql $DATABASE_URL < database/migrations/003_complete_schema_migration.sql

-- Enable UUID extension (no-op if already exists)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- WORKFLOW TABLES (Workflows feature: /workflows, orchestration)
-- =============================================================================

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

CREATE TABLE IF NOT EXISTS workflow_cases (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
  provider VARCHAR(50) NOT NULL,
  external_ref_id TEXT NOT NULL,
  status VARCHAR(20),
  latest_state JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_workflow_cases_workflow_provider_ref
  ON workflow_cases(workflow_id, provider, external_ref_id);
CREATE INDEX IF NOT EXISTS idx_workflow_cases_workflow_id ON workflow_cases(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_cases_updated_at ON workflow_cases(updated_at DESC);

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
CREATE UNIQUE INDEX IF NOT EXISTS uq_workflow_runs_workflow_id_idempotency_key
  ON workflow_runs(workflow_id, idempotency_key)
  WHERE idempotency_key IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_workflow_runs_workflow_id_provider_event_id
  ON workflow_runs(workflow_id, provider_event_id)
  WHERE provider_event_id IS NOT NULL;

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

-- =============================================================================
-- BLOG AGENT TABLES (Blog feature: document-centric workflow)
-- =============================================================================

CREATE TABLE IF NOT EXISTS blog_documents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  brand VARCHAR(20) NOT NULL CHECK (brand IN ('OPEN', 'Zwitch')),
  topic TEXT NOT NULL,
  target_audience VARCHAR(50) NOT NULL,
  intent VARCHAR(50) NOT NULL,
  created_by VARCHAR(255),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS blog_outline_versions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id UUID NOT NULL REFERENCES blog_documents(id) ON DELETE CASCADE,
  version INTEGER NOT NULL,
  structure JSONB NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'draft'
    CHECK (status IN ('draft', 'reviewed', 'approved')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE (document_id, version)
);

CREATE TABLE IF NOT EXISTS blog_draft_versions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id UUID NOT NULL REFERENCES blog_documents(id) ON DELETE CASCADE,
  outline_version_id UUID REFERENCES blog_outline_versions(id),
  version INTEGER NOT NULL,
  content TEXT NOT NULL,
  meta_description TEXT,
  word_count INTEGER,
  estimated_reading_time INTEGER,
  status VARCHAR(20) NOT NULL DEFAULT 'draft'
    CHECK (status IN ('draft', 'reviewed', 'approved')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE (document_id, version)
);

CREATE TABLE IF NOT EXISTS blog_feedback (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id UUID NOT NULL REFERENCES blog_documents(id) ON DELETE CASCADE,
  target_type VARCHAR(20) NOT NULL CHECK (target_type IN ('outline', 'draft')),
  target_version_id UUID NOT NULL,
  scope VARCHAR(20) NOT NULL CHECK (scope IN ('global', 'section')),
  target_section_id VARCHAR(255),
  comment TEXT NOT NULL,
  created_by VARCHAR(255),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_blog_documents_brand ON blog_documents(brand);
CREATE INDEX IF NOT EXISTS idx_blog_documents_created_at ON blog_documents(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_blog_outline_versions_document ON blog_outline_versions(document_id, version DESC);
CREATE INDEX IF NOT EXISTS idx_blog_draft_versions_document ON blog_draft_versions(document_id, version DESC);
CREATE INDEX IF NOT EXISTS idx_blog_feedback_document ON blog_feedback(document_id, target_type);
CREATE INDEX IF NOT EXISTS idx_blog_feedback_target_version ON blog_feedback(target_version_id);

-- =============================================================================
-- MCC TABLES (Site Scan Agent: Merchant Category Code lookup and audit)
-- =============================================================================

CREATE TABLE IF NOT EXISTS mcc_codes (
  mcc VARCHAR(4) PRIMARY KEY,
  description TEXT NOT NULL,
  category TEXT NOT NULL,
  subcategory TEXT NOT NULL,
  range TEXT NOT NULL,
  networks TEXT[] NOT NULL,
  risk_level TEXT DEFAULT 'medium',
  active BOOLEAN DEFAULT TRUE,
  version DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS mcc_audit_logs (
  id SERIAL PRIMARY KEY,
  scan_id VARCHAR(255) NOT NULL,
  mcc VARCHAR(4) NOT NULL REFERENCES mcc_codes(mcc),
  selected_by VARCHAR(255) NOT NULL,
  source VARCHAR(50) NOT NULL,
  reason TEXT,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mcc_audit_logs_scan_id ON mcc_audit_logs(scan_id);
CREATE INDEX IF NOT EXISTS idx_mcc_audit_logs_timestamp ON mcc_audit_logs(timestamp DESC);

-- =============================================================================
-- TRIGGERS (update updated_at on row update)
-- =============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_blog_document_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_workflows_updated_at ON workflows;
CREATE TRIGGER update_workflows_updated_at
  BEFORE UPDATE ON workflows
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_workflow_cases_updated_at ON workflow_cases;
CREATE TRIGGER update_workflow_cases_updated_at
  BEFORE UPDATE ON workflow_cases
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_blog_documents_updated_at ON blog_documents;
CREATE TRIGGER update_blog_documents_updated_at
  BEFORE UPDATE ON blog_documents
  FOR EACH ROW
  EXECUTE FUNCTION update_blog_document_updated_at();
