"""
KYC Decision Engine
Main orchestrator for KYC website screening

This engine wraps the existing ModularScanEngine and adds:
1. Deterministic decision rules (PASS/FAIL/ESCALATE)
2. Enhanced checkout flow validation
3. Legal entity consistency checking
4. Structured audit trail generation
5. Direct page_graph access for better analysis (V2.1)
6. Intent-aware content risk analysis (V2.1)
7. Multi-page corroboration for risk severity (V2.2)
8. Policy mention vs risk-contributing differentiation (V2.2)
"""

import asyncio
import json
import logging
import time
import uuid
import sys
import os
import concurrent.futures
from datetime import datetime
from typing import Dict, Any, Optional, List

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from .models.input_schema import MerchantKYCInput
    from .models.output_schema import (
        KYCDecisionOutput,
        KYCDecisionEnum,
        PolicyCheckResult,
        CheckoutFlowResult,
        EntityMatchResult,
        ComplianceScoreBreakdown,
        ContentRiskSummary,
        AuditTrailOutput,
        CheckRecord,
        TimestampRecord,
    )
    from .decision_rules import DecisionRules, KYCDecision
    from .checkout_validator import CheckoutValidator
    from .entity_matcher import EntityMatcher
    from .audit_builder import AuditBuilder
except ImportError:
    from models.input_schema import MerchantKYCInput
    from models.output_schema import (
        KYCDecisionOutput,
        KYCDecisionEnum,
        PolicyCheckResult,
        CheckoutFlowResult,
        EntityMatchResult,
        ComplianceScoreBreakdown,
        ContentRiskSummary,
        AuditTrailOutput,
        CheckRecord,
        TimestampRecord,
    )
    from decision_rules import DecisionRules, KYCDecision
    from checkout_validator import CheckoutValidator
    from entity_matcher import EntityMatcher
    from audit_builder import AuditBuilder


