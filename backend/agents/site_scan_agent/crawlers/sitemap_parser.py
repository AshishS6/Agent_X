"""
Sitemap Parser Module
Discover and parse sitemap.xml files
"""

import asyncio
import logging
import re
from typing import List, Optional, Tuple
from urllib.parse import urlparse, urljoin
import xml.etree.ElementTree as ET

import aiohttp
from bs4 import BeautifulSoup

from .url_utils import PageClassifier


class SitemapParser:
    """Discover and parse sitemaps with URL prioritization"""
    
    # Standard sitemap paths to try
    SITEMAP_PATHS = [
        '/sitemap.xml',
        '/sitemap_index.xml',
        '/sitemap-index.xml',
        '/sitemaps.xml',
    ]
    
    # Priority keywords for URL filtering
    PRIORITY_KEYWORDS = [
        'privacy', 'terms', 'about', 'pricing', 'product',
        'contact', 'refund', 'shipping', 'policy', 'legal'
    ]
    
    USER_AGENT = 'Agent_X_CrawlOrchestrator/1.0'
    TIMEOUT = 5  # seconds
    MAX_URLS = 100  # Max URLs to extract from sitemap
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    async def discover_and_parse(
        self,
        base_url: str,
        homepage_html: Optional[str] = None,
        robots_sitemaps: Optional[List[str]] = None,
        session: Optional[aiohttp.ClientSession] = None
    ) -> Tuple[List[str], bool]:
        """
        Discover and parse sitemaps from a website.
        
        Args:
            base_url: Base URL of the website
            homepage_html: Optional homepage HTML to check for sitemap links
            robots_sitemaps: Optional list of sitemaps from robots.txt
            session: Optional aiohttp session to reuse
            
        Returns:
            Tuple of (list of discovered URLs, sitemap_found boolean)
        """
        parsed = urlparse(base_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        
        all_urls: List[str] = []
        sitemap_found = False
        
        close_session = False
        if session is None:
            session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.TIMEOUT),
                headers={'User-Agent': self.USER_AGENT}
            )
            close_session = True
        
        try:
            # 1. Try sitemaps from robots.txt first
            if robots_sitemaps:
                for sitemap_url in robots_sitemaps[:3]:  # Limit to first 3
                    urls = await self._fetch_sitemap(sitemap_url, session)
                    if urls:
                        all_urls.extend(urls)
                        sitemap_found = True
                        self.logger.info(f"[CRAWL] Sitemap from robots.txt: {len(urls)} URLs")
            
            # 2. Try standard sitemap paths
            if not sitemap_found:
                for path in self.SITEMAP_PATHS:
                    sitemap_url = urljoin(base, path)
                    urls = await self._fetch_sitemap(sitemap_url, session)
                    if urls:
                        all_urls.extend(urls)
                        sitemap_found = True
                        self.logger.info(f"[CRAWL] Sitemap found at {path}: {len(urls)} URLs")
                        break
            
            # 3. Check homepage for <link rel="sitemap">
            if not sitemap_found and homepage_html:
                sitemap_url = self._find_sitemap_link(homepage_html, base)
                if sitemap_url:
                    urls = await self._fetch_sitemap(sitemap_url, session)
                    if urls:
                        all_urls.extend(urls)
                        sitemap_found = True
                        self.logger.info(f"[CRAWL] Sitemap from HTML link: {len(urls)} URLs")
            
        finally:
            if close_session:
                await session.close()
        
        # Filter and prioritize URLs
        filtered_urls = self._filter_and_prioritize(all_urls, base)
        
        if sitemap_found:
            self.logger.info(f"[CRAWL] Sitemap: {len(filtered_urls)} priority URLs from {len(all_urls)} total")
        
        return filtered_urls, sitemap_found
    
    async def _fetch_sitemap(
        self,
        sitemap_url: str,
        session: aiohttp.ClientSession
    ) -> List[str]:
        """Fetch and parse a single sitemap"""
        urls: List[str] = []
        
        try:
            async with session.get(sitemap_url) as response:
                if response.status != 200:
                    return urls
                
                content = await response.text()
                
                # Check if it's a sitemap index
                if '<sitemapindex' in content.lower():
                    urls = await self._parse_sitemap_index(content, session)
                else:
                    urls = self._parse_sitemap(content)
                    
        except asyncio.TimeoutError:
            self.logger.debug(f"[CRAWL] Sitemap timeout: {sitemap_url}")
        except Exception as e:
            self.logger.debug(f"[CRAWL] Sitemap error ({sitemap_url}): {e}")
        
        return urls[:self.MAX_URLS]
    
    async def _parse_sitemap_index(
        self,
        content: str,
        session: aiohttp.ClientSession
    ) -> List[str]:
        """Parse sitemap index and fetch child sitemaps"""
        all_urls: List[str] = []
        sitemap_urls: List[str] = []
        
        try:
            root = ET.fromstring(content)
            # Handle namespace
            ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            
            for sitemap in root.findall('.//sm:sitemap/sm:loc', ns):
                if sitemap.text:
                    sitemap_urls.append(sitemap.text.strip())
            
            # Fallback without namespace
            if not sitemap_urls:
                for sitemap in root.findall('.//sitemap/loc'):
                    if sitemap.text:
                        sitemap_urls.append(sitemap.text.strip())
        except ET.ParseError:
            # Try regex fallback
            sitemap_urls = re.findall(r'<loc>\s*(https?://[^<]+)\s*</loc>', content, re.I)
        
        # Fetch first few child sitemaps
        for sitemap_url in sitemap_urls[:3]:
            child_urls = await self._fetch_sitemap(sitemap_url, session)
            all_urls.extend(child_urls)
            if len(all_urls) >= self.MAX_URLS:
                break
        
        return all_urls
    
    def _parse_sitemap(self, content: str) -> List[str]:
        """Parse a regular sitemap"""
        urls: List[str] = []
        
        try:
            root = ET.fromstring(content)
            # Handle namespace
            ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            
            for url in root.findall('.//sm:url/sm:loc', ns):
                if url.text:
                    urls.append(url.text.strip())
            
            # Fallback without namespace
            if not urls:
                for url in root.findall('.//url/loc'):
                    if url.text:
                        urls.append(url.text.strip())
        except ET.ParseError:
            # Try regex fallback
            urls = re.findall(r'<loc>\s*(https?://[^<]+)\s*</loc>', content, re.I)
        
        return urls
    
    def _find_sitemap_link(self, html: str, base_url: str) -> Optional[str]:
        """Find <link rel="sitemap"> in HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            link = soup.find('link', rel='sitemap')
            if link and link.get('href'):
                return urljoin(base_url, link['href'])
        except Exception:
            pass
        return None
    
    def _filter_and_prioritize(self, urls: List[str], base_url: str) -> List[str]:
        """Filter internal URLs and prioritize important pages"""
        parsed_base = urlparse(base_url)
        base_domain = parsed_base.netloc.lower().replace('www.', '')
        
        # Filter and classify URLs
        scored_urls: List[Tuple[str, int]] = []
        seen = set()
        
        for url in urls:
            url = url.strip()
            if not url or url in seen:
                continue
            seen.add(url)
            
            # Check if internal
            parsed_url = urlparse(url)
            url_domain = parsed_url.netloc.lower().replace('www.', '')
            if url_domain != base_domain:
                continue
            
            # Classify and score
            classification = PageClassifier.classify(url)
            if classification['type'] == 'skip':
                continue
            
            priority = PageClassifier.get_priority_score(classification['type'])
            scored_urls.append((url, priority))
        
        # Sort by priority (descending) and take top URLs
        scored_urls.sort(key=lambda x: x[1], reverse=True)
        return [url for url, _ in scored_urls[:self.MAX_URLS]]
