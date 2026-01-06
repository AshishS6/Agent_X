"""
Markdown Report Builder
Generates human-readable Markdown report for internal reviews, GitHub, Notion, etc.
Bullet-first structure with headings only (#, ##, ###).
"""

from typing import Dict, Any
from datetime import datetime
from .report_model import ReportModel


class MarkdownBuilder:
    """
    Builds Markdown report from normalized report model.
    Human-readable format suitable for copy-paste into documentation.
    """
    
    def __init__(self):
        self.report_model = ReportModel()
    
    def build(self,
              scan_data: Dict[str, Any],
              task_id: str) -> str:
        """
        Build Markdown report from scan data.
        
        Args:
            scan_data: comprehensive_site_scan data structure
            task_id: Task/scan ID
            
        Returns:
            Markdown string
        """
        normalized = self.report_model.build(scan_data, task_id)
        
        lines = []
        
        # Title
        lines.append("# Site Compliance Report\n")
        
        # Overview
        lines.append("## Overview\n")
        meta = normalized["meta"]
        summary = normalized["summary"]
        lines.append(f"- **URL**: {meta['target_url']}")
        lines.append(f"- **Scan Date**: {meta['scanned_at']}")
        lines.append(f"- **Scan ID**: {meta['scan_id']}")
        lines.append(f"- **Business Context**: {meta['business_context']}")
        lines.append(f"- **Overall Score**: {summary['overall_score']}/100 ({summary['rating']})")
        lines.append(f"- **Status**: {'✅ Pass' if summary['pass'] else '❌ Fail'}")
        lines.append("")
        
        # Executive Summary
        lines.append("## Executive Summary\n")
        lines.append(summary['recommendation'])
        lines.append("")
        
        if summary['critical_issues'] > 0:
            lines.append(f"**Critical Issues**: {summary['critical_issues']}")
            lines.append("")
        
        # Issues Identified
        issues = normalized["issues"]
        if issues:
            lines.append("## Issues Identified\n")
            
            # Group by severity
            high_issues = [i for i in issues if i.get('severity') == 'HIGH']
            medium_issues = [i for i in issues if i.get('severity') == 'MEDIUM']
            low_issues = [i for i in issues if i.get('severity') == 'LOW']
            
            if high_issues:
                lines.append("### HIGH Severity\n")
                for issue in high_issues:
                    lines.append(f"- **{issue['title']}**")
                    lines.append(f"  - Category: {issue['category']}")
                    lines.append(f"  - Required: {'Yes' if issue['required'] else 'No'}")
                    lines.append(f"  - Reason: {issue['contextual_reason']}")
                    lines.append(f"  - Fix: {issue['recommended_fix']}")
                    lines.append("")
            
            if medium_issues:
                lines.append("### MEDIUM Severity\n")
                for issue in medium_issues:
                    lines.append(f"- **{issue['title']}**")
                    lines.append(f"  - Category: {issue['category']}")
                    lines.append(f"  - Fix: {issue['recommended_fix']}")
                    lines.append("")
            
            if low_issues:
                lines.append("### LOW Severity\n")
                for issue in low_issues:
                    lines.append(f"- **{issue['title']}**")
                    lines.append(f"  - Reason: {issue['contextual_reason']}")
                    lines.append("")
        else:
            lines.append("No issues identified.\n")
        
        # Compliance Breakdown
        lines.append("## Compliance Breakdown\n")
        scores = normalized["scores"]
        lines.append(f"- **Overall Score**: {scores['overall']}/100")
        lines.append(f"- **Technical**: {scores['technical']}/{scores['max_scores']['technical']}")
        lines.append(f"- **Policy**: {scores['policy']}/{scores['max_scores']['policy']}")
        lines.append(f"- **Trust & Risk**: {scores['trust']}/{scores['max_scores']['trust']}")
        lines.append("")
        
        # Business Context
        context = normalized["context"]
        lines.append("## Business Context\n")
        lines.append(f"- **Primary Context**: {context['primary']}")
        lines.append(f"- **Confidence**: {context['confidence']:.2%}")
        lines.append(f"- **Status**: {context['status']}")
        lines.append(f"- **Frontend Surface**: {context['frontend_surface']}")
        lines.append("")
        
        # MCC Classification
        mcc = normalized["mcc"]
        lines.append("## MCC Classification\n")
        if mcc.get('primary_mcc'):
            primary = mcc['primary_mcc']
            lines.append(f"- **Primary MCC**: {primary['code']} - {primary['description']}")
            lines.append(f"- **Category**: {primary['category']}")
            lines.append(f"- **Confidence**: {mcc['confidence']:.2%}")
            if mcc.get('keywords_matched'):
                lines.append(f"- **Keywords Matched**: {', '.join(mcc['keywords_matched'])}")
        else:
            lines.append("- No MCC classification available")
        lines.append("")
        
        # Recommendations
        recommendations = normalized["recommendations"]
        if recommendations:
            lines.append("## Recommendations\n")
            for i, rec in enumerate(recommendations, 1):
                lines.append(f"{i}. {rec}")
            lines.append("")
        
        # Footer
        lines.append("---\n")
        lines.append(f"*Generated by AgentX - Report Version {meta['report_version']}, Engine Version {meta['engine_version']}*")
        
        return "\n".join(lines)


