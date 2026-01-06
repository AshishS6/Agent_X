"""
Reports Module
Handles report building and formatting
"""

from .site_scan_report import SiteScanReportBuilder
from .severity_rules import SeverityRules
from .report_model import ReportModel
from .json_builder import JSONBuilder
from .markdown_builder import MarkdownBuilder

# Lazy import for PDFBuilder to avoid requiring reportlab for regular scans
def get_pdf_builder():
    """Lazy import for PDFBuilder - only imports when needed"""
    from .pdf_builder import PDFBuilder
    return PDFBuilder

__all__ = [
    'SiteScanReportBuilder',
    'SeverityRules',
    'ReportModel',
    'JSONBuilder',
    'MarkdownBuilder',
    'get_pdf_builder'
]
