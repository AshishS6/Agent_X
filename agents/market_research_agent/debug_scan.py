import requests
import json
import re
import ssl
import socket
from datetime import datetime
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import whois

# Mocking logger
class Logger:
    def info(self, msg): print(f"[INFO] {msg}")
    def error(self, msg): print(f"[ERROR] {msg}")
    def warning(self, msg): print(f"[WARN] {msg}")

logger = Logger()

def comprehensive_site_scan(url: str, business_name: str = "") -> str:
    # ... logic from main.py ...
    try:
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
        logger.info(f"Starting comprehensive scan for: {url}")
        
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
            logger.info(f"Checking WHOIS for domain: {domain}")
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
            logger.warning(f"WHOIS lookup failed: {e}")
        
        report["compliance"] = compliance_data

        
        # ===========================================
        # 2. CRAWL WEBSITE FOR POLICY & CONTENT
        # ===========================================
        
        try:
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
                "product": {"found": False, "url": "", "status": ""}
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
                    r'about[-_]?us', r'about', r'who[-_]?we[-_]?are'
                ],
                "faq": [
                    r'faq', r'frequently[-_]?asked', r'help'
                ],
                "product": [
                    r'products?', r'shop', r'store', r'catalog'
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
            # 4. BUSINESS NAME EXTRACTION
            # ===========================================
            
            if not business_name:
                # Try to extract from footer, about, or copyright
                footer = soup.find('footer')
                if footer:
                    copyright = footer.find(text=re.compile(r'©|\(c\)|copyright', re.I))
                    if copyright:
                        # Extract company name from copyright text
                        match = re.search(r'(?:©|\(c\)|copyright)\s*(?:\\d{4})?\s*([A-Z][\\w\\s&,.-]+)', copyright, re.I)
                        if match:
                            business_name = match.group(1).strip()
                            
                # Fallback: Check title
                if not business_name and soup.title:
                    # Often title is "Brand Name - Tagline"
                    title_parts = soup.title.string.split('-')
                    if title_parts:
                        business_name = title_parts[0].strip()
                
                # Fallback: Check for meta og:site_name
                if not business_name:
                    og_site_name = soup.find("meta", property="og:site_name")
                    if og_site_name:
                        business_name = og_site_name.get("content", "").strip()
            
            report["business_details"]["extracted_business_name"] = business_name
            
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
                "has_products": "product" in page_text or "shop" in page_text,
                "has_pricing": "price" in page_text or "$" in page_text or "₹" in page_text,
                "has_cart": "add to cart" in page_text or "buy now" in page_text,
                "ecommerce_platform": "shopify" in page_text or "woocommerce" in page_text
            }
            
            report["product_details"] = product_indicators
            
            # Wrap in root key to match Frontend expectation
            final_report = {
                "comprehensive_site_scan": report
            }
            
        except Exception as e:
            logger.error(f"Error during content analysis: {e}")
            final_report = {"comprehensive_site_scan": {"error": str(e), "url": url}}
        
        return json.dumps(final_report, indent=2)
        
    except Exception as e:
        logger.error(f"Comprehensive scan failed: {e}")
        return json.dumps({"error": str(e), "url": url})

if __name__ == "__main__":
    result = comprehensive_site_scan("https://www.opencapital.co.in/")
    print(result)
