-- Add Blog Agent to database
-- Run this if the blog agent is missing from your database

INSERT INTO agents (type, name, description, status, config) 
VALUES 
  ('blog', 'Blog Agent', 'Generates structured blog outlines and drafts for marketing teams.', 'active', '{}')
ON CONFLICT (type) DO UPDATE
SET 
  name = EXCLUDED.name,
  description = EXCLUDED.description,
  status = EXCLUDED.status,
  updated_at = NOW();
