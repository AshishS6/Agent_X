-- Migration: Fix timestamp columns to use timezone-aware types
-- This ensures proper timezone handling across different servers

-- Tasks table
ALTER TABLE tasks 
  ALTER COLUMN started_at TYPE TIMESTAMP WITH TIME ZONE,
  ALTER COLUMN completed_at TYPE TIMESTAMP WITH TIME ZONE,
  ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE;

-- Agents table
ALTER TABLE agents 
  ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE,
  ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE;

-- Conversations table
ALTER TABLE conversations 
  ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE;

-- Agent metrics table
ALTER TABLE agent_metrics 
  ALTER COLUMN timestamp TYPE TIMESTAMP WITH TIME ZONE;

-- Integrations table
ALTER TABLE integrations 
  ALTER COLUMN last_sync TYPE TIMESTAMP WITH TIME ZONE,
  ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE;

-- Note: TIMESTAMP WITH TIME ZONE stores all timestamps in UTC internally
-- and converts to/from local time on input/output based on the session timezone

