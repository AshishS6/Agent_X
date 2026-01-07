"""
URL Utilities Module
URL normalization, canonical resolution, and probabilistic page classification
"""

import re
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse, urljoin, urlunparse, parse_qs, urlencode
from bs4 import BeautifulSoup


class URLNormalizer:
    """Normalize URLs for deduplication and comparison"""
    
    # Query params to preserve (usually for content differentiation)
    PRESERVE_PARAMS = {'p', 'page', 'id', 'product', 'category'}
    
    @staticmethod
    def normalize(url: str) -> str:
        """
        Normalize URL for deduplication.
        - Removes fragments
        - Removes trailing slashes
        - Lowercases domain
        - Sorts and filters query params
        """
        try:
            parsed = urlparse(url)
            
            # Lowercase domain
            netloc = parsed.netloc.lower()
            
            # Normalize path (remove trailing slash, except for root)
            path = parsed.path.rstrip('/') or '/'
            
            # Filter and sort query params
            if parsed.query:
                params = parse_qs(parsed.query, keep_blank_values=False)
                filtered = {k: v for k, v in params.items() if k.lower() in URLNormalizer.PRESERVE_PARAMS}
                sorted_query = urlencode(sorted(filtered.items()), doseq=True) if filtered else ''
            else:
                sorted_query = ''
            
            # Rebuild without fragment
            normalized = urlunparse((
                parsed.scheme,
                netloc,
                path,
                '',  # params
                sorted_query,
                ''   # fragment
            ))
            
            return normalized
        except Exception:
            return url
    
    @staticmethod
    def extract_canonical(soup: BeautifulSoup, page_url: str) -> Optional[str]:
        """Extract canonical URL from <link rel="canonical">"""
        try:
            canonical_tag = soup.find('link', rel='canonical')
            if canonical_tag and canonical_tag.get('href'):
                canonical_href = canonical_tag['href']
                # Resolve relative canonical URLs
                return urljoin(page_url, canonical_href)
        except Exception:
            pass
        return None
    
    @staticmethod
    def is_internal(url: str, base_domain: str) -> bool:
        """Check if URL is internal to the base domain"""
        try:
            parsed = urlparse(url)
            url_domain = parsed.netloc.lower()
            base_domain = base_domain.lower()
            
            # Handle www prefix
            url_domain = url_domain.replace('www.', '')
            base_domain = base_domain.replace('www.', '')
            
            return url_domain == base_domain or url_domain.endswith('.' + base_domain)
        except Exception:
            return False
    
    @staticmethod
    def get_domain(url: str) -> str:
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower().replace('www.', '')
        except Exception:
            return ''


