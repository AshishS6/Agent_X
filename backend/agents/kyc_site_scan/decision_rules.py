"""
KYC Decision Rules Engine
Deterministic PASS/FAIL/ESCALATE rules per PRD Section 7

Key Principle: LLM reasoning CANNOT override deterministic compliance rules.
All decisions are based on rule evaluation, not AI interpretation.

V2.1 Updates:
- Intent-aware content risk analysis (prohibitive vs promotional)
- Multi-page corroboration for severity determination
- RDAP/domain age validation
- Page type context for false positive reduction

V2.2 Updates:
- Full integration with site scan's intent classification
- Differentiate policy_mentions_count vs risk_contributing_count
- Use corroboration status from multi-page content risk analysis
- Enhanced evidence extraction with intent context
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging

try:
    from .models.output_schema import (
        KYCDecisionEnum,
        ReasonCode,
        PolicyCheckResult,
        CheckoutFlowResult,
        EntityMatchResult,
    )
except ImportError:
    from models.output_schema import (
        KYCDecisionEnum,
        ReasonCode,
        PolicyCheckResult,
        CheckoutFlowResult,
        EntityMatchResult,
    )


class RuleCategory(str, Enum):
    """Categories for decision rules"""
    ACCESSIBILITY = "ACCESSIBILITY"
    POLICY = "POLICY"
    CONTENT_RISK = "CONTENT_RISK"
    CHECKOUT = "CHECKOUT"
    ENTITY = "ENTITY"
    PRODUCT = "PRODUCT"
    CONTACT = "CONTACT"


class RuleSeverity(str, Enum):
    """Severity levels for rules"""
    CRITICAL = "CRITICAL"  # Auto-FAIL
    HIGH = "HIGH"          # Auto-ESCALATE
    MEDIUM = "MEDIUM"      # Weighted consideration
    LOW = "LOW"            # Advisory only


@dataclass
class RuleResult:
    """Result of a single rule evaluation"""
    rule_id: str
    triggered: bool
    category: RuleCategory
    severity: RuleSeverity
    message: str
    evidence_url: Optional[str] = None
    evidence_snippet: Optional[str] = None
    is_auto_fail: bool = False
    is_auto_escalate: bool = False
    
    def to_reason_code(self) -> ReasonCode:
        """Convert to ReasonCode output schema"""
        return ReasonCode(
            code=self.rule_id,
            category=self.category.value,
            severity=self.severity.value,
            message=self.message,
            evidence_url=self.evidence_url,
            evidence_snippet=self.evidence_snippet,
            is_auto_fail=self.is_auto_fail,
            is_auto_escalate=self.is_auto_escalate,
        )


@dataclass
class KYCDecision:
    """Final KYC decision with all contributing factors"""
    decision: KYCDecisionEnum
    reason_codes: List[ReasonCode]
    confidence_score: float
    summary: str
    fail_reasons: List[str] = field(default_factory=list)
    escalate_reasons: List[str] = field(default_factory=list)


class DecisionRules:
    """
    Deterministic KYC decision rules engine.
    
    Rule Priority:
    1. FAIL conditions are evaluated first (site unreachable, missing mandatory policies, prohibited content)
    2. ESCALATE conditions are evaluated next (partial matches, missing optional but important items)
    3. PASS is returned only if no FAIL or ESCALATE conditions are met
    
    Per PRD Section 7:
    - IF prohibited_risk = HIGH → FAIL
    - IF missing T&C OR Privacy Policy → FAIL
    - IF site unreachable → FAIL
    - IF product mismatch → ESCALATE
    - IF checkout missing → ESCALATE
    - ELSE → PASS
    """
    
    # ==================== FAIL CONDITIONS ====================
    # These conditions trigger automatic FAIL - cannot be overridden
    
    FAIL_RULES = [
        # (rule_id, category, message_template)
        ("SITE_UNREACHABLE", RuleCategory.ACCESSIBILITY, "Website is unreachable or returned error status"),
        ("PARKED_DOMAIN", RuleCategory.ACCESSIBILITY, "Domain appears to be parked or under construction"),
        ("DNS_FAIL", RuleCategory.ACCESSIBILITY, "Could not resolve domain DNS"),
        ("SSL_ERROR", RuleCategory.ACCESSIBILITY, "SSL certificate error - site is not secure"),
        ("MISSING_PRIVACY_POLICY", RuleCategory.POLICY, "Privacy Policy page is missing (mandatory)"),
        ("MISSING_TERMS", RuleCategory.POLICY, "Terms & Conditions page is missing (mandatory)"),
        ("HIGH_RISK_CONTENT_GAMBLING", RuleCategory.CONTENT_RISK, "High-risk gambling content detected"),
        ("HIGH_RISK_CONTENT_ADULT", RuleCategory.CONTENT_RISK, "High-risk adult content detected"),
        ("HIGH_RISK_CONTENT_ILLEGAL", RuleCategory.CONTENT_RISK, "Illegal content or activities detected"),
        ("HIGH_RISK_CONTENT_WEAPONS", RuleCategory.CONTENT_RISK, "Weapons-related content detected"),
        ("HIGH_RISK_CONTENT_DRUGS", RuleCategory.CONTENT_RISK, "Drug-related content detected"),
        ("DEAD_CTAS_ONLY", RuleCategory.CHECKOUT, "All checkout CTAs are non-functional"),
        ("FAKE_PRICING", RuleCategory.CHECKOUT, "Pricing appears to be placeholder/fake"),
    ]
    
    # ==================== ESCALATE CONDITIONS ====================
    # These conditions trigger ESCALATE for human review
    
    ESCALATE_RULES = [
        ("PRODUCT_MISMATCH", RuleCategory.PRODUCT, "Website products do not match declared offerings"),
        ("NO_CHECKOUT_FLOW", RuleCategory.CHECKOUT, "No checkout/purchase flow detected"),
        ("CHECKOUT_INCOMPLETE", RuleCategory.CHECKOUT, "Checkout flow is incomplete or broken"),
        ("NO_CONTACT_METHOD", RuleCategory.CONTACT, "No contact information found"),
        ("LEGAL_ENTITY_MISMATCH", RuleCategory.ENTITY, "Legal entity name does not match website"),
        ("ADDRESS_MISMATCH", RuleCategory.ENTITY, "Registered address does not match website"),
        ("MEDIUM_RISK_CONTENT", RuleCategory.CONTENT_RISK, "Medium-risk content requires review"),
        ("MISSING_REFUND_POLICY", RuleCategory.POLICY, "Refund policy missing (e-commerce)"),
        ("DOMAIN_TOO_NEW", RuleCategory.ACCESSIBILITY, "Domain is less than 6 months old"),
        ("PARTIAL_ENTITY_MATCH", RuleCategory.ENTITY, "Legal entity name partially matches"),
        ("BUSINESS_TYPE_MISMATCH", RuleCategory.PRODUCT, "Detected business type differs from declared"),
    ]
    
    # High-risk content categories that trigger FAIL
    HIGH_RISK_CATEGORIES = {
        "gambling", "adult", "child_pornography", "weapons", "drugs",
        "illegal_goods", "hacking", "counterfeit"
    }
    
    # Medium-risk content categories that trigger ESCALATE
    MEDIUM_RISK_CATEGORIES = {
        "crypto", "forex", "binary", "pharmacy", "alcohol", "tobacco",
        "securities", "mlm", "dating_escort"
    }
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self._rule_results: List[RuleResult] = []
    
    def evaluate(
        self,
        scan_data: Dict[str, Any],
        merchant_input: Dict[str, Any],
        policy_checks: List[PolicyCheckResult],
        checkout_result: Optional[CheckoutFlowResult],
        entity_match: Optional[EntityMatchResult],
    ) -> KYCDecision:
        """
        Evaluate all rules and produce final KYC decision.
        
        Args:
            scan_data: Raw scan output from ModularScanEngine
            merchant_input: Original merchant KYC input
            policy_checks: Results of policy page checks
            checkout_result: Results of checkout flow validation
            entity_match: Results of legal entity matching
            
        Returns:
            KYCDecision with final decision and all contributing factors
        """
        self._rule_results = []
        fail_reasons = []
        escalate_reasons = []
        
        # Phase 1: Evaluate accessibility rules
        self._evaluate_accessibility_rules(scan_data)
        
        # Phase 2: Evaluate policy rules
        self._evaluate_policy_rules(policy_checks, scan_data)
        
        # Phase 3: Evaluate content risk rules
        self._evaluate_content_risk_rules(scan_data)
        
        # Phase 4: Evaluate checkout rules
        self._evaluate_checkout_rules(checkout_result, scan_data)
        
        # Phase 5: Evaluate entity matching rules
        self._evaluate_entity_rules(entity_match, merchant_input)
        
        # Phase 6: Evaluate product/business type matching
        self._evaluate_product_rules(scan_data, merchant_input)
        
        # Phase 7: Evaluate contact rules
        self._evaluate_contact_rules(scan_data, policy_checks)
        
        # Collect results
        for result in self._rule_results:
            if result.triggered:
                if result.is_auto_fail:
                    fail_reasons.append(result.message)
                elif result.is_auto_escalate:
                    escalate_reasons.append(result.message)
        
        # Determine final decision
        decision, confidence, summary = self._make_decision(
            fail_reasons, escalate_reasons, scan_data
        )
        
        # Build reason codes from triggered rules
        reason_codes = [
            r.to_reason_code() for r in self._rule_results if r.triggered
        ]
        
        return KYCDecision(
            decision=decision,
            reason_codes=reason_codes,
            confidence_score=confidence,
            summary=summary,
            fail_reasons=fail_reasons,
            escalate_reasons=escalate_reasons,
        )
    
    def _evaluate_accessibility_rules(self, scan_data: Dict[str, Any]) -> None:
        """Evaluate website accessibility rules"""
        scan_status = scan_data.get('scan_status', {})
        status = scan_status.get('status', 'SUCCESS')
        reason = scan_status.get('reason', '')
        
        # Site unreachable
        if status == 'FAILED':
            if reason == 'DNS_FAIL':
                self._add_fail_result(
                    "DNS_FAIL",
                    RuleCategory.ACCESSIBILITY,
                    "Could not resolve domain DNS",
                    evidence_snippet=scan_status.get('message', '')
                )
            elif reason in ['HTTP_403', 'HTTP_401']:
                self._add_fail_result(
                    "SITE_UNREACHABLE",
                    RuleCategory.ACCESSIBILITY,
                    f"Website access denied ({reason})",
                    evidence_snippet=scan_status.get('message', '')
                )
            elif reason == 'SSL_ERROR':
                self._add_fail_result(
                    "SSL_ERROR",
                    RuleCategory.ACCESSIBILITY,
                    "SSL certificate error - site is not secure",
                    evidence_snippet=scan_status.get('message', '')
                )
            elif reason == 'TIMEOUT':
                self._add_fail_result(
                    "SITE_UNREACHABLE",
                    RuleCategory.ACCESSIBILITY,
                    "Website connection timed out",
                    evidence_snippet=scan_status.get('message', '')
                )
            else:
                self._add_fail_result(
                    "SITE_UNREACHABLE",
                    RuleCategory.ACCESSIBILITY,
                    f"Website unreachable: {reason}",
                    evidence_snippet=scan_status.get('message', '')
                )
        
        # Check for parked domain indicators
        crawl_summary = scan_data.get('crawl_summary', {})
        if crawl_summary.get('is_parked_domain', False):
            self._add_fail_result(
                "PARKED_DOMAIN",
                RuleCategory.ACCESSIBILITY,
                "Domain appears to be parked or under construction",
            )
        
        # V2.2: Check domain age from RDAP data with multiple field names
        rdap = scan_data.get('rdap', {})
        # Support both 'domain_age_days' and 'age_days' field names
        domain_age_days = rdap.get('domain_age_days') or rdap.get('age_days')
        
        if domain_age_days is not None:
            try:
                domain_age_days = int(domain_age_days)
                if domain_age_days < 180:
                    # Domain less than 6 months old - ESCALATE
                    self._add_escalate_result(
                        "DOMAIN_TOO_NEW",
                        RuleCategory.ACCESSIBILITY,
                        f"Domain is only {domain_age_days} days old (less than 6 months)",
                        evidence_snippet=f"Registered: {rdap.get('registration_date', 'Unknown')}",
                    )
                elif domain_age_days < 365:
                    # Domain less than 1 year - advisory note in audit
                    self.logger.info(
                        f"[KYC] Domain age is {domain_age_days} days (6-12 months) - "
                        f"within acceptable range but noted for review"
                    )
            except (ValueError, TypeError):
                self.logger.warning(f"[KYC] Invalid domain_age_days value: {domain_age_days}")
    
    def _evaluate_policy_rules(
        self,
        policy_checks: List[PolicyCheckResult],
        scan_data: Dict[str, Any]
    ) -> None:
        """Evaluate mandatory policy page rules"""
        policy_map = {p.policy_type: p for p in policy_checks}
        
        # Privacy Policy - MANDATORY
        privacy = policy_map.get('privacy_policy')
        if not privacy or not privacy.found:
            self._add_fail_result(
                "MISSING_PRIVACY_POLICY",
                RuleCategory.POLICY,
                "Privacy Policy page is missing (mandatory for all merchants)",
            )
        
        # Terms & Conditions - MANDATORY
        terms = policy_map.get('terms_condition')
        if not terms or not terms.found:
            self._add_fail_result(
                "MISSING_TERMS",
                RuleCategory.POLICY,
                "Terms & Conditions page is missing (mandatory for all merchants)",
            )
        
        # Refund Policy - CONDITIONAL (required for e-commerce)
        business_context = scan_data.get('business_context') or {}
        context_type = business_context.get('primary', 'UNKNOWN') if isinstance(business_context, dict) else 'UNKNOWN'
        
        refund = policy_map.get('returns_refund')
        if context_type in ['ECOMMERCE', 'UNKNOWN']:
            if not refund or not refund.found:
                self._add_escalate_result(
                    "MISSING_REFUND_POLICY",
                    RuleCategory.POLICY,
                    "Refund/Returns policy missing for e-commerce site",
                )
    
    def _evaluate_content_risk_rules(self, scan_data: Dict[str, Any]) -> None:
        """
        Evaluate content risk rules with V2.2 intent-aware analysis.
        
        Key improvements:
        - Ignores keywords with prohibitive intent on policy pages (false positives)
        - Uses corroboration status for severity determination
        - Differentiates policy_mentions_count vs risk_contributing_count
        """
        content_risk = scan_data.get('content_risk', {})
        restricted_keywords = content_risk.get('restricted_keywords_found', [])
        
        # V2.2: Extract metadata about intent-aware processing
        policy_mentions_count = content_risk.get('policy_mentions_count', 0)
        risk_contributing_count = content_risk.get('risk_contributing_count', 0)
        corroboration = content_risk.get('corroboration', {})
        
        high_risk_found = []
        medium_risk_found = []
        
        # Policy page types where prohibitive intent should be ignored
        # V2.2: Expanded list to include all policy-like pages
        policy_page_types = {
            'privacy_policy', 'terms_conditions', 'terms_condition',
            'refund_policy', 'returns_refund', 'acceptable_use',
            'prohibited_activities', 'restricted_businesses',
            'shipping_delivery', 'shipping_policy', 'delivery_policy',
            'faq', 'help', 'support', 'legal', 'disclaimer',
            'cancellation_policy', 'cookie_policy', 'data_safety',
        }
        
        for item in restricted_keywords:
            category = item.get('category', '').lower()
            keyword = item.get('keyword', '')
            evidence = item.get('evidence', {})
            
            # V2.2: Check intent classification
            intent = item.get('intent', 'neutral')
            page_type = item.get('page_type', '')
            intent_context = item.get('intent_context', '')
            is_corroborated = evidence.get('corroborated', False) if isinstance(evidence, dict) else False
            
            # Skip keywords with prohibitive intent on policy pages
            # These are legal disclaimers, not actual business activities
            if intent == 'prohibitive' and page_type in policy_page_types:
                self.logger.debug(
                    f"[KYC] Skipping prohibitive mention on policy page: "
                    f"keyword='{keyword}', page_type={page_type}"
                )
                continue
            
            # Determine severity based on category and corroboration
            if category in self.HIGH_RISK_CATEGORIES:
                # V2.2: Only escalate to high_risk if corroborated or not on policy page
                if is_corroborated or page_type not in policy_page_types:
                    high_risk_found.append((category, keyword, evidence, intent, intent_context, is_corroborated))
                else:
                    # Single occurrence on non-policy page - still flag but as medium
                    medium_risk_found.append((category, keyword, evidence, intent, intent_context))
            elif category in self.MEDIUM_RISK_CATEGORIES:
                medium_risk_found.append((category, keyword, evidence, intent, intent_context))
        
        # High-risk content triggers FAIL - with corroboration awareness
        for category, keyword, evidence, intent, intent_context, is_corroborated in high_risk_found:
            rule_id = f"HIGH_RISK_CONTENT_{category.upper()}"
            
            # Build message with context
            message = f"High-risk {category} content detected (keyword: '{keyword}')"
            if is_corroborated:
                corroborating_urls = corroboration.get(category, [])
                if len(corroborating_urls) > 1:
                    message += f" - corroborated on {len(corroborating_urls)} pages"
            
            self._add_fail_result(
                rule_id,
                RuleCategory.CONTENT_RISK,
                message,
                evidence_url=evidence.get('source_url') if isinstance(evidence, dict) else None,
                evidence_snippet=evidence.get('evidence_snippet') if isinstance(evidence, dict) else None,
            )
        
        # Medium-risk content triggers ESCALATE
        if medium_risk_found and not high_risk_found:
            categories = set(c for c, _, _, _, _ in medium_risk_found)
            # Include intent context in evidence for human review
            evidence_items = []
            for cat, kw, ev, intent, intent_ctx in medium_risk_found[:3]:
                item_info = f"{kw}"
                if intent_ctx:
                    item_info += f" (context: {intent_ctx[:50]}...)"
                evidence_items.append(item_info)
            
            self._add_escalate_result(
                "MEDIUM_RISK_CONTENT",
                RuleCategory.CONTENT_RISK,
                f"Medium-risk content detected: {', '.join(categories)}",
                evidence_snippet="; ".join(evidence_items),
            )
        
        # V2.2: Log policy mentions for audit trail
        if policy_mentions_count > 0:
            self.logger.info(
                f"[KYC] Intent-aware analysis: {policy_mentions_count} policy mentions "
                f"(prohibitive/informational) ignored, {risk_contributing_count} risk-contributing items evaluated"
            )
        
        # Check for dummy/placeholder content
        if content_risk.get('dummy_words_detected', False):
            dummy_evidence = content_risk.get('dummy_words_evidence', [])
            evidence_snippet = None
            evidence_url = None
            if dummy_evidence and len(dummy_evidence) > 0:
                first_evidence = dummy_evidence[0]
                evidence_snippet = first_evidence.get('evidence_snippet')
                evidence_url = first_evidence.get('page_url')
            
            self._add_escalate_result(
                "PLACEHOLDER_CONTENT",
                RuleCategory.CONTENT_RISK,
                "Placeholder/dummy content detected (lorem ipsum)",
                evidence_url=evidence_url,
                evidence_snippet=evidence_snippet,
            )
    
    def _evaluate_checkout_rules(
        self,
        checkout_result: Optional[CheckoutFlowResult],
        scan_data: Dict[str, Any]
    ) -> None:
        """Evaluate checkout flow rules"""
        if checkout_result is None:
            # Fall back to basic product indicators from scan
            product_details = scan_data.get('product_details', {})
            has_cart = product_details.get('has_cart', False)
            has_pricing = product_details.get('has_pricing', False)
            
            if not has_cart and not has_pricing:
                self._add_escalate_result(
                    "NO_CHECKOUT_FLOW",
                    RuleCategory.CHECKOUT,
                    "No checkout/purchase flow detected on website",
                )
            return
        
        # Check for dead CTAs
        if checkout_result.dead_ctas and len(checkout_result.dead_ctas) > 0:
            if not checkout_result.cta_clickable:
                self._add_fail_result(
                    "DEAD_CTAS_ONLY",
                    RuleCategory.CHECKOUT,
                    f"All checkout CTAs are non-functional: {checkout_result.dead_ctas}",
                )
        
        # Check for missing checkout flow
        if not checkout_result.has_cta:
            self._add_escalate_result(
                "NO_CHECKOUT_FLOW",
                RuleCategory.CHECKOUT,
                "No checkout/purchase CTAs found on website",
            )
        elif not checkout_result.checkout_reachable:
            self._add_escalate_result(
                "CHECKOUT_INCOMPLETE",
                RuleCategory.CHECKOUT,
                "Checkout page is not reachable from CTAs",
            )
        
        # Check for visible pricing
        if not checkout_result.pricing_visible:
            self._add_escalate_result(
                "MISSING_PRICING",
                RuleCategory.CHECKOUT,
                "Product pricing is not visible on website",
            )
    
    def _evaluate_entity_rules(
        self,
        entity_match: Optional[EntityMatchResult],
        merchant_input: Dict[str, Any]
    ) -> None:
        """Evaluate legal entity matching rules"""
        if entity_match is None:
            return
        
        match_status = entity_match.match_status
        match_score = entity_match.match_score
        
        if match_status == "MISMATCH" or match_score < 60:
            self._add_escalate_result(
                "LEGAL_ENTITY_MISMATCH",
                RuleCategory.ENTITY,
                f"Legal entity name mismatch (score: {match_score:.1f}%): "
                f"declared '{entity_match.declared_name}' vs found '{entity_match.best_match or 'N/A'}'",
            )
        elif match_status == "PARTIAL_MATCH" or (60 <= match_score < 80):
            self._add_escalate_result(
                "PARTIAL_ENTITY_MATCH",
                RuleCategory.ENTITY,
                f"Legal entity name partially matches (score: {match_score:.1f}%)",
            )
        
        # Check address matching
        if entity_match.address_match:
            addr_match = entity_match.address_match
            if addr_match.get('status') == 'MISMATCH':
                self._add_escalate_result(
                    "ADDRESS_MISMATCH",
                    RuleCategory.ENTITY,
                    "Registered address does not match website",
                )
    
    def _evaluate_product_rules(
        self,
        scan_data: Dict[str, Any],
        merchant_input: Dict[str, Any]
    ) -> None:
        """Evaluate product/service matching rules"""
        # Get declared business type and detected type
        declared_type = merchant_input.get('declared_business_type', '').upper()
        business_context = scan_data.get('business_context') or {}
        detected_type = business_context.get('primary', 'UNKNOWN') if isinstance(business_context, dict) else 'UNKNOWN'
        
        # Check for business type mismatch
        type_mapping = {
            'E-COMMERCE': ['ECOMMERCE', 'RETAIL'],
            'ECOMMERCE': ['ECOMMERCE', 'RETAIL'],
            'SAAS': ['SAAS', 'SOFTWARE'],
            'SOFTWARE': ['SAAS', 'SOFTWARE'],
            'FINTECH': ['FINTECH', 'FINANCIAL'],
            'FINANCIAL': ['FINTECH', 'FINANCIAL'],
            'RETAIL': ['ECOMMERCE', 'RETAIL'],
        }
        
        allowed_types = type_mapping.get(declared_type, [declared_type])
        if detected_type != 'UNKNOWN' and detected_type not in allowed_types:
            self._add_escalate_result(
                "BUSINESS_TYPE_MISMATCH",
                RuleCategory.PRODUCT,
                f"Declared business type '{declared_type}' but detected '{detected_type}'",
            )
        
        # Product matching would require more sophisticated analysis
        # For now, we track it as an advisory check
        declared_products = merchant_input.get('declared_products_services', [])
        product_details = scan_data.get('product_details', {})
        extracted_products = product_details.get('extracted_products', [])
        
        if declared_products and not extracted_products:
            self._add_escalate_result(
                "PRODUCT_MISMATCH",
                RuleCategory.PRODUCT,
                "Could not verify declared products/services on website",
            )
    
    def _evaluate_contact_rules(
        self,
        scan_data: Dict[str, Any],
        policy_checks: List[PolicyCheckResult]
    ) -> None:
        """Evaluate contact information rules"""
        policy_map = {p.policy_type: p for p in policy_checks}
        
        contact = policy_map.get('contact_us')
        business_details = scan_data.get('business_details', {})
        contact_info = business_details.get('contact_info', {})
        
        has_contact_page = contact and contact.found
        has_email = contact_info.get('email', 'Not found') != 'Not found'
        has_phone = contact_info.get('phone', 'Not found') != 'Not found'
        has_address = contact_info.get('address', 'Not found') != 'Not found'
        
        if not has_contact_page and not has_email and not has_phone:
            self._add_escalate_result(
                "NO_CONTACT_METHOD",
                RuleCategory.CONTACT,
                "No contact information found (no contact page, email, or phone)",
            )
    
    def _add_fail_result(
        self,
        rule_id: str,
        category: RuleCategory,
        message: str,
        evidence_url: Optional[str] = None,
        evidence_snippet: Optional[str] = None,
    ) -> None:
        """Add a FAIL rule result"""
        self._rule_results.append(RuleResult(
            rule_id=rule_id,
            triggered=True,
            category=category,
            severity=RuleSeverity.CRITICAL,
            message=message,
            evidence_url=evidence_url,
            evidence_snippet=evidence_snippet,
            is_auto_fail=True,
            is_auto_escalate=False,
        ))
    
    def _add_escalate_result(
        self,
        rule_id: str,
        category: RuleCategory,
        message: str,
        evidence_url: Optional[str] = None,
        evidence_snippet: Optional[str] = None,
    ) -> None:
        """Add an ESCALATE rule result"""
        self._rule_results.append(RuleResult(
            rule_id=rule_id,
            triggered=True,
            category=category,
            severity=RuleSeverity.HIGH,
            message=message,
            evidence_url=evidence_url,
            evidence_snippet=evidence_snippet,
            is_auto_fail=False,
            is_auto_escalate=True,
        ))
    
    def _make_decision(
        self,
        fail_reasons: List[str],
        escalate_reasons: List[str],
        scan_data: Dict[str, Any]
    ) -> Tuple[KYCDecisionEnum, float, str]:
        """
        Make final decision based on collected reasons.
        
        Returns:
            Tuple of (decision, confidence_score, summary)
        """
        # FAIL takes priority
        if fail_reasons:
            confidence = 0.95  # High confidence for deterministic FAIL
            summary = f"KYC FAILED: {fail_reasons[0]}"
            if len(fail_reasons) > 1:
                summary += f" (+{len(fail_reasons)-1} more issues)"
            return KYCDecisionEnum.FAIL, confidence, summary
        
        # ESCALATE is next priority
        if escalate_reasons:
            confidence = 0.75  # Medium confidence for ESCALATE
            summary = f"KYC ESCALATED for review: {escalate_reasons[0]}"
            if len(escalate_reasons) > 1:
                summary += f" (+{len(escalate_reasons)-1} more items)"
            return KYCDecisionEnum.ESCALATE, confidence, summary
        
        # PASS if no issues
        compliance_intel = scan_data.get('compliance_intelligence', {})
        score = compliance_intel.get('score', 80)
        
        # Confidence based on compliance score
        if score >= 80:
            confidence = 0.95
        elif score >= 60:
            confidence = 0.85
        else:
            confidence = 0.75
        
        summary = f"KYC PASSED: All mandatory compliance checks satisfied (score: {score}/100)"
        return KYCDecisionEnum.PASS, confidence, summary

