"""
Database Initialization for Market Research Agent
"""

import logging
import sys
from shared.db_utils import get_db_connection

logger = logging.getLogger(__name__)

def init_tables():
    """Initialize agent-specific tables"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # 1. Page Cache Table
                cur.execute("""
                CREATE TABLE IF NOT EXISTS crawl_page_cache (
                    url TEXT PRIMARY KEY,
                    canonical_url TEXT,
                    page_type TEXT,
                    content_hash TEXT,
                    html TEXT,
                    status INTEGER,
                    headers JSONB DEFAULT '{}'::jsonb,
                    expires_at TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_page_cache_expires 
                ON crawl_page_cache(expires_at);
                """)
                
                # 2. Site Scan Snapshots Table (for change detection)
                cur.execute("""
                CREATE TABLE IF NOT EXISTS site_scan_snapshots (
                    id SERIAL PRIMARY KEY,
                    task_id TEXT,
                    target_url TEXT NOT NULL,
                    scan_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    page_hashes JSONB DEFAULT '{}'::jsonb,
                    derived_signals JSONB DEFAULT '{}'::jsonb
                );
                
                CREATE INDEX IF NOT EXISTS idx_scan_snapshots_url 
                ON site_scan_snapshots(target_url, scan_timestamp DESC);
                """)
                
                logger.info("Market Research Agent tables initialized successfully")
                
    except Exception as e:
        logger.error(f"Failed to initialize tables: {e}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_tables()
