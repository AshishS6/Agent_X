"""
JSON Report Builder
Generates lossless, machine-readable JSON export of scan data.
Includes report_version and engine_version for traceability.
"""

import json
from typing import Dict, Any
from .report_model import ReportModel


class JSONBuilder:
    """
    Builds JSON report from normalized report model.
    Provides complete, lossless scan data for audit logs, reprocessing, and integrations.
    """
    
    def __init__(self):
        self.report_model = ReportModel()
    
    def build(self,
              scan_data: Dict[str, Any],
              task_id: str) -> str:
        """
        Build JSON report from scan data.
        
        Args:
            scan_data: comprehensive_site_scan data structure
            task_id: Task/scan ID
            
        Returns:
            JSON string with complete report data
        """
        # Build normalized model
        normalized = self.report_model.build(scan_data, task_id)
        
        # Add raw scan data for completeness (but keep normalized structure primary)
        # This allows both normalized view and raw data access
        report = {
            "meta": normalized["meta"],
            "summary": normalized["summary"],
            "issues": normalized["issues"],
            "scores": normalized["scores"],
            "compliance_intelligence": normalized["scores"],  # Keep for backward compat
            "context": normalized["context"],
            "mcc": normalized["mcc"],
            "recommendations": normalized["recommendations"],
            # Include essential raw data for audit/reprocessing
            # Per PRD V2.1.1: Include crawl_summary and evidence metadata
            "raw_scan": {
                "url": scan_data.get('comprehensive_site_scan', {}).get('url', ''),
                "scan_timestamp": scan_data.get('comprehensive_site_scan', {}).get('scan_timestamp', ''),
                "compliance": scan_data.get('comprehensive_site_scan', {}).get('compliance', {}),
                "policy_details": scan_data.get('comprehensive_site_scan', {}).get('policy_details', {}),
                "content_risk": scan_data.get('comprehensive_site_scan', {}).get('content_risk', {}),
                "mcc_codes": scan_data.get('comprehensive_site_scan', {}).get('mcc_codes', {}),
                "crawl_summary": scan_data.get('comprehensive_site_scan', {}).get('crawl_summary', {}),
                "change_detection": scan_data.get('comprehensive_site_scan', {}).get('change_detection', {}),
                "change_intelligence": scan_data.get('comprehensive_site_scan', {}).get('change_intelligence', {})
            }
        }
        
        return json.dumps(report, indent=2, default=str)

