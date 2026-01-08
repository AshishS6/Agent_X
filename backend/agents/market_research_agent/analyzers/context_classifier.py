"""
Business Context Classifier
Classifies websites into high-level business contexts to refine compliance expectations.
"""

from typing import Dict, Any, List, Optional
from .context_evidence import EvidenceCollector

class BusinessContextClassifier:
    """
    Determines the primary business context of a website using evidence-based scoring.
    """
    
    # Contexts
    CONTEXT_ECOMMERCE = "ECOMMERCE_MERCHANT"
    CONTEXT_MARKETPLACE = "MARKETPLACE"
    CONTEXT_SAAS = "SAAS_PRODUCT"
    CONTEXT_FINTECH = "FINTECH_INFRASTRUCTURE"
    CONTEXT_BLOCKCHAIN = "BLOCKCHAIN_INFRASTRUCTURE"
    CONTEXT_CONTENT = "CONTENT_MEDIA"
    CONTEXT_DEV = "DEVELOPER_PLATFORM"
    CONTEXT_UNKNOWN = "UNKNOWN"

    # Statuses
    STATUS_DETERMINED = "DETERMINED"
    STATUS_LOW_CONFIDENCE = "LOW_CONFIDENCE"
    STATUS_UNDETERMINED = "UNDETERMINED"

    # Frontend Surfaces
    SURFACE_FULL_COMMERCE = "FULL_COMMERCE"     # Traditional catalog + cart
    SURFACE_MARKETING_SITE = "MARKETING_SITE"   # Landing page/Lead gen
    SURFACE_AUTH_GATED = "AUTH_GATED"           # Login required to see value (SaaS/Bank)
    SURFACE_CONTENT_ONLY = "CONTENT_ONLY"       # Blog/News
    SURFACE_API_DOCS = "API_DOCS"               # Developer portal
    SURFACE_UNKNOWN = "UNKNOWN"
    
    def __init__(self, logger=None):
        self.logger = logger
        self.collector = EvidenceCollector(logger)
        
    def classify(self, 
                 tech_stack: Dict[str, Any], 
                 product_indicators: Dict[str, Any],
                 page_text: str,
                 mcc_data: Optional[Dict[str, Any]] = None,
                 page_graph: Any = None) -> Dict[str, Any]:
        """
        Classify the website based on collected evidence.
        """
        
        # 1. Collect Evidence
        evidence = self.collector.collect(page_graph, tech_stack, product_indicators, page_text, mcc_data)
        
        # 2. Gating checks (Crawl failure)
        items_fetched = evidence['crawl'].get('pages_fetched', 0)
        is_blocked = evidence['crawl'].get('blocked', False)
        
        if items_fetched == 0:
            return self._build_result(
                self.CONTEXT_UNKNOWN, 
                self.STATUS_UNDETERMINED, 
                0.0, 
                self.SURFACE_UNKNOWN, 
                evidence, 
                reason="CRAWL_FAILED"
            )
            
        if is_blocked:
             return self._build_result(
                self.CONTEXT_UNKNOWN,
                self.STATUS_UNDETERMINED,
                0.0,
                self.SURFACE_AUTH_GATED, # Assumption if 403
                evidence,
                reason="ACCESS_BLOCKED"
            )

        # 3. Calculate Scores
        scores = self._calculate_scores(evidence)
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        primary_ctx, primary_score = sorted_scores[0]
        
        # 4. Determine Frontend Surface
        surface = self._determine_surface(evidence, primary_ctx)
        
        # 5. Determine Confidence & Status
        confidence = min(primary_score / 10.0, 1.0) # Normalize score (approx max 10-15)
        status = self.STATUS_DETERMINED
        
        # Confidence logic
        if confidence < 0.3:
            status = self.STATUS_LOW_CONFIDENCE
            if primary_score <= 1:
                primary_ctx = self.CONTEXT_UNKNOWN
                status = self.STATUS_UNDETERMINED
        
        # Gap analysis (if top two are close, low confidence?)
        if len(sorted_scores) > 1:
            second_score = sorted_scores[1][1]
            if primary_score > 0 and (primary_score - second_score) < 1.0:
                 # Tie-breaker situation
                 status = self.STATUS_LOW_CONFIDENCE

        return self._build_result(
            primary_ctx,
            status,
            confidence,
            surface,
            evidence,
            alternatives=[{"type": k, "score": v} for k, v in sorted_scores[1:3] if v > 0]
        )

    def _calculate_scores(self, evidence: Dict[str, Any]) -> Dict[str, float]:
        """Calculate score for each context based on evidence"""
        scores = {k: 0.0 for k in [
            self.CONTEXT_ECOMMERCE, self.CONTEXT_MARKETPLACE, self.CONTEXT_SAAS,
            self.CONTEXT_FINTECH, self.CONTEXT_BLOCKCHAIN, self.CONTEXT_CONTENT,
            self.CONTEXT_DEV
        ]}
        
        hits = evidence['content'].get('keyword_hits', {})
        tech = evidence['tech']
        struct = evidence['structure']
        
        # --- E-Commerce Signals ---
        if tech.get('ecommerce_platforms'): scores[self.CONTEXT_ECOMMERCE] += 5
        if struct.get('has_cart'): scores[self.CONTEXT_ECOMMERCE] += 3
        if struct.get('has_checkout'): scores[self.CONTEXT_ECOMMERCE] += 2
        if hits.get('ecommerce'): scores[self.CONTEXT_ECOMMERCE] += 1
        
        # --- SaaS Signals ---
        if hits.get('saas'): scores[self.CONTEXT_SAAS] += 2
        if struct.get('pricing_model') == 'Subscription': scores[self.CONTEXT_SAAS] += 3
        if struct.get('login_detected'): scores[self.CONTEXT_SAAS] += 1
        if tech.get('analytics'): scores[self.CONTEXT_SAAS] += 0.5
        
        # --- Fintech Signals ---
        if hits.get('fintech'): 
            # More generous scoring - payment gateways have many fintech keywords
            num_hits = len(hits['fintech'])
            scores[self.CONTEXT_FINTECH] += min(num_hits * 1.0, 8)  # Cap at 8 points
            # Extra boost for payment-specific keywords (strong signal)
            payment_keywords = {'payment gateway', 'payment processing', 'payment api', 'merchant', 
                              'payout', 'settlement', 'pci', 'razorpay', 'stripe', 'upi', 'netbanking'}
            payment_hits = len([k for k in hits['fintech'] if any(pk in k for pk in payment_keywords)])
            if payment_hits >= 2:
                scores[self.CONTEXT_FINTECH] += 3  # Strong fintech signal
        if evidence['mcc'].get('description') and 'financial' in evidence['mcc']['description'].lower():
            scores[self.CONTEXT_FINTECH] += 4
        
        # --- Blockchain Signals ---
        # Strong weighting for infrastructure
        if hits.get('blockchain_specific'): scores[self.CONTEXT_BLOCKCHAIN] += 5 # Validator, Consensus
        if hits.get('blockchain_generic'): scores[self.CONTEXT_BLOCKCHAIN] += 1
        if evidence['content'].get('has_whitepaper'): scores[self.CONTEXT_BLOCKCHAIN] += 2
        
        # --- Developer Platform Signals ---
        if hits.get('developer_docs'): scores[self.CONTEXT_DEV] += 3
        if evidence['content'].get('has_github'): scores[self.CONTEXT_DEV] += 1
        
        # --- Content Media Signals ---
        if hits.get('content'): scores[self.CONTEXT_CONTENT] += 2
        if tech.get('cms'): scores[self.CONTEXT_CONTENT] += 1
        
        # --- Cross-Correlation Adjustments ---
        
        # Trump Rule: Blockchain High Specificity
        if scores[self.CONTEXT_BLOCKCHAIN] >= 5:
             # Ensure it beats generic SaaS/Dev
             if scores[self.CONTEXT_SAAS] > 0: scores[self.CONTEXT_SAAS] -= 2
             if scores[self.CONTEXT_DEV] > 0: scores[self.CONTEXT_DEV] -= 2
             
        # Trump Rule: E-commerce Platform is definitive
        if tech.get('ecommerce_platforms'):
             # Boost E-com
             scores[self.CONTEXT_ECOMMERCE] += 2
        
        return scores

    def _determine_surface(self, evidence: Dict[str, Any], primary_context: str) -> str:
        """Determine the frontend surface type"""
        crawl = evidence['crawl']
        struct = evidence['structure']
        hits = evidence['content'].get('keyword_hits', {})
        
        if crawl.get('auth_gated') or struct.get('login_detected'):
            # If main content is hidden? Not necessarily.
            # But if simple marketing page + login -> Auth Gated/Marketing
            if struct.get('has_cart'): return self.SURFACE_FULL_COMMERCE
            return self.SURFACE_AUTH_GATED
            
        if struct.get('has_cart') or struct.get('has_checkout'):
            return self.SURFACE_FULL_COMMERCE
            
        if hits.get('developer_docs') and primary_context == self.CONTEXT_DEV:
            return self.SURFACE_API_DOCS
            
        if hits.get('content') and primary_context == self.CONTEXT_CONTENT:
            return self.SURFACE_CONTENT_ONLY
            
        return self.SURFACE_MARKETING_SITE

    def _build_result(self, primary, status, confidence, surface, evidence, reason=None, alternatives=None):
        return {
            "primary": primary,
            "status": status,
            "confidence": round(confidence, 2),
            "frontend_surface": surface,
            "reason": reason or f"Scored as {primary}",
            "evidence": evidence, # Raw evidence for debugging/UI
            "alternatives": alternatives or []
        }
