"""
Site Scan Report Builder
Assembles comprehensive site scan reports from module outputs
"""

from typing import Dict, Any
from datetime import datetime


class SiteScanReportBuilder:
    """Builds structured site scan reports"""
    
    VERSION = "v2.1.1"  # Per PRD V2.1.1
    
    def __init__(self):
        self.report = {}
    
    def initialize_report(self, url: str, business_name: str = "") -> None:
        """
        Initialize report structure
        
        Args:
            url: Target URL
            business_name: Business name (optional)
        """
        self.report = {
            "url": url,
            "business_name": business_name,
            "scan_timestamp": datetime.now().isoformat(),
            "compliance_checks": {},
            "policy_details": {},
            "mcc_codes": {},
            "product_details": {},
            "business_details": {}
        }
    
    def add_compliance_data(self, compliance_data: Dict[str, Any]) -> None:
        """Add compliance check results"""
        self.report["compliance"] = compliance_data
    
    def add_policy_details(self, policy_details: Dict[str, Any]) -> None:
        """Add policy page detection results"""
        self.report["policy_details"] = policy_details
    
    def add_mcc_codes(self, mcc_data: Dict[str, Any]) -> None:
        """Add MCC code classification"""
        self.report["mcc_codes"] = mcc_data
    
    def add_product_details(self, product_data: Dict[str, Any]) -> None:
        """Add product/ecommerce indicators"""
        self.report["product_details"] = product_data
    
    def add_business_details(self, business_data: Dict[str, Any]) -> None:
        """Add extracted business information"""
        self.report["business_details"] = business_data
    
    def add_content_risk(self, risk_data: Dict[str, Any]) -> None:
        """Add content risk analysis"""
        self.report["content_risk"] = risk_data

    def add_compliance_intelligence(self, intelligence_data: Dict[str, Any]) -> None:
        """Add compliance intelligence (score & risk)"""
        self.report["compliance_intelligence"] = intelligence_data
    
    def build(self) -> Dict[str, Any]:
        """
        Build final report with proper wrapping
        
        Returns:
            Complete report wrapped in 'comprehensive_site_scan' key
        """
        # Wrap in root key for frontend compatibility
        return {
            "comprehensive_site_scan": self.report
        }
