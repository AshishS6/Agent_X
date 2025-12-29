"""
Content Analyzer Module
Handles content risk detection and analysis
"""

import re
from typing import Dict, List


class ContentAnalyzer:
    """Analyzes page content for risks and quality issues"""
    
    # Lorem ipsum patterns
    LOREM_PATTERNS = [
        r'lorem\s+ipsum\s+dolor\s+sit\s+amet',
        r'consectetur\s+adipiscing',
        r'sed\s+do\s+eiusmod'
    ]
    
    # Restricted keywords by category
    RESTRICTED_KEYWORDS = {
        "gambling": ["casino", "poker", "betting", "slots", "lottery"],
        "adult": ["xxx", "adult content", "nsfw"],
        "crypto": ["cryptocurrency", "bitcoin", "ico"],
        "pharmacy": ["viagra", "cialis", "prescription drugs"]
    }
    
    @staticmethod
    def analyze_content_risk(page_text: str) -> Dict[str, any]:
        """
        Analyze content for risks
        
        Args:
            page_text: Full page text (lowercased)
            
        Returns:
            Dict with risk analysis
        """
        # Check for lorem ipsum
        dummy_words_found = []
        for pattern in ContentAnalyzer.LOREM_PATTERNS:
            if re.search(pattern, page_text):
                dummy_words_found.append(pattern)
        
        # Check for restricted keywords
        restricted_found = []
        for category, keywords in ContentAnalyzer.RESTRICTED_KEYWORDS.items():
            for keyword in keywords:
                if keyword in page_text:
                    restricted_found.append({
                        "category": category,
                        "keyword": keyword
                    })
        
        # Calculate risk score
        risk_score = len(restricted_found) * 20 + (50 if len(dummy_words_found) > 0 else 0)
        
        return {
            "dummy_words_detected": len(dummy_words_found) > 0,
            "dummy_words": dummy_words_found,
            "restricted_keywords_found": restricted_found,
            "risk_score": risk_score
        }
    
    @staticmethod
    def detect_product_indicators(page_text: str) -> Dict[str, bool]:
        """
        Detect product/ecommerce indicators
        
        Args:
            page_text: Full page text (lowercased)
            
        Returns:
            Dict with product indicators
        """
        return {
            "has_products": "product" in page_text or "shop" in page_text,
            "has_pricing": "price" in page_text or "$" in page_text or "₹" in page_text,
            "has_cart": "add to cart" in page_text or "buy now" in page_text,
            "ecommerce_platform": "shopify" in page_text or "woocommerce" in page_text
        }
