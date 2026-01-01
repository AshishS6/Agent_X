"""
Context Evidence Collector
Collects raw, non-interpretive signals for business context classification.
"""

from typing import Dict, Any, List, Optional, Set
import re

class EvidenceCollector:
    """
    Collects evidence from various scan sources to support business context classification.
    Focuses on raw observations (e.g. "found word X", "auth redirect detected") rather than conclusions.
    """
    
    def __init__(self, logger=None):
        self.logger = logger

    def collect(self, 
                page_graph: Any, 
                tech_stack: Dict[str, Any], 
                product_indicators: Dict[str, Any],
                page_text: str,
                mcc_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Collect signals from all available sources.
        
        Args:
            page_graph: NormalizedPageGraph object from crawl
            tech_stack: Detected technologies
            product_indicators: Product/Pricing/Cart detection data
            page_text: Combined text of home/key pages
            mcc_data: MCC classification data
            
        Returns:
            Dictionary of collected evidence grouped by category.
        """
        
        evidence = {
            "crawl": self._collect_crawl_signals(page_graph),
            "content": self._collect_content_signals(page_text),
            "structure": self._collect_structure_signals(product_indicators, page_text),
            "tech": self._collect_tech_signals(tech_stack),
            "mcc": self._collect_mcc_signals(mcc_data)
        }
        
        return evidence

    def _collect_crawl_signals(self, page_graph: Any) -> Dict[str, Any]:
        """Collect signals from the crawl process"""
        if not page_graph:
             return {"status": "failed", "pages_fetched": 0}
             
        home_page = page_graph.get_page_by_type('home')
        
        # Detect auth gating via redirects or 401/403
        auth_gated = False
        if home_page:
            if home_page.status in [401, 403]:
                auth_gated = True
            elif home_page.url != home_page.final_url:
                # Check if redirected to login
                final_path = home_page.final_url.lower()
                if any(x in final_path for x in ['/login', '/signin', '/auth', 'account']):
                    auth_gated = True

        return {
            "pages_fetched": page_graph.metadata.pages_fetched,
            "pages_discovered": page_graph.metadata.pages_discovered,
            "auth_gated": auth_gated,
            "blocked": home_page and home_page.status == 403,
            "has_robots_txt": page_graph.metadata.robots_checked,
            "sitemap_found": page_graph.metadata.sitemap_found
        }

    def _collect_content_signals(self, page_text: str) -> Dict[str, Any]:
        """Collect keyword hits and content patterns"""
        if not page_text:
            return {}
            
        text = page_text.lower()
        
        # Keyword Lists
        patterns = {
            "developer_docs": ['api reference', 'sdk', 'documentation', 'developer guide', 'git clone', 'npm install'],
            "blockchain_specific": ['validator', 'consensus', 'tokenomics', 'smart contract', 'faucet', 'mainnet', 'testnet', 'rpc endpoint'],
            "blockchain_generic": ['blockchain', 'crypto', 'web3', 'decentralized', 'protocol'],
            "fintech": ['banking', 'wealth management', 'insurance', 'loans', 'credit card', 'investing', 'brokerage'],
            "saas": ['dashboard', 'sign up', 'log in', 'pricing', 'subscription', 'software', 'platform'],
            "ecommerce": ['add to cart', 'checkout', 'shipping', 'store', 'shop now', 'buy now'],
            "content": ['blog', 'news', 'article', 'editorial', 'subscribe to newsletter', 'read more']
        }
        
        hits = {}
        for category, keywords in patterns.items():
            found = [k for k in keywords if k in text]
            if found:
                hits[category] = found
                
        return {
            "keyword_hits": hits,
            "has_whitepaper": "whitepaper" in text,
            "has_github": "github.com" in text or "github" in text
        }

    def _collect_structure_signals(self, product_indicators: Dict[str, Any], page_text: str) -> Dict[str, Any]:
        """Collect structural signals like cart, login, pricing"""
        return {
            "has_cart": product_indicators.get('has_cart', False) or 'cart' in page_text[:5000],
            "has_checkout": product_indicators.get('has_checkout', False),
            "pricing_model": product_indicators.get('pricing_model'),
            "has_pricing_page": product_indicators.get('source_pages', {}).get('pricing_page') is not None,
            "login_detected": "login" in page_text[:2000] or "sign in" in page_text[:2000]
        }

    def _collect_tech_signals(self, tech_stack: Dict[str, Any]) -> Dict[str, Any]:
        """Collect signals from detected technologies"""
        if not tech_stack or 'technologies' not in tech_stack:
            return {}
            
        tech_names = [t.get('name', '').lower() for t in tech_stack.get('technologies', [])]
        categories = [c.get('slug', '') for t in tech_stack.get('technologies', []) for c in t.get('categories', [])]
        
        return {
            "ecommerce_platforms": [t for t in tech_names if t in ['shopify', 'woocommerce', 'magento', 'bigcommerce']],
            "payment_processors": [t for t in tech_names if t in ['stripe', 'paypal', 'braintree', 'adyen']],
            "cms": [t for t in tech_names if t in ['wordpress', 'ghost', 'drupal']],
            "frontend_frameworks": [t for t in tech_names if t in ['react', 'vue', 'angular', 'next.js']],
            "analytics": [t for t in tech_names if t in ['google analytics', 'segment', 'mixpanel']]
        }

    def _collect_mcc_signals(self, mcc_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Collect MCC-based signals"""
        if not mcc_data or not mcc_data.get('primary_mcc'):
            return {}
            
        pmcc = mcc_data['primary_mcc']
        return {
            "category": pmcc.get('category'),
            "description": pmcc.get('description'),
            "confidence": pmcc.get('confidence', 0)
        }
