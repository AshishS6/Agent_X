"""
Integration tests for KYC Site Scan v2

Tests the end-to-end flow with sample merchant data.
"""

import pytest
import asyncio
import json
from datetime import datetime

# Import KYC components
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.input_schema import MerchantKYCInput, OptionalMerchantData, RiskTier
from models.output_schema import KYCDecisionEnum, KYCDecisionOutput
from decision_rules import DecisionRules, RuleCategory
from entity_matcher import EntityMatcher
from audit_builder import AuditBuilder


class TestInputSchema:
    """Test input schema validation"""
    
    def test_valid_input(self):
        """Test valid merchant input"""
        input_data = MerchantKYCInput(
            merchant_legal_name="TechStart Solutions Pvt Ltd",
            registered_address="Tower A, Tech Park, Whitefield, Bangalore, KA 560066, India",
            declared_business_type="SaaS",
            declared_products_services=["CRM Software", "Marketing Automation"],
            website_url="https://www.example.com",
            merchant_display_name="TechStart",
        )
        
        assert input_data.merchant_legal_name == "TechStart Solutions Pvt Ltd"
        assert input_data.website_url == "https://www.example.com"
        assert len(input_data.declared_products_services) == 2
    
    def test_url_normalization(self):
        """Test URL normalization adds https"""
        input_data = MerchantKYCInput(
            merchant_legal_name="Test Company",
            registered_address="123 Test Street, Test City 12345",
            declared_business_type="E-commerce",
            declared_products_services=["Products"],
            website_url="example.com",  # Without scheme
            merchant_display_name="Test",
        )
        
        assert input_data.website_url == "https://example.com"
    
    def test_empty_products_rejected(self):
        """Test that empty products list is rejected"""
        with pytest.raises(ValueError):
            MerchantKYCInput(
                merchant_legal_name="Test Company",
                registered_address="123 Test Street, Test City 12345",
                declared_business_type="E-commerce",
                declared_products_services=[],  # Empty - should fail
                website_url="https://example.com",
                merchant_display_name="Test",
            )
    
    def test_optional_data(self):
        """Test optional merchant data"""
        input_data = MerchantKYCInput(
            merchant_legal_name="Test Company",
            registered_address="123 Test Street, Test City 12345",
            declared_business_type="E-commerce",
            declared_products_services=["Products"],
            website_url="https://example.com",
            merchant_display_name="Test",
            optional_data=OptionalMerchantData(
                mcc="5411",
                country_of_incorporation="IN",
                risk_tier=RiskTier.LOW
            )
        )
        
        assert input_data.optional_data.mcc == "5411"
        assert input_data.optional_data.risk_tier == RiskTier.LOW


