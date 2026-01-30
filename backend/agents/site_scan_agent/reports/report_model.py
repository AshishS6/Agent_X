"""
Normalized Report Model
Transforms scan data into a consistent, opinionated structure for report generation.
Enforces strict boundaries: NO raw crawler output, NO UI-only fields, NO nested engine internals.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from urllib.parse import urlparse
from .severity_rules import SeverityRules


class ReportModel:
    """
    Normalized report model that transforms comprehensive_site_scan data
    into a consistent structure for all report formats.
    
    This is a TRANSFORMATION layer, not a passthrough.
    """
    
    REPORT_VERSION = "v2.1.1"  # Per PRD V2.1.1
    ENGINE_VERSION = "v2.1.1"
    
    def __init__(self):
        self.severity_rules = SeverityRules()
    
    def build(self, 
              scan_data: Dict[str, Any],
              task_id: str) -> Dict[str, Any]:
        """
        Build normalized report model from scan data.
        
        Args:
            scan_data: comprehensive_site_scan data structure
            task_id: Task/scan ID for traceability
            
        Returns:
            Normalized report model with meta, summary, issues, scores, context, mcc, recommendations
        """
        scan = scan_data.get('comprehensive_site_scan', scan_data)
        
        # Extract business context
        business_context = scan.get('business_context', {})
        if not business_context and 'context_classifier' in scan:
            business_context = scan['context_classifier']
        
        # Build normalized model
        return {
            "meta": self._build_meta(scan, task_id),
            "summary": self._build_summary(scan, business_context),
            "issues": self._build_issues(scan, business_context),
            "scores": self._build_scores(scan),
            "context": self._build_context(scan, business_context),
            "mcc": self._build_mcc(scan),
            "recommendations": self._build_recommendations(scan, business_context)
        }
    
    def _build_meta(self, scan: Dict[str, Any], task_id: str) -> Dict[str, Any]:
        """Build metadata section"""
        url = scan.get('url', '')
        domain = urlparse(url).netloc if url else 'unknown'
        
        return {
            "scan_id": task_id,
            "scanned_at": scan.get('scan_timestamp', datetime.now().isoformat()),
            "target_url": url,
            "business_context": scan.get('business_context', {}).get('primary', 'UNKNOWN'),
            "report_version": self.REPORT_VERSION,
            "engine_version": self.ENGINE_VERSION
        }
    
    def _build_summary(self, scan: Dict[str, Any], business_context: Dict[str, Any]) -> Dict[str, Any]:
        """Build executive summary"""
        compliance_intel = scan.get('compliance_intelligence', {})
        compliance = scan.get('compliance', {})
        general_compliance = compliance.get('general', {})
        
        overall_score = compliance_intel.get('score', 0)
        rating = compliance_intel.get('rating', 'Unknown')
        pass_status = general_compliance.get('pass', False)
        
        # Count critical issues
        issues = self._build_issues(scan, business_context)
        critical_issues = sum(1 for issue in issues if issue.get('severity') == 'HIGH')
        
        # Generate recommendation statement
        recommendation = self._generate_recommendation(overall_score, rating, critical_issues, pass_status)
        
        return {
            "overall_score": overall_score,
            "rating": rating,
            "pass": pass_status,
            "critical_issues": critical_issues,
            "recommendation": recommendation
        }
    
    def _build_issues(self, scan: Dict[str, Any], business_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build flattened issues list with severity classification"""
        issues = []
        
        # Extract business context
        context_type = business_context.get('primary', 'UNKNOWN') if business_context else 'UNKNOWN'
        
        # 1. Compliance alerts
        compliance = scan.get('compliance', {})
        general_alerts = compliance.get('general', {}).get('alerts', [])
        for alert in general_alerts:
            code = alert.get('code', '')
            message = alert.get('message', '')
            
            issue_type = 'ssl_missing' if code in ['NO_HTTPS', 'SSL_ERROR'] else 'compliance_failure'
            severity_info = self.severity_rules.classify_issue(
                issue_type,
                {'check_name': code, 'message': message},
                business_context
            )
            
            issues.append({
                "severity": severity_info['severity'],
                "category": "COMPLIANCE",
                "title": message or f"Compliance issue: {code}",
                "required": severity_info['required'],
                "contextual_reason": severity_info['contextual_reason'],
                "recommended_fix": self._get_fix_for_alert(code)
            })
        
        # 2. Policy missing issues
        policy_details = scan.get('policy_details', {})
        policy_map = {
            "privacy_policy": "Privacy Policy",
            "terms_condition": "Terms of Service",
            "returns_refund": "Refund Policy",
            "contact_us": "Contact Page"
        }
        
        for policy_key, policy_name in policy_map.items():
            policy_data = policy_details.get(policy_key, {})
            if not policy_data.get('found', False):
                expectation = self.severity_rules.get_policy_expectation(policy_key, business_context)
                
                severity_info = self.severity_rules.classify_issue(
                    'policy_missing',
                    {
                        'policy_name': policy_name,
                        'expectation': expectation
                    },
                    business_context
                )
                
                issues.append({
                    "severity": severity_info['severity'],
                    "category": "POLICY",
                    "title": f"{policy_name} missing",
                    "required": severity_info['required'],
                    "contextual_reason": severity_info['contextual_reason'],
                    "recommended_fix": f"Add {policy_name} page accessible from site navigation"
                })
        
        # 3. Content risk issues
        content_risk = scan.get('content_risk', {})
        
        # Restricted keywords
        restricted = content_risk.get('restricted_keywords_found', [])
        for item in restricted:
            category = item.get('category', '')
            keyword = item.get('keyword', '')
            
            severity_info = self.severity_rules.classify_issue(
                'restricted_content',
                {'category': category, 'keyword': keyword},
                business_context
            )
            
            issues.append({
                "severity": severity_info['severity'],
                "category": "CONTENT_RISK",
                "title": f"Restricted content detected: {category}",
                "required": severity_info['required'],
                "contextual_reason": severity_info['contextual_reason'],
                "recommended_fix": f"Review content for '{keyword}' - may require special compliance"
            })
        
        # Dummy text
        if content_risk.get('dummy_words_detected', False):
            severity_info = self.severity_rules.classify_issue('dummy_text', {}, business_context)
            issues.append({
                "severity": severity_info['severity'],
                "category": "QUALITY",
                "title": "Dummy/placeholder text detected",
                "required": severity_info['required'],
                "contextual_reason": severity_info['contextual_reason'],
                "recommended_fix": "Replace placeholder text with actual content before going live"
            })
        
        # 4. Domain age issues (if available)
        # Note: domain_vintage_days may not be in scan data directly
        # This would need to be passed separately or extracted from compliance_intelligence
        
        return issues
    
    def _build_scores(self, scan: Dict[str, Any]) -> Dict[str, Any]:
        """Build compliance score breakdown"""
        compliance_intel = scan.get('compliance_intelligence', {})
        breakdown = compliance_intel.get('breakdown', {})
        
        # Per PRD V2.1.1: Preserve signal classification and evidence
        scores = {
            "overall": compliance_intel.get('score', 0),
            "advisory_score": compliance_intel.get('advisory_score', compliance_intel.get('score', 0)),  # Per PRD: Label as Advisory Score
            "label": compliance_intel.get('label', 'Advisory Score'),  # Per PRD
            "technical": breakdown.get('technical', {}).get('score', 0),
            "policy": breakdown.get('policy', {}).get('score', 0),
            "trust": breakdown.get('trust', {}).get('score', 0),
            "max_scores": {
                "technical": 30,
                "policy": 40,
                "trust": 30
            },
            "signal_type": compliance_intel.get('signal_type', 'advisory'),
            "breakdown_visible": compliance_intel.get('breakdown_visible', True),
            "breakdown_details": breakdown  # Preserve full breakdown with evidence
        }
        
        return scores
    
    def _build_context(self, scan: Dict[str, Any], business_context: Dict[str, Any]) -> Dict[str, Any]:
        """Build business context section"""
        if not business_context:
            return {
                "primary": "UNKNOWN",
                "confidence": 0.0,
                "status": "UNDETERMINED",
                "frontend_surface": "UNKNOWN"
            }
        
        return {
            "primary": business_context.get('primary', 'UNKNOWN'),
            "confidence": business_context.get('confidence', 0.0),
            "status": business_context.get('status', 'UNDETERMINED'),
            "frontend_surface": business_context.get('frontend_surface', 'UNKNOWN'),
            "alternatives": business_context.get('alternatives', [])
        }
    
    def _build_mcc(self, scan: Dict[str, Any]) -> Dict[str, Any]:
        """Build MCC classification section"""
        mcc_codes = scan.get('mcc_codes', {})
        primary = mcc_codes.get('primary_mcc')
        
        # Per PRD V2.1.1: Preserve evidence and signal classification
        if not primary:
            return {
                "primary_mcc": None,
                "confidence": 0.0,
                "keywords_matched": [],
                "secondary_mccs": [],
                "signal_type": mcc_codes.get('signal_type', 'advisory'),
                "min_confidence_threshold": mcc_codes.get('min_confidence_threshold', 30.0)
            }
        
        secondary = mcc_codes.get('secondary_mcc')
        all_matches = mcc_codes.get('all_matches', [])
        
        # Preserve evidence from primary MCC
        primary_data = {
            "code": primary.get('mcc_code', ''),
            "description": primary.get('description', ''),
            "category": primary.get('category', ''),
            "confidence": primary.get('confidence', 0.0),
            "keywords_matched": primary.get('keywords_matched', []),
            "evidence": primary.get('evidence'),  # Per PRD: Preserve evidence
            "low_confidence": primary.get('low_confidence', False),
            "status": primary.get('status')
        }
        
        secondary_data = None
        if secondary:
            secondary_data = {
                "code": secondary.get('mcc_code', ''),
                "description": secondary.get('description', ''),
                "confidence": secondary.get('confidence', 0.0),
                "evidence": secondary.get('evidence')  # Preserve evidence
            }
        
        return {
            "primary_mcc": primary_data,
            "confidence": primary.get('confidence', 0.0),
            "keywords_matched": primary.get('keywords_matched', []),
            "secondary_mccs": [secondary_data] if secondary_data else [],
            "signal_type": mcc_codes.get('signal_type', 'advisory'),
            "min_confidence_threshold": mcc_codes.get('min_confidence_threshold', 30.0),
            "all_matches": all_matches  # Include all matches with evidence
        }
    
    def _build_recommendations(self, scan: Dict[str, Any], business_context: Dict[str, Any]) -> List[str]:
        """Build actionable recommendations"""
        recommendations = []
        issues = self._build_issues(scan, business_context)
        
        # Group by severity
        high_issues = [i for i in issues if i.get('severity') == 'HIGH']
        medium_issues = [i for i in issues if i.get('severity') == 'MEDIUM']
        
        # High priority recommendations
        for issue in high_issues[:3]:  # Top 3
            if issue.get('required'):
                fix = issue.get('recommended_fix', '')
                if fix and fix not in recommendations:
                    recommendations.append(fix)
        
        # Medium priority recommendations
        if len(recommendations) < 5:
            for issue in medium_issues[:2]:
                fix = issue.get('recommended_fix', '')
                if fix and fix not in recommendations:
                    recommendations.append(fix)
        
        return recommendations
    
    def _generate_recommendation(self, score: int, rating: str, critical_issues: int, pass_status: bool) -> str:
        """Generate executive recommendation statement"""
        if pass_status and critical_issues == 0:
            return f"This site is compliant with a {rating.lower()} rating (score: {score}/100). No critical issues found."
        elif pass_status:
            return f"This site is partially compliant with a {rating.lower()} rating (score: {score}/100). {critical_issues} critical issue(s) require attention."
        else:
            return f"This site is not compliant with a {rating.lower()} rating (score: {score}/100). {critical_issues} critical issue(s) must be resolved before approval."
    
    def _get_fix_for_alert(self, code: str) -> str:
        """Get recommended fix for compliance alert code"""
        fixes = {
            'NO_HTTPS': 'Enable HTTPS with valid SSL certificate',
            'SSL_ERROR': 'Fix SSL certificate configuration',
            'DOMAIN_TOO_NEW': 'Wait for domain age to mature or provide additional verification',
            'REDIRECT_DETECTED': 'Ensure direct access to content without redirects'
        }
        return fixes.get(code, 'Review and fix compliance issue')

