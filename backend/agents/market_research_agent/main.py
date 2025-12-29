"""
Market Research Agent Implementation
Handles market research, competitor analysis, and compliance monitoring
Using free tools: DuckDuckGo Search and BeautifulSoup
"""

# Path setup to allow running from any directory
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import requests
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from langchain.tools import tool
from duckduckgo_search import DDGS

from shared.base_agent import BaseAgent, AgentConfig


class MarketResearchAgent(BaseAgent):
    """
    Market Research Agent - Comprehensive intelligence gathering
    
    Capabilities:
    - Multi-source web research (via DuckDuckGo)
    - Competitor analysis and monitoring
    - Trend tracking
    - Compliance and risk monitoring
    - Web crawling for specific content
    - Automated report generation
    """
    
    def _register_tools(self):
        """Register market research-specific tools"""
        try:
            self.logger.info("Registering market research tools...")
            
            @tool
            def search_web(query: str, max_results: int = 5) -> str:
                """
                Search the web for information using DuckDuckGo (Free).
                
                Args:
                    query: Search query
                    max_results: Number of results to return (default: 5)
                
                Returns:
                    Search results with titles, snippets, and links
                """
                try:
                    results = []
                    with DDGS() as ddgs:
                        # Use text search
                        search_results = list(ddgs.text(query, max_results=max_results))
                        
                        for i, r in enumerate(search_results):
                            results.append(f"{i+1}. {r['title']}\n   Source: {r['href']}\n   Snippet: {r['body']}\n")
                    
                    if not results:
                        return f"No results found for query: {query}"
                    
                    return "\n".join(results)
                except Exception as e:
                    return f"Error performing search: {str(e)}"

            # Add logging to monitor_url
            # We need to inject logging into the inner function or wrap it
            # Since we are inside _register_tools, we can use self.logger
            
            # Let's redefine monitor_url with logging
            @tool
            def monitor_url(url: str, keywords: str = "", max_pages: int = 0, depth: int = 1, respect_robots_txt: bool = True, delay: float = 1.0) -> str:
                """
                Crawl a URL with advanced options.
                
                CRITICAL: You must return the raw JSON string output from this tool EXACTLY as is. 
                DO NOT summarize. DO NOT reformat. DO NOT wrap in markdown.
                Just return the JSON string.
                
                Args:
                    url: Base URL to monitor
                    keywords: Comma-separated keywords
                    max_pages: Max pages (0 for unlimited)
                    depth: Crawl depth
                    respect_robots_txt: Respect robots.txt
                    delay: Request delay
                
                Returns:
                    str: Raw JSON report
                """
                self.logger.info(f"Starting crawl for URL: {url} (Depth: {depth}, Max: {max_pages})")
                try:
                    import time
                    from urllib.parse import urljoin, urlparse
                    from urllib.robotparser import RobotFileParser
                    import re
                    
                    headers = {
                        'User-Agent': 'Agent_X_MarketResearchBot/1.0'
                    }
                    
                    # 1. Check robots.txt
                    if respect_robots_txt:
                        parsed_url = urlparse(url)
                        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
                        rp = RobotFileParser()
                        try:
                            self.logger.info(f"Checking robots.txt at {robots_url}")
                            rp.set_url(robots_url)
                            rp.read()
                            if not rp.can_fetch(headers['User-Agent'], url):
                                return json.dumps({
                                    "error": "Crawling forbidden by robots.txt",
                                    "url": url
                                }, indent=2)
                        except Exception as e:
                            self.logger.warning(f"Could not check robots.txt: {e}. Proceeding with caution.")

                    # Helper to crawl a single page
                    def crawl_page(page_url):
                        try:
                            self.logger.info(f"Crawling page: {page_url}")
                            time.sleep(delay) # Polite delay
                            resp = requests.get(page_url, headers=headers, timeout=10)
                            if resp.status_code != 200: 
                                self.logger.warning(f"Failed to fetch {page_url}: Status {resp.status_code}")
                                return None
                            
                            soup = BeautifulSoup(resp.content, 'html.parser')
                            
                            # Clean
                            for element in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "iframe", "svg"]):
                                element.decompose()
                                
                            text = soup.get_text(separator='\n', strip=True)
                            lines = (line.strip() for line in text.splitlines())
                            clean_text = '\n'.join(line for line in lines if line)
                            
                            # Find keywords WITH CONTEXT
                            keyword_matches = []  # List of {keyword, context, position}
                            if keywords:
                                keyword_list = [k.strip().lower() for k in keywords.split(',')]
                                
                                # Split text into sentences for context extraction
                                import re
                                sentences = re.split(r'(?<=[.!?])\s+', clean_text)
                                
                                for i, sentence in enumerate(sentences):
                                    sentence_lower = sentence.lower()
                                    for keyword in keyword_list:
                                        if keyword in sentence_lower:
                                            # Get context: current sentence + prev/next if available
                                            context_sentences = []
                                            if i > 0:
                                                context_sentences.append(sentences[i-1])
                                            context_sentences.append(sentence)
                                            if i < len(sentences) - 1:
                                                context_sentences.append(sentences[i+1])
                                            
                                            context = ' '.join(context_sentences)
                                            
                                            # Highlight the keyword in context (for JSON, we'll use **bold**)
                                            highlighted_context = re.sub(
                                                f'({re.escape(keyword)})',
                                                r'**\1**',
                                                context,
                                                flags=re.IGNORECASE
                                            )
                                            
                                            keyword_matches.append({
                                                'keyword': keyword,
                                                'context': highlighted_context,
                                                'sentence_index': i
                                            })
                            
                            # Extract links for recursion
                            links = []
                            for a_tag in soup.find_all('a', href=True):
                                href = a_tag['href']
                                full_url = urljoin(page_url, href)
                                # Only follow internal links or same domain
                                if urlparse(full_url).netloc == urlparse(url).netloc:
                                    links.append(full_url)

                            return {
                                "url": page_url,
                                "title": soup.title.string if soup.title else "No Title",
                                "text": clean_text,
                                "keyword_matches": keyword_matches,  # NEW: Detailed matches
                                "links": links,
                                "length": len(clean_text)
                            }
                        except Exception as e:
                            self.logger.error(f"Error crawling page {page_url}: {e}")
                            return None

                    # BFS Crawl
                    visited = set()
                    queue = [(url, 1)] # (url, current_depth)
                    results = []
                    
                    # If max_pages is 0 or negative, treat as unlimited (bounded by depth)
                    while queue and (max_pages <= 0 or len(results) < max_pages):
                        current_url, current_depth = queue.pop(0)
                        
                        if current_url in visited:
                            continue
                        
                        visited.add(current_url)
                        
                        # Check robots.txt for this specific URL if needed (simplified here to just base check above for now, 
                        # but ideally should check every URL if strict)
                        
                        page_data = crawl_page(current_url)
                        if page_data:
                            # Add to results (exclude links to keep JSON smaller)
                            result_entry = {k: v for k, v in page_data.items() if k != 'links'}
                            results.append(result_entry)
                            
                            # Add children to queue if depth allows
                            if current_depth < depth:
                                for link in page_data['links']:
                                    if link not in visited:
                                        queue.append((link, current_depth + 1))
                    
                    # Aggregate Report
                    total_keyword_matches = sum(len(r.get('keyword_matches', [])) for r in results)
                    
                    report = {
                        "base_url": url,
                        "pages_crawled": len(results),
                        "total_keyword_matches": total_keyword_matches,
                        "pages": []
                    }
                    
                    for res in results:
                        keyword_matches_data = res.get('keyword_matches', [])
                        
                        page_summary = {
                            "url": res['url'],
                            "title": res['title'],
                            "keyword_matches": keyword_matches_data,  # NEW: Full match details
                            "content_snippet": res['text'][:500] + "..." if len(res['text']) > 500 else res['text']
                        }
                        report["pages"].append(page_summary)

                    return json.dumps(report, indent=2)

                except Exception as e:
                    self.logger.error(f"Error crawling URL {url}: {str(e)}")
                    return json.dumps({"error": str(e)})

            @tool
            def comprehensive_site_scan(url: str, business_name: str = "") -> str:
                """
                Comprehensive website compliance and risk assessment scan.
                
                CRITICAL: You must return the raw JSON string output from this tool EXACTLY as is. 
                DO NOT summarize. DO NOT reformat. DO NOT wrap in markdown.
                Just return the JSON string.
                
                Args:
                    url: Website URL to scan
                    business_name: Business/Billing name (optional)
                
                Returns:
                    str: Raw JSON report with compliance, policy, MCC, and risk analysis
                """
                try:
                    import whois
                    import ssl
                    import socket
                    from datetime import datetime
                    from urllib.parse import urlparse, urljoin
                    import re
                    import time
                    
                    # Clean URL input (handle cases where LLM passes "url: https://..." or other garbage)
                    cleaned_url = url.strip()
                    # Remove "url:" prefix if present (case insensitive)
                    if re.match(r'^url:\s*', cleaned_url, re.IGNORECASE):
                        cleaned_url = re.sub(r'^url:\s*', '', cleaned_url, flags=re.IGNORECASE)
                    
                    # If the URL string contains other arguments like ", business_name:", split and take the first part
                    if ',' in cleaned_url and ('http://' in cleaned_url or 'https://' in cleaned_url):
                        # Simple heuristic: assume URL is the first part before a comma
                        cleaned_url = cleaned_url.split(',')[0].strip()
                        
                    # Ensure scheme
                    if not cleaned_url.startswith(('http://', 'https://')):
                        cleaned_url = 'https://' + cleaned_url
                        
                    url = cleaned_url
                    self.logger.info(f"Starting comprehensive scan for: {url}")
                    
                    # Initialize report structure
                    report = {
                        "url": url,
                        "business_name": business_name,
                        "scan_timestamp": datetime.now().isoformat(),
                        "compliance_checks": {},
                        "policy_details": {},
                        "mcc_codes": {},
                        "product_details": {},
                        "business_details": {}
                    }
                    
                    parsed_url = urlparse(url)
                    domain = parsed_url.netloc or parsed_url.path
                    
                    # ===========================================
                    # 1. COMPLIANCE CHECKS & ALERTS
                    # ===========================================
                    
                    # New Schema for Frontend "Enhanced Report"
                    compliance_data = {
                        "general": {
                            "pass": True,
                            "alerts": [],
                            "actions_needed": []
                        },
                        "payment_terms": {
                            "pass": False, # Will be updated based on policy checks
                            "alerts": [],
                            "actions_needed": []
                        }
                    }
                    
                    # Check Liveness
                    try:
                        headers = {'User-Agent': 'Agent_X_ComplianceScanner/1.0'}
                        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
                        final_url = response.url
                        
                        if response.status_code != 200:
                            compliance_data["general"]["pass"] = False
                            compliance_data["general"]["alerts"].append({
                                "code": "LIVENESS_FAIL",
                                "type": "Availability",
                                "description": f"Website returned status code {response.status_code}"
                            })
                            compliance_data["general"]["actions_needed"].append({
                                "description": "Ensure website is publicly accessible and returning 200 OK."
                            })
                            
                    except Exception as e:
                        compliance_data["general"]["pass"] = False
                        compliance_data["general"]["alerts"].append({
                            "code": "CONNECTION_FAIL",
                            "type": "Connectivity",
                            "description": f"Failed to connect: {str(e)}"
                        })
                         # If we can't connect, likely everything else will fail too
                        final_url = url

                    # Check Redirections
                    if len(response.history) > 1:
                         compliance_data["general"]["alerts"].append({
                            "code": "EXCESSIVE_REDIRECTS",
                            "type": "Performance",
                            "description": f"{len(response.history)} redirects detected."
                        })

                    # Check SSL Certificate
                    try:
                        if parsed_url.scheme == 'https':
                            context = ssl.create_default_context()
                            with socket.create_connection((domain, 443), timeout=5) as sock:
                                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                                    cert = ssock.getpeercert()
                                    # Basic validation passed if no exception
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
                        compliance_data["general"]["actions_needed"].append({
                            "description": "Verify SSL certificate validity."
                        })
                    
                    # Check Domain Age (Vintage)
                    try:
                        self.logger.info(f"Checking WHOIS for domain: {domain}")
                        w = whois.whois(domain)
                        creation_date = w.get('creation_date')
                        
                         # Handle list or single date
                        if isinstance(creation_date, list):
                            creation_date = creation_date[0]
                            
                        if creation_date:
                            if creation_date.tzinfo:
                                now = datetime.now(creation_date.tzinfo)
                            else:
                                now = datetime.now()
                            
                            age_days = (now - creation_date).days
                            
                            if age_days < 365:
                                compliance_data["general"]["alerts"].append({
                                    "code": "LOW_VINTAGE",
                                    "type": "Risk",
                                    "description": f"Domain is only {age_days} days old (less than 1 year)."
                                })
                        else:
                             # WHOIS often fails or returns None for hidden domains, treats as Warning not Fail
                             pass
                                
                    except Exception as e:
                        self.logger.warning(f"WHOIS lookup failed: {e}")
                    
                    report["compliance_checks"] = compliance_data # Legacy key for existing consumers? 
                    # THE FRONTEND uses 'compliance_checks' BUT checks for nested 'general' or 'payment_terms' inside it in the new view. 
                    # Wait, looking at frontend code:
                    # const siteScan = crawlData.comprehensive_site_scan;
                    # siteScan.compliance?.general?.pass
                    # So the report structure should be:
                    # report = { ... "compliance": { "general": ... } }  <-- Note key is "compliance" in frontend specific view
                    # But the variable initialized in line 299 as "compliance_checks".
                    # Let's add BOTH to be safe, or rename. 
                    
                    report["compliance"] = compliance_data
                    report["compliance_checks"] = compliance_data # Keep legacy structure populated above for backward compat if needed? 
                    # Actually, let's just make sure "compliance" key exists as that's what `siteScan.compliance` expects.

                    
                    # ===========================================
                    # 2. CRAWL WEBSITE FOR POLICY & CONTENT
                    # ===========================================
                    
                    try:
                        time.sleep(0.5)
                        resp = requests.get(final_url, headers=headers, timeout=10)
                        soup = BeautifulSoup(resp.content, 'html.parser')
                        
                        # Find all links
                        all_links = []
                        for a in soup.find_all('a', href=True):
                            href = a['href']
                            full_url = urljoin(final_url, href)
                            link_text = a.get_text(strip=True).lower()
                            all_links.append({"url": full_url, "text": link_text})
                        
                        # Extract text once for all analyses
                        page_text = soup.get_text(separator=' ', strip=True).lower()
                        
                        # ===========================================
                        # 3. POLICY PAGE DETECTION
                        # ===========================================
                        
                        policy_pages = {
                            "home_page": {"found": False, "url": final_url, "status": ""},
                            "privacy_policy": {"found": False, "url": "", "status": ""},
                            "shipping_delivery": {"found": False, "url": "", "status": ""},
                            "returns_refund": {"found": False, "url": "", "status": ""},
                            "terms_condition": {"found": False, "url": "", "status": ""},
                            "contact_us": {"found": False, "url": "", "status": ""},
                            "about_us": {"found": False, "url": "", "status": ""},
                            "faq": {"found": False, "url": "", "status": ""},
                            "product": {"found": False, "url": "", "status": ""},
                            "pricing": {"found": False, "url": "", "status": ""}
                        }
                        
                        # Home page is available by default
                        policy_pages["home_page"] = {
                            "found": True,
                            "url": final_url,
                            "status": "Home Page page is available"
                        }
                        
                        # Policy page patterns
                        patterns = {
                            "privacy_policy": [
                                r'privacy[-_]?policy', r'privacy', r'gdpr', r'data[-_]?protection'
                            ],
                            "terms_condition": [
                                r'terms?[-_]?(and[-_]?|&[-_]?)?conditions?', r'terms?[-_]?of[-_]?(service|use)', r't&c', r'tos'
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
                                r'about[-_]?us', r'about', r'who[-_]?we[-_]?are', r'company'
                            ],
                            "faq": [
                                r'faq', r'frequently[-_]?asked', r'help'
                            ],
                            "product": [
                                r'products?', r'shop', r'store', r'catalog', r'solutions?'
                            ],
                            "pricing": [
                                r'pricing', r'plans', r'subscription', r'fees'
                            ]
                        }
                        
                        for link_data in all_links:
                            link_url = link_data["url"]
                            link_text = link_data["text"]
                            link_path = urlparse(link_url).path.lower()
                            
                            for page_type, page_patterns in patterns.items():
                                if not policy_pages[page_type]["found"]:
                                    for pattern in page_patterns:
                                        if re.search(pattern, link_text) or re.search(pattern, link_path):
                                            policy_pages[page_type] = {
                                                "found": True,
                                                "url": link_url,
                                                "status": f"{page_type.replace('_', ' ').title()} page is available"
                                            }
                                            break
                        
                        report["policy_details"] = policy_pages
                        
                        # Logic to update Payment Terms status based on found policies
                        has_returns = policy_pages["returns_refund"]["found"]
                        has_terms = policy_pages["terms_condition"]["found"]
                        has_shipping = policy_pages["shipping_delivery"]["found"]
                        
                        if has_returns and has_terms:
                            compliance_data["payment_terms"]["pass"] = True
                        else:
                            compliance_data["payment_terms"]["pass"] = False
                            if not has_returns:
                                compliance_data["payment_terms"]["actions_needed"].append({
                                    "description": "Refund/Return Policy is missing. Please add a clear Refund Policy page."
                                })
                            if not has_terms:
                                compliance_data["payment_terms"]["actions_needed"].append({
                                    "description": "Terms & Conditions are missing. Please add a Terms of Service page."
                                })
                            if not has_shipping and "product" in page_text: # Only if it looks like a shop
                                 compliance_data["payment_terms"]["actions_needed"].append({
                                    "description": "Shipping Policy is recommended for e-commerce sites."
                                })

                        # Update the compliance object in report
                        report["compliance"] = compliance_data
                        
                        # ===========================================
                        # 4. BUSINESS NAME & DETAILS EXTRACTION
                        # ===========================================
                        
                        business_info = {
                            "extracted_business_name": business_name,
                            "company_summary": "Not found",
                            "mission_vision": "Not found",
                            "key_offerings": "Not found",
                            "source_urls": {
                                "about_us": policy_pages["about_us"]["url"] if policy_pages["about_us"]["found"] else None,
                                "contact_us": policy_pages["contact_us"]["url"] if policy_pages["contact_us"]["found"] else None,
                                "home": final_url
                            },
                            "contact_info": {
                                "email": "Not found",
                                "phone": "Not found",
                                "address": "Not found"
                            }
                        }

                        # Function to fetch and clean text from a page with better headers
                        def get_clean_page_text(page_url):
                            try:
                                browser_headers = {
                                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                                    'Accept-Language': 'en-US,en;q=0.9',
                                }
                                p_resp = requests.get(page_url, headers=browser_headers, timeout=10)
                                if p_resp.status_code == 200:
                                    p_soup = BeautifulSoup(p_resp.content, 'html.parser')
                                    for el in p_soup(["script", "style", "nav", "footer", "header", "aside"]):
                                        el.decompose()
                                    return p_soup.get_text(separator=' ', strip=True)
                                else:
                                    self.logger.warning(f"Failed to fetch {page_url}: Status {p_resp.status_code}")
                            except Exception as e:
                                self.logger.warning(f"Error fetching {page_url}: {e}")
                            return ""

                        # 4.1 Extract Business Name if not provided
                        if not business_name:
                            # Try to extract from footer, about, or copyright
                            footer = soup.find('footer')
                            if footer:
                                copyright_item = footer.find(text=re.compile(r'©|\(c\)|copyright', re.I))
                                if copyright_item:
                                    # Extract company name from copyright text
                                    match = re.search(r'(?:©|\(c\)|copyright)\s*(?:\d{4})?\s*([A-Z][\w\s&,.-]+)', copyright_item, re.I)
                                    if match:
                                        business_name = match.group(1).strip()
                            
                            # Fallback: Check title
                            if not business_name and soup.title:
                                # Often title is "Brand Name - Tagline"
                                title_str = soup.title.string or ""
                                title_parts = title_str.split('-')
                                if title_parts:
                                    business_name = title_parts[0].strip()
                            
                            # Fallback: Check for meta og:site_name
                            if not business_name:
                                og_site_name = soup.find("meta", property="og:site_name")
                                if og_site_name:
                                    business_name = og_site_name.get("content", "").strip()
                        
                        business_info["extracted_business_name"] = business_name or "Not found"

                        # 4.2 Visit About Us page for summary and offerings
                        if policy_pages["about_us"]["found"]:
                            self.logger.info(f"Visiting About Us for details: {policy_pages['about_us']['url']}")
                            about_text = get_clean_page_text(policy_pages["about_us"]["url"])
                            if about_text:
                                # Simple extraction (can be improved with LLM later if needed)
                                business_info["company_summary"] = about_text[:1000] + "..." if len(about_text) > 1000 else about_text
                                
                                # Try to find Mission/Vision with more patterns
                                mv_patterns = [
                                    r'(?:mission|vision|our\s+goal|purpose)\s*:?\s*([^.!?]{20,500}[.!?])',
                                    r'(?:strive\s+to|aim\s+to|committed\s+to)\s+([^.!?]{20,500}[.!?])'
                                ]
                                for mv_p in mv_patterns:
                                    mv_match = re.search(mv_p, about_text, re.I)
                                    if mv_match:
                                        business_info["mission_vision"] = mv_match.group(1).strip()
                                        break
                                
                                # Try to find offerings with more patterns
                                off_patterns = [
                                    r'(?:offerings|services|products|solutions|we\s+provide|features)\s*(?:include|are|offer)\s*:?\s*([^.!?]{20,500})',
                                    r'(?:wide\s+range\s+of)\s+([^.!?]{20,500})'
                                ]
                                for off_p in off_patterns:
                                    off_match = re.search(off_p, about_text, re.I)
                                    if off_match:
                                        business_info["key_offerings"] = off_match.group(1).strip()
                                        break

                        # 4.3 Visit Contact Us page for contact details
                        # Also check home page footer/content for contact info
                        contact_urls = []
                        if policy_pages["contact_us"]["found"]:
                            contact_urls.append(policy_pages["contact_us"]["url"])
                        contact_urls.append(final_url) # Always check home page
                        
                        for c_url in contact_urls:
                            self.logger.info(f"Checking for contact info on: {c_url}")
                            contact_text = get_clean_page_text(c_url)
                            if contact_text:
                                # Extract email
                                if business_info["contact_info"]["email"] == "Not found":
                                    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', contact_text)
                                    if email_match:
                                        business_info["contact_info"]["email"] = email_match.group(0)
                                
                                # Extract phone
                                if business_info["contact_info"]["phone"] == "Not found":
                                    phone_match = re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', contact_text)
                                    if phone_match:
                                        business_info["contact_info"]["phone"] = phone_match.group(0)
                                
                                # Extract Address
                                if business_info["contact_info"]["address"] == "Not found":
                                    # Look for common address patterns (e.g., Street, City, State, ZIP)
                                    addr_match = re.search(r'(?:\d{1,5}\s+[\w\s,.]+?(?:Street|St|Avenue|Ave|Road|Rd|Highway|Hwy|Square|Sq|Drive|Dr|Lane|Ln|Court|Ct|Parkway|Pkwy|Circle|Cir),\s*[\w\s]{2,}\s+\d{5,6})', contact_text, re.I)
                                    if addr_match:
                                        business_info["contact_info"]["address"] = addr_match.group(0)

                        report["business_details"] = business_info
                        
                        # ===========================================
                        # 5. CONTENT RISK DETECTION
                        # ===========================================
                        
                        # page_text extracted above
                        
                        #  Lorem ipsum detection
                        lorem_ipsum_patterns = [
                            r'lorem\s+ipsum\s+dolor\s+sit\s+amet',
                            r'consectetur\s+adipiscing',
                            r'sed\s+do\s+eiusmod'
                        ]
                        
                        dummy_words_found = []
                        for pattern in lorem_ipsum_patterns:
                            if re.search(pattern, page_text):
                                dummy_words_found.append(pattern)
                        
                        # Check for restricted keywords (basic set)
                        restricted_keywords = {
                            "gambling": ["casino", "poker", "betting", "slots", "lottery"],
                            "adult": ["xxx", "adult content", "nsfw"],
                            "crypto": ["cryptocurrency", "bitcoin", "ico"],
                            "pharmacy": ["viagra", "cialis", "prescription drugs"]
                        }
                        
                        restricted_found = []
                        for category, keywords in restricted_keywords.items():
                            for keyword in keywords:
                                if keyword in page_text:
                                    restricted_found.append({
                                        "category": category,
                                        "keyword": keyword
                                    })
                        
                        report["content_risk"] = {
                            "dummy_words_detected": len(dummy_words_found) > 0,
                            "dummy_words": dummy_words_found,
                            "restricted_keywords_found": restricted_found,
                            "risk_score": len(restricted_found) * 20 + (50 if len(dummy_words_found) > 0 else 0)
                        }
                        
                        # ===========================================
                        # 6. MCC CODE CLASSIFICATION
                        # ===========================================
                        
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
                                    "7372": {"description": "Computer Programming, Data Processing, and Integrated Systems Design Services", "keywords": ["software", "saas", "programming", "development", "it services", "cloud"]},
                                    "8999": {"description": "Professional Services (Not Elsewhere Classified)", "keywords": ["consulting", "agency", "professional", "expert"]},
                                    "8111": {"description": "Legal Services and Attorneys", "keywords": ["legal", "lawyer", "attorney", "law firm"]}
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
                                    score = 0
                                    for keyword in details["keywords"]:
                                        if keyword in page_text:
                                            score += 1
                                    
                                    if score > 0:
                                        matched_mccs.append({
                                            "category": category,
                                            "subcategory": subcategory,
                                            "mcc_code": mcc_code,
                                            "description": details["description"],
                                            "confidence": min(score * 15, 100),
                                            "keywords_matched": score
                                        })
                        
                        # Sort by confidence
                        matched_mccs.sort(key=lambda x: x["confidence"], reverse=True)
                        
                        report["mcc_codes"] = {
                            "primary_mcc": matched_mccs[0] if matched_mccs else None,
                            "secondary_mcc": matched_mccs[1] if len(matched_mccs) > 1 else None,
                            "all_matches": matched_mccs[:10]  # Top 10 matches
                        }
                        
                        # ===========================================
                        # 7. PRODUCT/SERVICE DETECTION
                        # ===========================================
                        
                        # Look for product indicators
                        product_indicators = {
                            "has_products": "product" in page_text or "shop" in page_text or "solution" in page_text,
                            "has_pricing": "price" in page_text or "$" in page_text or "₹" in page_text or "pricing" in page_text,
                            "has_cart": "add to cart" in page_text or "buy now" in page_text,
                            "ecommerce_platform": "shopify" in page_text or "woocommerce" in page_text,
                            "extracted_products": [],
                            "pricing_model": "Not found",
                            "source_pages": {
                                "product_page": policy_pages["product"]["url"] if policy_pages["product"]["found"] else None,
                                "pricing_page": policy_pages["pricing"]["url"] if policy_pages["pricing"]["found"] else None
                            }
                        }

                        # 7.1 Deep Product Extraction with LLM
                        content_for_ai = page_text[:2000] # Primary page text
                        
                        # Fetch and append product page content if different
                        if product_indicators["source_pages"]["product_page"] and product_indicators["source_pages"]["product_page"] != final_url:
                            p_text = get_clean_page_text(product_indicators["source_pages"]["product_page"])
                            content_for_ai += "\n\nPRODUCT PAGE CONTENT:\n" + p_text[:2000]
                            
                        # Fetch and append pricing page content if different
                        if product_indicators["source_pages"]["pricing_page"] and product_indicators["source_pages"]["pricing_page"] != final_url:
                            pr_text = get_clean_page_text(product_indicators["source_pages"]["pricing_page"])
                            content_for_ai += "\n\nPRICING PAGE CONTENT:\n" + pr_text[:2000]

                        try:
                            self.logger.info(f"Extracting product details via LLM for {domain}")
                            product_prompt = f"""
                            Review the following website content for {domain} and extract details about their products, services, and pricing.
                            
                            WEBSITE CONTENT:
                            {content_for_ai}
                            
                            Return the result as a JSON object with:
                            - "products": [list of products/services with name, brief_description, and price_if_found]
                            - "pricing_model": (e.g., Subscription, One-time, Free, Quote-based)
                            - "target_audience": (brief description of who this is for)
                            
                            Be concise and accurate. If not found, use empty list or "Not found".
                            """
                            
                            from langchain.schema import HumanMessage, SystemMessage
                            messages = [
                                SystemMessage(content="You are a precise data extraction specialist for market research."),
                                HumanMessage(content=product_prompt)
                            ]
                            
                            ai_resp = self.llm.invoke(messages)
                            ai_content = ai_resp.content
                            
                            # Clean up markdown if present
                            if "```json" in ai_content:
                                ai_content = ai_content.split("```json")[1].split("```")[0].strip()
                            elif "```" in ai_content:
                                ai_content = ai_content.split("```")[1].split("```")[0].strip()
                                
                            extracted = json.loads(ai_content)
                            product_indicators["extracted_products"] = extracted.get("products", [])
                            product_indicators["pricing_model"] = extracted.get("pricing_model", "Not found")
                            product_indicators["target_audience"] = extracted.get("target_audience", "Not found")
                            
                        except Exception as ai_err:
                            self.logger.error(f"AI Product Extraction failed: {ai_err}")

                        report["product_details"] = product_indicators
                        
                        # Wrap report in a root key to match Frontend "New View" expectation
                        final_report = {
                            "comprehensive_site_scan": report
                        }
                        
                    except Exception as e:
                        self.logger.error(f"Error during content analysis: {e}")
                        final_report = {"comprehensive_site_scan": {"error": str(e), "url": url}}
                    
                    return json.dumps(final_report, indent=2)
                    
                except Exception as e:
                    self.logger.error(f"Comprehensive scan failed: {e}")
                    return json.dumps({"error": str(e), "url": url})

            @tool
            def analyze_competitor(company_name: str) -> str:
                """
                Analyze a competitor by searching for key information.
                
                Args:
                    company_name: Name of the competitor
                
                Returns:
                    Competitor intelligence summary
                """
                # Use the search tool logic internally
                try:
                    queries = [
                        f"{company_name} company overview products",
                        f"{company_name} pricing model",
                        f"{company_name} recent news 2024",
                        f"{company_name} competitors"
                    ]
                    
                    combined_results = []
                    with DDGS() as ddgs:
                        for q in queries:
                            results = list(ddgs.text(q, max_results=2))
                            for r in results:
                                combined_results.append(f"- {r['title']}: {r['body']} ({r['href']})")
                    
                    return f"Raw Research Data for {company_name}:\n\n" + "\n".join(combined_results)
                except Exception as e:
                    return f"Error analyzing competitor: {str(e)}"

            @tool
            def track_trends(topic: str) -> str:
                """
                Track trends for a specific topic.
                
                Args:
                    topic: Topic to track
                
                Returns:
                    Trend analysis data
                """
                try:
                    queries = [
                        f"{topic} trends 2024 2025",
                        f"future of {topic}",
                        f"{topic} market growth statistics"
                    ]
                    
                    combined_results = []
                    with DDGS() as ddgs:
                        for q in queries:
                            results = list(ddgs.text(q, max_results=3))
                            for r in results:
                                combined_results.append(f"- {r['title']}: {r['body']} ({r['href']})")
                    
                    return f"Trend Research Data for {topic}:\n\n" + "\n".join(combined_results)
                except Exception as e:
                    return f"Error tracking trends: {str(e)}"

            @tool
            def compliance_check(topic: str, industry: str = "general") -> str:
                """
                Check for compliance and regulatory updates.
                
                Args:
                    topic: Specific compliance topic
                    industry: Industry sector
                
                Returns:
                    Regulatory information
                """
                try:
                    queries = [
                        f"{topic} regulations {industry} 2024",
                        f"{topic} compliance requirements",
                        f"{topic} legal risks {industry}"
                    ]
                    
                    combined_results = []
                    with DDGS() as ddgs:
                        for q in queries:
                            results = list(ddgs.text(q, max_results=3))
                            for r in results:
                                combined_results.append(f"- {r['title']}: {r['body']} ({r['href']})")
                    
                    return f"Compliance Research Data for {topic} ({industry}):\n\n" + "\n".join(combined_results)
                except Exception as e:
                    return f"Error checking compliance: {str(e)}"

            @tool
            def generate_report(research_data: str, report_type: str = "summary", format: str = "markdown") -> str:
                """
                Generate a structured research report from crawled data or research findings.
                
                Args:
                    research_data: JSON string or text summary of research findings
                    report_type: Type of report (summary, detailed, executive)
                    format: Output format (markdown, json, text)
                
                Returns:
                    Formatted report
                """
                try:
                    # Try to parse as JSON first
                    try:
                        data = json.loads(research_data)
                        is_json = True
                    except:
                        data = research_data
                        is_json = False
                    
                    if format == "markdown":
                        report = f"# Research Report\n\n"
                        report += f"**Report Type:** {report_type}\n\n"
                        
                        if is_json and isinstance(data, dict):
                            # Handle JSON from monitor_url
                            if "base_url" in data:
                                report += f"## Web Crawl Analysis\n\n"
                                report += f"**Target URL:** {data.get('base_url', 'N/A')}\n\n"
                                report += f"**Pages Crawled:** {data.get('pages_crawled', 0)}\n\n"
                                report += f"**Total Keyword Matches:** {data.get('total_keyword_matches', 0)}\n\n"
                                
                                if data.get('pages'):
                                    report += f"### Page Details\n\n"
                                    for i, page in enumerate(data['pages'], 1):
                                        report += f"#### {i}. {page.get('title', 'Untitled')}\n\n"
                                        report += f"**URL:** {page.get('url', 'N/A')}\n\n"
                                        
                                        # Display keyword matches with context
                                        keyword_matches = page.get('keyword_matches', [])
                                        if keyword_matches:
                                            report += f"**Keyword Matches Found:** {len(keyword_matches)}\n\n"
                                            for match in keyword_matches:
                                                keyword = match.get('keyword', 'N/A')
                                                context = match.get('context', 'No context available')
                                                report += f"- **Keyword:** `{keyword}`\n"
                                                report += f"  **Context:** {context}\n\n"
                                        else:
                                            report += "**Keyword Matches:** None\n\n"
                                        
                                        report += f"**Content Preview:**\n\n{page.get('content_snippet', 'No content')}\n\n"
                                        report += "---\n\n"
                            else:
                                # Generic JSON formatting
                                report += f"## Data Summary\n\n```json\n{json.dumps(data, indent=2)}\n```\n\n"
                        else:
                            # Plain text data
                            report += f"## Findings\n\n{data}\n\n"
                        
                        from datetime import datetime
                        report += f"\n---\n\n*Report generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
                        return report
                    
                    elif format == "json":
                        if is_json:
                            return json.dumps(data, indent=2)
                        else:
                            return json.dumps({"content": data, "type": report_type}, indent=2)
                    
                    else:  # text format
                        if is_json and isinstance(data, dict):
                            return f"Report Type: {report_type}\n\n" + json.dumps(data, indent=2)
                        else:
                            return f"Report Type: {report_type}\n\n{data}"
                
                except Exception as e:
                    self.logger.error(f"Error generating report: {str(e)}")
                    return f"Error generating report: {str(e)}"

            # Register all tools
            self.logger.info("Adding tools to agent...")
            self.add_tool(search_web)
            self.add_tool(monitor_url)
            self.add_tool(comprehensive_site_scan)  # NEW: Comprehensive compliance scanner
            self.add_tool(analyze_competitor)
            self.add_tool(track_trends)
            self.add_tool(compliance_check)
            self.add_tool(generate_report)
            self.logger.info(f"Tools registered: {[t.name for t in self.tools]}")
            
        except Exception as e:
            self.logger.error(f"Error registering tools: {str(e)}", exc_info=True)
            raise

    def _run_agent_loop(self, system_prompt: str, user_prompt: str, task: Any) -> Dict[str, Any]:
        """
        Agent loop for market research tasks
        """
        # Customize prompt based on action
        if hasattr(task, 'action'):
            if task.action == 'site_scan':
                # DIRECT TOOL EXECUTION (Bypass LLM for deterministic output)
                inputs = task.input_data if hasattr(task, 'input_data') else {}
                url = inputs.get('topic', '')
                business_name = inputs.get('filters', {}).get('business_name', '')
                
                # Find the tool
                tool = next((t for t in self.tools if t.name == "comprehensive_site_scan"), None)
                if tool:
                    self.logger.info(f"Directly executing tool: {tool.name}")
                    try:
                        # Tools in LangChain usually take a single string input or a dict depending on definition
                        # For @tool with multiple args, it expects a dict or formatted string.
                        # Since we defined it with @tool, we can try invoking it.
                        # But simpler: we have the function logic. 
                        # Best approach with LangChain tools is .invoke() with a dict of args
                        result = tool.invoke({"url": url, "business_name": business_name})
                        return {
                            "response": result,
                            "action": task.action,
                            "completed_at": "now"
                        }
                    except Exception as e:
                        self.logger.error(f"Direct tool execution failed: {e}")
                        # Fallback to LLM if direct execution fails (unlikely)
            
            elif task.action == 'web_crawler':
                # DIRECT TOOL EXECUTION
                inputs = task.input_data if hasattr(task, 'input_data') else {}
                url = inputs.get('topic', '')
                filters = inputs.get('filters', {})
                keywords = filters.get('industry', '') if filters else ''
                max_pages = inputs.get('max_pages', 5)
                depth = inputs.get('crawl_depth', 1)
                
                tool = next((t for t in self.tools if t.name == "monitor_url"), None)
                if tool:
                    self.logger.info(f"Directly executing tool: {tool.name}")
                    try:
                        result = tool.invoke({
                            "url": url, 
                            "keywords": keywords, 
                            "max_pages": max_pages, 
                            "depth": depth
                        })
                        return {
                            "response": result,
                            "action": task.action,
                            "completed_at": "now"
                        }
                    except Exception as e:
                        self.logger.error(f"Direct tool execution failed: {e}")

        # ... (Existing ReAct Agent Logic for other tasks) ... 

        # Optimize prompt for other tasks
        if hasattr(task, 'action'):
             # (Existing prompt setup logic can remain or move here if needed)
             pass 

        # Custom output parser for robust handling
        from langchain.agents.output_parsers import ReActSingleInputOutputParser
        from langchain.schema import AgentAction, AgentFinish, OutputParserException
        from langchain.agents import AgentExecutor, create_react_agent
        import re

        class RobustReActOutputParser(ReActSingleInputOutputParser):
            """Parser that tries to recover from common LLM formatting errors"""
            
            def parse(self, text: str):
                try:
                    # Clean up text - sometimes models put markdown blocks around everything
                    cleaned_text = text.strip()
                    if cleaned_text.startswith("```") and cleaned_text.endswith("```"):
                        # Remove first and last line
                        lines = cleaned_text.splitlines()
                        if len(lines) >= 2:
                            cleaned_text = "\n".join(lines[1:-1])
                    
                    # Try standard parsing first
                    return super().parse(cleaned_text)
                except Exception as e:
                    # Fallback recovery logic
                    
                    # Check if we have an Action and Action Input but formatting is slightly off
                    # e.g. "Action: tool_name\nAction Input: {json}" (missing Thought)
                    
                    action_match = re.search(r'Action:\s*([^\n]+)', text, re.IGNORECASE)
                    input_match = re.search(r'Action Input:\s*(.+)', text, re.IGNORECASE | re.DOTALL)
                    
                    if action_match and input_match:
                        action = action_match.group(1).strip()
                        action_input = input_match.group(1).strip()
                        
                        # Clean up action input if it has extra text at the end
                        # This is tricky without a clear delimiter, but let's try to parse JSON
                        # or take the first line if it looks like a simple string
                        
                        # Try to find a JSON block in the input
                        json_match = re.search(r'(\{.*\})', action_input, re.DOTALL)
                        if json_match:
                            action_input = json_match.group(1)
                        
                        return AgentAction(tool=action, tool_input=action_input, log=text)
                    
                    # Check if it's a Final Answer but malformed
                    final_answer_match = re.search(r'Final Answer:\s*(.+)', text, re.IGNORECASE | re.DOTALL)
                    if final_answer_match:
                        return AgentFinish(return_values={"output": final_answer_match.group(1).strip()}, log=text)
                        
                    # If we really can't parse it, but it looks like a final response (no Action keyword), treat as Final Answer
                    if "Action:" not in text:
                        return AgentFinish(return_values={"output": text}, log=text)
                        
                    raise OutputParserException(f"Could not parse LLM output: {text}")

        from langchain.prompts import PromptTemplate
        
        # Basic ReAct Prompt Template
        template = """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}"""

        prompt = PromptTemplate.from_template(template)
        
        # Construct the ReAct agent with custom parser
        agent = create_react_agent(self.llm, self.tools, prompt, output_parser=RobustReActOutputParser())
        
        # Custom error handler that provides clear feedback to the LLM
        def handle_parsing_error(error) -> str:
            """Provide clear feedback when the LLM generates malformed output"""
            return f"formatting_error: {str(error)}. Please follow the format: Action: <tool_name> [newline] Action Input: <input>"
        
        # Create an agent executor with improved error handling
        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=handle_parsing_error,
            max_iterations=10,  # Prevent infinite loops
            max_execution_time=300,  # 5 minute timeout
            return_intermediate_steps=True
        )
        
        # Execute
        try:
            # Combine system prompt and user prompt for the input
            full_input = f"{system_prompt}\n\nTask: {user_prompt}"
            
            result = agent_executor.invoke({"input": full_input})
            response_text = result.get("output", "")
            
            # Check if the result indicates a failure
            if not response_text or "Error executing agent" in response_text or "max iterations" in str(result).lower():
                self.logger.error(f"Agent failed to complete task properly. Result: {result}")
                # Don't raise immediately, try to return what we have
                if not response_text:
                     response_text = "Task executed but no final summary was generated."
            
        except Exception as e:
            # Agent execution failed - this will be caught by base class and returned as failed status
            self.logger.error(f"Agent execution failed: {e}", exc_info=True)
            raise  # Re-raise to let base class handle it properly

        return {
            "response": response_text,
            "action": task.action,
            "completed_at": "now" # In real code use datetime
        }
    
    def _get_system_prompt(self) -> str:
        """Market research agent system prompt"""
        return """CRITICAL INSTRUCTION:
    When using `monitor_url` or `comprehensive_site_scan`, you MUST return the raw JSON output from the tool exactly as is.
    DO NOT summarize. DO NOT reformat. DO NOT wrap in markdown (no ```json blocks).
    Just return the JSON string. The frontend needs RAW JSON to render the dashboard.
    
    You are an advanced Market Research AI Agent.
    Your goal is to gather deep market intelligence, analyze competitors, and track industry trends.
    
    Guidelines:
    - ALWAYS cite sources (URLs) for your information.
    - When asked to monitor a specific site, use `monitor_url` and return the JSON.
    - When asked for a site scan, use `comprehensive_site_scan` and return the JSON.
    - For OTHER tasks (competitor analysis, trends):
      - Structure it clearly with headings.
      - Include a "Key Findings" section.
      - Include a "Sources" section.
    """


# Create default market research agent instance
def create_market_research_agent(llm_provider: str = "openai") -> MarketResearchAgent:
    """Factory function to create market research agent"""
    # Determine model based on provider
    if llm_provider == "openai":
        model = "gpt-4-turbo-preview"
    elif llm_provider == "anthropic":
        model = "claude-3-sonnet-20240229"
    elif llm_provider == "ollama":
        model = os.getenv("LLM_MODEL", "deepseek-r1:7b")
    else:
        model = "gpt-3.5-turbo"  # Fallback

    config = AgentConfig(
        agent_type="market_research",
        name="Market Research Agent",
        description="Comprehensive market intelligence, competitor analysis, and compliance monitoring",
        llm_provider=llm_provider,
        model=model,
        temperature=0.5,
        tools=[
            "search_web",
            "monitor_url",
            "analyze_competitor",
            "track_trends",
            "compliance_check",
            "generate_report"
        ]
    )
    return MarketResearchAgent(config)
