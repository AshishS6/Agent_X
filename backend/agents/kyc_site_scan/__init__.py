"""
KYC Site Scan v2 Module
Automated Website Screening for Merchant KYC

This module provides a KYC Decision Layer that wraps the existing ModularScanEngine
to produce PASS/FAIL/ESCALATE decisions for merchant website screening.

Components:
- KYCDecisionEngine: Main orchestrator for KYC screening
- DecisionRules: Deterministic PASS/FAIL/ESCALATE rules
- CheckoutValidator: Browser-based checkout flow validation
- EntityMatcher: Legal entity fuzzy matching
- AuditBuilder: Audit trail generation

API Endpoints:
- POST /kyc/scan: Synchronous KYC scan
- POST /kyc/scan/async: Asynchronous scan with webhook callback
"""

__version__ = "2.0.0"

# Lazy imports to avoid circular dependency issues
def __getattr__(name):
    """Lazy import of module components"""
    if name == "KYCDecisionEngine":
        from .kyc_engine import KYCDecisionEngine
        return KYCDecisionEngine
    elif name == "DecisionRules":
        from .decision_rules import DecisionRules
        return DecisionRules
    elif name == "KYCDecision":
        from .decision_rules import KYCDecision
        return KYCDecision
    elif name == "CheckoutValidator":
        from .checkout_validator import CheckoutValidator
        return CheckoutValidator
    elif name == "EntityMatcher":
        from .entity_matcher import EntityMatcher
        return EntityMatcher
    elif name == "AuditBuilder":
        from .audit_builder import AuditBuilder
        return AuditBuilder
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "KYCDecisionEngine",
    "DecisionRules",
    "KYCDecision",
    "CheckoutValidator",
    "EntityMatcher",
    "AuditBuilder",
]