class TestDecisionRules:
    """Test decision rules engine"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.rules = DecisionRules()
        self.merchant_input = {
            "merchant_legal_name": "Test Company Pvt Ltd",
            "registered_address": "123 Test Street",
            "declared_business_type": "E-commerce",
            "declared_products_services": ["Clothing", "Accessories"],
            "website_url": "https://example.com",
            "merchant_display_name": "Test Shop",
        }
    
    def test_site_unreachable_fails(self):
        """Test that unreachable site triggers FAIL"""
        scan_data = {
            "scan_status": {
                "status": "FAILED",
                "reason": "DNS_FAIL",
                "message": "Could not resolve domain"
            }
        }
        
        decision = self.rules.evaluate(
            scan_data=scan_data,
            merchant_input=self.merchant_input,
            policy_checks=[],
            checkout_result=None,
            entity_match=None,
        )
        
        assert decision.decision == KYCDecisionEnum.FAIL
        assert any("DNS_FAIL" in r.code for r in decision.reason_codes)
    
    def test_missing_privacy_policy_fails(self):
        """Test that missing privacy policy triggers FAIL"""
        from models.output_schema import PolicyCheckResult
        
        scan_data = {
            "scan_status": {"status": "SUCCESS"},
            "business_context": {"primary": "ECOMMERCE"},
        }
        
        policy_checks = [
            PolicyCheckResult(
                policy_type="privacy_policy",
                found=False,  # Missing
                expectation="required"
            ),
            PolicyCheckResult(
                policy_type="terms_condition",
                found=True,
                url="https://example.com/terms",
                expectation="required"
            ),
        ]
        
        decision = self.rules.evaluate(
            scan_data=scan_data,
            merchant_input=self.merchant_input,
            policy_checks=policy_checks,
            checkout_result=None,
            entity_match=None,
        )
        
        assert decision.decision == KYCDecisionEnum.FAIL
        assert any("MISSING_PRIVACY_POLICY" in r.code for r in decision.reason_codes)
    
    def test_high_risk_content_fails(self):
        """Test that high-risk content triggers FAIL"""
        from models.output_schema import PolicyCheckResult
        
        scan_data = {
            "scan_status": {"status": "SUCCESS"},
            "business_context": {"primary": "ECOMMERCE"},
            "content_risk": {
                "restricted_keywords_found": [
                    {
                        "category": "gambling",
                        "keyword": "casino",
                        "evidence": {
                            "source_url": "https://example.com",
                            "evidence_snippet": "Play at our casino"
                        }
                    }
                ]
            }
        }
        
        policy_checks = [
            PolicyCheckResult(
                policy_type="privacy_policy",
                found=True,
                url="https://example.com/privacy",
                expectation="required"
            ),
            PolicyCheckResult(
                policy_type="terms_condition",
                found=True,
                url="https://example.com/terms",
                expectation="required"
            ),
        ]
        
        decision = self.rules.evaluate(
            scan_data=scan_data,
            merchant_input=self.merchant_input,
            policy_checks=policy_checks,
            checkout_result=None,
            entity_match=None,
        )
        
        assert decision.decision == KYCDecisionEnum.FAIL
        assert any("HIGH_RISK_CONTENT" in r.code for r in decision.reason_codes)
    
    def test_prohibitive_intent_on_policy_page_ignored(self):
        """
        V2.2: Test that keywords with prohibitive intent on policy pages don't trigger FAIL.
        This is the intent-aware content risk analysis feature.
        """
        from models.output_schema import PolicyCheckResult
        
        scan_data = {
            "scan_status": {"status": "SUCCESS"},
            "business_context": {"primary": "FINTECH"},
            "content_risk": {
                "restricted_keywords_found": [
                    {
                        "category": "gambling",
                        "keyword": "gambling",
                        "intent": "prohibitive",  # V2.2: Prohibitive intent
                        "page_type": "terms_conditions",  # On T&C page
                        "intent_context": "We do not allow gambling or betting activities",
                        "evidence": {
                            "source_url": "https://example.com/terms",
                            "evidence_snippet": "Prohibited activities: We do not allow gambling or betting"
                        }
                    }
                ],
                "policy_mentions_count": 1,  # One policy mention
                "risk_contributing_count": 0  # Zero risk-contributing items
            }
        }
        
        policy_checks = [
            PolicyCheckResult(
                policy_type="privacy_policy",
                found=True,
                url="https://example.com/privacy",
                expectation="required"
            ),
            PolicyCheckResult(
                policy_type="terms_condition",
                found=True,
                url="https://example.com/terms",
                expectation="required"
            ),
        ]
        
        decision = self.rules.evaluate(
            scan_data=scan_data,
            merchant_input=self.merchant_input,
            policy_checks=policy_checks,
            checkout_result=None,
            entity_match=None,
        )
        
        # Should PASS because the gambling mention is prohibitive (informational only)
        assert decision.decision == KYCDecisionEnum.PASS
        # Should NOT have HIGH_RISK_CONTENT reason code
        assert not any("HIGH_RISK_CONTENT" in r.code for r in decision.reason_codes)
    
    def test_promotional_intent_on_policy_page_still_flags(self):
        """
        V2.2: Test that keywords without prohibitive intent still trigger appropriate action.
        """
        from models.output_schema import PolicyCheckResult
        
        scan_data = {
            "scan_status": {"status": "SUCCESS"},
            "business_context": {"primary": "ECOMMERCE"},
            "content_risk": {
                "restricted_keywords_found": [
                    {
                        "category": "gambling",
                        "keyword": "casino",
                        "intent": "neutral",  # Not prohibitive
                        "page_type": "product",  # On product page
                        "evidence": {
                            "source_url": "https://example.com/products",
                            "evidence_snippet": "Try our casino games",
                            "corroborated": True  # Found on multiple pages
                        }
                    }
                ],
                "policy_mentions_count": 0,
                "risk_contributing_count": 1,
                "corroboration": {"gambling": ["https://example.com/products", "https://example.com/"]}
            }
        }
        
        policy_checks = [
            PolicyCheckResult(
                policy_type="privacy_policy",
                found=True,
                url="https://example.com/privacy",
                expectation="required"
            ),
            PolicyCheckResult(
                policy_type="terms_condition",
                found=True,
                url="https://example.com/terms",
                expectation="required"
            ),
        ]
        
        decision = self.rules.evaluate(
            scan_data=scan_data,
            merchant_input=self.merchant_input,
            policy_checks=policy_checks,
            checkout_result=None,
            entity_match=None,
        )
        
        # Should FAIL because it's promotional high-risk content (corroborated)
        assert decision.decision == KYCDecisionEnum.FAIL
        assert any("HIGH_RISK_CONTENT" in r.code for r in decision.reason_codes)
    
    def test_all_checks_pass(self):
        """Test that passing all checks results in PASS"""
        from models.output_schema import PolicyCheckResult, CheckoutFlowResult, EntityMatchResult
        
        scan_data = {
            "scan_status": {"status": "SUCCESS"},
            "business_context": {"primary": "ECOMMERCE"},
            "content_risk": {
                "restricted_keywords_found": [],
                "dummy_words_detected": False
            },
            "compliance_intelligence": {
                "score": 85
            },
            "business_details": {
                "contact_info": {
                    "email": "contact@example.com",
                    "phone": "123-456-7890"
                }
            },
            "product_details": {
                "extracted_products": [
                    {"name": "T-Shirt", "price": "$29.99"}
                ]
            }
        }
        
        policy_checks = [
            PolicyCheckResult(
                policy_type="privacy_policy",
                found=True,
                url="https://example.com/privacy",
                expectation="required"
            ),
            PolicyCheckResult(
                policy_type="terms_condition",
                found=True,
                url="https://example.com/terms",
                expectation="required"
            ),
            PolicyCheckResult(
                policy_type="returns_refund",
                found=True,
                url="https://example.com/refund",
                expectation="required"
            ),
            PolicyCheckResult(
                policy_type="contact_us",
                found=True,
                url="https://example.com/contact",
                expectation="required"
            ),
        ]
        
        checkout_result = CheckoutFlowResult(
            has_cta=True,
            cta_clickable=True,
            checkout_reachable=True,
            checkout_url="https://example.com/checkout",
            checkout_confidence=0.85,
            pricing_visible=True,
            form_fields_present=True,
        )
        
        entity_match = EntityMatchResult(
            declared_name="Test Company Pvt Ltd",
            extracted_names=["Test Company Private Limited"],
            best_match="Test Company Private Limited",
            match_score=92.5,
            match_status="MATCH",
        )
        
        decision = self.rules.evaluate(
            scan_data=scan_data,
            merchant_input=self.merchant_input,
            policy_checks=policy_checks,
            checkout_result=checkout_result,
            entity_match=entity_match,
        )
        
        assert decision.decision == KYCDecisionEnum.PASS
        assert decision.confidence_score >= 0.85


class TestEntityMatcher:
    """Test entity matching"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.matcher = EntityMatcher()
    
    def test_normalize_company_name(self):
        """Test company name normalization"""
        test_cases = [
            ("ABC Corp", "abc corp"),
            ("XYZ Pvt Ltd", "xyz"),
            ("TechStart Solutions Private Limited", "techstart solutions"),
            ("MyCo Inc.", "myco"),
            ("Test Company LLC", "test company"),
        ]
        
        for input_name, expected_base in test_cases:
            normalized = self.matcher._normalize_company_name(input_name)
            assert expected_base in normalized or normalized in expected_base, \
                f"Failed for {input_name}: got {normalized}, expected {expected_base}"
    
    def test_exact_match(self):
        """Test exact name match"""
        scan_data = {
            "business_details": {
                "extracted_business_name": "TechStart Solutions Pvt Ltd"
            }
        }
        
        result = self.matcher.match(
            declared_name="TechStart Solutions Pvt Ltd",
            declared_address="123 Test Street",
            scan_data=scan_data,
        )
        
        assert result.match_score >= 90.0
        assert result.match_status in ["MATCH", "PARTIAL_MATCH"]
    
    def test_partial_match(self):
        """Test partial name match"""
        scan_data = {
            "business_details": {
                "extracted_business_name": "TechStart Solutions"
            }
        }
        
        result = self.matcher.match(
            declared_name="TechStart Solutions Private Limited",
            declared_address="123 Test Street",
            scan_data=scan_data,
        )
        
        assert result.match_score >= 60.0
        assert result.match_status in ["MATCH", "PARTIAL_MATCH"]
    
    def test_no_match_found(self):
        """Test when no matching name found"""
        scan_data = {
            "business_details": {
                "extracted_business_name": "Not found"
            }
        }
        
        result = self.matcher.match(
            declared_name="Completely Different Company",
            declared_address="123 Test Street",
            scan_data=scan_data,
        )
        
        assert result.match_status in ["NO_MATCH", "MISMATCH"]


