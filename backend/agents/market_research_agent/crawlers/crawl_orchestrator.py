"""
Crawl Orchestrator Module
Main entry point for parallel website crawling
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse, urljoin

import aiohttp
from bs4 import BeautifulSoup

from .page_graph import NormalizedPageGraph, PageData, CrawlError, CrawlMetadata
from .url_utils import URLNormalizer, PageClassifier
from .robots_parser import RobotsTxtParser, RobotsRules
from .sitemap_parser import SitemapParser
from .navigation_discovery import NavigationDiscovery
from .crawl_cache import CrawlCache


class CrawlOrchestrator:
    """
    Orchestrates parallel website crawling with intelligent discovery.
    
    Features:
    - robots.txt checking
    - Sitemap discovery and parsing
    - Navigation link extraction (primary + fallback)
    - Parallel page fetching with aiohttp
    - Page budget enforcement with early-exit
    - Timeout handling
    """
    
    # Hard limits from PRD
    MAX_PAGES = 20
    MAX_DEPTH = 2
    PAGE_TIMEOUT = 3  # seconds per page
    TOTAL_TIMEOUT = 10  # seconds total
    CONCURRENCY = 10  # parallel requests
    
    # Required pages for early-exit
    REQUIRED_PAGES = {'privacy_policy', 'terms_conditions'}
    HIGH_VALUE_PAGES = {'about', 'contact', 'pricing', 'product'}
    
    USER_AGENT = 'Agent_X_CrawlOrchestrator/1.0'
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.robots_parser = RobotsTxtParser(logger=self.logger)
        self.sitemap_parser = SitemapParser(logger=self.logger)
        self.nav_discovery = NavigationDiscovery(logger=self.logger)
        self.cache = CrawlCache(logger=self.logger)
    
    async def crawl(self, url: str) -> NormalizedPageGraph:
        """
        Main entry point - crawl a website and return normalized page graph.
        
        Args:
            url: URL to crawl
            
        Returns:
            NormalizedPageGraph with all crawled pages
        """
        start_time = time.time()
        
        # Clean and normalize URL
        url = self._clean_url(url)
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        base_domain = parsed.netloc.lower().replace('www.', '')
        
        self.logger.info(f"[CRAWL] Starting crawl for: {url}")
        
        # Initialize page graph
        page_graph = NormalizedPageGraph(root_url=url)
        
        # Track URLs to fetch
        urls_to_fetch: List[Tuple[str, str, int]] = []  # (url, source, depth)
        fetched_urls: Set[str] = set()
        
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.TOTAL_TIMEOUT),
                headers={'User-Agent': self.USER_AGENT}
            ) as session:
                
                # Phase 1: Check robots.txt
                self.logger.info("[CRAWL] Checking robots.txt...")
                robots_rules = await self.robots_parser.fetch_and_parse(base_url, session)
                page_graph.metadata.robots_checked = True
                
                # Phase 2: Fetch homepage
                self.logger.info("[CRAWL] Fetching homepage...")
                home_page = await self._fetch_page(url, session, 'root', 0, robots_rules)
                
                if home_page.error:
                    self.logger.error(f"[CRAWL] Homepage fetch failed: {home_page.error.message}")
                    page_graph.metadata.add_error(url, home_page.error)
                    # Still add to graph even if failed
                    home_page.page_type = 'home'
                    home_page.classification_confidence = 1.0
                    page_graph.add_page(home_page)
                    page_graph.metadata.crawl_time_ms = int((time.time() - start_time) * 1000)
                    return page_graph
                
                # Add homepage to graph
                home_page.page_type = 'home'
                home_page.classification_confidence = 1.0
                page_graph.add_page(home_page)
                page_graph.metadata.pages_fetched = 1
                fetched_urls.add(URLNormalizer.normalize(url))
                self.logger.info(f"[CRAWL] Page fetched: / (200)")
                
                # Parse homepage
                home_soup = home_page.get_soup()
                if not home_soup:
                    self.logger.warning("[CRAWL] Failed to parse homepage HTML")
                    page_graph.metadata.crawl_time_ms = int((time.time() - start_time) * 1000)
                    return page_graph
                
                # Phase 3: Discover URLs from sitemap
                self.logger.info("[CRAWL] Discovering sitemap...")
                sitemap_urls, sitemap_found = await self.sitemap_parser.discover_and_parse(
                    base_url,
                    homepage_html=home_page.html,
                    robots_sitemaps=robots_rules.sitemaps if robots_rules.found else None,
                    session=session
                )
                page_graph.metadata.sitemap_found = sitemap_found
                page_graph.metadata.sitemap_urls_count = len(sitemap_urls)
                
                if sitemap_found:
                    self.logger.info(f"[CRAWL] Sitemap found ({len(sitemap_urls)} URLs)")
                
                # Phase 4: Discover navigation links
                nav_links = self.nav_discovery.extract_primary(home_soup, url)
                
                # If no sitemap, use secondary nav as fallback
                if not sitemap_found:
                    self.logger.info("[CRAWL] No sitemap, using secondary navigation")
                    seen_urls = {link['normalized_url'] for link in nav_links}
                    secondary = self.nav_discovery.extract_secondary(home_soup, url, seen_urls)
                    nav_links = self.nav_discovery.merge_and_dedupe(nav_links, secondary)
                
                # Phase 5: Build fetch queue
                # Priority order: sitemap URLs > nav links (already sorted by priority)
                
                # Add sitemap URLs
                for sitemap_url in sitemap_urls:
                    normalized = URLNormalizer.normalize(sitemap_url)
                    if normalized not in fetched_urls:
                        classification = PageClassifier.classify(sitemap_url)
                        if classification['type'] != 'skip':
                            urls_to_fetch.append((sitemap_url, 'sitemap', 1))
                            fetched_urls.add(normalized)
                
                # Add nav links
                for nav_link in nav_links:
                    normalized = nav_link['normalized_url']
                    if normalized not in fetched_urls:
                        source = 'nav_primary' if nav_link['source'] in ('nav', 'header', 'footer') else 'nav_secondary'
                        urls_to_fetch.append((nav_link['url'], source, 1))
                        fetched_urls.add(normalized)
                
                page_graph.metadata.pages_discovered = len(urls_to_fetch) + 1
                self.logger.info(f"[CRAWL] {len(urls_to_fetch)} URLs queued for fetching")
                
                # Phase 6: Parallel fetch with early-exit
                pages_to_fetch = min(self.MAX_PAGES - 1, len(urls_to_fetch))  # -1 for homepage
                
                if pages_to_fetch > 0:
                    fetched_pages = await self._fetch_pages_parallel(
                        urls_to_fetch[:pages_to_fetch],
                        session,
                        robots_rules,
                        page_graph
                    )
                    
                    for page in fetched_pages:
                        if page.status == 200:
                            self.logger.info(f"[CRAWL] Page fetched: {urlparse(page.url).path} ({page.status})")
                        page_graph.add_page(page)
                        page_graph.metadata.pages_fetched += 1
                        
                        if page.error:
                            page_graph.metadata.add_error(page.url, page.error)
                        
                        # Check early-exit condition
                        if page_graph.has_required_pages():
                            # Also check if we have high-value pages
                            found_types = set(page_graph.get_found_page_types())
                            if self.HIGH_VALUE_PAGES & found_types:
                                page_graph.metadata.early_exit = True
                                page_graph.metadata.early_exit_reason = "All required + high-value pages found"
                                self.logger.info(f"[CRAWL] Early exit: {page_graph.metadata.early_exit_reason}")
                                break
                
                if page_graph.metadata.pages_fetched >= self.MAX_PAGES:
                    self.logger.info(f"[CRAWL] Page budget reached ({self.MAX_PAGES} pages)")
                
        except asyncio.TimeoutError:
            self.logger.warning(f"[CRAWL] Total timeout exceeded ({self.TOTAL_TIMEOUT}s)")
        except Exception as e:
            self.logger.error(f"[CRAWL] Crawl error: {e}")
        
        # Finalize
        crawl_time = time.time() - start_time
        page_graph.metadata.crawl_time_ms = int(crawl_time * 1000)
        
        self.logger.info(f"[CRAWL] Crawl completed in {crawl_time:.2f}s - {page_graph.metadata.pages_fetched} pages")
        
        return page_graph
    
    async def _fetch_page(
        self,
        url: str,
        session: aiohttp.ClientSession,
        source: str,
        depth: int,
        robots_rules: RobotsRules
    ) -> PageData:
        """Fetch a single page"""
        
        # Check robots.txt
        if robots_rules.found:
            parsed = urlparse(url)
            if not robots_rules.is_allowed(parsed.path):
                return PageData(
                    url=url,
                    final_url=url,
                    status=0,
                    content_type='',
                    html='',
                    source=source,
                    page_type='other',
                    classification_confidence=0.0,
                    depth=depth,
                    error=CrawlError(type='blocked', message='Blocked by robots.txt')
                )
        
        # Check Cache
        try:
            cached_page = await asyncio.to_thread(self.cache.get, url)
            if cached_page:
                self.logger.info(f"[CACHE] HIT for {url}")
                cached_page.source = "cache"
                return cached_page
            else:
                self.logger.info(f"[CACHE] MISS for {url}")
        except Exception as e:
            self.logger.warning(f"[CACHE] Error checking cache: {e}")
        
        try:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=self.PAGE_TIMEOUT),
                allow_redirects=True
            ) as response:
                content_type = response.headers.get('Content-Type', '')
                
                # Only process HTML
                if 'text/html' not in content_type.lower():
                    return PageData(
                        url=url,
                        final_url=str(response.url),
                        status=response.status,
                        content_type=content_type,
                        html='',
                        source=source,
                        page_type='other',
                        classification_confidence=0.0,
                        depth=depth
                    )
                
                html = await response.text()
                final_url = str(response.url)
                
                # Parse and extract canonical
                soup = BeautifulSoup(html, 'html.parser')
                canonical = URLNormalizer.extract_canonical(soup, final_url)
                
                # Classify page
                title = ''
                title_tag = soup.find('title')
                if title_tag:
                    title = title_tag.get_text(strip=True)
                
                classification = PageClassifier.classify(url, '', title)
                
                page_data = PageData(
                    url=url,
                    final_url=final_url,
                    canonical_url=canonical,
                    status=response.status,
                    content_type=content_type,
                    html=html,
                    source=source,
                    page_type=classification['type'],
                    classification_confidence=classification['confidence'],
                    depth=depth,
                    error=CrawlError.from_exception(Exception(f"HTTP {response.status}"), response.status) if response.status >= 400 else None
                )
                
                # Update Cache
                if page_data.status == 200:
                    try:
                        await asyncio.to_thread(self.cache.set, page_data)
                    except Exception as e:
                        self.logger.warning(f"[CACHE] Failed to set cache: {e}")
                
                return page_data
                
        except asyncio.TimeoutError:
            return PageData(
                url=url,
                final_url=url,
                status=0,
                content_type='',
                html='',
                source=source,
                page_type='other',
                classification_confidence=0.0,
                depth=depth,
                error=CrawlError(type='timeout', message=f'Page timeout ({self.PAGE_TIMEOUT}s)')
            )
        except aiohttp.ClientError as e:
            return PageData(
                url=url,
                final_url=url,
                status=0,
                content_type='',
                html='',
                source=source,
                page_type='other',
                classification_confidence=0.0,
                depth=depth,
                error=CrawlError.from_exception(e)
            )
        except Exception as e:
            return PageData(
                url=url,
                final_url=url,
                status=0,
                content_type='',
                html='',
                source=source,
                page_type='other',
                classification_confidence=0.0,
                depth=depth,
                error=CrawlError.from_exception(e)
            )
    
    async def _fetch_pages_parallel(
        self,
        urls: List[Tuple[str, str, int]],
        session: aiohttp.ClientSession,
        robots_rules: RobotsRules,
        page_graph: NormalizedPageGraph
    ) -> List[PageData]:
        """Fetch multiple pages in parallel with concurrency control"""
        
        semaphore = asyncio.Semaphore(self.CONCURRENCY)
        
        async def fetch_with_semaphore(url: str, source: str, depth: int) -> PageData:
            async with semaphore:
                # Check for early exit before fetching
                if page_graph.metadata.early_exit:
                    return PageData(
                        url=url,
                        final_url=url,
                        status=0,
                        content_type='',
                        html='',
                        source=source,
                        page_type='other',
                        classification_confidence=0.0,
                        depth=depth,
                        error=CrawlError(type='skipped', message='Early exit triggered')
                    )
                return await self._fetch_page(url, session, source, depth, robots_rules)
        
        tasks = [
            fetch_with_semaphore(url, source, depth)
            for url, source, depth in urls
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        pages: List[PageData] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                url, source, depth = urls[i]
                pages.append(PageData(
                    url=url,
                    final_url=url,
                    status=0,
                    content_type='',
                    html='',
                    source=source,
                    page_type='other',
                    classification_confidence=0.0,
                    depth=depth,
                    error=CrawlError.from_exception(result)
                ))
            else:
                pages.append(result)
        
        return pages
    
    def _clean_url(self, url: str) -> str:
        """Clean and normalize URL input"""
        import re
        
        cleaned_url = url.strip()
        
        # Remove "url:" prefix if present
        if re.match(r'^url:\s*', cleaned_url, re.IGNORECASE):
            cleaned_url = re.sub(r'^url:\s*', '', cleaned_url, flags=re.IGNORECASE)
        
        # Handle comma-separated arguments
        if ',' in cleaned_url and ('http://' in cleaned_url or 'https://' in cleaned_url):
            cleaned_url = cleaned_url.split(',')[0].strip()
        
        # Ensure scheme
        if not cleaned_url.startswith(('http://', 'https://')):
            cleaned_url = 'https://' + cleaned_url
        
        return cleaned_url


# Synchronous wrapper for compatibility
def crawl_sync(url: str, logger: Optional[logging.Logger] = None) -> NormalizedPageGraph:
    """
    Synchronous wrapper for CrawlOrchestrator.
    Use this from non-async code.
    """
    orchestrator = CrawlOrchestrator(logger=logger)
    return asyncio.run(orchestrator.crawl(url))
