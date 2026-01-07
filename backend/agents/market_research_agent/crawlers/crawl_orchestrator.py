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
    PAGE_TIMEOUT = 12  # seconds per page (reduced from 60s, optimized for office networks)
    CONNECT_TIMEOUT = 5  # seconds for initial connection (fail fast)
    TOTAL_TIMEOUT = 600  # seconds total (10 minutes, increased to match Go backend timeout)
    CONCURRENCY = 10  # parallel requests
    MAX_RETRIES = 1  # Maximum retries per page (like Rust implementation)
    
    # Minimum pages to crawl before allowing early exit
    # This ensures all Policy Details pages have a chance to be discovered
    MIN_PAGES_BEFORE_EXIT = 10
    
    # Required pages for early-exit (core compliance pages)
    REQUIRED_PAGES = {'privacy_policy', 'terms_conditions'}
    
    # High value pages - business-critical pages that should be crawled
    HIGH_VALUE_PAGES = {'about', 'contact', 'pricing', 'product', 'solutions', 'faq'}
    
    # All policy detail pages we want to discover (for Policy Details tab)
    POLICY_DETAIL_PAGES = {
        'home', 'privacy_policy', 'terms_conditions', 'about', 'contact',
        'faq', 'product', 'solutions', 'refund_policy', 'shipping_delivery'
    }
    
    USER_AGENT = 'Agent_X_CrawlOrchestrator/1.0'
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.robots_parser = RobotsTxtParser(logger=self.logger)
        self.sitemap_parser = SitemapParser(logger=self.logger)
        self.nav_discovery = NavigationDiscovery(logger=self.logger)
        self.cache = CrawlCache(logger=self.logger)
        self._session: Optional[aiohttp.ClientSession] = None
    
    def _create_optimized_session(self) -> aiohttp.ClientSession:
        """Create an optimized aiohttp session with connection pooling and DNS caching"""
        # Optimized connector for office networks
        # Use force_close=True to ensure connections close immediately on cleanup
        # This prevents hanging on process exit (performance impact is minimal)
        connector = aiohttp.TCPConnector(
            limit=100,  # Total connection pool size
            limit_per_host=20,  # Max connections per host
            ttl_dns_cache=300,  # DNS cache for 5 minutes (office network optimization)
            force_close=True,  # Force close connections immediately (prevents exit delay)
            enable_cleanup_closed=True,  # Clean up closed connections
        )
        
        # Optimized timeout configuration
        timeout = aiohttp.ClientTimeout(
            total=self.PAGE_TIMEOUT,
            connect=self.CONNECT_TIMEOUT,
            sock_read=self.PAGE_TIMEOUT
        )
        
        # Create session with optimized settings
        session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': self.USER_AGENT}
        )
        
        self.logger.debug(f"[HTTP_CLIENT] Created optimized session: limit=100, limit_per_host=20, dns_cache=300s, connect_timeout={self.CONNECT_TIMEOUT}s")
        return session
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create the shared HTTP session"""
        if self._session is None or self._session.closed:
            self._session = self._create_optimized_session()
            self.logger.info(f"[HTTP_CLIENT] Created new session (reuse=False)")
        else:
            self.logger.debug(f"[HTTP_CLIENT] Reusing existing session (reuse=True)")
        return self._session
    
    async def _close_session(self):
        """Close the HTTP session and connector to allow process to exit cleanly"""
        if self._session and not self._session.closed:
            try:
                # With force_close=True, connections should close immediately
                # Use a short timeout to prevent hanging
                await asyncio.wait_for(self._session.close(), timeout=2.0)
                self._session = None
                self.logger.debug("[HTTP_CLIENT] Session closed")
            except asyncio.TimeoutError:
                # If close times out, clear reference anyway to allow process exit
                self.logger.debug("[HTTP_CLIENT] Session close timed out, clearing reference")
                self._session = None
            except Exception as e:
                # Log but don't fail - we want to ensure process can exit
                self.logger.debug(f"[HTTP_CLIENT] Error closing session: {e}")
                self._session = None
    
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
        
        # Initialize tracking variables
        pages_attempted = 0
        
        try:
            # Use optimized shared session
            session = await self._get_session()
            
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
            
            pages_success = 0
            pages_failed = 0
            retry_count = 0
            timeout_count = 0
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
                    
                    # Check if page was skipped (blocked by robots.txt or early exit)
                    is_skipped = False
                    if page.error:
                        if page.error.type in ('blocked', 'skipped'):
                            is_skipped = True
                            page_graph.metadata.pages_skipped += 1
                        else:
                            page_graph.metadata.add_error(page.url, page.error)
                    
                    if is_skipped:
                        # Don't count skipped pages as fetched
                        self.logger.debug(f"[CRAWL] Page skipped: {urlparse(page.url).path} - {page.error.message if page.error else 'unknown'}")
                    else:
                        # Only count non-skipped pages as fetched
                        page_graph.metadata.pages_fetched += 1
                        if page.status == 200:
                            pages_success += 1
                            self.logger.info(f"[CRAWL] Page fetched: {urlparse(page.url).path} ({page.status})")
                        else:
                            pages_failed += 1
                            if page.error:
                                if 'retry' in page.error.message.lower():
                                    retry_count += 1
                                if 'timeout' in page.error.message.lower():
                                    timeout_count += 1
                    
                    page_graph.add_page(page)
                    
                    # Phase 9: Early-Exit Evaluation
                    # Only consider early exit after MIN_PAGES_BEFORE_EXIT to ensure policy pages are discovered
                    if page_graph.metadata.pages_fetched >= self.MIN_PAGES_BEFORE_EXIT:
                        if page_graph.has_required_pages():
                            # Also check if we have high-value pages
                            found_types = set(page_graph.get_found_page_types())
                            if self.HIGH_VALUE_PAGES & found_types:
                                page_graph.metadata.early_exit = True
                                page_graph.metadata.early_exit_reason = "All required + high-value pages found"
                                early_exit_triggered = True
                                early_exit_at_count = pages_attempted
                                required_pages_found = [pt for pt in self.REQUIRED_PAGES if page_graph.get_page_by_type(pt)]
                                high_value_found = [pt for pt in self.HIGH_VALUE_PAGES if page_graph.get_page_by_type(pt)]
                                self.logger.info(f"[SCAN][{scan_id_display}][EARLY_EXIT] Early exit triggered at crawl_count={early_exit_at_count} - required_pages_found={required_pages_found}, high_value_found={high_value_found}, reason={page_graph.metadata.early_exit_reason}")
                                self.logger.info(f"[CRAWL] Early exit: {page_graph.metadata.early_exit_reason}")
                                break
            
            if not early_exit_triggered:
                required_pages_found = [pt for pt in self.REQUIRED_PAGES if page_graph.get_page_by_type(pt)]
                self.logger.info(f"[SCAN][{scan_id_display}][EARLY_EXIT] Early exit not triggered - required_pages_found={required_pages_found}")
            
            if page_graph.metadata.pages_fetched >= self.MAX_PAGES:
                self.logger.info(f"[CRAWL] Page budget reached ({self.MAX_PAGES} pages)")
            
            crawl_exec_duration = time.monotonic() - crawl_exec_start_time
            self.logger.info(f"[SCAN][{scan_id_display}][CRAWL] Crawl execution completed in {crawl_exec_duration:.2f}s - attempted={pages_attempted}, success={pages_success}, failed={pages_failed}, retries={retry_count}, timeouts={timeout_count}")
            
            # Log HTTP connection reuse metrics
            if hasattr(session, 'connector') and session.connector:
                try:
                    # Log connector statistics if available
                    self.logger.debug(f"[HTTP_CLIENT] Session connector active: {not session.closed}")
                except Exception:
                    pass
            
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
        finally:
            # Close session to allow process to exit cleanly
            # This prevents hanging connections that delay process termination
            try:
                await self._close_session()
            except Exception as e:
                # Log but don't fail - we want to ensure process can exit
                self.logger.debug(f"[HTTP_CLIENT] Error closing session: {e}")
            
            # Cancel any remaining tasks to ensure clean event loop shutdown
            # This prevents the event loop from waiting for tasks that will never complete
            try:
                loop = asyncio.get_running_loop()
                # Get all tasks except the current one
                tasks = [t for t in asyncio.all_tasks(loop) if t != asyncio.current_task()]
                if tasks:
                    self.logger.debug(f"[HTTP_CLIENT] Cancelling {len(tasks)} pending tasks")
                    for task in tasks:
                        task.cancel()
                    # Wait briefly for cancellations, but don't block
                    await asyncio.gather(*tasks, return_exceptions=True)
            except Exception as e:
                # Ignore errors - we're just trying to clean up
                self.logger.debug(f"[HTTP_CLIENT] Error cancelling tasks: {e}")
        
            # Finalize
        crawl_time = time.time() - start_time
        total_crawl_duration = time.monotonic() - crawl_start_time
        page_graph.metadata.crawl_time_ms = int(crawl_time * 1000)
        
        # Calculate pages skipped (discovered but not fetched)
        # This includes:
        # 1. Pages skipped due to robots.txt blocking (already counted above)
        # 2. Pages skipped due to early exit (already counted above)
        # 3. Pages discovered but not attempted due to page budget
        total_discovered = page_graph.metadata.pages_discovered
        total_fetched = page_graph.metadata.pages_fetched
        # pages_attempted includes homepage (counted separately), so subtract 1
        pages_not_attempted = max(0, total_discovered - pages_attempted - 1)  # -1 for homepage
        page_graph.metadata.pages_skipped += pages_not_attempted
        
        # Set early exit reason if not already set
        if page_graph.metadata.early_exit and not page_graph.metadata.early_exit_reason:
            page_graph.metadata.early_exit_reason = "All required pages found"
        elif not page_graph.metadata.early_exit and page_graph.metadata.pages_fetched >= self.MAX_PAGES:
            page_graph.metadata.early_exit = True
            page_graph.metadata.early_exit_reason = f"Page budget limit reached ({self.MAX_PAGES} pages)"
        elif not page_graph.metadata.early_exit and pages_not_attempted > 0:
            # Some pages were discovered but not attempted due to budget
            page_graph.metadata.early_exit = True
            page_graph.metadata.early_exit_reason = f"Page budget limit reached ({self.MAX_PAGES} pages), {pages_not_attempted} pages not attempted"
        
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
        """Fetch a single page with retry logic and optimized timeouts"""
        
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
        
        # Retry logic with exponential backoff (like Rust implementation)
        retries = 0
        initial_backoff_ms = 2000  # 2 seconds initial backoff
        backoff_ms = initial_backoff_ms
        
        while retries <= self.MAX_RETRIES:
            try:
                # Use session's configured timeout (already optimized)
                async with session.get(
                    url,
                    allow_redirects=True
                ) as response:
                    content_type = response.headers.get('Content-Type', '')
                    status_code = response.status
                    
                    # Don't retry on 4xx errors (client errors)
                    if 400 <= status_code < 500:
                        if status_code == 410:
                            # HTTP 410 Gone - don't retry
                            return PageData(
                                url=url,
                                final_url=str(response.url),
                                status=status_code,
                                content_type=content_type,
                                html='',
                                source=source,
                                page_type='other',
                                classification_confidence=0.0,
                                depth=depth,
                                error=CrawlError(type='http_error', message=f'HTTP {status_code} Gone', status_code=status_code)
                            )
                        # Other 4xx errors - return immediately without retry
                        html = await response.text() if 'text/html' in content_type.lower() else ''
                        return PageData(
                            url=url,
                            final_url=str(response.url),
                            status=status_code,
                            content_type=content_type,
                            html=html,
                            source=source,
                            page_type='other',
                            classification_confidence=0.0,
                            depth=depth,
                            error=CrawlError(type='http_error', message=f'HTTP {status_code}', status_code=status_code)
                        )
                    
                    # Retry on 5xx errors if retries remaining
                    if 500 <= status_code < 600:
                        # Read response body to avoid connection leaks
                        try:
                            await response.read()
                        except Exception:
                            pass
                        
                        if retries < self.MAX_RETRIES:
                            retries += 1
                            self.logger.debug(f"[CRAWL] Server error {status_code} for {url}, retrying ({retries}/{self.MAX_RETRIES})")
                            await asyncio.sleep(backoff_ms / 1000.0)
                            backoff_ms *= 2
                            continue
                        else:
                            # Max retries reached
                            return PageData(
                                url=url,
                                final_url=str(response.url),
                                status=status_code,
                                content_type=content_type,
                                html='',
                                source=source,
                                page_type='other',
                                classification_confidence=0.0,
                                depth=depth,
                                error=CrawlError(type='http_error', message=f'HTTP {status_code} after {self.MAX_RETRIES} retries', status_code=status_code)
                            )
                    
                    # Only process HTML
                    if 'text/html' not in content_type.lower():
                        return PageData(
                            url=url,
                            final_url=str(response.url),
                            status=status_code,
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
                        status=status_code,
                        content_type=content_type,
                        html=html,
                        source=source,
                        page_type=classification['type'],
                        classification_confidence=classification['confidence'],
                        depth=depth,
                        error=None if status_code < 400 else CrawlError.from_exception(Exception(f"HTTP {status_code}"), status_code)
                    )
                    
                    # Update Cache
                    if page_data.status == 200:
                        try:
                            await asyncio.to_thread(self.cache.set, page_data)
                        except Exception as e:
                            self.logger.warning(f"[CACHE] Failed to set cache: {e}")
                    
                    return page_data
                    
            except asyncio.TimeoutError:
                if retries < self.MAX_RETRIES:
                    retries += 1
                    self.logger.debug(f"[CRAWL] Timeout for {url}, retrying ({retries}/{self.MAX_RETRIES})")
                    await asyncio.sleep(backoff_ms / 1000.0)
                    backoff_ms *= 2
                    continue
                else:
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
                        error=CrawlError(type='timeout', message=f'Page timeout ({self.PAGE_TIMEOUT}s) after {self.MAX_RETRIES} retries')
                    )
            except aiohttp.ClientError as e:
                if retries < self.MAX_RETRIES:
                    retries += 1
                    self.logger.debug(f"[CRAWL] Client error for {url}, retrying ({retries}/{self.MAX_RETRIES}): {e}")
                    await asyncio.sleep(backoff_ms / 1000.0)
                    backoff_ms *= 2
                    continue
                else:
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
                if retries < self.MAX_RETRIES:
                    retries += 1
                    self.logger.debug(f"[CRAWL] Error for {url}, retrying ({retries}/{self.MAX_RETRIES}): {e}")
                    await asyncio.sleep(backoff_ms / 1000.0)
                    backoff_ms *= 2
                    continue
                else:
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
        
        # Should not reach here, but return error if we do
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
            error=CrawlError(type='unknown', message='Max retries exceeded')
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
