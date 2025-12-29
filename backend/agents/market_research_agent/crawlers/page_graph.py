"""
Page Graph Module
Normalized page data structures for crawl results
"""

import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from bs4 import BeautifulSoup


@dataclass
class CrawlError:
    """Classified crawl error"""
    type: str  # 'timeout', 'blocked', 'ssl', 'dns', 'http_error', 'parse_error'
    message: str
    status_code: Optional[int] = None
    
    @classmethod
    def from_exception(cls, e: Exception, status_code: Optional[int] = None) -> 'CrawlError':
        """Create CrawlError from exception"""
        error_str = str(e).lower()
        
        if 'timeout' in error_str or 'timed out' in error_str:
            return cls(type='timeout', message=str(e), status_code=status_code)
        elif 'ssl' in error_str or 'certificate' in error_str:
            return cls(type='ssl', message=str(e), status_code=status_code)
        elif 'dns' in error_str or 'nodename nor servname' in error_str or 'name resolution' in error_str:
            return cls(type='dns', message=str(e), status_code=status_code)
        elif status_code and status_code in (403, 429):
            return cls(type='blocked', message=str(e), status_code=status_code)
        elif status_code and status_code >= 400:
            return cls(type='http_error', message=str(e), status_code=status_code)
        else:
            return cls(type='unknown', message=str(e), status_code=status_code)


@dataclass
class PageData:
    """Individual page data with classification and metadata"""
    url: str
    final_url: str
    status: int
    content_type: str
    html: str
    source: str  # 'root', 'sitemap', 'nav_primary', 'nav_secondary'
    page_type: str  # 'home', 'about', 'privacy_policy', etc.
    classification_confidence: float  # 0.0 - 1.0
    canonical_url: Optional[str] = None
    content_hash: Optional[str] = None  # SHA-256 for determinism
    error: Optional[CrawlError] = None
    depth: int = 0
    
    def __post_init__(self):
        """Compute content hash if HTML present"""
        if self.html and not self.content_hash:
            # Clean HTML for consistent hashing (remove dynamic elements)
            clean_html = self._clean_for_hash(self.html)
            self.content_hash = hashlib.sha256(clean_html.encode('utf-8')).hexdigest()
    
    def _clean_for_hash(self, html: str) -> str:
        """Remove dynamic content for consistent hashing"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            # Remove script and style tags
            for tag in soup(['script', 'style', 'noscript']):
                tag.decompose()
            return soup.get_text(separator=' ', strip=True)[:10000]  # Cap at 10k chars
        except Exception:
            return html[:10000]
    
    def get_soup(self) -> Optional[BeautifulSoup]:
        """Parse HTML into BeautifulSoup"""
        if self.html:
            return BeautifulSoup(self.html, 'html.parser')
        return None


@dataclass
class CrawlMetadata:
    """Crawl execution metadata"""
    crawl_time_ms: int = 0
    pages_fetched: int = 0
    pages_discovered: int = 0
    sitemap_found: bool = False
    sitemap_urls_count: int = 0
    robots_checked: bool = False
    early_exit: bool = False
    early_exit_reason: Optional[str] = None
    errors: List[Dict] = field(default_factory=list)
    
    def add_error(self, url: str, error: CrawlError):
        """Record a crawl error"""
        self.errors.append({
            'url': url,
            'type': error.type,
            'message': error.message,
            'status_code': error.status_code
        })


class NormalizedPageGraph:
    """
    Container for all crawled pages.
    Provides methods to access pages by type.
    """
    
    # Required pages for early-exit check
    REQUIRED_PAGES = {'privacy_policy', 'terms_conditions'}
    HIGH_VALUE_PAGES = {'about', 'contact', 'pricing', 'product'}
    
    def __init__(self, root_url: str):
        self.root_url = root_url
        self.pages: Dict[str, PageData] = {}  # keyed by page_type or normalized URL
        self.metadata = CrawlMetadata()
        self._canonical_map: Dict[str, str] = {}  # canonical_url -> page_type
    
    def add_page(self, page: PageData) -> bool:
        """
        Add a page to the graph.
        Returns False if duplicate (by canonical URL).
        """
        # Check for duplicate by canonical URL
        if page.canonical_url:
            if page.canonical_url in self._canonical_map:
                return False
            self._canonical_map[page.canonical_url] = page.page_type
        
        # Store by page_type if it's a known type, otherwise by URL
        if page.page_type != 'other':
            # Only keep highest confidence for each type
            existing = self.pages.get(page.page_type)
            if existing and existing.classification_confidence >= page.classification_confidence:
                return False
            self.pages[page.page_type] = page
        else:
            self.pages[page.url] = page
        
        return True
    
    def get_page_by_type(self, page_type: str) -> Optional[PageData]:
        """Get page by type (home, about, privacy_policy, etc.)"""
        return self.pages.get(page_type)
    
    def get_soup_for_page(self, page_type: str) -> Optional[BeautifulSoup]:
        """Get parsed BeautifulSoup for a page type"""
        page = self.get_page_by_type(page_type)
        if page:
            return page.get_soup()
        return None
    
    def get_all_links(self) -> List[Dict[str, str]]:
        """
        Get all links from home page for PolicyDetector compatibility.
        Returns list of dicts with 'url' and 'text' keys.
        """
        home_page = self.get_page_by_type('home')
        if not home_page or not home_page.html:
            return []
        
        soup = home_page.get_soup()
        if not soup:
            return []
        
        from urllib.parse import urljoin
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            full_url = urljoin(home_page.final_url, href)
            link_text = a.get_text(strip=True).lower()
            links.append({'url': full_url, 'text': link_text})
        
        return links
    
    def has_required_pages(self) -> bool:
        """Check if all required pages are found (for early-exit)"""
        for page_type in self.REQUIRED_PAGES:
            page = self.pages.get(page_type)
            if not page or page.classification_confidence < 0.7:
                return False
        return True
    
    def get_found_page_types(self) -> List[str]:
        """Get list of all found page types"""
        return [
            page_type for page_type, page in self.pages.items()
            if isinstance(page, PageData) and page.status == 200
        ]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'root_url': self.root_url,
            'pages': {
                key: {
                    'url': page.url,
                    'final_url': page.final_url,
                    'status': page.status,
                    'content_type': page.content_type,
                    'source': page.source,
                    'page_type': page.page_type,
                    'classification_confidence': page.classification_confidence,
                    'canonical_url': page.canonical_url,
                    'content_hash': page.content_hash,
                    'error': {
                        'type': page.error.type,
                        'message': page.error.message,
                        'status_code': page.error.status_code
                    } if page.error else None
                }
                for key, page in self.pages.items()
                if isinstance(page, PageData)
            },
            'metadata': {
                'crawl_time_ms': self.metadata.crawl_time_ms,
                'pages_fetched': self.metadata.pages_fetched,
                'pages_discovered': self.metadata.pages_discovered,
                'sitemap_found': self.metadata.sitemap_found,
                'sitemap_urls_count': self.metadata.sitemap_urls_count,
                'robots_checked': self.metadata.robots_checked,
                'early_exit': self.metadata.early_exit,
                'early_exit_reason': self.metadata.early_exit_reason,
                'errors': self.metadata.errors
            }
        }
