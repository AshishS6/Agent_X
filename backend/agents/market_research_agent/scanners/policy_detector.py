"""
Policy Detector Module
Handles detection of policy pages (privacy, terms, refund, etc.)
Per PRD V2.1.1: Policy presence is authoritative, validity is advisory.
"""

import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse


class PolicyDetector:
    """Detects policy and important pages on websites"""
    
    # URL paths to exclude from policy page detection (blogs, news, articles, etc.)
    EXCLUDED_URL_PATTERNS = [
        r'/blog/',
        r'/blogs/',
        r'/news/',
        r'/article/',
        r'/articles/',
        r'/post/',
        r'/posts/',
        r'/insights/',
        r'/resources/',
        r'/webinars?/',
        r'/events?/',
        r'/press/',
        r'/media/',
        r'/case[-_]?stud(y|ies)/',
    ]
    
    # Policy page patterns with confidence scores (higher = more specific/reliable)
    # Format: (pattern, confidence) - patterns are tried in order, but best confidence wins
    PATTERNS_WITH_CONFIDENCE = {
        "privacy_policy": [
            (r'privacy[-_]?policy', 1.0),
            (r'/privacy/?$', 0.9),
            (r'gdpr', 0.7),
            (r'data[-_]?protection', 0.7),
        ],
        "terms_condition": [
            # Hyphen/underscore versions (for URLs)
            (r'terms?[-_]?(and[-_]?|\&[-_]?)?conditions?', 1.0),
            (r'terms?[-_]?of[-_]?(service|use)', 1.0),
            # Space versions (for link text like "Terms of Use", "Terms and Conditions")
            (r'terms?\s+of\s+(service|use)', 1.0),
            (r'terms?\s+(and|&)\s+conditions?', 1.0),
            # "Website Terms" variation (common on corporate sites)
            (r'website[-_\s]?terms?', 0.95),
            # URL path matches
            (r'/terms/?$', 0.9),
            (r'/tos/?$', 0.9),
            # T&C variations
            (r't\s*&\s*c', 0.8),
            (r't\&c', 0.8),
        ],
        "shipping_delivery": [
            (r'shipping[-_]?policy', 1.0),
            (r'delivery[-_]?policy', 1.0),
            (r'/shipping/?$', 0.9),
            (r'/delivery/?$', 0.9),
            (r'dispatch', 0.6),
        ],
        "returns_refund": [
            (r'refund[-_]?policy', 1.0),
            (r'return[-_]?policy', 1.0),
            (r'/refunds?/?$', 0.9),
            (r'/returns?/?$', 0.9),
            (r'cancellation', 0.6),
        ],
        "contact_us": [
            (r'contact[-_]?us', 1.0),
            (r'/contact/?$', 0.9),
            (r'get[-_]?in[-_]?touch', 0.8),
        ],
        "about_us": [
            # Highly specific patterns first
            (r'about[-_]?us', 1.0),
            (r'/about/?$', 0.95),
            (r'who[-_]?we[-_]?are', 0.9),
            (r'our[-_]?story', 0.9),
            (r'[-/]story/?$', 0.85),  # Matches /idfy-story/, /company-story/
            (r'/company/?$', 0.85),
            (r'company[-_]?info', 0.8),
            # NOTE: Generic 'about' or 'company' in text is NOT included - too many false positives
        ],
        "faq": [
            (r'/faq/?$', 1.0),
            (r'frequently[-_]?asked', 0.9),
            (r'/help/?$', 0.6),
        ],
        "product": [
            (r'/products?/?$', 0.9),
            (r'/shop/?$', 0.8),
            (r'/store/?$', 0.8),
            (r'/catalog/?$', 0.7),
        ],
        "solutions": [
            (r'/solutions?/?$', 1.0),
            (r'/services?/?$', 1.0),
            (r'/offerings?/?$', 0.9),
            (r'/platform/?$', 0.8),
            (r'/capabilities/?$', 0.7),
            (r'what[-_]?we[-_]?do', 0.8),
        ]
    }
    
    # Legacy patterns for backward compatibility (used if confidence-based detection finds nothing)
    PATTERNS = {
        "privacy_policy": [
            r'privacy[-_]?policy', r'privacy', r'gdpr', r'data[-_]?protection'
        ],
        "terms_condition": [
            r'terms?[-_]?(and[-_]?|\&[-_]?)?conditions?', r'terms?[-_]?of[-_]?(service|use)',
            r'terms?\s+of\s+(service|use)', r'terms?\s+(and|&)\s+conditions?',
            r'website[-_\s]?terms?', r't\s*&\s*c', r't\&c', r'tos'
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
        ],
        "solutions": [
            r'solutions?', r'services?', r'offerings?', r'platform', r'capabilities'
        ]
    }
    
    @staticmethod
    def _is_excluded_url(url: str) -> bool:
        """Check if URL should be excluded from policy detection (blog, news, etc.)"""
        url_lower = url.lower()
        for pattern in PolicyDetector.EXCLUDED_URL_PATTERNS:
            if re.search(pattern, url_lower):
                return True
        return False
    
    @staticmethod
    def detect_policies(links: List[Dict[str, str]], home_url: str) -> Dict[str, Dict[str, any]]:
        """
        Detect policy pages from a list of links.
        Per PRD V2.1.1: Returns "Policy Detected" (not "Valid Policy").
        Each detected policy includes evidence: source URL and detection method.
        
        Uses confidence-based matching to select the best candidate for each policy type,
        and excludes blog/news/article URLs from detection.
        
        Args:
            links: List of dicts with 'url' and 'text' keys
            home_url: Home page URL
            
        Returns:
            Dict of detected policy pages with evidence metadata
        """
        policy_pages = {
            "home_page": {
                "found": True,
                "url": home_url,
                "status": "Home Page detected",
                "detection_method": "home_url",
                "evidence": {
                    "source_url": home_url,
                    "triggering_rule": "Home page URL provided",
                    "evidence_snippet": f"Home page URL: {home_url}",
                    "confidence": 100.0
                }
            },
            "privacy_policy": {"found": False, "url": "", "status": "", "detection_method": None, "evidence": None},
            "shipping_delivery": {"found": False, "url": "", "status": "", "detection_method": None, "evidence": None},
            "returns_refund": {"found": False, "url": "", "status": "", "detection_method": None, "evidence": None},
            "terms_condition": {"found": False, "url": "", "status": "", "detection_method": None, "evidence": None},
            "contact_us": {"found": False, "url": "", "status": "", "detection_method": None, "evidence": None},
            "about_us": {"found": False, "url": "", "status": "", "detection_method": None, "evidence": None},
            "faq": {"found": False, "url": "", "status": "", "detection_method": None, "evidence": None},
            "product": {"found": False, "url": "", "status": "", "detection_method": None, "evidence": None},
            "solutions": {"found": False, "url": "", "status": "", "detection_method": None, "evidence": None}
        }
        
        # Track best candidates per policy type (url, confidence, detection_method, pattern, link_text)
        best_candidates: Dict[str, Tuple[str, float, str, str, str]] = {}
        
        for link_data in links:
            link_url = link_data["url"]
            link_text = link_data.get("text", "").strip()
            
            # Skip excluded URLs (blogs, news, articles, etc.)
            if PolicyDetector._is_excluded_url(link_url):
                continue
            
            link_path = urlparse(link_url).path.lower()
            
            # First pass: Use confidence-based patterns
            for page_type, patterns_with_conf in PolicyDetector.PATTERNS_WITH_CONFIDENCE.items():
                for pattern, base_confidence in patterns_with_conf:
                    # Check URL path match (more reliable)
                    path_match = re.search(pattern, link_path, re.IGNORECASE)
                    # Check link text match
                    text_match = re.search(pattern, link_text, re.IGNORECASE) if link_text else None
                    
                    if path_match or text_match:
                        # URL path matches get full confidence, text matches get reduced confidence
                        if path_match:
                            confidence = base_confidence
                            detection_method = "url_pattern"
                        else:
                            confidence = base_confidence * 0.8  # Text matches are less reliable
                            detection_method = "anchor_text"
                        
                        # Update if this is the best candidate so far
                        current_best = best_candidates.get(page_type)
                        if not current_best or confidence > current_best[1]:
                            best_candidates[page_type] = (link_url, confidence, detection_method, pattern, link_text)
        
        # Populate policy_pages from best candidates
        for page_type, (url, confidence, detection_method, pattern, link_text) in best_candidates.items():
            link_path = urlparse(url).path.lower()
            evidence_snippet = f"URL path: '{link_path}'" if detection_method == "url_pattern" else f"Link text: '{link_text}'"
            
            evidence = {
                "source_url": url,
                "triggering_rule": f"Policy detection via {detection_method} (pattern: {pattern})",
                "evidence_snippet": evidence_snippet,
                "confidence": confidence * 100  # Convert to percentage
            }
            
            policy_pages[page_type] = {
                "found": True,
                "url": url,
                "status": f"{page_type.replace('_', ' ').title()} page detected",
                "detection_method": detection_method,
                "evidence": evidence
            }
        
        # Second pass: Fallback to legacy patterns for any still-missing policies
        # This maintains backward compatibility but uses exclusion filtering
        for link_data in links:
            link_url = link_data["url"]
            link_text = link_data.get("text", "").strip()
            
            # Skip excluded URLs
            if PolicyDetector._is_excluded_url(link_url):
                continue
            
            link_path = urlparse(link_url).path.lower()
            
            for page_type, page_patterns in PolicyDetector.PATTERNS.items():
                if not policy_pages[page_type]["found"]:
                    for pattern in page_patterns:
                        # For "about_us", skip the generic "about" pattern in legacy mode
                        # (too many false positives)
                        if page_type == "about_us" and pattern == r'about':
                            continue
                        
                        text_match = re.search(pattern, link_text, re.IGNORECASE) if link_text else False
                        path_match = re.search(pattern, link_path, re.IGNORECASE)
                        
                        if text_match or path_match:
                            if text_match:
                                detection_method = "anchor_text"
                                evidence_snippet = f"Link text: '{link_text}'"
                            else:
                                detection_method = "url_pattern"
                                evidence_snippet = f"URL path: '{link_path}'"
                            
                            evidence = {
                                "source_url": link_url,
                                "triggering_rule": f"Policy detection via {detection_method} (pattern: {pattern})",
                                "evidence_snippet": evidence_snippet,
                                "confidence": 60.0  # Lower confidence for legacy fallback
                            }
                            
                            policy_pages[page_type] = {
                                "found": True,
                                "url": link_url,
                                "status": f"{page_type.replace('_', ' ').title()} page detected",
                                "detection_method": detection_method,
                                "evidence": evidence
                            }
                            break
        
        # Special handling for "Products" and "Solutions" nav items
        # These are often dropdown toggles with exact text matches
        for link_data in links:
            link_text = link_data.get("text", "").strip().lower()
            link_url = link_data["url"]
            
            # Detect "Products" nav item (exact or near-exact match)
            if not policy_pages["product"]["found"]:
                if link_text in ['products', 'product', 'our products', 'all products']:
                    policy_pages["product"] = {
                        "found": True,
                        "url": link_url,
                        "status": "Products section detected (navigation menu)",
                        "detection_method": "nav_dropdown",
                        "evidence": {
                            "source_url": link_url,
                            "triggering_rule": "Exact 'Products' anchor text match in navigation",
                            "evidence_snippet": f"Link text: '{link_text}'",
                            "confidence": 75.0
                        }
                    }
            
            # Detect "Solutions" nav item (exact or near-exact match)
            if not policy_pages["solutions"]["found"]:
                if link_text in ['solutions', 'solution', 'our solutions', 'all solutions', 'services', 'our services']:
                    policy_pages["solutions"] = {
                        "found": True,
                        "url": link_url,
                        "status": "Solutions section detected (navigation menu)",
                        "detection_method": "nav_dropdown",
                        "evidence": {
                            "source_url": link_url,
                            "triggering_rule": "Exact 'Solutions' anchor text match in navigation",
                            "evidence_snippet": f"Link text: '{link_text}'",
                            "confidence": 75.0
                        }
                    }
        
        return policy_pages
