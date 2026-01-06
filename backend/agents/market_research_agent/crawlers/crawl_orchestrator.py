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
    
    async def crawl(self, url: str, scan_id: str = None) -> NormalizedPageGraph:
        """
        Main entry point - crawl a website and return normalized page graph.
        
        Args:
            url: URL to crawl
            scan_id: Scan ID for logging (optional)
            
        Returns:
            NormalizedPageGraph with all crawled pages
        """
        crawl_start_time = time.monotonic()
        start_time = time.time()
        scan_id_display = scan_id if scan_id else "unknown"
        
        # Phase 2: Seed URL Resolution
        seed_start_time = time.monotonic()
        self.logger.info(f"[SCAN][{scan_id_display}][SEED] Seed URL resolution started")
        
        # Clean and normalize URL
        original_url = url
        url = self._clean_url(url)
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        base_domain = parsed.netloc.lower().replace('www.', '')
        
        seed_duration = time.monotonic() - seed_start_time
        redirects_followed = "none" if original_url == url else f"original={original_url}, final={url}"
        self.logger.info(f"[SCAN][{scan_id_display}][SEED] Seed URL resolved in {seed_duration:.2f}s - canonicalized_url={url}, redirects={redirects_followed}")
        
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
                
                # Phase 3: Robots.txt Fetch
                robots_start_time = time.monotonic()
                robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
                self.logger.info(f"[SCAN][{scan_id_display}][ROBOTS] Fetching robots.txt from {robots_url}")
                self.logger.info("[CRAWL] Checking robots.txt...")
                robots_rules = await self.robots_parser.fetch_and_parse(base_url, session)
                page_graph.metadata.robots_checked = True
                robots_duration = time.monotonic() - robots_start_time
                robots_status = "found" if robots_rules.found else "not_found"
                self.logger.info(f"[SCAN][{scan_id_display}][ROBOTS] Robots.txt fetch completed in {robots_duration:.2f}s - status={robots_status}")
                
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
                
                # Phase 4: Sitemap Discovery
                sitemap_start_time = time.monotonic()
                self.logger.info(f"[SCAN][{scan_id_display}][SITEMAP] Sitemap discovery started")
                self.logger.info("[CRAWL] Discovering sitemap...")
                sitemap_urls, sitemap_found = await self.sitemap_parser.discover_and_parse(
                    base_url,
                    homepage_html=home_page.html,
                    robots_sitemaps=robots_rules.sitemaps if robots_rules.found else None,
                    session=session
                )
                page_graph.metadata.sitemap_found = sitemap_found
                page_graph.metadata.sitemap_urls_count = len(sitemap_urls)
                sitemap_duration = time.monotonic() - sitemap_start_time
                sitemap_urls_list = robots_rules.sitemaps[:3] if robots_rules.found and robots_rules.sitemaps else []
                self.logger.info(f"[SCAN][{scan_id_display}][SITEMAP] Sitemap discovery completed in {sitemap_duration:.2f}s - found={sitemap_found}, urls_extracted={len(sitemap_urls)}, sitemap_urls={sitemap_urls_list}")
                
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
                
                # Phase 5: URL Normalization & Filtering
                normalization_start_time = time.monotonic()
                self.logger.info(f"[SCAN][{scan_id_display}][NORMALIZE] URL normalization and filtering started")
                
                # Phase 6: Build fetch queue
                # Priority order: sitemap URLs > nav links (already sorted by priority)
                
                urls_before_normalization = len(sitemap_urls) + len(nav_links)
                filtered_duplicates = 0
                filtered_assets = 0
                filtered_patterns = 0
                
                # Add sitemap URLs
                for sitemap_url in sitemap_urls:
                    normalized = URLNormalizer.normalize(sitemap_url)
                    if normalized in fetched_urls:
                        filtered_duplicates += 1
                        continue
                    classification = PageClassifier.classify(sitemap_url)
                    if classification['type'] == 'skip':
                        filtered_patterns += 1
                        continue
                    urls_to_fetch.append((sitemap_url, 'sitemap', 1))
                    fetched_urls.add(normalized)
                
                # Add nav links
                for nav_link in nav_links:
                    normalized = nav_link['normalized_url']
                    if normalized in fetched_urls:
                        filtered_duplicates += 1
                        continue
                    source = 'nav_primary' if nav_link['source'] in ('nav', 'header', 'footer') else 'nav_secondary'
                    urls_to_fetch.append((nav_link['url'], source, 1))
                    fetched_urls.add(normalized)
                
                normalization_duration = time.monotonic() - normalization_start_time
                urls_after_normalization = len(urls_to_fetch)
                total_filtered = filtered_duplicates + filtered_assets + filtered_patterns
                self.logger.info(f"[SCAN][{scan_id_display}][NORMALIZE] URL normalization completed in {normalization_duration:.2f}s - before={urls_before_normalization}, after={urls_after_normalization}, filtered={total_filtered} (duplicates={filtered_duplicates}, assets={filtered_assets}, patterns={filtered_patterns})")
                
                # Phase 6: Crawl Queue Construction
                queue_start_time = time.monotonic()
                self.logger.info(f"[SCAN][{scan_id_display}][QUEUE] Crawl queue construction started")
                
                page_graph.metadata.pages_discovered = len(urls_to_fetch) + 1
                
                # Count URLs by priority
                required_count = 0
                high_value_count = 0
                low_value_count = 0
                for url_tuple in urls_to_fetch:
                    url, source, depth = url_tuple
                    classification = PageClassifier.classify(url)
                    page_type = classification['type']
                    if page_type in self.REQUIRED_PAGES:
                        required_count += 1
                    elif page_type in self.HIGH_VALUE_PAGES:
                        high_value_count += 1
                    else:
                        low_value_count += 1
                
                max_pages_applied = min(self.MAX_PAGES - 1, len(urls_to_fetch))
                queue_duration = time.monotonic() - queue_start_time
                self.logger.info(f"[SCAN][{scan_id_display}][QUEUE] Crawl queue constructed in {queue_duration:.2f}s - total_queued={len(urls_to_fetch)}, priority_breakdown=required={required_count}, high={high_value_count}, low={low_value_count}, max_pages_limit={self.MAX_PAGES}, pages_to_fetch={max_pages_applied}")
                
                self.logger.info(f"[CRAWL] {len(urls_to_fetch)} URLs queued for fetching")
                
                # Phase 7: Crawl Execution
                crawl_exec_start_time = time.monotonic()
                pages_to_fetch = min(self.MAX_PAGES - 1, len(urls_to_fetch))  # -1 for homepage
                
                self.logger.info(f"[SCAN][{scan_id_display}][CRAWL] Crawl execution started - pages_to_attempt={pages_to_fetch}")
                
                pages_attempted = 0
                pages_success = 0
                pages_failed = 0
                retry_count = 0
                early_exit_triggered = False
                early_exit_at_count = 0
                
                if pages_to_fetch > 0:
                    fetched_pages = await self._fetch_pages_parallel(
                        urls_to_fetch[:pages_to_fetch],
                        session,
                        robots_rules,
                        page_graph,
                        scan_id=scan_id
                    )
                    
                    for page in fetched_pages:
                        pages_attempted += 1
                        if page.status == 200:
                            pages_success += 1
                            self.logger.info(f"[CRAWL] Page fetched: {urlparse(page.url).path} ({page.status})")
                        else:
                            pages_failed += 1
                            if page.error and 'retry' in page.error.message.lower():
                                retry_count += 1
                        
                        page_graph.add_page(page)
                        page_graph.metadata.pages_fetched += 1
                        
                        if page.error:
                            page_graph.metadata.add_error(page.url, page.error)
                        
                        # Phase 9: Early-Exit Evaluation
                        if page_graph.has_required_pages():
                            # Also check if we have high-value pages
                            found_types = set(page_graph.get_found_page_types())
                            if self.HIGH_VALUE_PAGES & found_types:
                                page_graph.metadata.early_exit = True
                                page_graph.metadata.early_exit_reason = "All required + high-value pages found"
                                early_exit_triggered = True
                                early_exit_at_count = pages_attempted
                                required_pages_found = [pt for pt in self.REQUIRED_PAGES if page_graph.get_page_by_type(pt)]
                                self.logger.info(f"[SCAN][{scan_id_display}][EARLY_EXIT] Early exit triggered at crawl_count={early_exit_at_count} - required_pages_found={required_pages_found}, reason={page_graph.metadata.early_exit_reason}")
                                self.logger.info(f"[CRAWL] Early exit: {page_graph.metadata.early_exit_reason}")
                                break
                
                if not early_exit_triggered:
                    required_pages_found = [pt for pt in self.REQUIRED_PAGES if page_graph.get_page_by_type(pt)]
                    self.logger.info(f"[SCAN][{scan_id_display}][EARLY_EXIT] Early exit not triggered - required_pages_found={required_pages_found}")
                
                if page_graph.metadata.pages_fetched >= self.MAX_PAGES:
                    self.logger.info(f"[CRAWL] Page budget reached ({self.MAX_PAGES} pages)")
                
                crawl_exec_duration = time.monotonic() - crawl_exec_start_time
                self.logger.info(f"[SCAN][{scan_id_display}][CRAWL] Crawl execution completed in {crawl_exec_duration:.2f}s - attempted={pages_attempted}, success={pages_success}, failed={pages_failed}, retries={retry_count}")
                
                # Phase 8: Page Classification
                classification_start_time = time.monotonic()
                self.logger.info(f"[SCAN][{scan_id_display}][CLASSIFY] Page classification started")
                
                page_type_counts = {}
                for page_type, page in page_graph.pages.items():
                    if isinstance(page, PageData) and page.status == 200:
                        pt = page.page_type
                        page_type_counts[pt] = page_type_counts.get(pt, 0) + 1
                
                classification_duration = time.monotonic() - classification_start_time
                type_summary = ", ".join([f"{pt}={count}" for pt, count in sorted(page_type_counts.items())])
                self.logger.info(f"[SCAN][{scan_id_display}][CLASSIFY] Page classification completed in {classification_duration:.2f}s - counts={type_summary}")
                
        except asyncio.TimeoutError:
            self.logger.warning(f"[SCAN][{scan_id_display}][CRAWL] Total timeout exceeded ({self.TOTAL_TIMEOUT}s)")
            self.logger.warning(f"[CRAWL] Total timeout exceeded ({self.TOTAL_TIMEOUT}s)")
        except Exception as e:
            self.logger.error(f"[SCAN][{scan_id_display}][CRAWL] Crawl error: {e}")
            self.logger.error(f"[CRAWL] Crawl error: {e}")
        
        # Finalize
        crawl_time = time.time() - start_time
        total_crawl_duration = time.monotonic() - crawl_start_time
        page_graph.metadata.crawl_time_ms = int(crawl_time * 1000)
        
        self.logger.info(f"[SCAN][{scan_id_display}][CRAWL] Total crawl duration: {total_crawl_duration:.2f}s")
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
        page_graph: NormalizedPageGraph,
        scan_id: str = None
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
