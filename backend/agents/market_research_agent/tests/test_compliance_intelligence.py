"""
Tests for Compliance Intelligence Module (Context Aware)
"""
import pytest
from backend.agents.market_research_agent.analyzers.compliance_intelligence import ComplianceIntelligence
from backend.agents.market_research_agent.analyzers.context_classifier import BusinessContextClassifier

@pytest.fixture
def engine():
    return ComplianceIntelligence()

def test_blockchain_infrastructure_context(engine):
    """
    Verify Blockchain Infra site:
    - Crypto keywords are neutral (0 penalty).
    - Refund policy is N/A (full score for that item).
    - Contact page is Optional (full score).
    """
    compliance = {"general": {"pass": True, "alerts": []}} # Tech: 15
    
    # Missing Refund and Contact
    policies = {
        "privacy_policy": {"found": True}, # 10
        "terms_condition": {"found": True}, # 10
        "returns_refund": {"found": False}, # Missing but N/A -> 10 pts
        "contact_us": {"found": False} # Missing but Optional -> 10 pts
    } # Total Policy: 40!
    
    risk = {
        "restricted_keywords_found": [{"category": "crypto", "keyword": "bitcoin"}], # Neutral -> 0 penalty
        "dummy_words_detected": False
    } # Trust: 30
    
    vintage = 2000 # > 3yr -> 15 pts
    
    context = {"primary": BusinessContextClassifier.CONTEXT_BLOCKCHAIN}
    
    result = engine.analyze(compliance, policies, risk, vintage, context)
    
    # Calculation:
    # Tech: 15 + 15 = 30
    # Policy: 10 + 10 + 10(N/A) + 10(Optional) = 40
    # Trust: 30 - 0 = 30
    # Total: 100
    
    assert result['score'] == 100
    assert result['rating'] == "Good"
    assert result['context'] == BusinessContextClassifier.CONTEXT_BLOCKCHAIN
    
    # Verify breakdown notes
    refund_item = next(x for x in result['breakdown']['policy']['details'] if x['item'] == 'Refund Policy')
    assert refund_item['expectation'] == 'n/a'
    assert refund_item['score'] == 10

def test_ecommerce_missing_refund(engine):
    """
    Verify E-commerce site missing Refund gets penalized differently than Blockchain.
    """
    compliance = {"general": {"pass": True}} # Tech: Need mock inputs? Default is 0 if empty warnings
    # Wait, my code checks alerts. Empty alerts = Pass.
    compliance = {"general": {"pass": True, "alerts": []}}
    
    policies = {
        "privacy_policy": {"found": True}, 
        "terms_condition": {"found": True},
        "returns_refund": {"found": False}, # Missing & Required -> 0 pts
        "contact_us": {"found": True}
    }
    
    risk = {"restricted_keywords_found": [], "dummy_words_detected": False}
    vintage = 2000
    
    context = {"primary": BusinessContextClassifier.CONTEXT_ECOMMERCE}
    
    result = engine.analyze(compliance, policies, risk, vintage, context)
    
    # Policy: 10 + 10 + 0 + 10 = 30
    assert result['breakdown']['policy']['score'] == 30
    assert result['score'] == 90 # 30(Tech) + 30(Pol) + 30(Trust)

def test_saas_optional_refund(engine):
    """
    Verify SaaS site missing Refund (Optional) gets full points.
    """
    compliance = {"general": {"pass": True, "alerts": []}}
    policies = {
        "privacy_policy": {"found": True}, 
        "terms_condition": {"found": True},
        "returns_refund": {"found": False}, # Optional -> 10 pts
        "contact_us": {"found": True}
    }
    risk = {"restricted_keywords_found": [], "dummy_words_detected": False}
    vintage = 2000
    context = {"primary": BusinessContextClassifier.CONTEXT_SAAS}
    
    result = engine.analyze(compliance, policies, risk, vintage, context)
    
    # Policy: 40
    assert result['breakdown']['policy']['score'] == 40
    assert result['score'] == 100

def test_crypto_penalty_for_ecommerce(engine):
    """
    Verify Crypto is still a risk for standard E-commerce.
    """
    compliance = {"general": {"pass": True, "alerts": []}}
    policies = {
        "privacy_policy": {"found": True}, "terms_condition": {"found": True},
        "returns_refund": {"found": True}, "contact_us": {"found": True}
    }
    risk = {
        "restricted_keywords_found": [{"category": "crypto", "keyword": "bitcoin"}],
        "dummy_words_detected": False
    }
    vintage = 2000
    context = {"primary": BusinessContextClassifier.CONTEXT_ECOMMERCE}
    
    result = engine.analyze(compliance, policies, risk, vintage, context)
    
    # Trust: 30 - 5 = 25
    assert result['breakdown']['trust']['score'] == 25
    assert result['score'] == 95 # 30 + 40 + 25
