"""
Evidence Builder Module
Wraps signals with evidence metadata for explainability.
Every signal must include: source URL, triggering rule, evidence snippet, confidence/severity.
"""

from typing import Dict, Any, Optional, List
from urllib.parse import urlparse


class EvidenceBuilder:
    """
    Builds evidence metadata for signals to ensure explainability.
    
    Required fields per PRD:
    - source_url: URL where signal was detected
    - triggering_rule: Rule or pattern that triggered the signal
    - evidence_snippet: Text snippet or data that supports the signal
    - confidence_or_severity: Confidence score (0-100) or severity level
    """
    
    @staticmethod
    def build_evidence(
        source_url: str,
        triggering_rule: str,
        evidence_snippet: str,
        confidence: Optional[float] = None,
        severity: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build evidence dictionary for a signal.
        
        Args:
            source_url: URL where signal was detected
            triggering_rule: Rule, pattern, or method that triggered detection
            evidence_snippet: Text snippet, data, or description supporting the signal
            confidence: Confidence score 0-100 (for advisory signals)
            severity: Severity level (for risk signals: "critical", "moderate", "info")
            additional_context: Additional context data (optional)
            
        Returns:
            Evidence dictionary with all required fields
        """
        evidence = {
            "source_url": source_url,
            "triggering_rule": triggering_rule,
            "evidence_snippet": evidence_snippet
        }
        
        # Add confidence or severity (at least one required)
        if confidence is not None:
            evidence["confidence"] = max(0, min(100, confidence))  # Clamp to 0-100
        
        if severity is not None:
            evidence["severity"] = severity
        
        # If neither provided, default to low confidence
        if confidence is None and severity is None:
            evidence["confidence"] = 0.0
            evidence["severity"] = "info"
        
        # Add additional context if provided
        if additional_context:
            evidence["additional_context"] = additional_context
        
        return evidence
    
    @staticmethod
    def build_policy_evidence(
        policy_url: str,
        detection_method: str,
        anchor_text: Optional[str] = None,
        page_title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build evidence for policy detection.
        
        Args:
            policy_url: URL of detected policy page
            detection_method: How it was detected ("url_pattern", "anchor_text", "title", "page_graph")
            anchor_text: Link text that matched (if applicable)
            page_title: Page title (if applicable)
            
        Returns:
            Evidence dictionary for policy detection
        """
        snippet_parts = []
        if anchor_text:
            snippet_parts.append(f"Link text: '{anchor_text}'")
        if page_title:
            snippet_parts.append(f"Page title: '{page_title}'")
        if not snippet_parts:
            snippet_parts.append(f"Detected via {detection_method}")
        
        evidence_snippet = " | ".join(snippet_parts)
        
        return EvidenceBuilder.build_evidence(
            source_url=policy_url,
            triggering_rule=f"Policy detection via {detection_method}",
            evidence_snippet=evidence_snippet,
            confidence=100.0 if policy_url else 0.0  # Presence is authoritative
        )
    
    @staticmethod
    def build_content_risk_evidence(
        page_url: str,
        keyword: str,
        category: str,
        text_snippet: str,
        severity: str = "moderate"
    ) -> Dict[str, Any]:
        """
        Build evidence for content risk detection.
        
        Args:
            page_url: URL where risk was detected
            keyword: Keyword that triggered detection
            category: Risk category (gambling, adult, crypto, etc.)
            text_snippet: Text snippet containing the keyword (max 200 chars)
            severity: Severity level
            
        Returns:
            Evidence dictionary for content risk
        """
        # Truncate snippet if too long
        if len(text_snippet) > 200:
            text_snippet = text_snippet[:197] + "..."
        
        return EvidenceBuilder.build_evidence(
            source_url=page_url,
            triggering_rule=f"Rule-based keyword matching: '{keyword}' in category '{category}'",
            evidence_snippet=text_snippet,
            severity=severity,
            confidence=50.0  # Rule-based detection has moderate confidence
        )
    
    @staticmethod
    def build_mcc_evidence(
        matched_keywords: List[str],
        pages_matched: List[str],
        confidence: float,
        render_types_by_url: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Build evidence for MCC classification.
        
        Args:
            matched_keywords: List of keywords that matched
            pages_matched: List of page URLs where keywords were found
            confidence: Confidence score 0-100
            
        Returns:
            Evidence dictionary for MCC classification
        """
        evidence_snippet = f"Matched keywords: {', '.join(matched_keywords[:5])}"
        if len(matched_keywords) > 5:
            evidence_snippet += f" (+{len(matched_keywords) - 5} more)"
        
        return EvidenceBuilder.build_evidence(
            source_url=pages_matched[0] if pages_matched else "",
            triggering_rule="Keyword-based MCC classification",
            evidence_snippet=evidence_snippet,
            confidence=confidence,
            additional_context={
                "keywords_matched": matched_keywords,
                "pages_matched": pages_matched,
                # Provenance: whether pages were fetched via http/js/cache (when provided)
                "render_types_by_url": render_types_by_url or {}
            }
        )
    
    @staticmethod
    def build_change_evidence(
        page_url: str,
        change_type: str,
        change_description: str,
        classification: str = "informational"
    ) -> Dict[str, Any]:
        """
        Build evidence for change detection.
        
        Args:
            page_url: URL of changed page
            change_type: Type of change (content_change, pricing_change, product_change)
            change_description: Description of what changed
            classification: Why it matters (informational, moderate, critical)
            
        Returns:
            Evidence dictionary for change detection
        """
        return EvidenceBuilder.build_evidence(
            source_url=page_url,
            triggering_rule=f"Content hash comparison: {change_type}",
            evidence_snippet=change_description,
            severity=classification,
            confidence=100.0  # Hash-based detection is deterministic
        )
    
    @staticmethod
    def validate_evidence(evidence: Dict[str, Any]) -> bool:
        """
        Validate that evidence has all required fields.
        If missing fields, downgrade severity.
        
        Args:
            evidence: Evidence dictionary to validate
            
        Returns:
            True if evidence is complete, False if missing required fields
        """
        required_fields = ["source_url", "triggering_rule", "evidence_snippet"]
        
        for field in required_fields:
            if field not in evidence or not evidence[field]:
                return False
        
        # Must have either confidence or severity
        if "confidence" not in evidence and "severity" not in evidence:
            return False
        
        return True
    
    @staticmethod
    def downgrade_missing_evidence(evidence: Dict[str, Any]) -> Dict[str, Any]:
        """
        Downgrade evidence if fields are missing.
        Sets confidence to 0 and severity to "info" if missing.
        
        Args:
            evidence: Evidence dictionary (may be incomplete)
            
        Returns:
            Evidence dictionary with downgraded confidence/severity if incomplete
        """
        if not EvidenceBuilder.validate_evidence(evidence):
            evidence["confidence"] = 0.0
            evidence["severity"] = "info"
            evidence["missing_fields"] = True
        
        return evidence

