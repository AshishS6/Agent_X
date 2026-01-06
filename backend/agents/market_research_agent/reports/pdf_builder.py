"""
PDF Report Builder
Generates formal compliance PDF report suitable for bank onboarding, PSP underwriting, and risk review.
Uses reportlab for layout + text, Pillow for images only.
NO HTML-to-PDF conversion.
"""

from typing import Dict, Any, List
from io import BytesIO
from datetime import datetime
from urllib.parse import urlparse
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from .report_model import ReportModel


class PDFBuilder:
    """
    Builds PDF compliance report from normalized report model.
    Formal document suitable for compliance teams, banks, and PSPs.
    """
    
    def __init__(self):
        self.report_model = ReportModel()
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        # Get body style (either modified BodyText or CustomBodyText)
        self.body_style = self.styles.get('CustomBodyText', self.styles['BodyText'])
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        if 'CustomTitle' not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name='CustomTitle',
                parent=self.styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=30,
                alignment=TA_CENTER
            ))
        
        # Section heading
        if 'SectionHeading' not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name='SectionHeading',
                parent=self.styles['Heading2'],
                fontSize=16,
                textColor=colors.HexColor('#2c3e50'),
                spaceAfter=12,
                spaceBefore=20
            ))
        
        # Body text - modify existing instead of adding new
        if 'BodyText' in self.styles.byName:
            # Modify existing BodyText style
            body_style = self.styles['BodyText']
            body_style.fontSize = 10
            body_style.leading = 14
            body_style.textColor = colors.HexColor('#333333')
        else:
            # Fallback: create custom body style with different name
            self.styles.add(ParagraphStyle(
                name='CustomBodyText',
                parent=self.styles['Normal'],
                fontSize=10,
                leading=14,
                textColor=colors.HexColor('#333333')
            ))
        
        # Footer style
        if 'Footer' not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name='Footer',
                parent=self.styles['Normal'],
                fontSize=8,
                textColor=colors.HexColor('#666666'),
                alignment=TA_CENTER
            ))
    
    def build(self,
              scan_data: Dict[str, Any],
              task_id: str) -> bytes:
        """
        Build PDF report from scan data.
        
        Args:
            scan_data: comprehensive_site_scan data structure
            task_id: Task/scan ID
            
        Returns:
            PDF bytes
        """
        normalized = self.report_model.build(scan_data, task_id)
        
        # Create PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        # Build content
        story = []
        
        # Cover page
        story.extend(self._build_cover_page(normalized))
        story.append(PageBreak())
        
        # Executive summary
        story.extend(self._build_executive_summary(normalized))
        story.append(PageBreak())
        
        # Compliance score breakdown
        story.extend(self._build_score_breakdown(normalized))
        
        # Business context
        story.extend(self._build_business_context(normalized))
        
        # Policy presence matrix
        story.extend(self._build_policy_matrix(scan_data, normalized))
        
        # Payment & risk findings
        story.extend(self._build_risk_findings(normalized))
        
        # MCC classification
        story.extend(self._build_mcc_section(normalized))
        
        # Technical summary
        story.extend(self._build_technical_summary(scan_data, normalized))
        
        # Build PDF
        doc.build(story, onFirstPage=self._add_footer, onLaterPages=self._add_footer)
        
        buffer.seek(0)
        return buffer.getvalue()
    
    def _build_cover_page(self, normalized: Dict[str, Any]) -> List:
        """Build cover page"""
        meta = normalized["meta"]
        summary = normalized["summary"]
        
        story = []
        story.append(Spacer(1, 2*inch))
        
        # Title
        story.append(Paragraph("Site Compliance Report", self.styles['CustomTitle']))
        story.append(Spacer(1, 0.5*inch))
        
        # Site URL
        story.append(Paragraph(f"<b>Site URL:</b> {meta['target_url']}", self.body_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Scan ID
        story.append(Paragraph(f"<b>Scan ID:</b> {meta['scan_id']}", self.body_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Scan Timestamp
        story.append(Paragraph(f"<b>Scan Date:</b> {meta['scanned_at']}", self.body_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Business Context
        story.append(Paragraph(f"<b>Business Context:</b> {meta['business_context']}", self.body_style))
        story.append(Spacer(1, 0.5*inch))
        
        # Overall Score & Rating
        story.append(Paragraph(
            f"<b>Overall Score:</b> {summary['overall_score']}/100 ({summary['rating']})",
            self.body_style
        ))
        story.append(Spacer(1, 0.2*inch))
        
        # Status
        status_text = "✅ COMPLIANT" if summary['pass'] else "❌ NOT COMPLIANT"
        story.append(Paragraph(f"<b>Status:</b> {status_text}", self.body_style))
        
        return story
    
    def _build_executive_summary(self, normalized: Dict[str, Any]) -> List:
        """Build executive summary section"""
        story = []
        summary = normalized["summary"]
        
        story.append(Paragraph("Executive Summary", self.styles['SectionHeading']))
        story.append(Spacer(1, 0.2*inch))
        
        story.append(Paragraph(summary['recommendation'], self.body_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Top 3 issues
        issues = normalized["issues"]
        high_issues = [i for i in issues if i.get('severity') == 'HIGH']
        
        if high_issues:
            story.append(Paragraph("<b>Top Critical Issues:</b>", self.body_style))
            story.append(Spacer(1, 0.1*inch))
            
            for i, issue in enumerate(high_issues[:3], 1):
                story.append(Paragraph(
                    f"{i}. {issue['title']}",
                    self.body_style
                ))
        
        return story
    
    def _build_score_breakdown(self, normalized: Dict[str, Any]) -> List:
        """Build compliance score breakdown table"""
        story = []
        scores = normalized["scores"]
        
        story.append(Paragraph("Compliance Score Breakdown", self.styles['SectionHeading']))
        story.append(Spacer(1, 0.2*inch))
        
        # Create table
        data = [
            ['Category', 'Score', 'Max', 'Status'],
            ['Technical', str(scores['technical']), str(scores['max_scores']['technical']), 
             self._get_status_label(scores['technical'], scores['max_scores']['technical'])],
            ['Policy', str(scores['policy']), str(scores['max_scores']['policy']),
             self._get_status_label(scores['policy'], scores['max_scores']['policy'])],
            ['Trust & Risk', str(scores['trust']), str(scores['max_scores']['trust']),
             self._get_status_label(scores['trust'], scores['max_scores']['trust'])],
            ['Overall', str(scores['overall']), '100', normalized["summary"]["rating"]]
        ]
        
        table = Table(data, colWidths=[2*inch, 1*inch, 1*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.3*inch))
        
        return story
    
    def _build_business_context(self, normalized: Dict[str, Any]) -> List:
        """Build business context determination section"""
        story = []
        context = normalized["context"]
        
        story.append(Paragraph("Business Context Determination", self.styles['SectionHeading']))
        story.append(Spacer(1, 0.2*inch))
        
        story.append(Paragraph(f"<b>Primary Context:</b> {context['primary']}", self.body_style))
        story.append(Paragraph(f"<b>Confidence:</b> {context['confidence']:.2%}", self.body_style))
        story.append(Paragraph(f"<b>Status:</b> {context['status']}", self.body_style))
        story.append(Paragraph(f"<b>Frontend Surface:</b> {context['frontend_surface']}", self.body_style))
        
        if context.get('alternatives'):
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph("<b>Alternative Contexts:</b>", self.body_style))
            for alt in context['alternatives']:
                story.append(Paragraph(
                    f"- {alt.get('type', '')} (score: {alt.get('score', 0)})",
                    self.body_style
                ))
        
        story.append(Spacer(1, 0.3*inch))
        
        return story
    
    def _build_policy_matrix(self, scan_data: Dict[str, Any], normalized: Dict[str, Any]) -> List:
        """Build policy presence matrix"""
        story = []
        scan = scan_data.get('comprehensive_site_scan', scan_data)
        policy_details = scan.get('policy_details', {})
        
        story.append(Paragraph("Policy Presence Matrix", self.styles['SectionHeading']))
        story.append(Spacer(1, 0.2*inch))
        
        policy_map = {
            "privacy_policy": "Privacy Policy",
            "terms_condition": "Terms of Service",
            "returns_refund": "Refund Policy",
            "contact_us": "Contact Page"
        }
        
        data = [['Policy', 'Required', 'Found', 'URL', 'Notes']]
        
        for policy_key, policy_name in policy_map.items():
            policy_data = policy_details.get(policy_key, {})
            found = policy_data.get('found', False)
            url = policy_data.get('url', 'N/A') if found else 'N/A'
            
            # Determine if required based on context
            context = normalized.get('context', {})
            required = "Yes"  # Default, would need severity_rules to determine
            
            notes = "Found" if found else "Missing"
            
            data.append([
                policy_name,
                required,
                "Yes" if found else "No",
                url[:50] + "..." if len(url) > 50 else url,
                notes
            ])
        
        table = Table(data, colWidths=[1.5*inch, 0.8*inch, 0.6*inch, 1.5*inch, 1.2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.3*inch))
        
        return story
    
    def _build_risk_findings(self, normalized: Dict[str, Any]) -> List:
        """Build payment & risk findings section"""
        story = []
        issues = normalized["issues"]
        
        story.append(Paragraph("Payment & Risk Findings", self.styles['SectionHeading']))
        story.append(Spacer(1, 0.2*inch))
        
        if not issues:
            story.append(Paragraph("No issues identified.", self.body_style))
            story.append(Spacer(1, 0.3*inch))
            return story
        
        # Group by severity
        high_issues = [i for i in issues if i.get('severity') == 'HIGH']
        medium_issues = [i for i in issues if i.get('severity') == 'MEDIUM']
        low_issues = [i for i in issues if i.get('severity') == 'LOW']
        
        for issue in high_issues + medium_issues + low_issues:
            severity = issue.get('severity', 'MEDIUM')
            title = issue.get('title', '')
            description = issue.get('contextual_reason', '')
            fix = issue.get('recommended_fix', '')
            
            story.append(Paragraph(
                f"<b>[{severity}] {title}</b>",
                self.body_style
            ))
            story.append(Paragraph(description, self.body_style))
            story.append(Paragraph(f"<i>Recommended Fix:</i> {fix}", self.body_style))
            story.append(Spacer(1, 0.15*inch))
        
        story.append(Spacer(1, 0.3*inch))
        
        return story
    
    def _build_mcc_section(self, normalized: Dict[str, Any]) -> List:
        """Build MCC classification section"""
        story = []
        mcc = normalized["mcc"]
        
        story.append(Paragraph("MCC Classification", self.styles['SectionHeading']))
        story.append(Spacer(1, 0.2*inch))
        
        if mcc.get('primary_mcc'):
            primary = mcc['primary_mcc']
            story.append(Paragraph(f"<b>Primary MCC:</b> {primary['code']}", self.body_style))
            story.append(Paragraph(f"<b>Description:</b> {primary['description']}", self.body_style))
            story.append(Paragraph(f"<b>Category:</b> {primary['category']}", self.body_style))
            story.append(Paragraph(f"<b>Confidence:</b> {mcc['confidence']:.2%}", self.body_style))
            
            if mcc.get('keywords_matched'):
                story.append(Paragraph(
                    f"<b>Keywords Matched:</b> {', '.join(mcc['keywords_matched'])}",
                    self.body_style
                ))
            
            if mcc.get('secondary_mccs'):
                story.append(Spacer(1, 0.1*inch))
                story.append(Paragraph("<b>Secondary MCCs:</b>", self.body_style))
                for sec in mcc['secondary_mccs']:
                    story.append(Paragraph(
                        f"- {sec['code']}: {sec['description']}",
                        self.body_style
                    ))
        else:
            story.append(Paragraph("No MCC classification available.", self.body_style))
        
        story.append(Spacer(1, 0.3*inch))
        
        return story
    
    def _build_technical_summary(self, scan_data: Dict[str, Any], normalized: Dict[str, Any]) -> List:
        """Build condensed technical summary"""
        story = []
        scan = scan_data.get('comprehensive_site_scan', scan_data)
        
        story.append(Paragraph("Technical Summary", self.styles['SectionHeading']))
        story.append(Spacer(1, 0.2*inch))
        
        # SSL
        compliance = scan.get('compliance', {})
        general_alerts = compliance.get('general', {}).get('alerts', [])
        ssl_issues = [a for a in general_alerts if a.get('code') in ['NO_HTTPS', 'SSL_ERROR']]
        ssl_status = "✅ Valid" if not ssl_issues else "❌ Invalid"
        story.append(Paragraph(f"<b>SSL:</b> {ssl_status}", self.body_style))
        
        # Tech Stack (if available)
        tech_stack = scan.get('tech_stack', {})
        if tech_stack:
            story.append(Paragraph(f"<b>CMS:</b> {tech_stack.get('cms', 'Unknown')}", self.body_style))
            story.append(Paragraph(f"<b>Hosting:</b> {tech_stack.get('hosting', 'Unknown')}", self.body_style))
        
        # SEO (if available)
        seo = scan.get('seo_analysis', {})
        if seo:
            story.append(Paragraph(f"<b>SEO Score:</b> {seo.get('seo_score', 0)}/100", self.body_style))
            story.append(Paragraph(f"<b>Indexable:</b> {'Yes' if seo.get('indexable') else 'No'}", self.body_style))
        
        story.append(Spacer(1, 0.3*inch))
        
        return story
    
    def _add_footer(self, canvas, doc):
        """Add footer to each page"""
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#666666'))
        
        # Footer text
        text = "Generated by AgentX"
        canvas.drawCentredString(A4[0]/2, 0.5*inch, text)
        
        # Page number
        page_num = canvas.getPageNumber()
        canvas.drawRightString(A4[0] - 0.75*inch, 0.5*inch, f"Page {page_num}")
        
        canvas.restoreState()
    
    def _get_status_label(self, score: int, max_score: int) -> str:
        """Get status label for score"""
        percentage = (score / max_score) * 100
        if percentage >= 80:
            return "Good"
        elif percentage >= 50:
            return "Fair"
        else:
            return "Poor"

