"""
Modular Scan Engine V2
Production-ready comprehensive site scan using modular architecture
Now with CrawlOrchestrator for parallel page discovery
"""

import os
import json
import ssl
import socket
import requests
import asyncio
import uuid
import time
import threading
from datetime import datetime
from urllib.parse import urlparse
from typing import List
import re
import logging

# Import modular components (absolute imports)
from scanners.site_crawler import SiteCrawler
from scanners.policy_detector import PolicyDetector
from scanners.tech_detector import TechDetector
from extractors.links import LinkExtractor
from extractors.metadata import MetadataExtractor
from analyzers.content_analyzer import ContentAnalyzer
from analyzers.seo_analyzer import SEOAnalyzer
from analyzers.change_detector import ChangeDetector
from analyzers.change_intelligence import ChangeIntelligenceEngine
from analyzers.compliance_intelligence import ComplianceIntelligence
from analyzers.context_classifier import BusinessContextClassifier
from reports.site_scan_report import SiteScanReportBuilder

# Import new Crawl Orchestrator
from crawlers.crawl_orchestrator import CrawlOrchestrator
from crawlers.page_graph import NormalizedPageGraph



class ModularScanEngine:
    """V2 Scan Engine using modular architecture with CrawlOrchestrator"""
    
    VERSION = "v2.1.1"  # Per PRD V2.1.1 - Accuracy & Trust Hardening
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.orchestrator = CrawlOrchestrator(logger=self.logger)
        self.change_detector = ChangeDetector(logger=self.logger)
        self.intelligence_engine = ChangeIntelligenceEngine(logger=self.logger)
        self.compliance_engine = ComplianceIntelligence(logger=self.logger)
        self.context_classifier = BusinessContextClassifier(logger=self.logger)
    
    def comprehensive_site_scan(self, url: str, business_name: str = "", task_id: str = None) -> str:
        """
        Comprehensive website scan using modular components
        
        Args:
            url: Website URL to scan
            business_name: Business/Billing name (optional)
            task_id: Task ID for scan tracking (optional)
            
        Returns:
            JSON string with comprehensive scan results
        """
        # Generate scan_id from task_id or create UUID
        scan_id = task_id if task_id else str(uuid.uuid4())[:8]
        scan_start_time = time.monotonic()
        scan_start_timestamp = datetime.now().isoformat()
        
        try:
            # Phase 1: Scan Start
            self.logger.info(f"[SCAN][{scan_id}][START] Scan started - root_url={url}, timestamp={scan_start_timestamp}")
            
            # Clean URL input
            cleaned_url = self._clean_url(url)
            url = cleaned_url
            
            self.logger.info(f"[V2.1] Starting comprehensive scan for: {url}")
            
            # Initialize report builder
            report_builder = SiteScanReportBuilder()
            report_builder.initialize_report(url, business_name)
            
            parsed_url = urlparse(url)
            domain = parsed_url.netloc or parsed_url.path
            
            # Initialize compliance data
            compliance_data = {
                "general": {
                    "pass": True,
                    "alerts": [],
                    "actions_needed": []
                },
                "payment_terms": {
                    "pass": False,
                    "alerts": [],
                    "actions_needed": []
                }
            }
            
            # Use CrawlOrchestrator for parallel page discovery
            self.logger.info("[V2.1] Running CrawlOrchestrator...")
            
            crawl_start_time = time.monotonic()
            # Run crawl in async context
            # Use asyncio.run() which creates a new event loop and ensures it's closed after completion
            page_graph = asyncio.run(self.orchestrator.crawl(url, scan_id=scan_id))
            # After asyncio.run() completes, the event loop is automatically closed
            # This ensures no hanging async resources prevent process exit
            crawl_duration = time.monotonic() - crawl_start_time
            
            # Phase 10: Post-Crawl Analysis Start
            post_crawl_start_time = time.monotonic()
            self.logger.info(f"[SCAN][{scan_id}][POST_CRAWL] Post-crawl analysis started")
            
            # Change Detection: Fetch previous snapshot (before processing logic if we wanted, but we leverage page graph content hash)
            # We can construct a partial current snapshot object for comparison 
            # OR we defer comparison until we have full derived signals at the end.
            # Comparison happens best at the end.
            previous_snapshot = self.change_detector.get_previous_snapshot(url)
            
            # Check crawl success
            home_page = page_graph.get_page_by_type('home')
            scan_success = False
            scan_status = {
                "status": "SUCCESS",
                "reason": "OK",
                "message": "Scan completed successfully",
                "target_url": url, # For frontend redirect
                "retryable": False
            }

            if not home_page:
                scan_status["status"] = "FAILED"
                scan_status["reason"] = "DNS_FAIL"
                scan_status["message"] = "Could not resolve domain or connect to host."
                scan_status["retryable"] = True
            elif home_page.status != 200:
                scan_status["status"] = "FAILED"
                scan_status["target_url"] = home_page.final_url or url
                if home_page.status in [403, 401]:
                    scan_status["reason"] = "HTTP_403"
                    scan_status["message"] = f"Access denied ({home_page.status}). The site blocked the scan."
                    scan_status["retryable"] = False
                elif home_page.status == 0: # Timeout or cert error usually
                     if "SSL" in str(home_page.error):
                         scan_status["reason"] = "SSL_ERROR"
                         scan_status["message"] = "SSL Certificate handshake failed."
                     else:
                         scan_status["reason"] = "TIMEOUT"
                         scan_status["message"] = "Connection timed out."
                     scan_status["retryable"] = True
                else:
                    scan_status["reason"] = f"HTTP_{home_page.status}"
                    scan_status["message"] = f"Website returned error status {home_page.status}"
                    scan_status["retryable"] = True
            elif len(page_graph.pages) <= 1:
                 # Single page might be okay, but let's check
                 scan_success = True
            else:
                 scan_success = True
            
            # Gating Logic
            if scan_status["status"] != "SUCCESS":
                 self.logger.warning(f"[V2.1] Scan Failed: {scan_status['reason']}")
                 
                 # Still fetch RDAP data even for failed crawls - it doesn't depend on website content
                 rdap_details = {}
                 try:
                     self.logger.info(f"[V2.1] Fetching RDAP for failed crawl: {domain}")
                     compliance_data_temp = {"general": {"pass": True, "alerts": []}}
                     rdap_details = self._check_domain_age(domain, compliance_data_temp)
                     self.logger.info(f"[V2.1] RDAP fetched successfully for {domain}")
                 except Exception as e:
                     self.logger.warning(f"[V2.1] RDAP fetch failed: {e}")
                     rdap_details = {"error": str(e)}
                 
                 # Return limited report with RDAP data
                 crawl_summary = page_graph.get_crawl_summary()
                 
                 final_report = {
                     "comprehensive_site_scan": {
                            "scan_status": scan_status,
                            "url": url,
                            "final_url": scan_status.get("target_url", url),
                            "timestamp": datetime.now().isoformat(),
                            "crawl_metadata": {
                                "pages_scanned": len(page_graph.pages),
                                "duration": 0
                            },
                            "crawl_summary": crawl_summary,
                            "rdap": rdap_details,  # Include RDAP even for failed crawls
                             # Empty placeholders to prevent frontend crashes if it ignores status check (backstop)
                            "compliance_intelligence": None, 
                            "business_context": None
                     }
                 }
                 return json.dumps(final_report, indent=2)

            # --- Proceed with Success Flow ---
            
            # Convert to legacy format for backward compatibility
            crawler = SiteCrawler()  # Keep for parse_html compatibility
            if home_page and home_page.status == 200:
                page_data = {
                    'success': True,
                    'url': home_page.url,
                    'final_url': home_page.final_url,
                    'status_code': home_page.status,
                    'content': home_page.html.encode('utf-8') if home_page.html else b'',
                    'text': home_page.html or '',
                    'headers': {},  # Headers not stored in page graph
                    'redirect_count': 0
                }
            else:
                # This branch is now technically unreachable due to gating above, 
                # but kept for logic consistency if we change gating later.
                error_msg = home_page.error.message if home_page and home_page.error else 'Unknown error'
                page_data = {
                    'success': False,
                    'url': url,
                    'error': error_msg
                }
            
            final_url = page_data['final_url']
            response_headers = page_data.get('headers', {})
            
            # Add scan status to report
            report_builder.report["scan_status"] = scan_status
            
            # Check status code (Legacy compliance data logic)
            # We already validated 200 OK above for Success status.
                
            # Check redirects
            if page_data['redirect_count'] > 1:
                compliance_data["general"]["alerts"].append({
                    "code": "EXCESSIVE_REDIRECTS",
                    "type": "Performance",
                    "description": f"{page_data['redirect_count']} redirects detected."
                })
            
            # Phase 11: Compliance Checks
            compliance_start_time = time.monotonic()
            self.logger.info(f"[SCAN][{scan_id}][COMPLIANCE] Compliance checks started")
            
            # Check SSL
            self._check_ssl(parsed_url, domain, compliance_data)
            
            # Check domain age + RDAP details
            rdap_details = self._check_domain_age(domain, compliance_data)
            domain_vintage_days = rdap_details.get("age_days")
            # Attach RDAP details early to report structure
            report_builder.report["rdap"] = rdap_details
            
            compliance_duration = time.monotonic() - compliance_start_time
            compliance_passed = compliance_data["general"]["pass"] and compliance_data["payment_terms"]["pass"]
            compliance_summary = f"general={'pass' if compliance_data['general']['pass'] else 'fail'}, payment_terms={'pass' if compliance_data['payment_terms']['pass'] else 'fail'}"
            self.logger.info(f"[SCAN][{scan_id}][COMPLIANCE] Compliance checks completed in {compliance_duration:.2f}s - {compliance_summary}")
            
            report_builder.add_compliance_data(compliance_data)
            
            # Parse HTML and extract data using modular components
            if page_data.get('success'):
                # Per plan: prefer single-pass PageArtifact from PageGraph (avoids re-parsing)
                home_pg = page_graph.get_page_by_type('home')
                soup = home_pg.get_soup() if home_pg else crawler.parse_html(page_data['content'])
                html_text = home_pg.html if home_pg and home_pg.html else page_data['text']
                page_text = (home_pg.visible_text if home_pg and home_pg.visible_text else soup.get_text(separator=' ', strip=True)).lower()

                # Policy detection inputs: use extracted_links (already resolved) when available
                links_for_policy = []
                if home_pg and home_pg.extracted_links:
                    links_for_policy = [{"url": l.get("url", ""), "text": l.get("text", "")} for l in home_pg.extracted_links if l.get("url")]
                else:
                    links_for_policy = LinkExtractor.extract_all_links(soup, final_url)

                # Detect policies - Enhanced with page graph data
                policy_pages = PolicyDetector.detect_policies(links_for_policy, final_url)
                
                # Enhance policy_pages with pages discovered by orchestrator
                # Per PRD V2.1.1: Add evidence for policy detection
                from analyzers.evidence_builder import EvidenceBuilder
                
                page_type_mapping = {
                    'about': 'about_us',
                    'contact': 'contact_us',
                    'privacy_policy': 'privacy_policy',
                    'terms_conditions': 'terms_condition',
                    'refund_policy': 'returns_refund',
                    'shipping_delivery': 'shipping_delivery',
                    'product': 'product',
                    'pricing': 'pricing',
                    'faq': 'faq',
                    'solutions': 'solutions'
                }
                for graph_type, policy_key in page_type_mapping.items():
                    page = page_graph.get_page_by_type(graph_type)
                    if page and page.status == 200 and policy_key in policy_pages:
                        if not policy_pages[policy_key].get('found'):
                            # Build evidence for page graph discovery
                            evidence = EvidenceBuilder.build_policy_evidence(
                                policy_url=page.url,
                                detection_method="page_graph",
                                page_title=page.page_type
                            )
                            
                            policy_pages[policy_key] = {
                                'found': True,
                                'url': page.url,
                                'status': f"{policy_key.replace('_', ' ').title()} page detected",  # Changed to "detected"
                                'detection_method': 'page_graph',
                                'evidence': evidence
                            }
                
                # Validate policy URLs and prefer PageGraph candidates if detected
                # This fixes cases where anchor detection pointed to a wrong/404 link (e.g., ?page_id=3)
                reverse_mapping = {
                    'about_us': 'about',
                    'contact_us': 'contact',
                    'privacy_policy': 'privacy_policy',
                    'terms_condition': 'terms_conditions',
                    'returns_refund': 'refund_policy',
                    'shipping_delivery': 'shipping_delivery',
                    'product': 'product',
                    'pricing': 'pricing',
                    'faq': 'faq',
                    'solutions': 'solutions'
                }
                for key, data in list(policy_pages.items()):
                    if key == 'home_page':
                        continue
                    graph_type = reverse_mapping.get(key)
                    graph_page = page_graph.get_page_by_type(graph_type) if graph_type else None
                    
                    # PRIORITY 1: If page graph has a valid page, use it (most reliable)
                    if graph_page and graph_page.status == 200 and graph_page.url:
                        policy_pages[key]['found'] = True
                        policy_pages[key]['url'] = graph_page.url
                        policy_pages[key]['status'] = f"{key.replace('_', ' ').title()} page validated via page graph (HTTP 200)"
                        policy_pages[key]['detection_method'] = 'page_graph'
                        policy_pages[key]['evidence'] = {
                            "source_url": graph_page.url,
                            "triggering_rule": "Validated via PageGraph (HTTP 200)",
                            "evidence_snippet": "status: 200",
                            "confidence": 100.0
                        }
                    elif data.get('found'):
                        # PRIORITY 2: Validate anchor-detected URL
                        url_to_check = data.get('url')
                        
                        # Skip validation if URL is clearly invalid (javascript:, mailto:, etc.)
                        if not url_to_check or not url_to_check.startswith(('http://', 'https://')):
                            # Invalid URL detected - mark as not found if no graph alternative
                            policy_pages[key]['found'] = False
                            policy_pages[key]['status'] = f"Detected link invalid (non-HTTP URL: {url_to_check[:50]}). Removed."
                            policy_pages[key]['url'] = ""
                        else:
                            # Validate by fetching
                            try:
                                fetched = crawler.fetch_page(url_to_check)
                                if not fetched or not fetched.get('success') or fetched.get('status_code') != 200:
                                    # Invalid response - mark as not found
                                    policy_pages[key]['found'] = False
                                    policy_pages[key]['status'] = f"Detected link invalid (HTTP {fetched.get('status_code', 'unknown')}). Removed."
                                    policy_pages[key]['url'] = ""
                            except Exception as e:
                                # On fetch error, mark as uncertain but keep it
                                policy_pages[key]['status'] = f"{policy_pages[key].get('status','Detected')} (validation error: {str(e)[:50]})"
                
                report_builder.add_policy_details(policy_pages)
                
                # Update payment terms compliance
                self._update_payment_compliance(policy_pages, page_text, compliance_data)
                report_builder.add_compliance_data(compliance_data)
                
                # Tech Stack Detection (V2 Feature)
                self.logger.info("[V2] Detecting tech stack...")
                tech_stack = TechDetector.detect_all(soup, html_text, response_headers)
                report_builder.report["tech_stack"] = tech_stack
                
                # SEO Analysis (V2 Feature)
                self.logger.info("[V2] Analyzing SEO...")
                seo_analysis = SEOAnalyzer.analyze_seo(soup, final_url)
                report_builder.report["seo_analysis"] = seo_analysis
                
                # Enhanced Business Metadata (V2 Feature)
                self.logger.info("[V2] Extracting enhanced business metadata...")
                extracted_name = MetadataExtractor.extract_business_name(soup, business_name)
                contact_info = MetadataExtractor.extract_contact_info(soup, page_text)
                social_links = MetadataExtractor.extract_social_links(soup)
                
                # Extract additional business details from About page (use pre-fetched from page graph)
                company_summary = "No summary available."
                mission_vision = "Mission/Vision statement not found."
                key_offerings = "Product/Service details not found."
                
                # Try to get about page from page graph first
                about_page = page_graph.get_page_by_type('about')
                about_soup = None
                if about_page and about_page.status == 200 and about_page.html:
                    self.logger.info(f"[V2.1] Using pre-fetched about page from page graph")
                    about_soup = about_page.get_soup()
                elif policy_pages.get("about_us", {}).get("found"):
                    # Fallback to fetching if not in page graph
                    about_url = policy_pages["about_us"]["url"]
                    self.logger.info(f"[V2.1] Fetching about page (fallback): {about_url}")
                    about_data = crawler.fetch_page(about_url)
                    if about_data.get("success"):
                        about_soup = crawler.parse_html(about_data["content"])
                
                if about_soup:
                        # Remove nav/footer/header for cleaner text
                        for el in about_soup(["script", "style", "nav", "footer", "header", "aside"]):
                            el.decompose()
                        about_text = about_soup.get_text(separator=' ', strip=True)
                        
                        # Company summary from about page
                        if len(about_text) > 50:
                            company_summary = about_text[:1000] + "..." if len(about_text) > 1000 else about_text
                        
                        # Mission/Vision extraction
                        mv_patterns = [
                            r'(?:mission|vision|our\s+goal|purpose)\s*:?\s*([^.!?]{20,500}[.!?])',
                            r'(?:strive\s+to|aim\s+to|committed\s+to)\s+([^.!?]{20,500}[.!?])'
                        ]
                        for mv_p in mv_patterns:
                            mv_match = re.search(mv_p, about_text, re.I)
                            if mv_match:
                                mission_vision = mv_match.group(1).strip()
                                break
                        
                        # Key offerings extraction
                        off_patterns = [
                            r'(?:offerings|services|products|solutions|we\s+provide|features)\s*(?:include|are|offer)\s*:?\s*([^.!?]{20,500})',
                            r'(?:wide\s+range\s+of)\s+([^.!?]{20,500})'
                        ]
                        for off_p in off_patterns:
                            off_match = re.search(off_p, about_text, re.I)
                            if off_match:
                                key_offerings = off_match.group(1).strip()
                                break
                
                enhanced_business_details = {
                    "extracted_business_name": extracted_name,
                    "company_summary": company_summary,
                    "mission_vision": mission_vision,
                    "key_offerings": key_offerings,
                    "contact_info": contact_info,
                    "social_links": social_links,
                    "source_urls": {
                        "home": final_url,
                        "about_us": policy_pages.get("about_us", {}).get("url"),
                        "contact_us": policy_pages.get("contact_us", {}).get("url")
                    }
                }
                report_builder.add_business_details(enhanced_business_details)
                
                # Enhanced Product Indicators (Scraping-based)
                product_indicators = ContentAnalyzer.detect_product_indicators(page_text)
                
                # Add source pages and enhanced extraction
                product_indicators["source_pages"] = {
                    "product_page": policy_pages.get("product", {}).get("url"),
                    "pricing_page": policy_pages.get("pricing", {}).get("url")
                }
                product_indicators["pricing_model"] = "Not identified"
                product_indicators["target_audience"] = "General"
                product_indicators["extracted_products"] = []
                
                # Extract products from homepage navigation menu (before processing other pages)
                # This captures products listed in navigation dropdowns like open.money
                try:
                    if soup:
                        self.logger.info(f"[V2.1] Starting product extraction from navigation...")
                        # Look for navigation menus
                        nav_elements = soup.find_all(['nav', 'header'], limit=3)
                        self.logger.debug(f"[V2.1] Found {len(nav_elements)} navigation elements")
                        nav_products = []
                        
                        # First, find the "Products" menu item to identify its dropdown
                        products_menu = None
                        products_menu_parent = None
                        for nav in nav_elements:
                            # Look for a link or button with "Products" text (case-insensitive)
                            all_links = nav.find_all(['a', 'button'], limit=50)
                            self.logger.debug(f"[V2.1] Checking {len(all_links)} links in nav for Products menu")
                            for link in all_links:
                                link_text_clean = link.get_text(strip=True).lower()
                                if link_text_clean == 'products' or link_text_clean == 'product':
                                    products_menu = link
                                    # Find its parent container (usually <li> or <div>)
                                    products_menu_parent = link.find_parent(['li', 'div', 'nav'])
                                    self.logger.info(f"[V2.1] Found Products menu: {link.get_text(strip=True)}")
                                    break
                            if products_menu:
                                break
                        
                        if not products_menu:
                            self.logger.debug(f"[V2.1] No 'Products' menu found, will use broader extraction")
                        
                        for nav in nav_elements:
                            # Find all links in navigation (including dropdown menus and hidden ones)
                            # Use find_all with recursive=True to get nested links in dropdowns
                            nav_links = nav.find_all('a', href=True, recursive=True, limit=100)  # Increased limit for dropdowns
                            self.logger.debug(f"[V2.1] Found {len(nav_links)} total links in navigation")
                            
                            for link in nav_links:
                                link_text = link.get_text(strip=True)
                                href = link.get('href', '').lower()
                                
                                # Skip generic navigation items
                                skip_texts = ['home', 'about', 'contact', 'blog', 'login', 'sign up', 'sign in', 
                                            'get started', 'company', 'solutions', 'partners', 'pricing', 
                                            'features', 'products', 'overview', 'menu', 'close', 'all', 'view all',
                                            'contact sales', 'login', 'sign in', 'sign up', 'privacy', 'terms']
                                
                                # Check if this looks like a product name
                                # Products are usually: 2-50 chars, not in skip list
                                passes_basic_filter = (link_text and 
                                    2 <= len(link_text) <= 50 and 
                                    link_text.lower() not in [s.lower() for s in skip_texts] and
                                    not any(skip.lower() in link_text.lower() for skip in skip_texts))
                                
                                
                                if passes_basic_filter:
                                    
                                    # Check if URL or context suggests it's a product
                                    is_product = False
                                    
                                    # Direct product indicators in URL (including industry segments)
                                    url_indicators = ['/product', '/feature', '/solution', '/service', 
                                                                              '/pay', '/get-paid', '/spend', '/banking', '/accounting', 
                                                                              '/payroll', '/gst', '/invoice', '/receivables', '/payables',
                                                                              '/startup', '/enterprise', '/sme', '/retail', '/ecommerce',
                                                                              '/manufactur', '/healthcare', '/hospitality', '/real-estate',
                                                                              '/software', '/technology', '/professional', '/consultant',
                                                                              '/freelancer', '/small-business']
                                    url_match = any(indicator in href for indicator in url_indicators)
                                    if url_match:
                                        is_product = True
                                        self.logger.debug(f"[V2.1] Product candidate (URL match): {link_text} ({href})")
                                    # Check if link is in a dropdown/submenu under "Products" menu
                                    else:
                                        # Find parent elements to check context
                                        parent = link.find_parent(['li', 'div', 'ul', 'nav', 'section'])
                                        
                                        # Method 1: Check if link is structurally related to Products menu
                                        if products_menu_parent:
                                            # Check if link is a descendant of the Products menu's parent
                                            try:
                                                # Get all links within the Products menu parent
                                                parent_links = products_menu_parent.find_all('a', recursive=True)
                                                in_parent = link in parent_links and link != products_menu
                                                if in_parent:
                                                    is_product = True
                                            except Exception as e:
                                                pass
                                        
                                        # Method 1b: Check siblings and next elements (common dropdown pattern)
                                        if not is_product and products_menu:
                                            # Look for <ul> or <div> that comes after Products link (dropdown container)
                                            next_elem = products_menu.find_next(['ul', 'div', 'nav'])
                                            if next_elem:
                                                try:
                                                    if link in next_elem.find_all('a', recursive=True):
                                                        is_product = True
                                                except:
                                                    pass
                                            
                                            # Also check parent's next siblings
                                            if not is_product and products_menu_parent:
                                                siblings = products_menu_parent.find_next_siblings(['ul', 'div', 'li'], limit=3)
                                                for sibling in siblings:
                                                    try:
                                                        if link in sibling.find_all('a', recursive=True):
                                                            is_product = True
                                                            break
                                                    except:
                                                        pass
                                        
                                        # Method 2: Check parent context
                                        if not is_product and parent:
                                            # Get all text from parent to check for "product" context
                                            parent_text = parent.get_text(strip=True).lower()
                                            
                                            # Check if parent contains "product" keyword or is in a dropdown
                                            parent_classes = ' '.join(parent.get('class', [])).lower()
                                            parent_id = (parent.get('id') or '').lower()
                                            
                                            # Check if it's in a dropdown menu (more lenient)
                                            is_dropdown = any(keyword in parent_classes or keyword in parent_id 
                                                            for keyword in ['dropdown', 'menu', 'submenu', 'nav', 'mega', 'flyout'])
                                            
                                            # Check if parent has "product" context
                                            has_product_context = ('product' in parent_text or 
                                                                  'product' in parent_classes or
                                                                  'product' in parent_id)
                                            
                                            # Check if link is nested under a "Products" link (more lenient)
                                            products_parent = link.find_parent('a', href=True)
                                            if products_parent:
                                                parent_link_text = products_parent.get_text(strip=True).lower()
                                                if 'product' in parent_link_text:
                                                    is_product = True
                                            
                                            if (is_dropdown and has_product_context):
                                                is_product = True
                                        
                                        # Method 3: Check if it's a short, descriptive name that could be a product
                                        if not is_product:
                                            # Short product names (1-4 words) that aren't generic
                                            words = link_text.split()
                                            if (1 <= len(words) <= 4 and 
                                                len(link_text) >= 3 and
                                                not any(skip in link_text.lower() for skip in ['company', 'solutions', 'partners', 'blog', 'help', 'support', 'resources'])):
                                                # If it's in navigation and looks like a product name, include it
                                                # This is a fallback for cases where dropdown detection fails
                                                if parent and any(keyword in ' '.join(parent.get('class', [])).lower() 
                                                                  for keyword in ['nav', 'menu', 'header']):
                                                    is_product = True
                                                    self.logger.debug(f"[V2.1] Product candidate (fallback match): {link_text}")
                                        
                                        # Method 4: If no Products menu found, be more lenient with navigation links
                                        # This catches industry segments, solutions, etc. that might be considered "products"
                                        if not is_product and not products_menu:
                                            # Check if it's a standalone navigation link that could be a product/solution
                                            words = link_text.split()
                                            if (1 <= len(words) <= 3 and 
                                                len(link_text) >= 4 and
                                                href.startswith('/') and  # Relative URL suggests it's a page
                                                not href.startswith('/#') and  # Not an anchor link
                                                not any(skip in link_text.lower() for skip in ['home', 'about', 'contact', 'blog', 'login', 'sign', 'privacy', 'terms', 'faq'])):
                                                # Check if parent is in navigation structure
                                                if parent:
                                                    parent_classes = ' '.join(parent.get('class', [])).lower()
                                                    if any(keyword in parent_classes for keyword in ['nav', 'menu', 'header', 'dropdown', 'submenu']):
                                                        is_product = True
                                                        self.logger.debug(f"[V2.1] Product candidate (lenient match): {link_text} ({href})")
                                    
                                    if is_product:
                                        # Avoid duplicates
                                        if not any(p['name'].lower() == link_text.lower() for p in nav_products):
                                            nav_products.append({
                                                "name": link_text,
                                                "brief_description": "Product identified from navigation menu",
                                                "price_if_found": None,
                                                "source": "navigation"
                                            })
                        
                        if nav_products:
                            product_indicators["extracted_products"].extend(nav_products)
                            self.logger.info(f"[V2.1] Extracted {len(nav_products)} products from navigation menu: {[p['name'] for p in nav_products[:5]]}")
                        else:
                            self.logger.debug(f"[V2.1] No products extracted from navigation menu")
                            
                        # Fallback: Extract products from homepage content sections (product cards, feature sections, etc.)
                        if not nav_products and soup:
                            try:
                                content_products = []
                                
                                # Look for common product section patterns
                                product_sections = soup.find_all(['section', 'div'], 
                                                               class_=re.compile(r'product|feature|solution|service', re.I),
                                                               limit=10)
                                
                                # Also look for headings that suggest products
                                product_headings = soup.find_all(['h2', 'h3', 'h4'], 
                                                                string=re.compile(r'product|feature|solution|service|what we|our', re.I),
                                                                limit=10)
                                
                                # Extract from product sections
                                for section in product_sections:
                                    # Find links or headings in product sections
                                    section_links = section.find_all('a', href=True, limit=20)
                                    section_headings = section.find_all(['h2', 'h3', 'h4'], limit=10)
                                    
                                    for link in section_links:
                                        link_text = link.get_text(strip=True)
                                        if (link_text and 3 <= len(link_text) <= 50 and
                                            link_text.lower() not in ['learn more', 'read more', 'get started', 'view all', 'see all']):
                                            # Check if it looks like a product name
                                            if not any(skip in link_text.lower() for skip in ['home', 'about', 'contact', 'blog', 'login']):
                                                if not any(p['name'].lower() == link_text.lower() for p in content_products):
                                                    content_products.append({
                                                        "name": link_text,
                                                        "brief_description": "Product identified from homepage content",
                                                        "price_if_found": None,
                                                        "source": "homepage_content"
                                                    })
                                    
                                    for heading in section_headings:
                                        heading_text = heading.get_text(strip=True)
                                        if (heading_text and 3 <= len(heading_text) <= 50 and
                                            heading_text.lower() not in ['products', 'features', 'solutions', 'services']):
                                            if not any(p['name'].lower() == heading_text.lower() for p in content_products):
                                                content_products.append({
                                                    "name": heading_text,
                                                    "brief_description": "Product identified from homepage heading",
                                                    "price_if_found": None,
                                                    "source": "homepage_content"
                                                })
                                
                                # Extract from product headings context
                                for heading in product_headings:
                                    # Get parent section
                                    parent_section = heading.find_parent(['section', 'div', 'article'])
                                    if parent_section:
                                        # Find links or sub-headings in this section
                                        section_items = parent_section.find_all(['a', 'h3', 'h4'], limit=15)
                                        for item in section_items:
                                            item_text = item.get_text(strip=True)
                                            if (item_text and 3 <= len(item_text) <= 50 and
                                                item_text != heading.get_text(strip=True) and
                                                item_text.lower() not in ['learn more', 'read more', 'get started', 'view all']):
                                                if not any(p['name'].lower() == item_text.lower() for p in content_products):
                                                    content_products.append({
                                                        "name": item_text,
                                                        "brief_description": "Product identified from homepage section",
                                                        "price_if_found": None,
                                                        "source": "homepage_content"
                                                    })
                                
                                if content_products:
                                    # Limit to top 10 to avoid noise
                                    content_products = content_products[:10]
                                    product_indicators["extracted_products"].extend(content_products)
                                    self.logger.info(f"[V2.1] Extracted {len(content_products)} products from homepage content: {[p['name'] for p in content_products[:5]]}")
                                    
                            except Exception as e2:
                                self.logger.debug(f"[V2.1] Homepage content product extraction warning: {e2}")
                            
                except Exception as e:
                    self.logger.warning(f"[V2.1] Navigation product extraction warning: {e}", exc_info=True)
                
                # Extract products/pricing from product and pricing pages (use pre-fetched when available)
                content_for_extraction = page_text
                prod_soup = None
                price_soup = None
                
                # Try product page from page graph first
                product_page = page_graph.get_page_by_type('product')
                if product_page and product_page.status == 200 and product_page.html:
                    self.logger.info(f"[V2.1] Using pre-fetched product page from page graph")
                    prod_soup = product_page.get_soup()
                elif product_indicators["source_pages"]["product_page"]:
                    # Fallback to fetching
                    prod_data = crawler.fetch_page(product_indicators["source_pages"]["product_page"])
                    if prod_data.get("success"):
                        prod_soup = crawler.parse_html(prod_data["content"])
                
                if prod_soup:
                    # Prefer PageArtifact visible_text when available (avoids extra DOM traversal)
                    if product_page and getattr(product_page, "visible_text", None):
                        content_for_extraction += " " + product_page.visible_text.lower()
                    else:
                        for el in prod_soup(["script", "style", "nav", "footer", "header"]):
                            el.decompose()
                        content_for_extraction += " " + prod_soup.get_text(separator=' ', strip=True).lower()
                
                # Try pricing page from page graph first
                pricing_page = page_graph.get_page_by_type('pricing')
                if pricing_page and pricing_page.status == 200 and pricing_page.html:
                    self.logger.info(f"[V2.1] Using pre-fetched pricing page from page graph")
                    price_soup = pricing_page.get_soup()
                elif product_indicators["source_pages"]["pricing_page"]:
                    # Fallback to fetching
                    price_data = crawler.fetch_page(product_indicators["source_pages"]["pricing_page"])
                    if price_data.get("success"):
                        price_soup = crawler.parse_html(price_data["content"])
                
                if price_soup:
                    # Prefer PageArtifact visible_text when available (avoids extra DOM traversal)
                    if pricing_page and getattr(pricing_page, "visible_text", None):
                        content_for_extraction += " " + pricing_page.visible_text.lower()
                    else:
                        for el in price_soup(["script", "style", "nav", "footer", "header"]):
                            el.decompose()
                        content_for_extraction += " " + price_soup.get_text(separator=' ', strip=True).lower()
                
                # Detect pricing model from content
                if "subscription" in content_for_extraction or "monthly" in content_for_extraction or "per month" in content_for_extraction:
                    product_indicators["pricing_model"] = "Subscription"
                elif "one-time" in content_for_extraction or "one time" in content_for_extraction:
                    product_indicators["pricing_model"] = "One-time"
                elif "free" in content_for_extraction and ("trial" in content_for_extraction or "freemium" in content_for_extraction):
                    product_indicators["pricing_model"] = "Freemium"
                elif "quote" in content_for_extraction or "contact us" in content_for_extraction or "enterprise" in content_for_extraction:
                    product_indicators["pricing_model"] = "Quote-based"
                elif product_indicators["has_pricing"]:
                    product_indicators["pricing_model"] = "Fixed Price"
                
                # Detect target audience
                if "enterprise" in content_for_extraction or "b2b" in content_for_extraction or "business" in content_for_extraction:
                    product_indicators["target_audience"] = "Enterprise / B2B"
                elif "developer" in content_for_extraction or "api" in content_for_extraction:
                    product_indicators["target_audience"] = "Developers"
                elif "startup" in content_for_extraction or "small business" in content_for_extraction:
                    product_indicators["target_audience"] = "SMBs / Startups"
                elif "consumer" in content_for_extraction or "personal" in content_for_extraction:
                    product_indicators["target_audience"] = "Consumers"
                
                # Extract additional products from product page headings (if product page found)
                # Note: Navigation products were already extracted above (lines 395-454)
                try:
                    # Start with products already extracted from navigation
                    extracted_products = product_indicators["extracted_products"].copy()
                    
                    # Extract from product page headings (if product page found)
                    if prod_soup:
                        h2_tags = prod_soup.find_all(['h2', 'h3'], limit=10)
                        for h_tag in h2_tags:
                            heading_text = h_tag.get_text(strip=True)
                            # Skip generic headings
                            if heading_text and len(heading_text) > 3 and len(heading_text) < 100:
                                skip_words = ['about', 'contact', 'home', 'menu', 'navigation', 'footer', 'header']
                                if not any(sw in heading_text.lower() for sw in skip_words):
                                    # Check if not already extracted from nav
                                    if not any(p['name'].lower() == heading_text.lower() for p in extracted_products):
                                        extracted_products.append({
                                        "name": heading_text,
                                            "brief_description": "Product/Feature identified from page headings",
                                            "price_if_found": None,
                                            "source": "page_headings"
                                        })
                    
                    # If still no products, try extracting from homepage content sections
                    if len(extracted_products) == 0:
                        if soup:
                            # Look for common product listing patterns
                            product_sections = soup.find_all(['section', 'div'], class_=re.compile(r'product|feature|service|solution', re.I), limit=5)
                            for section in product_sections:
                                # Look for headings or links in product sections
                                section_headings = section.find_all(['h2', 'h3', 'h4'], limit=5)
                                for heading in section_headings:
                                    heading_text = heading.get_text(strip=True)
                                    if heading_text and 3 < len(heading_text) < 60:
                                        skip_words = ['about', 'contact', 'home', 'menu', 'navigation', 'footer', 'header', 'overview', 'features']
                                        if not any(sw in heading_text.lower() for sw in skip_words):
                                            extracted_products.append({
                                                "name": heading_text,
                                                "brief_description": "Product identified from homepage section",
                                                "price_if_found": None,
                                                "source": "homepage_section"
                                            })
                    
                    # Final fallback: Extract from homepage HTML by parsing ALL links (including hidden ones)
                    # This catches cases like open.money where products are listed as industry segments
                    # but the navigation menu is JavaScript-rendered and not in static HTML
                    # We parse the soup directly to find ALL <a> tags, even in hidden dropdowns
                    if len(extracted_products) == 0 and soup:
                        self.logger.info(f"[V2.1] Using final fallback: extracting from all homepage links (including hidden)")
                        
                        # Extract ALL links from homepage HTML (including hidden dropdowns)
                        # Use recursive=True to get nested links
                        all_homepage_links = soup.find_all('a', href=True, recursive=True)
                        
                        solution_indicators = ['startup', 'enterprise', 'sme', 'retail', 'ecommerce', 'manufactur',
                                              'healthcare', 'hospitality', 'real-estate', 'software', 'technology',
                                              'professional', 'consultant', 'freelancer', 'small-business', 'business']
                        
                        skip_url_patterns = ['/blog', '/contact', '/about', '/privacy', '/terms', '/pricing', '/faq', '/help']
                        skip_text_patterns = ['blog', 'contact', 'about', 'privacy', 'terms', 'pricing', 'faq', 'help', 'login', 'sign', 'get started']
                        
                        for link in all_homepage_links:
                            href = link.get('href', '')
                            if not href:
                                continue
                            
                            # Get link text - try direct text first, then get_text() for nested content
                            link_text = link.string
                            if not link_text or not link_text.strip():
                                link_text = link.get_text(strip=True)
                            
                            # Skip if still no text (but continue for URL-based extraction)
                            if not link_text or not link_text.strip():
                                # Still try to extract from URL if it looks like a product
                                link_text = ""
                            
                            try:
                                # Resolve relative URLs
                                from urllib.parse import urljoin
                                full_url = urljoin(final_url, href)
                                parsed = urlparse(full_url)
                                
                                # Only process internal links
                                if parsed.netloc and parsed.netloc.lower() not in [urlparse(final_url).netloc.lower(), '']:
                                    continue
                                
                                path = parsed.path.lower()
                                
                                # Skip obvious non-product pages
                                if any(skip in path for skip in skip_url_patterns):
                                    continue
                                
                                # Skip if link text suggests it's not a product
                                if link_text and any(skip in link_text.lower() for skip in skip_text_patterns):
                                    continue
                                
                                # Check if link is in a Products dropdown menu
                                is_in_products_menu = False
                                parent = link.find_parent(['li', 'div', 'ul', 'nav'])
                                if parent:
                                    parent_text = parent.get_text(strip=True).lower()
                                    parent_classes = ' '.join(parent.get('class', [])).lower()
                                    parent_id = (parent.get('id') or '').lower()
                                    
                                    # Check if parent contains "product" context
                                    if ('product' in parent_text or 'product' in parent_classes or 'product' in parent_id):
                                        is_in_products_menu = True
                                    
                                    # Also check if link is under a "Products" menu item
                                    products_parent_link = link.find_parent('a', href=True)
                                    if products_parent_link:
                                        parent_link_text = products_parent_link.get_text(strip=True)
                                        if parent_link_text and re.match(r'^products?$', parent_link_text, re.I):
                                            is_in_products_menu = True
                                
                                # Also check if link text itself suggests it's a product (common product names)
                                product_keywords = ['pay', 'get paid', 'spend', 'banking', 'account', 'card', 'loan', 'investment', 'payroll', 'accounting', 'invoice', 'integration']
                                if not is_in_products_menu and link_text:
                                    link_text_lower = link_text.lower()
                                    if any(keyword in link_text_lower for keyword in product_keywords):
                                        # Check if it's not a generic navigation term
                                        if not any(skip in link_text_lower for skip in ['contact', 'about', 'blog', 'help', 'login', 'sign']):
                                            is_in_products_menu = True
                                
                                # Check if URL suggests it's a solution/industry page
                                matches_indicator = any(ind in path for ind in solution_indicators)
                                
                                # Extract product if:
                                # 1. It's in a Products menu, OR
                                # 2. It matches industry indicators, OR
                                # 3. It's a short descriptive name that looks like a product, OR
                                # 4. URL path suggests it's a product (even without link text)
                                should_extract = False
                                product_name = None
                                
                                # Check URL for product indicators
                                url_product_indicators = ['pay', 'payment', 'account', 'banking', 'card', 'loan', 'investment', 'payroll', 'accounting', 'invoice', 'integration', 'spend', 'vendor']
                                url_looks_like_product = any(ind in path for ind in url_product_indicators)
                                
                                if is_in_products_menu:
                                    # Use link text as product name if in Products menu
                                    if link_text and link_text.strip():
                                        product_name = link_text.strip()
                                        should_extract = True
                                    elif url_looks_like_product:
                                        # Extract from URL if no link text
                                        path_parts = [p for p in path.strip('/').split('/') if p]
                                        if path_parts:
                                            product_name = path_parts[-1].replace('-', ' ').replace('_', ' ').title()
                                            should_extract = True
                                elif matches_indicator:
                                    # Extract from URL path for industry segments
                                    path_parts = [p for p in path.strip('/').split('/') if p]
                                    if path_parts:
                                        product_name = path_parts[-1].replace('-', ' ').replace('_', ' ').title()
                                        should_extract = True
                                elif link_text and 2 <= len(link_text.strip()) <= 50:
                                    # Check if link text looks like a product name
                                    # Products are usually: short descriptive names, not generic navigation
                                    words = link_text.strip().split()
                                    if (1 <= len(words) <= 5 and 
                                        not any(skip in link_text.lower() for skip in ['go to', 'learn more', 'read more', 'view all', 'see all', 'all'])):
                                        # Check if URL path suggests it's a product page (not a category)
                                        if path and len(path) > 1 and not any(cat in path for cat in ['/category', '/tag', '/archive', '/page']):
                                            product_name = link_text.strip()
                                            should_extract = True
                                elif url_looks_like_product and path and len(path) > 1:
                                    # Extract from URL even if no link text
                                    path_parts = [p for p in path.strip('/').split('/') if p]
                                    if path_parts:
                                        product_name = path_parts[-1].replace('-', ' ').replace('_', ' ').title()
                                        should_extract = True
                                
                                if should_extract and product_name:
                                    # Clean up the name
                                    if product_name and 2 <= len(product_name) <= 50:
                                        if not any(p['name'].lower() == product_name.lower() for p in extracted_products):
                                            extracted_products.append({
                                                "name": product_name,
                                                "brief_description": f"Product: {product_name}" if is_in_products_menu else f"Solution for {product_name}",
                                                "price_if_found": None,
                                                "source": "homepage_html_products_menu" if is_in_products_menu else "homepage_html"
                                            })
                                            self.logger.debug(f"[V2.1] Extracted from homepage HTML: {product_name} ({path})")
                            except Exception as e:
                                continue
                        
                        if len(extracted_products) > 0:
                            self.logger.info(f"[V2.1] Fallback extraction from homepage HTML found {len(extracted_products)} products/solutions")
                    
                    # Filter and prioritize products
                    # Remove non-product items (policies, careers, etc.)
                    non_product_keywords = ['policy', 'career', 'grievance', 'disclosure', 'guideline', 'corporate information', 
                                          'connect with us', 'email', 'hiring', 'we\'re hiring', 'contact', 'about', 'blog']
                    
                    filtered_products = []
                    for product in extracted_products:
                        product_name_lower = product.get('name', '').lower()
                        # Skip if it's clearly not a product
                        if any(non_prod in product_name_lower for non_prod in non_product_keywords):
                            continue
                        filtered_products.append(product)
                    
                    # Prioritize: products from products menu first, then URL-based products, then industry segments
                    prioritized_products = []
                    # 1. Products from products menu (highest priority)
                    for product in filtered_products:
                        if product.get('source') == 'homepage_html_products_menu':
                            prioritized_products.append(product)
                    
                    # 2. URL-based products (medium priority)
                    for product in filtered_products:
                        if product.get('source') == 'homepage_html' and 'solution for' not in product.get('brief_description', '').lower():
                            if product not in prioritized_products:
                                prioritized_products.append(product)
                    
                    # 3. Industry segments (lowest priority, only if we don't have enough real products)
                    if len(prioritized_products) < 15:
                        for product in filtered_products:
                            if product not in prioritized_products:
                                prioritized_products.append(product)
                    
                    # Limit to top 20 products (prioritized)
                    prioritized_products = prioritized_products[:20]
                    
                    product_indicators["extracted_products"] = prioritized_products
                    
                    if len(extracted_products) > 0:
                        self.logger.info(f"[V2.1] Total extracted products: {len(extracted_products)} (from navigation and pages)")
                    
                except Exception as e:
                    self.logger.warning(f"[V2.1] Product extraction warning: {e}")
                
                # Log final product indicators before adding to report
                final_product_count = len(product_indicators.get("extracted_products", []))
                self.logger.info(f"[V2.1] Final product count: {final_product_count}")
                if final_product_count > 0:
                    self.logger.info(f"[V2.1] Products to be added to report: {[p.get('name', 'Unknown') for p in product_indicators.get('extracted_products', [])[:5]]}")
                else:
                    self.logger.warning(f"[V2.1] WARNING: No products extracted! Product indicators: {list(product_indicators.keys())}")
                
                report_builder.add_product_details(product_indicators)
                
                # Update policy_pages based on extracted products/solutions
                # This ensures Policy Details shows Product/Solutions as found when extracted from nav
                # even if there's no dedicated /products or /solutions landing page
                extracted_products = product_indicators.get("extracted_products", [])
                if extracted_products and not policy_pages.get("product", {}).get("found"):
                    # Find the first product with a source URL
                    first_product_url = None
                    for prod in extracted_products:
                        if prod.get("source") == "navigation":
                            first_product_url = "Navigation menu (dropdown)"
                            break
                    
                    policy_pages["product"] = {
                        "found": True,
                        "url": first_product_url or "Products extracted from navigation",
                        "status": f"Products detected ({len(extracted_products)} found in navigation)",
                        "detection_method": "product_extraction",
                        "evidence": {
                            "source_url": final_url,
                            "triggering_rule": f"Product extraction from navigation menu",
                            "evidence_snippet": f"Products: {', '.join([p.get('name', 'Unknown') for p in extracted_products[:3]])}",
                            "confidence": 80.0
                        }
                    }
                    self.logger.info(f"[V2.1] Updated policy_pages['product'] based on extracted products")
                
                # Check if any extracted products look like solutions/services
                solution_keywords = ['service', 'solution', 'platform', 'api', 'integration', 'suite', 'consulting', 'professional']
                solutions_found = [p for p in extracted_products if any(kw in p.get('name', '').lower() for kw in solution_keywords)]
                if solutions_found and not policy_pages.get("solutions", {}).get("found"):
                    policy_pages["solutions"] = {
                        "found": True,
                        "url": "Solutions extracted from navigation",
                        "status": f"Solutions detected ({len(solutions_found)} found)",
                        "detection_method": "product_extraction",
                        "evidence": {
                            "source_url": final_url,
                            "triggering_rule": "Solution extraction from navigation menu",
                            "evidence_snippet": f"Solutions: {', '.join([p.get('name', 'Unknown') for p in solutions_found[:3]])}",
                            "confidence": 70.0
                        }
                    }
                    self.logger.info(f"[V2.1] Updated policy_pages['solutions'] based on extracted solutions")
                
                # Re-add updated policy_details to report
                report_builder.add_policy_details(policy_pages)
                
                # Content Risk Analysis - coverage-first across all fetched pages
                # Per plan: consume PageArtifact (visible_text) rather than re-parsing pages again.
                pages_for_risk = []
                for _, p in (page_graph.pages or {}).items():
                    try:
                        if not p or getattr(p, "status", 0) != 200:
                            continue
                        text = (getattr(p, "visible_text", "") or "").strip()
                        if not text and getattr(p, "html", ""):
                            text = getattr(p, "html", "")
                        if not text:
                            continue
                        pages_for_risk.append(
                            {
                                "url": getattr(p, "final_url", None) or getattr(p, "url", None) or "unknown",
                                "text": text.lower(),
                                "page_type": getattr(p, "page_type", None),
                                "render_type": getattr(p, "render_type", "http"),
                            }
                        )
                    except Exception:
                        continue

                content_risk = ContentAnalyzer.analyze_content_risk_multi_pages(pages_for_risk)
                report_builder.add_content_risk(content_risk)
                
                # MCC Classification
                # Per plan: use combined text across all fetched pages for better context
                page_texts_by_url = {}
                render_types_by_url = {}
                combined_text_parts = []
                for entry in pages_for_risk:
                    u = entry.get("url") or "unknown"
                    t = entry.get("text") or ""
                    if not t:
                        continue
                    page_texts_by_url[u] = t
                    render_types_by_url[u] = entry.get("render_type") or "http"
                    combined_text_parts.append(t)
                combined_text_for_mcc = " ".join(combined_text_parts)
                if len(combined_text_for_mcc) > 600000:
                    combined_text_for_mcc = combined_text_for_mcc[:600000]

                # Per PRD V2.1.1: Pass pages_scanned count for transparency
                pages_scanned_count = len(page_graph.pages) if page_graph else 0
                mcc_data = self._classify_mcc(
                    combined_text_for_mcc,
                    page_urls=list(page_texts_by_url.keys()),
                    pages_scanned=pages_scanned_count,
                    page_texts_by_url=page_texts_by_url,
                    render_types_by_url=render_types_by_url
                )
                report_builder.add_mcc_codes(mcc_data)
                
                # Phase E.1: Business Context Classification
                self.logger.info("[V2.1] Classifying Business Context...")
                business_context = self.context_classifier.classify(
                    tech_stack,
                    product_indicators,
                    combined_text_for_mcc,
                    mcc_data,
                    page_graph=page_graph
                )
                report_builder.report["business_context"] = business_context
                
                # Compliance Intelligence (Phase E + E.1)
                self.logger.info("[V2.1] Running Context-Aware Compliance Intelligence...")
                # Ensure we have all pieces. 'compliance_data' is updated by reference throughout.
                # 'policy_pages' has details. 'content_risk' has keywords.
                compliance_intel = self.compliance_engine.analyze(
                    compliance_data,
                    policy_pages,
                    content_risk,
                    domain_vintage_days,
                    business_context
                )
                report_builder.add_compliance_intelligence(compliance_intel)
            
            # Build final report
            final_report = report_builder.build()
            
            # Add crawl summary to report (PRD V2.1.1 requirement)
            if "comprehensive_site_scan" in final_report:
                crawl_summary = page_graph.get_crawl_summary()
                final_report["comprehensive_site_scan"]["crawl_summary"] = crawl_summary
            
            # Run Change Detection Comparison
            # We need to construct a 'virtual' current snapshot for comparison logic from the report data
            # Or we can just reuse the save_snapshot logic logic which extracts from report
            # Let's manually construct the minimal set for 'compare' method
            
            # Helper to extract hash from graph
            def _get_hash(ptype):
                p = page_graph.get_page_by_type(ptype)
                return p.content_hash if p else None
                
            current_snapshot_data = {
                'page_hashes': {
                    'home': _get_hash('home'),
                    'privacy_policy': _get_hash('privacy_policy'),
                    'terms_conditions': _get_hash('terms_conditions'),
                    'product': _get_hash('product'),
                    'pricing': _get_hash('pricing')
                },
                'derived_signals': {
                    'pricing_model': product_indicators.get('pricing_model') if 'product_indicators' in locals() else None,
                    'extracted_products': product_indicators.get('extracted_products', []) if 'product_indicators' in locals() else []
                }
            }
            
            # Per PRD V2.1.1: Pass current scan timestamp for comparison metadata
            change_report = self.change_detector.compare(
                current_snapshot_data, 
                previous_snapshot,
                current_scan_timestamp=scan_start_timestamp
            )
            
            # Add change detection to final report
            # Wrapping it inside comprehensive_site_scan to keep structure clean
            if "comprehensive_site_scan" in final_report:
                final_report["comprehensive_site_scan"]["change_detection"] = change_report
                
                # Run Change Intelligence (Phase D)
                intelligence_report = self.intelligence_engine.analyze_intelligence(change_report)
                final_report["comprehensive_site_scan"]["change_intelligence"] = intelligence_report
            
            # Phase 12: Snapshot / Persistence (Non-blocking)
            self.logger.info(f"[SCAN][{scan_id}][SNAPSHOT] Starting background snapshot save...")
            
            def save_snapshot_background():
                """Save snapshot in background thread"""
                snapshot_start = time.monotonic()
                try:
                    self.change_detector.save_snapshot(task_id, url, page_graph, final_report)
                    snapshot_duration = time.monotonic() - snapshot_start
                    self.logger.info(f"[SCAN][{scan_id}][SNAPSHOT] Background snapshot saved in {snapshot_duration:.2f}s")
                except Exception as e:
                    snapshot_duration = time.monotonic() - snapshot_start
                    self.logger.error(f"[SCAN][{scan_id}][SNAPSHOT] Background snapshot save failed after {snapshot_duration:.2f}s: {e}", exc_info=True)
            
            # Start snapshot save in background thread (non-blocking)
            snapshot_thread = threading.Thread(target=save_snapshot_background, daemon=True)
            snapshot_thread.start()
            self.logger.info(f"[SCAN][{scan_id}][SNAPSHOT] Snapshot save started in background (non-blocking)")
            
            # Phase 10: Post-Crawl Analysis End
            post_crawl_duration = time.monotonic() - post_crawl_start_time
            self.logger.info(f"[SCAN][{scan_id}][POST_CRAWL] Post-crawl analysis completed in {post_crawl_duration:.2f}s")
            
            # Phase 13: Scan Completion Summary
            total_scan_duration = time.monotonic() - scan_start_time
            timeout_buffer = self.orchestrator.TOTAL_TIMEOUT - crawl_duration if hasattr(self.orchestrator, 'TOTAL_TIMEOUT') else None
            
            self.logger.info(f"[SCAN][{scan_id}][SUMMARY] Scan completed - total_duration={total_scan_duration:.2f}s, crawl_duration={crawl_duration:.2f}s, post_processing_duration={post_crawl_duration:.2f}s" + 
                           (f", timeout_buffer={timeout_buffer:.2f}s" if timeout_buffer is not None and timeout_buffer > 0 else ""))
            
            return json.dumps(final_report, indent=2)
            
        except Exception as e:
            if 'scan_id' in locals():
                self.logger.error(f"[SCAN][{scan_id}][ERROR] Comprehensive scan failed: {e}", exc_info=True)
            self.logger.error(f"[V2.1] Comprehensive scan failed: {e}", exc_info=True)
            return json.dumps({"error": str(e), "url": url})
    
    def _clean_url(self, url: str) -> str:
        """Clean and normalize URL input"""
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
    
    def _check_ssl(self, parsed_url, domain, compliance_data):
        """Check SSL certificate"""
        try:
            if parsed_url.scheme == 'https':
                context = ssl.create_default_context()
                with socket.create_connection((domain, 443), timeout=5) as sock:
                    with context.wrap_socket(sock, server_hostname=domain) as ssock:
                        cert = ssock.getpeercert()
            else:
                compliance_data["general"]["pass"] = False
                compliance_data["general"]["alerts"].append({
                    "code": "NO_HTTPS",
                    "type": "Security",
                    "description": "Website does not use HTTPS."
                })
                compliance_data["general"]["actions_needed"].append({
                    "description": "Install an SSL certificate and enforce HTTPS."
                })
        except Exception as e:
            compliance_data["general"]["pass"] = False
            compliance_data["general"]["alerts"].append({
                "code": "SSL_ERROR",
                "type": "Security",
                "description": f"SSL Handshake failed: {str(e)}"
            })
    
    def _check_domain_age(self, domain, compliance_data):
        """Check domain age via RDAP (more reliable/faster than WHOIS)
        Also returns rich RDAP details for reporting."""
        try:
            # RDAP lookups often fail with www prefix, so strip it
            clean_domain = domain.lower()
            if clean_domain.startswith('www.'):
                clean_domain = clean_domain[4:]
            # Extract TLD for fallback resolution
            tld = clean_domain.split('.')[-1] if '.' in clean_domain else clean_domain
                
            self.logger.info(f"[V2] Checking RDAP for domain: {clean_domain}")
            
            # 1. Try generic RDAP bootstrap
            rdap_url = f"https://rdap.org/domain/{clean_domain}"
            response = requests.get(rdap_url, timeout=5)
            
            # 2. Fallback resolution
            if response.status_code != 200:
                candidate_urls = []
                # Verisign for .com/.net
                if tld in ('com', 'net'):
                    candidate_urls.append(f"https://rdap.verisign.com/{tld}/v1/domain/{clean_domain}")
                # IANA bootstrap mapping (broad coverage)
                try:
                    iana_bootstrap = requests.get("https://data.iana.org/rdap/dns.json", timeout=5)
                    if iana_bootstrap.status_code == 200:
                        data = iana_bootstrap.json()
                        for service in data.get('services', []):
                            tlds, urls = service
                            if tld in tlds:
                                for base in urls:
                                    base = base.rstrip('/')
                                    # Ensure '/domain/' path exists
                                    if not base.endswith('/domain'):
                                        candidate_urls.append(f"{base}/domain/{clean_domain}")
                                    else:
                                        candidate_urls.append(f"{base}/{clean_domain}")
                                break
                except Exception as e:
                    self.logger.debug(f"[V2] IANA RDAP bootstrap fetch failed: {e}")
                
                # Curated registry fallbacks (common modern TLD registries)
                curated_bases = [
                    "https://rdap.identitydigital.services/rdap",   # Identity Digital (Donuts)
                    "https://rdap.donuts.co/rdap",                  # Legacy Donuts
                    "https://rdap.centralnic.com",                  # CentralNic
                    "https://rdap.publicinterestregistry.net/rdap", # PIR (.org)
                    "https://rdap.dot.google/rdap",                 # Google Registry (.app, .dev, ...)
                ]
                for base in curated_bases:
                    base = base.rstrip('/')
                    candidate_urls.append(f"{base}/domain/{clean_domain}")
                
                # Deduplicate while preserving order
                seen = set()
                candidate_urls = [u for u in candidate_urls if not (u in seen or seen.add(u))]
                
                # Try candidates in order
                try:
                    for cand in candidate_urls:
                        resp = requests.get(cand, timeout=5)
                        if resp.status_code == 200:
                            response = resp
                            rdap_url = cand
                            break
                except Exception:
                    pass

            if response.status_code == 200:
                data = response.json()
                events = data.get('events', [])
                creation_date_str = None
                updated_date_str = None
                expires_date_str = None
                
                # Find registration/creation/expiration events
                for event in events:
                    action = event.get('eventAction')
                    if action in ['registration', 'creation'] and not creation_date_str:
                        creation_date_str = event.get('eventDate')
                    if action in ['last changed', 'last update', 'update'] and not updated_date_str:
                        updated_date_str = event.get('eventDate')
                    if action in ['expiration', 'expire', 'expiry'] and not expires_date_str:
                        expires_date_str = event.get('eventDate')
                
                def _parse_iso(d):
                    if not d:
                        return None
                    try:
                        d = d.replace('Z', '+00:00')
                        return datetime.fromisoformat(d)
                    except Exception:
                        return None
                
                creation_date = _parse_iso(creation_date_str)
                updated_date = _parse_iso(updated_date_str)
                expires_date = _parse_iso(expires_date_str)
                
                # Registrar info
                registrar_name = None
                registrar_iana_id = None
                registrar_rdap = None
                entities = data.get('entities', []) or []
                for ent in entities:
                    roles = ent.get('roles', [])
                    if roles and any(r.lower() == 'registrar' for r in roles):
                        # vCard
                        vcard = ent.get('vcardArray', [])
                        try:
                            if isinstance(vcard, list) and len(vcard) >= 2:
                                for item in vcard[1]:
                                    if item and item[0] == 'fn' and len(item) >= 3:
                                        registrar_name = item[3]
                                    if item and item[0] == 'version':
                                        continue
                        except Exception:
                            pass
                        # Public IDs
                        public_ids = ent.get('publicIds', [])
                        if public_ids:
                            for pid in public_ids:
                                if pid.get('type', '').lower() == 'iana registrar id':
                                    registrar_iana_id = pid.get('identifier')
                                    break
                        # Links
                        links = ent.get('links', [])
                        if links:
                            registrar_rdap = links[0].get('href')
                        break
                
                # Nameservers
                nameservers = []
                for ns in data.get('nameservers', []) or []:
                    ldh = ns.get('ldhName') or ns.get('objectClassName') or ''
                    if ldh:
                        nameservers.append(ldh)
                
                # Status codes
                status = data.get('status', []) or []
                
                # DNSSEC
                secure_dns = data.get('secureDNS', {})
                dnssec_enabled = bool(secure_dns) and (secure_dns.get('delegationSigned') or secure_dns.get('dsData') or secure_dns.get('keyData'))
                
                # Compute age
                age_days = None
                if creation_date:
                    now = datetime.now(creation_date.tzinfo) if creation_date.tzinfo else datetime.now()
                    age_days = (now - creation_date).days
                    self.logger.info(f"[V2] Domain age: {age_days} days")
                    if age_days < 365:
                        compliance_data["general"]["alerts"].append({
                            "code": "LOW_VINTAGE",
                            "type": "Risk",
                            "description": f"Domain is only {age_days} days old (less than 1 year)."
                        })
                else:
                    self.logger.warning("[V2] RDAP response missing creation date")
                
                # Build rich details
                rdap_details = {
                    "age_days": age_days,
                    "created_on": creation_date_str,
                    "updated_on": updated_date_str,
                    "expires_on": expires_date_str,
                    "registrar": {
                        "name": registrar_name,
                        "iana_id": registrar_iana_id,
                        "rdap": registrar_rdap
                    },
                    "nameservers": nameservers[:10],
                    "status": status,
                    "dnssec": bool(dnssec_enabled),
                    "rdap_source": rdap_url
                }
                
                return rdap_details
            else:
                 self.logger.warning(f"[V2] RDAP lookup failed: {response.status_code}")
                 
        except Exception as e:
            # Swallow error to prevent scan failure from blocking
            self.logger.warning(f"[V2] RDAP/Domain age check failed: {e}")
            
        # On failure, return minimal structure
        return {
            "age_days": None,
            "created_on": None,
            "updated_on": None,
            "expires_on": None,
            "registrar": None,
            "nameservers": [],
            "status": [],
            "dnssec": None,
            "rdap_source": None
        }
    
    def _update_payment_compliance(self, policy_pages, page_text, compliance_data):
        """Update payment terms compliance based on policies"""
        has_returns = policy_pages["returns_refund"]["found"]
        has_terms = policy_pages["terms_condition"]["found"]
        has_shipping = policy_pages["shipping_delivery"]["found"]
        
        if has_returns and has_terms:
            compliance_data["payment_terms"]["pass"] = True
        else:
            if not has_returns:
                compliance_data["payment_terms"]["actions_needed"].append({
                    "description": "Refund/Return Policy is missing. Please add a clear Refund Policy page."
                })
            if not has_terms:
                compliance_data["payment_terms"]["actions_needed"].append({
                    "description": "Terms & Conditions are missing. Please add a Terms of Service page."
                })
            if not has_shipping and "product" in page_text:
                compliance_data["payment_terms"]["actions_needed"].append({
                    "description": "Shipping Policy is recommended for e-commerce sites."
                })
    
    def _classify_mcc(
        self,
        page_text,
        page_urls: List[str] = None,
        pages_scanned: int = 0,
        page_texts_by_url: dict = None,
        render_types_by_url: dict = None
    ):
        """
        Classify MCC codes based on page content.
        Per PRD V2.1.1: Enforce minimum confidence threshold (30%), show evidence, keep advisory.
        Must show: confidence %, keywords matched, pages contributing, pages scanned vs matched.
        
        Args:
            page_text: Combined page text for keyword matching
            page_urls: List of page URLs where keywords were found (for evidence)
            pages_scanned: Total number of pages scanned (for transparency)
        """
        from analyzers.evidence_builder import EvidenceBuilder
        from analyzers.signal_classifier import SignalClassifier
        
        # Per PRD: Minimum confidence threshold
        MIN_CONFIDENCE_THRESHOLD = 30.0
        # Comprehensive MCC Database with Categories
        mcc_database = {
            "Retail": {
                "Fashion & Clothing": {
                    "5621": {"description": "Women's Ready-to-Wear Stores", "keywords": ["women", "dress", "fashion", "boutique", "bridal", "maternity"]},
                    "5651": {"description": "Family Clothing Stores", "keywords": ["clothing", "apparel", "jeans", "casual", "wear", "family"]},
                    "5691": {"description": "Men's and Women's Clothing Stores", "keywords": ["unisex", "clothing", "apparel", "fashion"]},
                    "5611": {"description": "Men's and Boy's Clothing and Accessories Stores", "keywords": ["men", "suits", "shirts", "ties", "menswear"]},
                    "5631": {"description": "Women's Accessory and Specialty Shops", "keywords": ["accessories", "handbags", "lingerie", "scarves"]}
                },
                "Groceries & Food": {
                    "5411": {"description": "Grocery Stores, Supermarkets", "keywords": ["grocery", "supermarket", "food", "produce", "vegetables", "fruits", "organic"]},
                    "5499": {"description": "Misc. Food Stores - Convenience Stores", "keywords": ["convenience", "snack", "beverage", "kiosk"]},
                    "5462": {"description": "Bakeries", "keywords": ["bakery", "bread", "cake", "pastry", "cookies"]}
                },
                "Electronics & Appliances": {
                    "5732": {"description": "Electronics Stores", "keywords": ["electronics", "computer", "phone", "laptop", "camera", "gadget"]},
                    "5722": {"description": "Household Appliance Stores", "keywords": ["appliance", "refrigerator", "washer", "dryer", "microwave"]}
                },
                "Home & Garden": {
                    "5712": {"description": "Furniture, Home Furnishings, and Equipment Stores", "keywords": ["furniture", "sofa", "bed", "table", "chair", "decor"]},
                    "5200": {"description": "Home Supply Warehouse Stores", "keywords": ["home improvement", "diy", "lumber", "building materials"]},
                    "5261": {"description": "Lawn and Garden Supply Stores", "keywords": ["garden", "plants", "seeds", "fertilizer", "nursery"]}
                }
            },
            "Services": {
                "Professional Services": {
                    "7372": {"description": "Computer Programming, Data Processing, and Integrated Systems Design Services", "keywords": ["software", "saas", "programming", "development", "it services", "cloud", "api", "platform"]},
                    "8999": {"description": "Professional Services (Not Elsewhere Classified)", "keywords": ["consulting", "agency", "professional", "expert"]},
                    "8111": {"description": "Legal Services and Attorneys", "keywords": ["legal", "lawyer", "attorney", "law firm"]}
                },
                "Financial Services": {
                    "6012": {"description": "Financial Institutions – Merchandise and Services", "keywords": ["bank", "banking", "finance", "payment", "payments", "fintech", "transaction"]},
                    "6211": {"description": "Security Brokers and Dealers", "keywords": ["investment", "trading", "stocks", "securities", "broker"]}
                },
                "Education": {
                    "8299": {"description": "Schools and Educational Services (Not Elsewhere Classified)", "keywords": ["course", "training", "learning", "education", "tutor", "class"]},
                    "8220": {"description": "Colleges, Universities, Professional Schools, and Junior Colleges", "keywords": ["university", "college", "degree", "campus"]}
                },
                "Health & Beauty": {
                    "7230": {"description": "Beauty and Barber Shops", "keywords": ["salon", "hair", "beauty", "spa", "barber"]},
                    "8099": {"description": "Medical Services and Health Practitioners (Not Elsewhere Classified)", "keywords": ["health", "medical", "clinic", "care", "wellness"]}
                }
            },
            "Travel & Entertainment": {
                "Travel": {
                    "4722": {"description": "Travel Agencies and Tour Operators", "keywords": ["travel", "tour", "booking", "trip", "vacation"]},
                    "7011": {"description": "Lodging - Hotels, Motels, Resorts, Central Reservation Services", "keywords": ["hotel", "motel", "resort", "stay", "room"]}
                },
                "Dining": {
                    "5812": {"description": "Eating places and Restaurants", "keywords": ["restaurant", "dining", "cafe", "bistro", "food"]},
                    "5814": {"description": "Fast Food Restaurants", "keywords": ["fast food", "burger", "pizza", "takeout", "drive-thru"]}
                }
            }
        }
        
        matched_mccs = []
        
        # Flatten and search
        for category, subcategories in mcc_database.items():
            for subcategory, codes in subcategories.items():
                for mcc_code, details in codes.items():
                    matched_kws = []
                    score = 0
                    pages_contributing = set()
                    for keyword in details["keywords"]:
                        if keyword in page_text:
                            score += 1
                            matched_kws.append(keyword)
                            # Track pages contributing for this MCC match (per plan)
                            if isinstance(page_texts_by_url, dict) and page_texts_by_url:
                                for u, t in page_texts_by_url.items():
                                    try:
                                        if t and keyword in t:
                                            pages_contributing.add(u)
                                    except Exception:
                                        continue
                    
                    if score > 0:
                        matched_mccs.append({
                            "category": category,
                            "subcategory": subcategory,
                            "mcc_code": mcc_code,
                            "description": details["description"],
                            "confidence": min(score * 15, 100),
                            "keywords_matched": matched_kws,
                            "pages_contributing": sorted(list(pages_contributing)) if pages_contributing else (page_urls or [])
                        })
        
        # Sort by confidence
        matched_mccs.sort(key=lambda x: x["confidence"], reverse=True)
        
        # Per PRD V2.1.1: Enforce minimum confidence threshold for Primary MCC
        primary_mcc = None
        secondary_mcc = None
        all_matches = matched_mccs[:10]  # Top 10 matches
        
        if matched_mccs:
            primary = matched_mccs[0]
            if primary["confidence"] >= MIN_CONFIDENCE_THRESHOLD:
                primary_mcc = primary
                # Add evidence per PRD
                primary_mcc["evidence"] = EvidenceBuilder.build_mcc_evidence(
                    matched_keywords=primary.get("keywords_matched", []),
                    pages_matched=page_urls or ["unknown"],
                    confidence=primary["confidence"],
                    render_types_by_url=render_types_by_url
                )
                primary_mcc["signal_type"] = SignalClassifier.classify_signal("mcc_classification")
            else:
                # Below threshold - mark as low confidence
                primary_mcc = {
                    **primary,
                    "confidence": primary["confidence"],
                    "low_confidence": True,
                    "status": "Low confidence classification (below 30% threshold)",
                    "evidence": EvidenceBuilder.build_mcc_evidence(
                        matched_keywords=primary.get("keywords_matched", []),
                        pages_matched=page_urls or ["unknown"],
                        confidence=primary["confidence"],
                        render_types_by_url=render_types_by_url
                    ),
                    "signal_type": SignalClassifier.classify_signal("mcc_classification")
                }
            
            # Secondary MCC (if available and above threshold)
            if len(matched_mccs) > 1:
                secondary = matched_mccs[1]
                if secondary["confidence"] >= MIN_CONFIDENCE_THRESHOLD:
                    secondary_mcc = secondary
                    secondary_mcc["evidence"] = EvidenceBuilder.build_mcc_evidence(
                        matched_keywords=secondary.get("keywords_matched", []),
                        pages_matched=page_urls or ["unknown"],
                        confidence=secondary["confidence"],
                        render_types_by_url=render_types_by_url
                    )
        
        # Add evidence to all matches
        for match in all_matches:
            if "evidence" not in match:
                match["evidence"] = EvidenceBuilder.build_mcc_evidence(
                    matched_keywords=match.get("keywords_matched", []),
                    pages_matched=page_urls or ["unknown"],
                    confidence=match["confidence"],
                    render_types_by_url=render_types_by_url
                )
            match["signal_type"] = SignalClassifier.classify_signal("mcc_classification")
        
        # Per PRD V2.1.1: Show pages contributing and pages scanned vs matched
        primary_pages = []
        try:
            primary_pages = (primary_mcc or {}).get("pages_contributing", []) if isinstance(primary_mcc, dict) else []
        except Exception:
            primary_pages = []
        pages_matched_count = len(primary_pages) if primary_pages else (len(page_urls) if page_urls else 0)
        
        return {
            "primary_mcc": primary_mcc,
            "secondary_mcc": secondary_mcc,
            "all_matches": all_matches,
            "signal_type": SignalClassifier.classify_signal("mcc_classification"),  # Per PRD: Advisory
            "min_confidence_threshold": MIN_CONFIDENCE_THRESHOLD,
            # Per PRD V2.1.1: Transparency metrics
            "pages_scanned": pages_scanned,
            "pages_matched": pages_matched_count,
            "pages_contributing": primary_pages or (page_urls or []),  # URLs contributing to primary MCC
            "classification_method": "Keyword-based dictionary matching"
        }
