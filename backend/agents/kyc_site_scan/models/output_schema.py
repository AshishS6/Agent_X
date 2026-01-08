"""
KYC Site Scan Output Schema
Defines the KYC decision output structure
Per PRD Section 8: Output Schema
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class KYCDecisionEnum(str, Enum):
    """KYC Decision outcomes per PRD Section 7"""
    PASS = "PASS"
    FAIL = "FAIL"
    ESCALATE = "ESCALATE"


class ReasonCode(BaseModel):
    """
    Reason code for KYC decision.
    Each reason code is deterministic and traceable.
    """
    code: str = Field(
        ...,
        description="Unique reason code identifier",
        examples=["MISSING_PRIVACY_POLICY", "HIGH_RISK_CONTENT", "SITE_UNREACHABLE"]
    )
    category: str = Field(
        ...,
        description="Category of the reason",
        examples=["POLICY", "CONTENT_RISK", "ACCESSIBILITY", "ENTITY_MISMATCH"]
    )
    severity: str = Field(
        ...,
        description="Severity level: CRITICAL, HIGH, MEDIUM, LOW",
        examples=["CRITICAL", "HIGH"]
    )
    message: str = Field(
        ...,
        description="Human-readable description of the issue"
    )
    evidence_url: Optional[str] = Field(
        default=None,
        description="URL where the issue was detected"
    )
    evidence_snippet: Optional[str] = Field(
        default=None,
        description="Text snippet showing the evidence"
    )
    is_auto_fail: bool = Field(
        default=False,
        description="Whether this reason triggers automatic FAIL"
    )
    is_auto_escalate: bool = Field(
        default=False,
        description="Whether this reason triggers automatic ESCALATE"
    )


class CheckRecord(BaseModel):
    """Record of a compliance check performed"""
    check_id: str = Field(..., description="Unique check identifier")
    check_name: str = Field(..., description="Name of the check")
    check_type: str = Field(..., description="Type: DETERMINISTIC or ADVISORY")
    status: str = Field(..., description="Status: PASS, FAIL, SKIP, ERROR")
    timestamp: datetime = Field(default_factory=datetime.now)
    duration_ms: Optional[int] = Field(default=None, description="Check duration in milliseconds")
    details: Optional[Dict[str, Any]] = Field(default=None)


class EvidenceSnippet(BaseModel):
    """Text snippet extracted as evidence"""
    source_url: str = Field(..., description="URL where snippet was found")
    snippet_text: str = Field(..., description="The extracted text")
    context: Optional[str] = Field(default=None, description="Surrounding context")
    extraction_method: str = Field(
        default="rule_based",
        description="How the snippet was extracted"
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score for the extraction"
    )


class KeywordTrigger(BaseModel):
    """Record of a triggered keyword detection with V2.2 intent classification"""
    keyword: str = Field(..., description="The keyword that was triggered")
    category: str = Field(..., description="Category of the keyword")
    source_url: str = Field(..., description="URL where keyword was found")
    snippet: str = Field(..., description="Text snippet containing the keyword")
    severity: str = Field(default="MEDIUM", description="Severity level")
    # V2.2: Intent classification fields
    intent: Optional[str] = Field(
        default="neutral",
        description="Intent classification: prohibitive, promotional, or neutral"
    )
    page_type: Optional[str] = Field(
        default=None,
        description="Type of page where keyword was found (e.g., privacy_policy, terms_conditions)"
    )
    intent_context: Optional[str] = Field(
        default=None,
        description="Surrounding text that determined the intent classification"
    )
    is_corroborated: bool = Field(
        default=False,
        description="Whether this keyword was found on multiple pages"
    )


class TimestampRecord(BaseModel):
    """Timestamp record for audit trail"""
    event: str = Field(..., description="Event name")
    timestamp: datetime = Field(default_factory=datetime.now)
    details: Optional[str] = Field(default=None)


class AuditTrailOutput(BaseModel):
    """
    Complete audit trail for KYC decision.
    Per PRD Section 9: Every check must be deterministic, logged, reproducible.
    """
    scan_id: str = Field(..., description="Unique scan identifier")
    scan_started_at: datetime = Field(..., description="Scan start timestamp")
    scan_completed_at: datetime = Field(..., description="Scan completion timestamp")
    scan_duration_seconds: float = Field(..., description="Total scan duration")
    
    # URLs and pages
    target_url: str = Field(..., description="Original target URL")
    final_url: str = Field(..., description="Final URL after redirects")
    urls_visited: List[str] = Field(default_factory=list, description="All URLs visited during scan")
    pages_scanned: int = Field(default=0, description="Number of pages scanned")
    
    # Checks and evidence
    checks_performed: List[CheckRecord] = Field(
        default_factory=list,
        description="List of all checks performed"
    )
    keywords_triggered: List[KeywordTrigger] = Field(
        default_factory=list,
        description="Keywords that triggered risk flags"
    )
    text_snippets: List[EvidenceSnippet] = Field(
        default_factory=list,
        description="Evidence text snippets"
    )
    timestamps: List[TimestampRecord] = Field(
        default_factory=list,
        description="Timeline of events"
    )
    
    # Raw scan data reference
    raw_scan_reference: Optional[str] = Field(
        default=None,
        description="Reference to full scan data (for deep audit)"
    )


class PolicyCheckResult(BaseModel):
    """Result of a policy page check"""
    policy_type: str = Field(..., description="Type of policy")
    found: bool = Field(..., description="Whether the policy was found")
    url: Optional[str] = Field(default=None, description="URL of the policy page")
    content_length: Optional[int] = Field(default=None, description="Content length in characters")
    has_required_keywords: bool = Field(default=False)
    expectation: str = Field(default="required", description="required/optional/n_a")


class CheckoutFlowResult(BaseModel):
    """Result of checkout flow validation"""
    has_cta: bool = Field(default=False, description="Whether CTAs were found")
    cta_clickable: bool = Field(default=False, description="Whether CTAs are clickable")
    checkout_reachable: bool = Field(default=False, description="Whether checkout page is reachable")
    pricing_visible: bool = Field(default=False, description="Whether pricing is visible")
    form_fields_present: bool = Field(default=False, description="Whether form fields exist")
    dead_ctas: List[str] = Field(default_factory=list, description="List of dead CTAs found")
    evidence: Optional[Dict[str, Any]] = Field(default=None)


class EntityMatchResult(BaseModel):
    """Result of legal entity matching"""
    declared_name: str = Field(..., description="Merchant's declared legal name")
    extracted_names: List[str] = Field(default_factory=list, description="Names extracted from website")
    best_match: Optional[str] = Field(default=None, description="Best matching name found")
    match_score: float = Field(default=0.0, ge=0.0, le=100.0, description="Match score percentage")
    match_status: str = Field(default="NO_MATCH", description="MATCH/PARTIAL_MATCH/MISMATCH/NO_MATCH")
    address_match: Optional[Dict[str, Any]] = Field(default=None, description="Address matching result")
    evidence: Optional[Dict[str, Any]] = Field(default=None)


class ComplianceScoreBreakdown(BaseModel):
    """Breakdown of compliance score components"""
    overall_score: int = Field(..., ge=0, le=100)
    technical_score: int = Field(..., ge=0, le=30)
    policy_score: int = Field(..., ge=0, le=40)
    trust_score: int = Field(..., ge=0, le=30)
    rating: str = Field(..., description="Good/Fair/Poor")


class ContentRiskSummary(BaseModel):
    """
    V2.2: Summary of content risk analysis with intent classification.
    Provides transparency into how risk scores were calculated.
    """
    total_keywords_found: int = Field(
        default=0,
        description="Total number of restricted keywords found across all pages"
    )
    risk_contributing_count: int = Field(
        default=0,
        description="Keywords that actually contribute to risk score (excludes policy mentions)"
    )
    policy_mentions_count: int = Field(
        default=0,
        description="Keywords found in prohibitive context on policy pages (informational only)"
    )
    corroborated_categories: List[str] = Field(
        default_factory=list,
        description="Categories with keywords found on multiple pages"
    )
    pages_analyzed: int = Field(
        default=0,
        description="Number of pages analyzed for content risk"
    )
    high_risk_categories: List[str] = Field(
        default_factory=list,
        description="High-risk categories detected (may trigger FAIL)"
    )
    medium_risk_categories: List[str] = Field(
        default_factory=list,
        description="Medium-risk categories detected (may trigger ESCALATE)"
    )
    dummy_content_detected: bool = Field(
        default=False,
        description="Whether placeholder/lorem ipsum content was detected"
    )


class KYCDecisionOutput(BaseModel):
    """
    Complete KYC decision output.
    Per PRD Section 8: Output Schema
    """
    # Core decision
    decision: KYCDecisionEnum = Field(
        ...,
        description="Final KYC decision: PASS, FAIL, or ESCALATE"
    )
    reason_codes: List[ReasonCode] = Field(
        default_factory=list,
        description="List of reason codes contributing to the decision"
    )
    summary: str = Field(
        ...,
        description="Human-readable summary of the decision"
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for the decision (0.0-1.0)"
    )
    
    # Detailed results
    policy_checks: List[PolicyCheckResult] = Field(
        default_factory=list,
        description="Results of policy page checks"
    )
    checkout_flow: Optional[CheckoutFlowResult] = Field(
        default=None,
        description="Results of checkout flow validation"
    )
    entity_match: Optional[EntityMatchResult] = Field(
        default=None,
        description="Results of legal entity matching"
    )
    compliance_score: Optional[ComplianceScoreBreakdown] = Field(
        default=None,
        description="Compliance score breakdown"
    )
    
    # Business context
    detected_business_type: Optional[str] = Field(
        default=None,
        description="Business type detected from website"
    )
    detected_mcc: Optional[str] = Field(
        default=None,
        description="MCC code detected from website"
    )
    product_match_status: Optional[str] = Field(
        default=None,
        description="Match/Partial/Mismatch status for declared products"
    )
    
    # V2.2: Content risk analysis summary
    content_risk_summary: Optional[ContentRiskSummary] = Field(
        default=None,
        description="V2.2: Summary of intent-aware content risk analysis"
    )
    
    # Audit trail
    audit_trail: AuditTrailOutput = Field(
        ...,
        description="Complete audit trail for compliance review"
    )
    
    # Metadata
    scan_version: str = Field(
        default="v2.0.0",
        description="Version of the KYC scan engine"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "decision": "PASS",
                "reason_codes": [],
                "summary": "Website screening passed. All mandatory compliance checks satisfied.",
                "confidence_score": 0.95,
                "policy_checks": [
                    {"policy_type": "privacy_policy", "found": True, "url": "https://example.com/privacy"},
                    {"policy_type": "terms_condition", "found": True, "url": "https://example.com/terms"}
                ],
                "checkout_flow": {
                    "has_cta": True,
                    "cta_clickable": True,
                    "checkout_reachable": True,
                    "pricing_visible": True,
                    "form_fields_present": True
                },
                "entity_match": {
                    "declared_name": "TechStart Solutions Pvt Ltd",
                    "best_match": "TechStart Solutions Private Limited",
                    "match_score": 92.5,
                    "match_status": "MATCH"
                },
                "detected_business_type": "SAAS",
                "detected_mcc": "7372"
            }
        }

