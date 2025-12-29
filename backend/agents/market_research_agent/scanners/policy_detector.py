"""
Policy Detector Module
Handles detection of policy pages (privacy, terms, refund, etc.)
"""

import re
from typing import Dict, List
from urllib.parse import urlparse


class PolicyDetector:
    """Detects policy and important pages on websites"""
    
    # Policy page patterns
    PATTERNS = {
        "privacy_policy": [
            r'privacy[-_]?policy', r'privacy', r'gdpr', r'data[-_]?protection'
        ],
        "terms_condition": [
            r'terms?[-_]?(and[-_]?|\&[-_]?)?conditions?', r'terms?[-_]?of[-_]?(service|use)', r't\&c', r'tos'
        ],
        "shipping_delivery": [
            r'shipping', r'delivery', r'dispatch'
        ],
        "returns_refund": [
            r'returns?', r'refunds?', r'cancellation'
        ],
        "contact_us": [
            r'contact[-_]?us', r'contact', r'support'
        ],
        "about_us": [
            r'about[-_]?us', r'about', r'who[-_]?we[-_]?are'
        ],
        "faq": [
            r'faq', r'frequently[-_]?asked', r'help'
        ],
        "product": [
            r'products?', r'shop', r'store', r'catalog'
        ]
    }
    
    @staticmethod
    def detect_policies(links: List[Dict[str, str]], home_url: str) -> Dict[str, Dict[str, any]]:
        """
        Detect policy pages from a list of links
        
        Args:
            links: List of dicts with 'url' and 'text' keys
            home_url: Home page URL
            
        Returns:
            Dict of detected policy pages
        """
        policy_pages = {
            "home_page": {
                "found": True,
                "url": home_url,
                "status": "Home Page page is available"
            },
            "privacy_policy": {"found": False, "url": "", "status": ""},
            "shipping_delivery": {"found": False, "url": "", "status": ""},
            "returns_refund": {"found": False, "url": "", "status": ""},
            "terms_condition": {"found": False, "url": "", "status": ""},
            "contact_us": {"found": False, "url": "", "status": ""},
            "about_us": {"found": False, "url": "", "status": ""},
            "faq": {"found": False, "url": "", "status": ""},
            "product": {"found": False, "url": "", "status": ""}
        }
        
        for link_data in links:
            link_url = link_data["url"]
            link_text = link_data["text"]
            link_path = urlparse(link_url).path.lower()
            
            for page_type, page_patterns in PolicyDetector.PATTERNS.items():
                if not policy_pages[page_type]["found"]:
                    for pattern in page_patterns:
                        if re.search(pattern, link_text) or re.search(pattern, link_path):
                            policy_pages[page_type] = {
                                "found": True,
                                "url": link_url,
                                "status": f"{page_type.replace('_', ' ').title()} page is available"
                            }
                            break
        
        return policy_pages
