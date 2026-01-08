"""
Audit Trail Builder
Generates complete, reproducible audit trails for KYC decisions

Per PRD Section 9: Audit & Compliance Requirements
- Every check must be deterministic
- Every check must be logged
- Every check must be reproducible
- No black-box decisions
- Evidence must be human-reviewable
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

try:
    from .models.output_schema import (
        AuditTrailOutput,
        CheckRecord,
        EvidenceSnippet,
        KeywordTrigger,
        TimestampRecord,
    )
except ImportError:
    from models.output_schema import (
        AuditTrailOutput,
        CheckRecord,
        EvidenceSnippet,
        KeywordTrigger,
        TimestampRecord,
    )


class AuditBuilder:
    """
    Builds structured audit trails for KYC screening.
    
    All checks are logged with:
    - Unique check ID
    - Check type (DETERMINISTIC or ADVISORY)
    - Timestamp
    - Duration
    - Status
    - Evidence/details
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self._reset()
    
    def _reset(self):
        """Reset audit state for new scan"""
        self._scan_id: Optional[str] = None
        self._target_url: Optional[str] = None
        self._merchant_name: Optional[str] = None
        self._start_time: Optional[datetime] = None
        self._checks: List[CheckRecord] = []
        self._timestamps: List[TimestampRecord] = []
        self._keywords: List[KeywordTrigger] = []
        self._snippets: List[EvidenceSnippet] = []
        self._urls_visited: List[str] = []
    
    def start_audit(
        self,
        scan_id: str,
        target_url: str,
        merchant_name: str,
    ) -> None:
        """
        Initialize a new audit trail.
        
        Args:
            scan_id: Unique scan identifier
            target_url: Website URL being scanned
            merchant_name: Merchant legal name
        """
        self._reset()
        self._scan_id = scan_id
        self._target_url = target_url
        self._merchant_name = merchant_name
        self._start_time = datetime.now()
        
        self.add_timestamp("AUDIT_INITIALIZED", f"Starting KYC scan for {merchant_name}")
        self.logger.debug(f"[AUDIT][{scan_id}] Audit trail initialized")
    
    def add_timestamp(self, event: str, details: Optional[str] = None) -> None:
        """
        Add a timestamp event to the audit trail.
        
        Args:
            event: Event name (e.g., "SCAN_START", "POLICY_CHECK_COMPLETE")
            details: Optional event details
        """
        record = TimestampRecord(
            event=event,
            timestamp=datetime.now(),
            details=details,
        )
        self._timestamps.append(record)
        self.logger.debug(f"[AUDIT][{self._scan_id}] Event: {event}")
    
    def add_check(
        self,
        check_id: str,
        check_name: str,
        check_type: str,
        status: str,
        details: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[int] = None,
    ) -> None:
        """
        Add a check record to the audit trail.
        
        Args:
            check_id: Unique check identifier
            check_name: Human-readable check name
            check_type: "DETERMINISTIC" or "ADVISORY"
            status: "PASS", "FAIL", "SKIP", "ERROR", or "REVIEW"
            details: Check-specific details
            duration_ms: Check duration in milliseconds
        """
        record = CheckRecord(
            check_id=check_id,
            check_name=check_name,
            check_type=check_type,
            status=status,
            timestamp=datetime.now(),
            duration_ms=duration_ms,
            details=details,
        )
        self._checks.append(record)
        self.logger.debug(f"[AUDIT][{self._scan_id}] Check: {check_name} = {status}")
    
    def add_keyword_trigger(
        self,
        keyword: str,
        category: str,
        source_url: str,
        snippet: str,
        severity: str = "MEDIUM",
    ) -> None:
        """
        Add a keyword trigger to the audit trail.
        
        Args:
            keyword: The keyword that was triggered
            category: Category of the keyword (e.g., "gambling", "crypto")
            source_url: URL where keyword was found
            snippet: Text snippet containing the keyword
            severity: Severity level
        """
        trigger = KeywordTrigger(
            keyword=keyword,
            category=category,
            source_url=source_url,
            snippet=snippet,
            severity=severity,
        )
        self._keywords.append(trigger)
        self.logger.debug(f"[AUDIT][{self._scan_id}] Keyword trigger: {keyword} ({category})")
    
    def add_evidence_snippet(
        self,
        source_url: str,
        snippet_text: str,
        context: Optional[str] = None,
        extraction_method: str = "rule_based",
        confidence: float = 1.0,
    ) -> None:
        """
        Add an evidence snippet to the audit trail.
        
        Args:
            source_url: URL where snippet was found
            snippet_text: The extracted text
            context: Surrounding context
            extraction_method: How the snippet was extracted
            confidence: Confidence score (0.0-1.0)
        """
        snippet = EvidenceSnippet(
            source_url=source_url,
            snippet_text=snippet_text,
            context=context,
            extraction_method=extraction_method,
            confidence=confidence,
        )
        self._snippets.append(snippet)
    
    def add_url_visited(self, url: str) -> None:
        """Add a URL to the list of visited URLs"""
        if url not in self._urls_visited:
            self._urls_visited.append(url)
    
    def add_urls_visited(self, urls: List[str]) -> None:
        """Add multiple URLs to the list of visited URLs"""
        for url in urls:
            self.add_url_visited(url)
    
    def build_audit_trail(
        self,
        scan_completed_at: datetime,
        scan_duration_seconds: float,
        final_url: str,
        pages_scanned: int,
        raw_scan_reference: Optional[str] = None,
    ) -> AuditTrailOutput:
        """
        Build the final audit trail output.
        
        Args:
            scan_completed_at: When the scan completed
            scan_duration_seconds: Total scan duration
            final_url: Final URL after redirects
            pages_scanned: Number of pages scanned
            raw_scan_reference: Reference to full raw scan data
            
        Returns:
            Complete AuditTrailOutput
        """
        self.add_timestamp("AUDIT_COMPLETE", f"KYC scan completed in {scan_duration_seconds:.2f}s")
        
        return AuditTrailOutput(
            scan_id=self._scan_id or str(uuid.uuid4())[:8],
            scan_started_at=self._start_time or datetime.now(),
            scan_completed_at=scan_completed_at,
            scan_duration_seconds=scan_duration_seconds,
            target_url=self._target_url or "",
            final_url=final_url,
            urls_visited=self._urls_visited,
            pages_scanned=pages_scanned,
            checks_performed=self._checks,
            keywords_triggered=self._keywords,
            text_snippets=self._snippets,
            timestamps=self._timestamps,
            raw_scan_reference=raw_scan_reference,
        )
    
    def import_scan_evidence(self, scan_data: Dict[str, Any]) -> None:
        """
        Import evidence from scan data into the audit trail.
        
        Args:
            scan_data: Raw scan data from ModularScanEngine
        """
        # Import URLs visited
        crawl_summary = scan_data.get('crawl_summary', {})
        visited_urls = crawl_summary.get('urls_visited', [])
        self.add_urls_visited(visited_urls)
        
        # Import content risk keywords
        content_risk = scan_data.get('content_risk', {})
        restricted = content_risk.get('restricted_keywords_found', [])
        
        for item in restricted:
            evidence = item.get('evidence', {})
            self.add_keyword_trigger(
                keyword=item.get('keyword', ''),
                category=item.get('category', ''),
                source_url=evidence.get('source_url', ''),
                snippet=evidence.get('evidence_snippet', ''),
                severity=evidence.get('severity', 'MEDIUM'),
            )
        
        # Import policy evidence
        policy_details = scan_data.get('policy_details', {})
        for policy_type, policy_data in policy_details.items():
            if policy_data.get('found'):
                evidence = policy_data.get('evidence', {})
                if evidence:
                    self.add_evidence_snippet(
                        source_url=policy_data.get('url', ''),
                        snippet_text=evidence.get('evidence_snippet', f"{policy_type} detected"),
                        context=evidence.get('triggering_rule', ''),
                        extraction_method=policy_data.get('detection_method', 'rule_based'),
                        confidence=evidence.get('confidence', 100.0) / 100.0,
                    )
        
        # Import compliance intelligence breakdown
        compliance_intel = scan_data.get('compliance_intelligence', {})
        breakdown = compliance_intel.get('breakdown', {})
        
        # Technical checks
        tech_details = breakdown.get('technical', {}).get('details', [])
        for item in tech_details:
            self.add_check(
                check_id=f"tech_{item.get('item', 'unknown').lower().replace(' ', '_')}",
                check_name=item.get('item', 'Unknown'),
                check_type="DETERMINISTIC",
                status="PASS" if item.get('score', 0) > 0 else "FAIL",
                details={
                    'score': item.get('score'),
                    'max': item.get('max'),
                    'status': item.get('status'),
                    'signal_reference': item.get('signal_reference'),
                },
            )
        
        # Policy checks
        policy_intel = breakdown.get('policy', {}).get('details', [])
        for item in policy_intel:
            self.add_check(
                check_id=f"policy_{item.get('item', 'unknown').lower().replace(' ', '_')}",
                check_name=item.get('item', 'Unknown'),
                check_type="DETERMINISTIC",
                status="PASS" if item.get('score', 0) > 0 else "FAIL",
                details={
                    'score': item.get('score'),
                    'max': item.get('max'),
                    'status': item.get('status'),
                    'expectation': item.get('expectation'),
                    'signal_reference': item.get('signal_reference'),
                },
            )
        
        # Trust/risk checks
        risk_flags = breakdown.get('trust', {}).get('details', [])
        for flag in risk_flags:
            self.add_check(
                check_id=f"risk_{flag.get('type', 'unknown').lower().replace(' ', '_')}",
                check_name=flag.get('type', 'Unknown'),
                check_type="DETERMINISTIC",
                status="FLAG" if flag.get('penalty', 0) > 0 else "PASS",
                details={
                    'severity': flag.get('severity'),
                    'message': flag.get('message'),
                    'penalty': flag.get('penalty'),
                    'triggering_keyword': flag.get('triggering_keyword'),
                    'triggering_category': flag.get('triggering_category'),
                },
            )
    
    def generate_summary_report(self) -> str:
        """
        Generate a human-readable summary of the audit trail.
        
        Returns:
            Markdown-formatted summary
        """
        lines = [
            f"# KYC Audit Trail Summary",
            f"",
            f"**Scan ID:** {self._scan_id}",
            f"**Target URL:** {self._target_url}",
            f"**Merchant:** {self._merchant_name}",
            f"**Start Time:** {self._start_time.isoformat() if self._start_time else 'N/A'}",
            f"",
            f"## Checks Performed ({len(self._checks)} total)",
            f"",
        ]
        
        # Group checks by status
        passed = [c for c in self._checks if c.status == "PASS"]
        failed = [c for c in self._checks if c.status == "FAIL"]
        flagged = [c for c in self._checks if c.status in ["FLAG", "REVIEW"]]
        
        lines.append(f"- **Passed:** {len(passed)}")
        lines.append(f"- **Failed:** {len(failed)}")
        lines.append(f"- **Flagged for Review:** {len(flagged)}")
        lines.append("")
        
        if failed:
            lines.append("### Failed Checks")
            for check in failed:
                lines.append(f"- **{check.check_name}** ({check.check_type})")
                if check.details:
                    lines.append(f"  - Details: {check.details}")
            lines.append("")
        
        if flagged:
            lines.append("### Flagged Checks")
            for check in flagged:
                lines.append(f"- **{check.check_name}** ({check.check_type})")
                if check.details:
                    lines.append(f"  - Details: {check.details}")
            lines.append("")
        
        if self._keywords:
            lines.append(f"## Keyword Triggers ({len(self._keywords)} total)")
            lines.append("")
            for kw in self._keywords[:10]:  # Limit to 10
                lines.append(f"- **{kw.keyword}** ({kw.category}, {kw.severity})")
                lines.append(f"  - Source: {kw.source_url}")
            lines.append("")
        
        lines.append(f"## Timeline ({len(self._timestamps)} events)")
        lines.append("")
        for ts in self._timestamps:
            lines.append(f"- [{ts.timestamp.strftime('%H:%M:%S')}] **{ts.event}**")
            if ts.details:
                lines.append(f"  - {ts.details}")
        
        return "\n".join(lines)