class PageClassifier:
    """
    Probabilistic page classification based on URL, anchor text, and title.
    Returns both type and confidence score.
    """
    
    # Page type patterns with weights
    PAGE_PATTERNS = {
        'privacy_policy': {
            'url_patterns': [
                (r'privacy[-_]?policy', 1.0),
                (r'/privacy/?$', 0.9),
                (r'gdpr', 0.8),
                (r'data[-_]?protection', 0.8),
            ],
            'text_patterns': [
                (r'privacy\s*policy', 1.0),
                (r'privacy', 0.6),
                (r'data\s*protection', 0.7),
            ]
        },
        'terms_conditions': {
            'url_patterns': [
                (r'terms[-_]?(and[-_]?)?conditions?', 1.0),
                (r'terms[-_]?of[-_]?(service|use)', 1.0),
                (r'/terms/?$', 0.9),
                (r'/tos/?$', 0.9),
                (r't-?and-?c', 0.8),
            ],
            'text_patterns': [
                (r'terms\s*(and|&)?\s*conditions?', 1.0),
                (r'terms\s*of\s*(service|use)', 1.0),
                (r'terms', 0.5),
            ]
        },
        'refund_policy': {
            'url_patterns': [
                (r'refund[-_]?policy', 1.0),
                (r'return[-_]?policy', 1.0),
                (r'/refunds?/?$', 0.9),
                (r'/returns?/?$', 0.9),
                (r'cancellation', 0.7),
            ],
            'text_patterns': [
                (r'refund\s*policy', 1.0),
                (r'return\s*policy', 1.0),
                (r'refund', 0.6),
                (r'cancellation', 0.5),
            ]
        },
        'shipping_delivery': {
            'url_patterns': [
                (r'shipping', 0.9),
                (r'delivery', 0.9),
                (r'dispatch', 0.7),
            ],
            'text_patterns': [
                (r'shipping\s*(policy|info)', 1.0),
                (r'delivery\s*(info|policy)', 1.0),
                (r'shipping', 0.6),
            ]
        },
        'about': {
            'url_patterns': [
                (r'about[-_]?us', 1.0),
                (r'/about/?$', 0.95),
                (r'who[-_]?we[-_]?are', 0.9),
                (r'our[-_]?story', 0.9),
                (r'[-/][a-z]+-story/?$', 0.85),  # Matches /idfy-story/, /company-story/, etc.
                (r'/company/?$', 0.85),
                (r'/story/?$', 0.8),
            ],
            'text_patterns': [
                (r'about\s*us', 1.0),
                (r'who\s*we\s*are', 0.9),
                (r'our\s*story', 0.85),
                (r'^company$', 0.8),  # Exact match for "Company" link text
                # NOTE: Generic 'about' removed - too many false positives from blog titles
            ]
        },
        'contact': {
            'url_patterns': [
                (r'contact[-_]?us', 1.0),
                (r'/contact/?$', 0.9),
                (r'support', 0.6),
                (r'help', 0.5),
            ],
            'text_patterns': [
                (r'contact\s*us', 1.0),
                (r'get\s*in\s*touch', 0.9),
                (r'contact', 0.6),
            ]
        },
        'pricing': {
            'url_patterns': [
                (r'/pricing/?$', 1.0),
                (r'/plans?/?$', 0.9),
                (r'/packages?/?$', 0.8),
            ],
            'text_patterns': [
                (r'pricing', 1.0),
                (r'plans?\s*(and|&)?\s*pricing', 1.0),
                (r'plans', 0.6),
            ]
        },
        'product': {
            'url_patterns': [
                (r'/products?/?$', 0.9),
                (r'/shop/?$', 0.8),
                (r'/store/?$', 0.8),
                (r'/catalog/?$', 0.7),
                (r'/features?/?$', 0.7),
            ],
            'text_patterns': [
                (r'products?', 0.7),
                (r'features?', 0.6),
                (r'shop', 0.5),
            ]
        },
        'solutions': {
            'url_patterns': [
                (r'/solutions?/?$', 1.0),
                (r'/services?/?$', 1.0),
                (r'/offerings?/?$', 0.9),
                (r'/platform/?$', 0.8),
                (r'/capabilities/?$', 0.7),
                (r'/what[-_]?we[-_]?do/?$', 0.8),
            ],
            'text_patterns': [
                (r'^solutions?$', 1.0),
                (r'^services?$', 1.0),
                (r'our\s*solutions?', 0.9),
                (r'our\s*services?', 0.9),
                (r'what\s*we\s*(do|offer)', 0.8),
                (r'platform', 0.6),
            ]
        },
        'faq': {
            'url_patterns': [
                (r'/faq/?$', 1.0),
                (r'frequently[-_]?asked', 0.9),
                (r'/help/?$', 0.6),
            ],
            'text_patterns': [
                (r'faq', 1.0),
                (r'frequently\s*asked', 0.9),
                (r'questions', 0.4),
            ]
        },
        'docs': {
            'url_patterns': [
                (r'/docs?/?$', 0.9),
                (r'/documentation/?$', 1.0),
                (r'/api/?$', 0.7),
                (r'/guide/?$', 0.7),
            ],
            'text_patterns': [
                (r'documentation', 1.0),
                (r'docs', 0.8),
                (r'api\s*reference', 0.8),
            ]
        },
        'blog': {
            'url_patterns': [
                (r'/blog/', 1.0),  # Matches any blog path (including posts)
                (r'/blog/?$', 1.0),
                (r'/news/', 0.9),
                (r'/news/?$', 0.8),
                (r'/articles?/', 0.8),
                (r'/articles?/?$', 0.7),
                (r'/insights/', 0.7),
                (r'/resources/', 0.6),
                (r'/webinars?/', 0.6),
            ],
            'text_patterns': [
                (r'blog', 1.0),
                (r'news', 0.6),
            ]
        },
    }
    
    # URL patterns that indicate content pages (blogs, news, etc.) that should not be classified as policy pages
    CONTENT_URL_PATTERNS = [
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
    
    # Skip patterns - URLs to ignore
    SKIP_PATTERNS = [
        r'\.pdf$',
        r'\.jpg$',
        r'\.png$',
        r'\.gif$',
        r'\.css$',
        r'\.js$',
        r'/cdn[-_]cgi/',
        r'javascript:',
        r'mailto:',
        r'tel:',
        r'#',
    ]
    
    @classmethod
    def _is_content_url(cls, url: str) -> bool:
        """Check if URL is a content page (blog, news, article) that shouldn't be classified as policy."""
        url_lower = url.lower()
        for pattern in cls.CONTENT_URL_PATTERNS:
            if re.search(pattern, url_lower):
                return True
        return False
    
    @classmethod
    def classify(cls, url: str, anchor_text: str = "", title: str = "") -> Dict[str, any]:
        """
        Classify a page by type with confidence score.
        
        Args:
            url: Page URL
            anchor_text: Text of the link pointing to this page
            title: Page title (from <title> tag)
            
        Returns:
            {"type": "privacy_policy", "confidence": 0.92}
        """
        # Check if URL should be skipped
        url_lower = url.lower()
        for pattern in cls.SKIP_PATTERNS:
            if re.search(pattern, url_lower):
                return {"type": "skip", "confidence": 1.0}
        
        path = urlparse(url).path.lower()
        anchor_lower = anchor_text.lower() if anchor_text else ""
        title_lower = title.lower() if title else ""
        
        # Check if this is a content URL (blog, news, etc.) - these should NOT be classified as policy pages
        is_content_url = cls._is_content_url(url)
        
        best_type = "other"
        best_confidence = 0.0
        
        # Policy page types that should not match content URLs
        policy_types = {'about', 'contact', 'privacy_policy', 'terms_conditions', 
                       'refund_policy', 'shipping_delivery', 'faq', 'product', 'pricing', 'solutions'}
        
        for page_type, patterns in cls.PAGE_PATTERNS.items():
            # Skip policy page types for content URLs (blogs shouldn't be classified as "about", etc.)
            if is_content_url and page_type in policy_types:
                continue
            
            confidence = 0.0
            
            # Check URL patterns
            for pattern, weight in patterns['url_patterns']:
                if re.search(pattern, path):
                    confidence = max(confidence, weight)
                    break
            
            # Check anchor text patterns (add to confidence)
            for pattern, weight in patterns['text_patterns']:
                if re.search(pattern, anchor_lower):
                    confidence = min(1.0, confidence + weight * 0.3)
                    break
            
            # Check title patterns (add to confidence)
            for pattern, weight in patterns['text_patterns']:
                if re.search(pattern, title_lower):
                    confidence = min(1.0, confidence + weight * 0.2)
                    break
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_type = page_type
        
        return {
            "type": best_type,
            "confidence": round(best_confidence, 2)
        }
    
    @classmethod
    def get_priority_score(cls, page_type: str) -> int:
        """Get priority score for page type (higher = more important to crawl)"""
        priority = {
            'home': 100,
            'privacy_policy': 95,
            'terms_conditions': 95,
            'refund_policy': 90,
            'about': 85,
            'contact': 80,
            'pricing': 75,
            'product': 70,
            'solutions': 70,  # SaaS/service companies - equally important as products
            'shipping_delivery': 65,
            'faq': 50,
            'docs': 40,
            'blog': 20,
            'other': 10,
        }
        return priority.get(page_type, 10)
