-- Add Blog Agent tables

-- Blog Documents table
CREATE TABLE IF NOT EXISTS blog_documents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  brand VARCHAR(50) NOT NULL,
  topic TEXT NOT NULL,
  target_audience TEXT NOT NULL,
  intent TEXT NOT NULL,
  created_by VARCHAR(255),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Blog Outline Versions table
CREATE TABLE IF NOT EXISTS blog_outline_versions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id UUID NOT NULL REFERENCES blog_documents(id) ON DELETE CASCADE,
  version INTEGER NOT NULL,
  structure JSONB NOT NULL DEFAULT '{}',
  status VARCHAR(50) NOT NULL DEFAULT 'draft',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Blog Draft Versions table
CREATE TABLE IF NOT EXISTS blog_draft_versions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id UUID NOT NULL REFERENCES blog_documents(id) ON DELETE CASCADE,
  outline_version_id UUID REFERENCES blog_outline_versions(id) ON DELETE SET NULL,
  version INTEGER NOT NULL,
  content TEXT NOT NULL,
  meta_description TEXT,
  word_count INTEGER,
  estimated_reading_time INTEGER,
  status VARCHAR(50) NOT NULL DEFAULT 'draft',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Blog Feedback table
CREATE TABLE IF NOT EXISTS blog_feedback (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id UUID NOT NULL REFERENCES blog_documents(id) ON DELETE CASCADE,
  target_type VARCHAR(50) NOT NULL, -- 'outline' or 'draft'
  target_version_id UUID NOT NULL,
  scope VARCHAR(50) NOT NULL, -- 'global' or 'section'
  target_section_id VARCHAR(255),
  comment TEXT NOT NULL,
  created_by VARCHAR(255),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_blog_documents_created_at ON blog_documents(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_blog_outline_versions_document_id ON blog_outline_versions(document_id);
CREATE INDEX IF NOT EXISTS idx_blog_draft_versions_document_id ON blog_draft_versions(document_id);
CREATE INDEX IF NOT EXISTS idx_blog_feedback_document_id ON blog_feedback(document_id);
CREATE INDEX IF NOT EXISTS idx_blog_feedback_target_version_id ON blog_feedback(target_version_id);

-- Trigger for updated_at on blog_documents
DROP TRIGGER IF EXISTS update_blog_documents_updated_at ON blog_documents;
CREATE TRIGGER update_blog_documents_updated_at
  BEFORE UPDATE ON blog_documents
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();
