"""
Crawl Cache Module
Persist and retrieve crawled pages with TTL validation
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Optional, Dict
from psycopg2.extras import Json

from shared.db_utils import get_db_connection
from .page_graph import PageData

class CrawlCache:
    """
    Manages caching of crawled pages.
    """
    
    # TTL Rules (in seconds)
    TTL_RULES = {
        'privacy_policy': 7 * 86400,    # 7 days
        'terms_conditions': 7 * 86400,  # 7 days
        'about': 1 * 86400,             # 1 day
        'contact': 1 * 86400,           # 1 day
        'product': 86400,               # 1 day
        'pricing': 86400,               # 1 day
        'home': 21600,                  # 6 hours
        'other': 3600                   # 1 hour
    }
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def get(self, url: str) -> Optional[PageData]:
        """
        Retrieve a page from cache if it exists and hasn't expired.
        """
        # Fast path: skip cache if DB is unavailable
        from shared.db_utils import is_db_available
        if not is_db_available():
            return None
        
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT * FROM crawl_page_cache 
                        WHERE url = %s AND expires_at > NOW()
                    """, (url,))
                    
                    row = cur.fetchone()
                    if row:
                        # Convert tuple/row to dictionary (assuming implementation detail)
                        # We need to map row columns to dict keys. 
                        # Since shared.db_utils doesn't enforce RealDictCursor on raw conn, 
                        # we rely on consistent columns or schema knowledge.
                        # Schema: url, canonical_url, page_type, content_hash, html, status, headers, expires_at, created_at
                        
                        return PageData(
                            url=row[0],
                            canonical_url=row[1],
                            page_type=row[2],
                            html=row[4],
                            status=row[5],
                            classification_confidence=1.0, # Cached pages are assumed confident
                            final_url=row[0], # Assuming cached URL is final
                            source="cache",
                            content_type="text/html" # Simplified for now
                        )
            
        except Exception as e:
            self.logger.warning(f"Cache get failed for {url}: {e}")
            return None
            
        return None

    def set(self, page_data: PageData):
        """
        Save a page to the cache.
        """
        if not page_data.html or page_data.status != 200:
            return

        # Fast path: skip cache if DB is unavailable
        from shared.db_utils import is_db_available
        if not is_db_available():
            return

        ttl = self._get_ttl(page_data.page_type)
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO crawl_page_cache 
                        (url, canonical_url, page_type, content_hash, html, status, headers, expires_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (url) DO UPDATE SET
                            canonical_url = EXCLUDED.canonical_url,
                            page_type = EXCLUDED.page_type,
                            content_hash = EXCLUDED.content_hash,
                            html = EXCLUDED.html,
                            status = EXCLUDED.status,
                            headers = EXCLUDED.headers,
                            expires_at = EXCLUDED.expires_at
                    """, (
                        page_data.url,
                        page_data.canonical_url,
                        page_data.page_type,
                        page_data.content_hash,
                        page_data.html,
                        page_data.status,
                        Json({}), # Not storing full headers for now to save space
                        expires_at
                    ))
        except Exception as e:
            self.logger.warning(f"Cache set failed for {page_data.url}: {e}")

    def _get_ttl(self, page_type: str) -> int:
        return self.TTL_RULES.get(page_type, self.TTL_RULES['other'])
