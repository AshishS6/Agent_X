"""
Navigation Discovery Module
Two-tiered navigation link extraction
"""

import logging
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse, urljoin

from bs4 import BeautifulSoup

from .url_utils import URLNormalizer, PageClassifier


class NavigationDiscovery:
    """
    Extract navigation links with primary + fallback strategy.
    
    Primary: Header nav + footer links (most important pages)
    Secondary: All internal links (fallback if sitemap missing)
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def extract_primary(
        self,
        soup: BeautifulSoup,
        base_url: str
    ) -> List[Dict]:
        """
        Extract primary navigation links from header and footer.
        
        Args:
            soup: Parsed HTML
            base_url: Base URL for resolving relative links
            
        Returns:
            List of dicts with url, text, source, classification
        """
        links: List[Dict] = []
        seen_urls: Set[str] = set()
        
        parsed_base = urlparse(base_url)
        base_domain = parsed_base.netloc.lower().replace('www.', '')
        
        # 1. Extract from <nav> elements (highest priority)
        for nav in soup.find_all('nav'):
            nav_links = self._extract_links_from_element(
                nav, base_url, base_domain, 'nav', seen_urls
            )
            links.extend(nav_links)
        
        # 2. Extract from <header>
        header = soup.find('header')
        if header:
            header_links = self._extract_links_from_element(
                header, base_url, base_domain, 'header', seen_urls
            )
            links.extend(header_links)
        
        # 3. Extract from <footer>
        footer = soup.find('footer')
        if footer:
            footer_links = self._extract_links_from_element(
                footer, base_url, base_domain, 'footer', seen_urls
            )
            links.extend(footer_links)
        
        # 4. Look for common navigation patterns
        # Menu containers often have class/id containing 'menu', 'nav'
        for selector in ['[class*="menu"]', '[class*="nav"]', '[id*="menu"]', '[id*="nav"]']:
            try:
                for element in soup.select(selector)[:5]:  # Limit to avoid over-extraction
                    if element.name not in ('nav', 'header', 'footer'):
                        menu_links = self._extract_links_from_element(
                            element, base_url, base_domain, 'menu', seen_urls
                        )
                        links.extend(menu_links)
            except Exception:
                pass
        
        # Sort by classification priority
        links.sort(key=lambda x: PageClassifier.get_priority_score(x['classification']['type']), reverse=True)
        
        self.logger.info(f"[CRAWL] Primary nav: {len(links)} links from header/footer")
        return links
    
    def extract_secondary(
        self,
        soup: BeautifulSoup,
        base_url: str,
        exclude_urls: Optional[Set[str]] = None
    ) -> List[Dict]:
        """
        Extract all internal links as fallback.
        Use when sitemap is missing.
        
        Args:
            soup: Parsed HTML
            base_url: Base URL for resolving relative links
            exclude_urls: URLs already discovered to skip
            
        Returns:
            List of dicts with url, text, source, classification
        """
        links: List[Dict] = []
        seen_urls: Set[str] = exclude_urls or set()
        
        parsed_base = urlparse(base_url)
        base_domain = parsed_base.netloc.lower().replace('www.', '')
        
        # Extract from main content area first
        main_content = soup.find('main') or soup.find(id='content') or soup.find(class_='content')
        if main_content:
            content_links = self._extract_links_from_element(
                main_content, base_url, base_domain, 'content', seen_urls
            )
            links.extend(content_links)
        
        # Then extract from body, excluding script/style
        body = soup.find('body')
        if body:
            body_links = self._extract_links_from_element(
                body, base_url, base_domain, 'body', seen_urls
            )
            links.extend(body_links)
        
        # Sort by priority and limit
        links.sort(key=lambda x: PageClassifier.get_priority_score(x['classification']['type']), reverse=True)
        
        self.logger.info(f"[CRAWL] Secondary nav: {len(links)} links from page content")
        return links[:50]  # Cap secondary links
    
    def _extract_links_from_element(
        self,
        element: BeautifulSoup,
        base_url: str,
        base_domain: str,
        source: str,
        seen_urls: Set[str]
    ) -> List[Dict]:
        """Extract and classify links from an element"""
        links: List[Dict] = []
        
        for a in element.find_all('a', href=True):
            href = a['href']
            
            # Skip anchor-only, javascript, mailto, tel links
            if href.startswith('#') or href.startswith('javascript:') or \
               href.startswith('mailto:') or href.startswith('tel:'):
                continue
            
            # Resolve relative URLs
            full_url = urljoin(base_url, href)
            
            # Normalize URL
            normalized_url = URLNormalizer.normalize(full_url)
            
            # Skip if already seen
            if normalized_url in seen_urls:
                continue
            
            # Check if internal
            if not URLNormalizer.is_internal(full_url, base_domain):
                continue
            
            # Get anchor text
            anchor_text = a.get_text(strip=True)
            
            # Classify the page
            classification = PageClassifier.classify(full_url, anchor_text)
            
            # Skip non-content pages
            if classification['type'] == 'skip':
                continue
            
            seen_urls.add(normalized_url)
            
            links.append({
                'url': full_url,
                'normalized_url': normalized_url,
                'text': anchor_text,
                'source': source,
                'classification': classification
            })
        
        return links
    
    def merge_and_dedupe(
        self,
        *link_lists: List[Dict]
    ) -> List[Dict]:
        """
        Merge multiple link lists and deduplicate.
        Keeps highest priority classification for each URL.
        """
        url_to_link: Dict[str, Dict] = {}
        
        for links in link_lists:
            for link in links:
                normalized = link.get('normalized_url', URLNormalizer.normalize(link['url']))
                
                if normalized not in url_to_link:
                    url_to_link[normalized] = link
                else:
                    # Keep link with higher confidence
                    existing = url_to_link[normalized]
                    if link['classification']['confidence'] > existing['classification']['confidence']:
                        url_to_link[normalized] = link
        
        # Sort by priority
        result = list(url_to_link.values())
        result.sort(key=lambda x: PageClassifier.get_priority_score(x['classification']['type']), reverse=True)
        
        return result
