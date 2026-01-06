"""
Change Detector Module
Compare current scan results with previous snapshots
"""

import logging
import json
from typing import Dict, Any, Optional, List
from psycopg2.extras import Json
from shared.db_utils import get_db_connection

class ChangeDetector:
    """
    Detects changes between current scan and previous snapshots.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def get_previous_snapshot(self, target_url: str) -> Optional[Dict[str, Any]]:
        """
        Fetch the most recent snapshot for a URL.
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT * FROM site_scan_snapshots 
                        WHERE target_url = %s 
                        ORDER BY scan_timestamp DESC 
                        LIMIT 1
                    """, (target_url,))
                    
                    row = cur.fetchone()
                    if row:
                        # Schema: id, task_id, target_url, scan_timestamp, page_hashes, derived_signals
                        return {
                            'id': row[0],
                            'task_id': row[1],
                            'target_url': row[2],
                            'scan_timestamp': row[3],
                            'page_hashes': row[4],
                            'derived_signals': row[5]
                        }
        except Exception as e:
            self.logger.warning(f"Failed to fetch previous snapshot: {e}")
        return None

    def compare(self, current_snapshot: Dict[str, Any], previous_snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare two snapshots and return a change report.
        """
        if not previous_snapshot:
            return {
                "since_last_scan": False,
                "summary": "First scan detected.",
                "changes": [],
                "snapshot_id": None
            }
            
        changes = []
        
        # 1. Check Page Content Changes (using hashes)
        current_hashes = current_snapshot.get('page_hashes', {})
        prev_hashes = previous_snapshot.get('page_hashes', {})
        
        for page_type, curr_hash in current_hashes.items():
            prev_hash = prev_hashes.get(page_type)
            if prev_hash and curr_hash != prev_hash:
                changes.append({
                    "type": "content_change",
                    "severity": "moderate" if page_type in ['product', 'pricing'] else "minor",
                    "description": f"{page_type.replace('_', ' ').title()} page content has changed."
                })
        
        # 2. Check Derived Signal Changes
        current_signals = current_snapshot.get('derived_signals', {})
        prev_signals = previous_snapshot.get('derived_signals', {})
        
        # Pricing Model Change
        if current_signals.get('pricing_model') != prev_signals.get('pricing_model'):
             changes.append({
                "type": "pricing_change",
                "severity": "critical",
                "description": f"Pricing model changed from {prev_signals.get('pricing_model')} to {current_signals.get('pricing_model')}."
            })
            
        # Product Count Change
        curr_prod_count = len(current_signals.get('extracted_products', []))
        prev_prod_count = len(prev_signals.get('extracted_products', []))
        if abs(curr_prod_count - prev_prod_count) >= 1:
             changes.append({
                "type": "product_change",
                "severity": "moderate",
                "description": f"Number of detected products changed from {prev_prod_count} to {curr_prod_count}."
            })

        return {
            "since_last_scan": True,
            "last_scan_date": previous_snapshot['scan_timestamp'].isoformat(),
            "summary": f"{len(changes)} changes detected." if changes else "No significant changes detected.",
            "changes": changes,
            "snapshot_id": previous_snapshot['id']
        }

    def save_snapshot(self, task_id: str, target_url: str, page_graph: Any, report: Dict[str, Any]):
        """
        Save the current scan state as a snapshot.
        """
        import time
        snapshot_start = time.monotonic()
        
        try:
            # key extraction from page_graph
            self.logger.debug(f"[SNAPSHOT] Extracting page hashes...")
            page_hashes = {}
            # Assuming page_graph has a way to iterate pages or get by type
            # We will use the ones we care about
            interesting_types = ['home', 'privacy_policy', 'terms_conditions', 'product', 'pricing', 'about']
            for p_type in interesting_types:
                page = page_graph.get_page_by_type(p_type)
                if page and page.content_hash:
                    page_hashes[p_type] = page.content_hash
            
            # Extract key signals from the final report
            self.logger.debug(f"[SNAPSHOT] Extracting derived signals...")
            # The report structure follows SiteScanReportBuilder
            # it wraps in comprehensive_site_scan usually
            data = report.get('comprehensive_site_scan', report)
            product_details = data.get('product_details', {})
            
            derived_signals = {
                'pricing_model': product_details.get('pricing_model'),
                'extracted_products': product_details.get('extracted_products', [])
            }
            
            self.logger.debug(f"[SNAPSHOT] Connecting to database...")
            db_connect_start = time.monotonic()
            with get_db_connection() as conn:
                db_connect_time = time.monotonic() - db_connect_start
                self.logger.debug(f"[SNAPSHOT] Database connection established in {db_connect_time:.2f}s")
                
                with conn.cursor() as cur:
                    self.logger.debug(f"[SNAPSHOT] Executing INSERT statement...")
                    insert_start = time.monotonic()
                    cur.execute("""
                        INSERT INTO site_scan_snapshots 
                        (task_id, target_url, page_hashes, derived_signals)
                        VALUES (%s, %s, %s, %s)
                    """, (
                        task_id, 
                        target_url, 
                        Json(page_hashes), 
                        Json(derived_signals)
                    ))
                    insert_time = time.monotonic() - insert_start
                    self.logger.debug(f"[SNAPSHOT] INSERT completed in {insert_time:.2f}s")
                    
                    conn.commit()
                    total_time = time.monotonic() - snapshot_start
                    self.logger.info(f"[SNAPSHOT] Saved snapshot for {target_url} in {total_time:.2f}s (db_connect={db_connect_time:.2f}s, insert={insert_time:.2f}s)")
                    
        except Exception as e:
            total_time = time.monotonic() - snapshot_start
            self.logger.warning(f"[SNAPSHOT] Failed to save snapshot after {total_time:.2f}s: {e}", exc_info=True)
