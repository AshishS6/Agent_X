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
from datetime import datetime
from urllib.parse import urlparse
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
    
    VERSION = "v2.1"  # Upgraded with CrawlOrchestrator
    
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
            
        Returns:
            JSON string with comprehensive scan results
        """
        try:
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
            page_graph = asyncio.run(self.orchestrator.crawl(url))
            
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
                 # Return limited report
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
            
            # Check SSL
            self._check_ssl(parsed_url, domain, compliance_data)
            
            # Check domain age
            domain_vintage_days = self._check_domain_age(domain, compliance_data)
            
            report_builder.add_compliance_data(compliance_data)
            
            # Parse HTML and extract data using modular components
            if page_data.get('success'):
                soup = crawler.parse_html(page_data['content'])
                html_text = page_data['text']
                page_text = soup.get_text(separator=' ', strip=True).lower()
                
                # Extract links
                all_links = LinkExtractor.extract_all_links(soup, final_url)
                
                # Detect policies - Enhanced with page graph data
                policy_pages = PolicyDetector.detect_policies(all_links, final_url)
                
                # Enhance policy_pages with pages discovered by orchestrator
                page_type_mapping = {
                    'about': 'about_us',
                    'contact': 'contact_us',
                    'privacy_policy': 'privacy_policy',
                    'terms_conditions': 'terms_condition',
                    'refund_policy': 'returns_refund',
                    'shipping_delivery': 'shipping_delivery',
                    'product': 'product',
                    'pricing': 'pricing',
                    'faq': 'faq'
                }
                for graph_type, policy_key in page_type_mapping.items():
                    page = page_graph.get_page_by_type(graph_type)
                    if page and page.status == 200 and policy_key in policy_pages:
                        if not policy_pages[policy_key].get('found'):
                            policy_pages[policy_key] = {
                                'found': True,
                                'url': page.url,
                                'status': f"{policy_key.replace('_', ' ').title()} page discovered by orchestrator"
                            }
                
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
                
                # Content Risk Analysis
                content_risk = ContentAnalyzer.analyze_content_risk(page_text)
                report_builder.add_content_risk(content_risk)
                
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
                
                # Extract product names from headings (simple heuristic)
                try:
                    if prod_soup:
                        h2_tags = prod_soup.find_all(['h2', 'h3'], limit=10)
                        for h_tag in h2_tags:
                            heading_text = h_tag.get_text(strip=True)
                            # Skip generic headings
                            if heading_text and len(heading_text) > 3 and len(heading_text) < 100:
                                skip_words = ['about', 'contact', 'home', 'menu', 'navigation', 'footer', 'header']
                                if not any(sw in heading_text.lower() for sw in skip_words):
                                    product_indicators["extracted_products"].append({
                                        "name": heading_text,
                                        "brief_description": "Product/Feature identified from page",
                                        "price_if_found": None
                                    })
                        # Limit to first 5 products
                        product_indicators["extracted_products"] = product_indicators["extracted_products"][:5]
                except Exception as e:
                    self.logger.warning(f"[V2.1] Product extraction warning: {e}")
                
                report_builder.add_product_details(product_indicators)
                
                # MCC Classification
                mcc_data = self._classify_mcc(page_text)
                report_builder.add_mcc_codes(mcc_data)
                
                # Phase E.1: Business Context Classification
                self.logger.info("[V2.1] Classifying Business Context...")
                business_context = self.context_classifier.classify(
                    tech_stack,
                    product_indicators,
                    page_text,
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
            
            change_report = self.change_detector.compare(current_snapshot_data, previous_snapshot)
            
            # Add change detection to final report
            # Wrapping it inside comprehensive_site_scan to keep structure clean
            if "comprehensive_site_scan" in final_report:
                final_report["comprehensive_site_scan"]["change_detection"] = change_report
                
                # Run Change Intelligence (Phase D)
                intelligence_report = self.intelligence_engine.analyze_intelligence(change_report)
                final_report["comprehensive_site_scan"]["change_intelligence"] = intelligence_report
            
            # Save new snapshot
            self.change_detector.save_snapshot(task_id, url, page_graph, final_report)
            
            return json.dumps(final_report, indent=2)
            
        except Exception as e:
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
        """Check domain age via RDAP (more reliable/faster than WHOIS)"""
        try:
            # RDAP lookups often fail with www prefix, so strip it
            clean_domain = domain.lower()
            if clean_domain.startswith('www.'):
                clean_domain = clean_domain[4:]
                
            self.logger.info(f"[V2] Checking RDAP for domain: {clean_domain}")
            
            # 1. Try generic RDAP bootstrap
            rdap_url = f"https://rdap.org/domain/{clean_domain}"
            response = requests.get(rdap_url, timeout=5)
            
            # 2. Fallback for .com/.net if generic fails (often more reliable)
            if response.status_code != 200 and (clean_domain.endswith('.com') or clean_domain.endswith('.net')):
                self.logger.info(f"[V2] Generic RDAP failed, trying Verisign fallback...")
                rdap_url = f"https://rdap.verisign.com/com/v1/domain/{clean_domain}" if clean_domain.endswith('.com') else f"https://rdap.verisign.com/net/v1/domain/{clean_domain}"
                try:
                    response = requests.get(rdap_url, timeout=5)
                except Exception:
                    pass # Keep original response if fallback errors out

            if response.status_code == 200:
                data = response.json()
                events = data.get('events', [])
                creation_date_str = None
                
                # Find registration/creation event
                for event in events:
                    if event.get('eventAction') in ['registration', 'creation', 'last changed']:
                        creation_date_str = event.get('eventDate')
                        if event.get('eventAction') == 'registration':
                            break # Prefer registration date
                
                if creation_date_str:
                    # Parse ISO format (e.g., 2020-05-15T10:00:00Z)
                    creation_date_str = creation_date_str.replace('Z', '+00:00')
                    creation_date = datetime.fromisoformat(creation_date_str)
                    
                    if creation_date.tzinfo:
                        now = datetime.now(creation_date.tzinfo)
                    else:
                        now = datetime.now()
                    
                    age_days = (now - creation_date).days
                    self.logger.info(f"[V2] Domain age: {age_days} days")
                    
                    if age_days < 365:
                        compliance_data["general"]["alerts"].append({
                            "code": "LOW_VINTAGE",
                            "type": "Risk",
                            "description": f"Domain is only {age_days} days old (less than 1 year)."
                        })
                    
                    return age_days
                else:
                    self.logger.warning("[V2] RDAP response missing creation date")
            else:
                 self.logger.warning(f"[V2] RDAP lookup failed: {response.status_code}")
                 
        except Exception as e:
            # Swallow error to prevent scan failure from blocking
            self.logger.warning(f"[V2] RDAP/Domain age check failed: {e}")
            
        return None
    
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
    
    def _classify_mcc(self, page_text):
        """Classify MCC codes based on page content"""
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
                    for keyword in details["keywords"]:
                        if keyword in page_text:
                            score += 1
                            matched_kws.append(keyword)
                    
                    if score > 0:
                        matched_mccs.append({
                            "category": category,
                            "subcategory": subcategory,
                            "mcc_code": mcc_code,
                            "description": details["description"],
                            "confidence": min(score * 15, 100),
                            "keywords_matched": matched_kws
                        })
        
        # Sort by confidence
        matched_mccs.sort(key=lambda x: x["confidence"], reverse=True)
        
        return {
            "primary_mcc": matched_mccs[0] if matched_mccs else None,
            "secondary_mcc": matched_mccs[1] if len(matched_mccs) > 1 else None,
            "all_matches": matched_mccs[:10]  # Top 10 matches
        }
