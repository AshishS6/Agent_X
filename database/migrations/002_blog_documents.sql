-- Blog Agent v2 - Document-Centric Schema Migration
-- Creates tables for blog documents, outline versions, draft versions, and feedback

-- 1. blog_documents table
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

-- 2. blog_outline_versions table
CREATE TABLE IF NOT EXISTS blog_outline_versions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id UUID NOT NULL REFERENCES blog_documents(id) ON DELETE CASCADE,
  version INTEGER NOT NULL,
  structure JSONB NOT NULL, -- {title, outline: [{heading, intent, subsections}]}
  status VARCHAR(20) NOT NULL DEFAULT 'draft' 
    CHECK (status IN ('draft', 'reviewed', 'approved')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(document_id, version)
);

-- 3. blog_draft_versions table
CREATE TABLE IF NOT EXISTS blog_draft_versions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id UUID NOT NULL REFERENCES blog_documents(id) ON DELETE CASCADE,
  outline_version_id UUID REFERENCES blog_outline_versions(id),
  version INTEGER NOT NULL,
  content TEXT NOT NULL, -- Full markdown content
  meta_description TEXT,
  word_count INTEGER,
  estimated_reading_time INTEGER,
  status VARCHAR(20) NOT NULL DEFAULT 'draft'
    CHECK (status IN ('draft', 'reviewed', 'approved')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(document_id, version)
);

-- 4. blog_feedback table
CREATE TABLE IF NOT EXISTS blog_feedback (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id UUID NOT NULL REFERENCES blog_documents(id) ON DELETE CASCADE,
  target_type VARCHAR(20) NOT NULL CHECK (target_type IN ('outline', 'draft')),
  target_version_id UUID NOT NULL, -- References outline_version_id or draft_version_id
  scope VARCHAR(20) NOT NULL CHECK (scope IN ('global', 'section')),
  target_section_id VARCHAR(255), -- For section-specific feedback
  comment TEXT NOT NULL,
  created_by VARCHAR(255),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Indexes for performance
CREATE INDEX IF NOT EXISTS idx_blog_documents_brand ON blog_documents(brand);
CREATE INDEX IF NOT EXISTS idx_blog_documents_created_at ON blog_documents(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_blog_outline_versions_document ON blog_outline_versions(document_id, version DESC);
CREATE INDEX IF NOT EXISTS idx_blog_draft_versions_document ON blog_draft_versions(document_id, version DESC);
CREATE INDEX IF NOT EXISTS idx_blog_feedback_document ON blog_feedback(document_id, target_type);
CREATE INDEX IF NOT EXISTS idx_blog_feedback_target_version ON blog_feedback(target_version_id);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_blog_document_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_blog_documents_updated_at ON blog_documents;
CREATE TRIGGER update_blog_documents_updated_at
  BEFORE UPDATE ON blog_documents
  FOR EACH ROW
  EXECUTE FUNCTION update_blog_document_updated_at();