class KYCDecisionEngine:
    """
    Main KYC Decision Engine that orchestrates website screening.
    
    Flow:
    1. Accept merchant KYC input
    2. Run ModularScanEngine on website (with CrawlOrchestrator for page_graph)
    3. Extract page_graph for direct access to crawled pages (V2.1)
    4. Run enhanced checkout validation using pre-fetched pages (V2.1)
    5. Run legal entity matching with page_graph data (V2.1)
    6. Apply deterministic decision rules with intent-aware content risk (V2.1)
    7. Generate audit trail
    8. Return structured KYC decision
    """
    
    VERSION = "v2.2.0"  # V2.2: Intent-aware content risk, multi-page corroboration
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.decision_rules = DecisionRules(logger=self.logger)
        self.checkout_validator = CheckoutValidator(logger=self.logger)
        self.entity_matcher = EntityMatcher(logger=self.logger)
        self.audit_builder = AuditBuilder(logger=self.logger)
        
        # Lazy import scan engine to avoid circular imports
        self._scan_engine = None
        # Cache for page_graph from last scan (V2.1)
        self._last_page_graph = None
    
    def _get_scan_engine(self):
        """Lazy load the ModularScanEngine"""
        if self._scan_engine is None:
            try:
                from market_research_agent.scan_engine import ModularScanEngine
                self._scan_engine = ModularScanEngine(logger=self.logger)
            except ImportError:
                # Try alternative import path
                try:
                    sys.path.insert(0, os.path.join(
                        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'market_research_agent'
                    ))
                    from scan_engine import ModularScanEngine
                    self._scan_engine = ModularScanEngine(logger=self.logger)
                except ImportError as e:
                    self.logger.error(f"Failed to import ModularScanEngine: {e}")
                    raise
        return self._scan_engine
    
    async def process(self, merchant_input: MerchantKYCInput) -> KYCDecisionOutput:
        """
        Process a merchant KYC screening request.
        
        Args:
            merchant_input: Validated merchant KYC input data
            
        Returns:
            KYCDecisionOutput with decision, reason codes, and audit trail
        """
        scan_id = str(uuid.uuid4())[:8]
        start_time = time.monotonic()
        start_timestamp = datetime.now()
        
        self.logger.info(f"[KYC][{scan_id}] Starting KYC screening for: {merchant_input.website_url}")
        
        # Initialize audit builder
        self.audit_builder.start_audit(
            scan_id=scan_id,
            target_url=merchant_input.website_url,
            merchant_name=merchant_input.merchant_legal_name,
        )
        
        try:
            # Phase 1: Run website scan
            self.audit_builder.add_timestamp("SCAN_START", "Starting website scan")
            scan_data = await self._run_website_scan(
                merchant_input.website_url,
                merchant_input.merchant_display_name,
                scan_id
            )
            self.audit_builder.add_timestamp("SCAN_COMPLETE", "Website scan completed")
            
            # Check if scan failed early
            scan_status = scan_data.get('scan_status', {})
            if scan_status.get('status') == 'FAILED':
                self.logger.warning(f"[KYC][{scan_id}] Scan failed: {scan_status.get('reason')}")
                # Still process through decision rules to generate proper FAIL decision
            
            # Phase 2: Extract policy check results
            policy_checks = self._extract_policy_checks(scan_data)
            self.audit_builder.add_check(
                check_id="policy_detection",
                check_name="Policy Page Detection",
                check_type="DETERMINISTIC",
                status="PASS" if any(p.found for p in policy_checks) else "FAIL",
                details={"policies_found": [p.policy_type for p in policy_checks if p.found]}
            )
            
            # Phase 3: Run checkout validation (enhanced)
            checkout_result = None
            if scan_status.get('status') != 'FAILED':
                self.audit_builder.add_timestamp("CHECKOUT_VALIDATION_START", "Starting checkout flow validation")
                checkout_result = await self._validate_checkout_flow(
                    merchant_input.website_url,
                    scan_data,
                    scan_id
                )
                self.audit_builder.add_timestamp("CHECKOUT_VALIDATION_COMPLETE", "Checkout validation completed")
                
                if checkout_result:
                    self.audit_builder.add_check(
                        check_id="checkout_validation",
                        check_name="Checkout Flow Validation",
                        check_type="DETERMINISTIC",
                        status="PASS" if checkout_result.checkout_reachable else "FAIL",
                        details=checkout_result.model_dump()
                    )
            
            # Phase 4: Run entity matching
            self.audit_builder.add_timestamp("ENTITY_MATCH_START", "Starting legal entity matching")
            self.logger.info(f"[KYC][{scan_id}] Starting entity matching...")
            try:
                # Add timeout to prevent hanging
                entity_match = await asyncio.wait_for(
                    self._match_legal_entity(
                        merchant_input,
                        scan_data,
                        scan_id
                    ),
                    timeout=30.0  # 30 second timeout
                )
                self.logger.info(f"[KYC][{scan_id}] Entity matching completed")
            except asyncio.TimeoutError:
                self.logger.warning(f"[KYC][{scan_id}] Entity matching timed out after 30s, continuing...")
                entity_match = None
            except Exception as e:
                self.logger.error(f"[KYC][{scan_id}] Entity matching error: {e}", exc_info=True)
                entity_match = None
            self.audit_builder.add_timestamp("ENTITY_MATCH_COMPLETE", "Entity matching completed")
            
            if entity_match:
                self.audit_builder.add_check(
                    check_id="entity_matching",
                    check_name="Legal Entity Matching",
                    check_type="DETERMINISTIC",
                    status="PASS" if entity_match.match_status == "MATCH" else "REVIEW",
                    details=entity_match.model_dump()
                )
            
            # Phase 5: Apply decision rules with V2.2 enhanced context
            self.audit_builder.add_timestamp("DECISION_RULES_START", "Applying decision rules")
            
            # V2.2: Extract content risk metadata for audit trail
            content_risk = scan_data.get('content_risk', {})
            policy_mentions_count = content_risk.get('policy_mentions_count', 0)
            risk_contributing_count = content_risk.get('risk_contributing_count', 0)
            
            if policy_mentions_count > 0:
                self.audit_builder.add_check(
                    check_id="content_risk_intent_analysis",
                    check_name="Intent-Aware Content Risk Analysis",
                    check_type="DETERMINISTIC",
                    status="PASS",
                    details={
                        "policy_mentions_ignored": policy_mentions_count,
                        "risk_contributing_items": risk_contributing_count,
                        "note": "Prohibitive mentions on policy pages excluded from risk score"
                    }
                )
            
            merchant_dict = merchant_input.model_dump()
            kyc_decision = self.decision_rules.evaluate(
                scan_data=scan_data,
                merchant_input=merchant_dict,
                policy_checks=policy_checks,
                checkout_result=checkout_result,
                entity_match=entity_match,
            )
            
            self.audit_builder.add_timestamp("DECISION_RULES_COMPLETE", f"Decision: {kyc_decision.decision.value}")
            
            # Phase 6: Build final output
            end_time = time.monotonic()
            duration = end_time - start_time
            
            # Get compliance score breakdown
            compliance_score = self._extract_compliance_score(scan_data)
            
            # V2.2: Extract content risk summary with intent classification
            content_risk_summary = self._extract_content_risk_summary(scan_data)
            
            # Build audit trail - extract pages_scanned from correct location
            # The scan_engine puts it in crawl_summary.pages_fetched for successful scans
            crawl_summary = scan_data.get('crawl_summary', {})
            pages_scanned = (
                crawl_summary.get('pages_fetched') or 
                scan_data.get('crawl_metadata', {}).get('pages_scanned') or 
                0
            )
            
            audit_trail = self.audit_builder.build_audit_trail(
                scan_completed_at=datetime.now(),
                scan_duration_seconds=duration,
                final_url=scan_data.get('final_url', merchant_input.website_url),
                pages_scanned=pages_scanned,
            )
            
            # Build output
            output = KYCDecisionOutput(
                decision=kyc_decision.decision,
                reason_codes=kyc_decision.reason_codes,
                summary=kyc_decision.summary,
                confidence_score=kyc_decision.confidence_score,
                policy_checks=policy_checks,
                checkout_flow=checkout_result,
                entity_match=entity_match,
                compliance_score=compliance_score,
                detected_business_type=scan_data.get('business_context', {}).get('primary'),
                detected_mcc=scan_data.get('mcc_codes', {}).get('primary_mcc', {}).get('mcc_code') if scan_data.get('mcc_codes', {}).get('primary_mcc') else None,
                product_match_status=self._get_product_match_status(scan_data, merchant_input),
                content_risk_summary=content_risk_summary,  # V2.2
                audit_trail=audit_trail,
                scan_version=self.VERSION,
            )
            
            self.logger.info(
                f"[KYC][{scan_id}] Screening complete: {output.decision.value} "
                f"(confidence: {output.confidence_score:.2f}, duration: {duration:.2f}s)"
            )
            
            return output
            
        except Exception as e:
            self.logger.error(f"[KYC][{scan_id}] Screening failed with error: {e}", exc_info=True)
            
            # Return ESCALATE decision on error
            audit_trail = self.audit_builder.build_audit_trail(
                scan_completed_at=datetime.now(),
                scan_duration_seconds=time.monotonic() - start_time,
                final_url=merchant_input.website_url,
                pages_scanned=0,
            )
            
            return KYCDecisionOutput(
                decision=KYCDecisionEnum.ESCALATE,
                reason_codes=[],
                summary=f"KYC screening encountered an error: {str(e)}",
                confidence_score=0.0,
                audit_trail=audit_trail,
                scan_version=self.VERSION,
            )
    
    async def _run_website_scan(
        self,
        url: str,
        business_name: str,
        scan_id: str
    ) -> Dict[str, Any]:
        """
        Run the ModularScanEngine on the website.
        
        V2.1: Also captures page_graph for direct access to crawled pages,
        enabling better checkout validation and entity matching.
        """
        try:
            scan_engine = self._get_scan_engine()
            
            # Run comprehensive scan in a thread pool to avoid event loop conflicts
            # The scan_engine.comprehensive_site_scan uses asyncio.run() internally,
            # which conflicts with an already running event loop
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                result_json = await loop.run_in_executor(
                    executor,
                    lambda: scan_engine.comprehensive_site_scan(
                        url=url,
                        business_name=business_name,
                        task_id=scan_id
                    )
                )
            
            # Parse JSON result
            result = json.loads(result_json)
            
            # Extract the inner scan data
            scan_data = result.get('comprehensive_site_scan', result)
            
            # V2.1: Try to access page_graph from orchestrator for enhanced analysis
            try:
                if hasattr(scan_engine, 'orchestrator') and scan_engine.orchestrator:
                    # Note: page_graph is transient per scan, this captures last state
                    self._last_page_graph = getattr(scan_engine.orchestrator, '_last_page_graph', None)
            except Exception as e:
                self.logger.debug(f"[KYC][{scan_id}] Could not access page_graph: {e}")
            
            return scan_data
            
        except Exception as e:
            self.logger.error(f"[KYC][{scan_id}] Website scan failed: {e}")
            return {
                'scan_status': {
                    'status': 'FAILED',
                    'reason': 'SCAN_ERROR',
                    'message': str(e)
                }
            }
    
    def _extract_policy_checks(self, scan_data: Dict[str, Any]) -> List[PolicyCheckResult]:
        """Extract policy check results from scan data"""
        if not scan_data:
            scan_data = {}
        policy_details = scan_data.get('policy_details') or {}
        results = []
        
        policy_mapping = {
            'privacy_policy': 'privacy_policy',
            'terms_condition': 'terms_condition',
            'returns_refund': 'returns_refund',
            'contact_us': 'contact_us',
            'about_us': 'about_us',
            'faq': 'faq',
            'shipping_delivery': 'shipping_delivery',
        }
        
        for key, policy_type in policy_mapping.items():
            policy_data = policy_details.get(key) or {}
            
            # Determine expectation based on business context
            business_context_data = scan_data.get('business_context') or {}
            business_context = business_context_data.get('primary', 'UNKNOWN') if business_context_data else 'UNKNOWN'
            expectation = self._get_policy_expectation(policy_type, business_context)
            
            results.append(PolicyCheckResult(
                policy_type=policy_type,
                found=policy_data.get('found', False),
                url=policy_data.get('url') if policy_data.get('found') else None,
                content_length=policy_data.get('content_length'),
                has_required_keywords=policy_data.get('has_specific_keywords', False),
                expectation=expectation,
            ))
        
        return results
    
    def _get_policy_expectation(self, policy_type: str, business_context: str) -> str:
        """Determine policy expectation based on business context"""
        # Mandatory for all
        if policy_type in ['privacy_policy', 'terms_condition']:
            return 'required'
        
        # Context-dependent
        if policy_type == 'returns_refund':
            if business_context in ['SAAS', 'FINTECH', 'BLOCKCHAIN']:
                return 'optional'
            return 'required'  # E-commerce default
        
        if policy_type == 'contact_us':
            if business_context == 'CONTENT':
                return 'optional'
            return 'required'
        
        return 'optional'
    
    async def _validate_checkout_flow(
        self,
        url: str,
        scan_data: Dict[str, Any],
        scan_id: str
    ) -> Optional[CheckoutFlowResult]:
        """
        Validate checkout flow using browser automation.
        
        V2.1: Enhanced to use page_graph data for initial CTA detection,
        reducing the need for additional browser automation.
        """
        try:
            # Check if this is a commerce site
            business_context = scan_data.get('business_context', {})
            context_primary = business_context.get('primary', 'UNKNOWN') if isinstance(business_context, dict) else 'UNKNOWN'
            product_details = scan_data.get('product_details', {})
            
            # Skip checkout validation for non-commerce sites
            if context_primary in ['CONTENT', 'INFORMATIONAL']:
                self.logger.info(f"[KYC][{scan_id}] Skipping checkout validation for {context_primary} site")
                return None
            
            # V2.1: Check for pricing page in crawl_summary/policy_details
            crawl_summary = scan_data.get('crawl_summary', {})
            policy_details = scan_data.get('policy_details', {})
            
            # Enhanced product detection from scan data
            has_pricing_page = policy_details.get('pricing', {}).get('found', False)
            has_product_page = policy_details.get('product', {}).get('found', False)
            extracted_products = product_details.get('extracted_products', [])
            
            # Pre-populate enhanced scan data for checkout validator
            enhanced_scan_data = {
                **scan_data,
                '_kyc_enhanced': {
                    'has_pricing_page': has_pricing_page,
                    'has_product_page': has_product_page,
                    'product_count': len(extracted_products),
                    'pricing_model': product_details.get('pricing_model', 'Unknown'),
                }
            }
            
            # Run checkout validation with enhanced data
            result = await self.checkout_validator.validate(
                url=url,
                scan_data=enhanced_scan_data,
                scan_id=scan_id
            )
            
            # V2.1: Enhance result with pricing page presence
            if result and has_pricing_page and not result.pricing_visible:
                result = CheckoutFlowResult(
                    has_cta=result.has_cta,
                    cta_clickable=result.cta_clickable,
                    checkout_reachable=result.checkout_reachable,
                    checkout_url=result.checkout_url,
                    checkout_confidence=result.checkout_confidence,
                    pricing_visible=True,  # Pricing page found
                    form_fields_present=result.form_fields_present,
                    dead_ctas=result.dead_ctas,
                    evidence={
                        **(result.evidence or {}),
                        'pricing_page_url': policy_details.get('pricing', {}).get('url'),
                        'enhanced_by': 'kyc_v2.1_page_graph'
                    }
                )
            
            return result
            
        except Exception as e:
            self.logger.warning(f"[KYC][{scan_id}] Checkout validation failed: {e}")
            # Return basic result from scan data
            product_details = scan_data.get('product_details', {})
            policy_details = scan_data.get('policy_details', {})
            return CheckoutFlowResult(
                has_cta=product_details.get('has_cart', False),
                cta_clickable=False,  # Unknown
                checkout_reachable=False,  # Unknown
                checkout_url=None,
                checkout_confidence=0.0,
                pricing_visible=product_details.get('has_pricing', False) or policy_details.get('pricing', {}).get('found', False),
                form_fields_present=False,  # Unknown
            )
    
    async def _match_legal_entity(
        self,
        merchant_input: MerchantKYCInput,
        scan_data: Dict[str, Any],
        scan_id: str
    ) -> Optional[EntityMatchResult]:
        """Match merchant legal entity against website data"""
        try:
            result = self.entity_matcher.match(
                declared_name=merchant_input.merchant_legal_name,
                declared_address=merchant_input.registered_address,
                scan_data=scan_data,
            )
            return result
            
        except Exception as e:
            self.logger.warning(f"[KYC][{scan_id}] Entity matching failed: {e}")
            return None
    
    def _extract_compliance_score(self, scan_data: Dict[str, Any]) -> Optional[ComplianceScoreBreakdown]:
        """Extract compliance score breakdown from scan data"""
        compliance_intel = scan_data.get('compliance_intelligence', {})
        
        if not compliance_intel:
            return None
        
        breakdown = compliance_intel.get('breakdown', {})
        
        return ComplianceScoreBreakdown(
            overall_score=compliance_intel.get('score', 0),
            technical_score=breakdown.get('technical', {}).get('score', 0),
            policy_score=breakdown.get('policy', {}).get('score', 0),
            trust_score=breakdown.get('trust', {}).get('score', 0),
            rating=compliance_intel.get('rating', 'Unknown'),
        )
    
    def _get_product_match_status(
        self,
        scan_data: Dict[str, Any],
        merchant_input: MerchantKYCInput
    ) -> Optional[str]:
        """Determine product match status"""
        declared_products = merchant_input.declared_products_services
        extracted = scan_data.get('product_details', {}).get('extracted_products', [])
        
        if not declared_products:
            return None
        
        if not extracted:
            return "UNABLE_TO_VERIFY"
        
        # Simple match logic - could be enhanced with NLP
        declared_lower = [p.lower() for p in declared_products]
        extracted_names = [p.get('name', '').lower() for p in extracted if isinstance(p, dict)]
        
        matches = sum(1 for d in declared_lower if any(d in e or e in d for e in extracted_names))
        
        if matches == 0:
            return "MISMATCH"
        elif matches < len(declared_products) / 2:
            return "PARTIAL_MATCH"
        else:
            return "MATCH"
    
    def _extract_content_risk_summary(self, scan_data: Dict[str, Any]) -> Optional[ContentRiskSummary]:
        """
        V2.2: Extract content risk summary with intent classification details.
        
        Provides transparency into how risk scores were calculated and
        which keywords contributed to the risk vs being informational.
        """
        content_risk = scan_data.get('content_risk', {})
        
        if not content_risk:
            return None
        
        # Extract corroboration data
        corroboration = content_risk.get('corroboration', {})
        corroborated_categories = list(corroboration.keys()) if corroboration else []
        
        # Categorize restricted keywords by risk level
        restricted_keywords = content_risk.get('restricted_keywords_found', [])
        
        # High-risk categories (from DecisionRules)
        high_risk_cats = {
            "gambling", "adult", "child_pornography", "weapons", "drugs",
            "illegal_goods", "hacking", "counterfeit"
        }
        medium_risk_cats = {
            "crypto", "forex", "binary", "pharmacy", "alcohol", "tobacco",
            "securities", "mlm", "dating_escort"
        }
        
        high_risk_found = set()
        medium_risk_found = set()
        
        for item in restricted_keywords:
            category = item.get('category', '').lower()
            intent = item.get('intent', 'neutral')
            page_type = item.get('page_type', '')
            
            # Only count items that aren't prohibitive mentions on policy pages
            # V2.2: Expanded list to include all policy-like pages  
            policy_page_types = {
                'privacy_policy', 'terms_conditions', 'terms_condition',
                'refund_policy', 'returns_refund', 'acceptable_use',
                'prohibited_activities', 'restricted_businesses',
                'shipping_delivery', 'shipping_policy', 'delivery_policy',
                'faq', 'help', 'support', 'legal', 'disclaimer',
                'cancellation_policy', 'cookie_policy', 'data_safety',
            }
            
            if intent == 'prohibitive' and page_type in policy_page_types:
                continue  # Skip - this is informational only
            
            if category in high_risk_cats:
                high_risk_found.add(category)
            elif category in medium_risk_cats:
                medium_risk_found.add(category)
        
        return ContentRiskSummary(
            total_keywords_found=len(restricted_keywords),
            risk_contributing_count=content_risk.get('risk_contributing_count', 0),
            policy_mentions_count=content_risk.get('policy_mentions_count', 0),
            corroborated_categories=corroborated_categories,
            pages_analyzed=content_risk.get('pages_analyzed', 0),
            high_risk_categories=list(high_risk_found),
            medium_risk_categories=list(medium_risk_found),
            dummy_content_detected=content_risk.get('dummy_words_detected', False)
        )
    
    def process_sync(self, merchant_input: MerchantKYCInput) -> KYCDecisionOutput:
        """
        Synchronous wrapper for process method.
        Use this when calling from non-async context.
        """
        import asyncio
        
        # Check if we're already in an event loop
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context, need to use a different approach
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self.process(merchant_input))
                return future.result()
        except RuntimeError:
            # No event loop running, safe to use asyncio.run
            return asyncio.run(self.process(merchant_input))