class TestAuditBuilder:
    """Test audit trail builder"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.builder = AuditBuilder()
    
    def test_audit_initialization(self):
        """Test audit trail initialization"""
        self.builder.start_audit(
            scan_id="test123",
            target_url="https://example.com",
            merchant_name="Test Company"
        )
        
        assert self.builder._scan_id == "test123"
        assert self.builder._target_url == "https://example.com"
        assert len(self.builder._timestamps) == 1
    
    def test_add_check(self):
        """Test adding check records"""
        self.builder.start_audit(
            scan_id="test123",
            target_url="https://example.com",
            merchant_name="Test Company"
        )
        
        self.builder.add_check(
            check_id="policy_privacy",
            check_name="Privacy Policy Check",
            check_type="DETERMINISTIC",
            status="PASS",
            details={"url": "https://example.com/privacy"}
        )
        
        assert len(self.builder._checks) == 1
        assert self.builder._checks[0].check_id == "policy_privacy"
        assert self.builder._checks[0].status == "PASS"
    
    def test_build_audit_trail(self):
        """Test building complete audit trail"""
        self.builder.start_audit(
            scan_id="test123",
            target_url="https://example.com",
            merchant_name="Test Company"
        )
        
        self.builder.add_timestamp("SCAN_START", "Starting scan")
        self.builder.add_check(
            check_id="test_check",
            check_name="Test Check",
            check_type="DETERMINISTIC",
            status="PASS"
        )
        self.builder.add_url_visited("https://example.com")
        self.builder.add_url_visited("https://example.com/about")
        
        audit = self.builder.build_audit_trail(
            scan_completed_at=datetime.now(),
            scan_duration_seconds=5.5,
            final_url="https://example.com",
            pages_scanned=2
        )
        
        assert audit.scan_id == "test123"
        assert audit.scan_duration_seconds == 5.5
        assert len(audit.urls_visited) == 2
        assert len(audit.checks_performed) == 1
        assert len(audit.timestamps) >= 2  # Initial + complete


class TestCheckoutValidator:
    """Test checkout validator (basic tests without browser)"""
    
    def test_analyze_scan_data(self):
        """Test basic scan data analysis"""
        from checkout_validator import CheckoutValidator
        
        validator = CheckoutValidator()
        
        scan_data = {
            "product_details": {
                "has_cart": True,
                "has_pricing": True
            },
            "crawl_summary": {
                "page_texts": {
                    "https://example.com": "buy now add to cart $99.99"
                }
            },
            "policy_details": {
                "pricing": {"found": True, "url": "https://example.com/pricing"}
            }
        }
        
        result = validator._analyze_scan_data(scan_data)
        
        assert result.has_cta == True
        assert result.pricing_visible == True


# Sample data for end-to-end testing
SAMPLE_MERCHANT_DATA = {
    "e_commerce": MerchantKYCInput(
        merchant_legal_name="Fashion Hub India Pvt Ltd",
        registered_address="Plot 42, Industrial Area, Phase 2, Gurugram, HR 122001, India",
        declared_business_type="E-commerce",
        declared_products_services=["Clothing", "Accessories", "Footwear"],
        website_url="https://www.myntra.com",  # Example - use test URL in real tests
        merchant_display_name="Fashion Hub",
    ),
    "saas": MerchantKYCInput(
        merchant_legal_name="CloudTools Software Inc",
        registered_address="100 Tech Lane, San Francisco, CA 94105, USA",
        declared_business_type="SaaS",
        declared_products_services=["Project Management", "Team Collaboration", "Analytics"],
        website_url="https://www.atlassian.com",  # Example - use test URL in real tests
        merchant_display_name="CloudTools",
    ),
    "fintech": MerchantKYCInput(
        merchant_legal_name="PayQuick Financial Services Ltd",
        registered_address="Fintech Tower, BKC, Mumbai, MH 400051, India",
        declared_business_type="Fintech",
        declared_products_services=["Payment Gateway", "Invoice Financing", "Business Loans"],
        website_url="https://razorpay.com",  # Example - use test URL in real tests
        merchant_display_name="PayQuick",
    ),
}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

