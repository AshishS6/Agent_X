"""
Legal Entity Matcher
Fuzzy matching of merchant legal entity against website data

Per PRD Section 6.7: Legal Entity Consistency Check
- Extract legal name from footer / T&Cs
- Extract address details
- Fuzzy match vs KYC data
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple

try:
    from rapidfuzz import fuzz, process
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False

try:
    from .models.output_schema import EntityMatchResult
except ImportError:
    from models.output_schema import EntityMatchResult


class EntityMatcher:
    """
    Matches merchant legal entity information against website data.
    
    Extraction sources:
    - Footer copyright text (e.g., "(c) 2024 Company Name")
    - Terms & Conditions page (legal name mentions)
    - Contact/About page (registered address)
    - Meta tags (og:site_name)
    
    Matching thresholds:
    - >= 80%: MATCH
    - 60-79%: PARTIAL_MATCH
    - < 60%: MISMATCH
    """
    
    # Match thresholds
    MATCH_THRESHOLD = 80.0
    PARTIAL_MATCH_THRESHOLD = 60.0
    
    # Common company suffixes to normalize
    COMPANY_SUFFIXES = [
        # Full forms
        'private limited',
        'pvt ltd',
        'pvt. ltd.',
        'pvt. ltd',
        'pvt ltd.',
        'limited liability company',
        'llc',
        'l.l.c.',
        'l.l.c',
        'incorporated',
        'inc.',
        'inc',
        'corporation',
        'corp.',
        'corp',
        'limited',
        'ltd.',
        'ltd',
        'company',
        'co.',
        'co',
        'plc',
        'p.l.c.',
        'gmbh',
        'ag',
        's.a.',
        'sa',
        'pty ltd',
        'pty. ltd.',
        # Indian specific
        'opc pvt ltd',
        'opc private limited',
        'llp',
        'l.l.p.',
    ]
    
    # Patterns for extracting legal names
    # V2.2.1: Enhanced patterns to handle various copyright formats
    # Including: "© 2025 | Company Name", "© 2025 Company Name", "© Company Name"
    COPYRIGHT_PATTERNS = [
        # Simple pattern: "Copyright © 2025 Company Name" or "© 2025 Company Name"
        r'[Cc]opyright\s*(?:©|\(c\))?\s*\d{4}\s+([A-Z][A-Za-z0-9\s&,\'-]+?)(?:\s*\.?\s*(?:All\s*[Rr]ights|[Rr]eserved)|$)',
        r'©\s*\d{4}\s+([A-Z][A-Za-z0-9\s&,\'-]+?)(?:\s*\.?\s*(?:All\s*[Rr]ights|[Rr]eserved)|$)',
        # With separator (|, -, –)
        r'©\s*\d{4}\s*[-|–]\s*([A-Z][A-Za-z0-9\s&,\'-]+?)(?:\s*\.?\s*(?:All\s*[Rr]ights|[Rr]eserved)|$)',
        r'[Cc]opyright\s*(?:©|\(c\))?\s*\d{4}\s*[-|–]\s*([A-Z][A-Za-z0-9\s&,\'-]+?)(?:\s*\.?\s*(?:All\s*[Rr]ights|[Rr]eserved)|$)',
        # Without year
        r'©\s+([A-Z][A-Za-z0-9\s&,\'-]+?)(?:\s*\.?\s*(?:All\s*[Rr]ights|[Rr]eserved)|$)',
        r'\(c\)\s*\d{4}\s+([A-Z][A-Za-z0-9\s&,\'-]+?)(?:\s*\.?\s*(?:All\s*[Rr]ights|[Rr]eserved)|$)',
    ]
    
    # V2.2.1: Descriptive patterns for "Company Name is a ..." - separate for clarity
    # NOTE: These patterns are used with re.IGNORECASE, so [A-Z] becomes [a-zA-Z]
    # We need word boundaries to avoid capturing prefix words like "us", "at", "about"
    DESCRIPTIVE_PATTERNS = [
        # "Company Private Limited is a ..." pattern
        # Use word boundary \b and require the company name to start after certain delimiters
        r'(?:^|[.\n])\s*([A-Z][A-Za-z0-9\s&.\'-]*(?:Private\s+Limited|Pvt\.?\s*Ltd\.?|Limited|Ltd\.?|Inc\.?|LLC|LLP))\s+is\s+(?:a|an|the|your)\s+',
        # "At Company Name, we..." pattern
        r'(?:^|[.\n])\s*(?:At\s+)?([A-Z][A-Za-z0-9\s&.\'-]*(?:Private\s+Limited|Pvt\.?\s*Ltd\.?|Limited|Ltd\.?|Inc\.?|LLC|LLP))\s*,\s*we\s+',
        # "Welcome to Company Name" pattern
        r'(?:Welcome\s+to|Visit)\s+([A-Z][A-Za-z0-9\s&.\'-]+(?:Private\s+Limited|Pvt\.?\s*Ltd\.?|Limited|Ltd\.?|Inc\.?|LLC|LLP))',
        # V2.2.2: "Operated by COMPANY NAME" pattern (common on about pages)
        r'[Oo]perated\s+by\s+([A-Z][A-Za-z0-9\s&.\'-]*(?:Private\s+Limited|Pvt\.?\s*Ltd\.?|Limited|Ltd\.?|Inc\.?|LLC|LLP))',
        # "Owned by COMPANY NAME" pattern
        r'[Oo]wned\s+by\s+([A-Z][A-Za-z0-9\s&.\'-]*(?:Private\s+Limited|Pvt\.?\s*Ltd\.?|Limited|Ltd\.?|Inc\.?|LLC|LLP))',
        # "Run by COMPANY NAME" pattern
        r'[Rr]un\s+by\s+([A-Z][A-Za-z0-9\s&.\'-]*(?:Private\s+Limited|Pvt\.?\s*Ltd\.?|Limited|Ltd\.?|Inc\.?|LLC|LLP))',
        # "A venture of COMPANY NAME" pattern
        r'[Aa]\s+(?:venture|unit|division|subsidiary)\s+of\s+([A-Z][A-Za-z0-9\s&.\'-]*(?:Private\s+Limited|Pvt\.?\s*Ltd\.?|Limited|Ltd\.?|Inc\.?|LLC|LLP))',
        # "COMPANY NAME, a registered" pattern
        r'([A-Z][A-Za-z0-9\s&.\'-]*(?:Private\s+Limited|Pvt\.?\s*Ltd\.?|Limited|Ltd\.?|Inc\.?|LLC|LLP))\s*,\s*a\s+registered',
    ]
    
    # Words that should NOT be part of company names (prefix noise)
    NOISE_PREFIXES = {'us', 'at', 'about', 'the', 'a', 'an', 'our', 'your', 'their', 'by', 'for', 'to', 'from', 'with'}
    
    # Patterns for extracting addresses (more specific to avoid navigation text)
    ADDRESS_PATTERNS = [
        # Indian address format - requires "Address:", "Office:", etc. followed by content ending with PIN or India
        r'(?:address|office|headquarter|location|registered\s+office|head\s+office)[\s:]+([A-Za-z0-9\s,\-\(\)]+(?:India|IN|\b\d{5,6}\b))',
        # US address format
        r'(\d+\s+[\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Way)[,\s]+[\w\s]+[,\s]+[A-Z]{2}\s+\d{5}(?:-\d{4})?)',
        # UK address format
        r'(\d+\s+[\w\s]+[,\s]+[\w\s]+[,\s]+[\w\s]+[,\s]+[A-Z]{1,2}\d{1,2}\s*\d[A-Z]{2})',
        # Indian address with PIN code pattern (must have location keywords)
        r'((?:Khasra|Plot|Shop|Office|Building|Flat|Room)\s+[A-Za-z0-9\s,\-\(\)]+(?:Road|Street|St|Nagar|Colony|Area|Sector|Phase|District|City)[\s,\-]+[A-Za-z\s]+(?:India|IN|\b\d{5,6}\b))',
        # Address starting with location indicators
        r'((?:Behind|Near|Opposite|Adjacent\s+to)\s+[A-Za-z0-9\s,\-\(\)]+(?:Road|Street|Nagar|Colony|Area)[\s,\-]+[A-Za-z\s]+(?:India|IN|\b\d{5,6}\b))',
    ]
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        
        if not RAPIDFUZZ_AVAILABLE:
            self.logger.warning("rapidfuzz not installed, falling back to basic matching")
    
    def match(
        self,
        declared_name: str,
        declared_address: str,
        scan_data: Dict[str, Any],
    ) -> EntityMatchResult:
        """
        Match declared merchant entity against website data.
        
        Args:
            declared_name: Merchant's declared legal name
            declared_address: Merchant's registered address
            scan_data: Scan data from ModularScanEngine
            
        Returns:
            EntityMatchResult with match status and evidence
        """
        self.logger.debug(f"Matching entity: {declared_name}")
        
        # Extract names from website
        self.logger.info("Extracting legal names from website...")
        extracted_names = self._extract_legal_names(scan_data)
        self.logger.info(f"Extracted {len(extracted_names)} legal names")
        
        # Extract addresses from website
        extracted_addresses = self._extract_addresses(scan_data)
        
        # Perform name matching
        best_match, match_score, match_details = self._match_names(
            declared_name, extracted_names
        )
        
        # Determine match status
        if match_score >= self.MATCH_THRESHOLD:
            match_status = "MATCH"
        elif match_score >= self.PARTIAL_MATCH_THRESHOLD:
            match_status = "PARTIAL_MATCH"
        elif not extracted_names:
            match_status = "NO_MATCH"
        else:
            match_status = "MISMATCH"
        
        # Perform address matching
        self.logger.debug(f"Extracted {len(extracted_addresses)} addresses for matching")
        if extracted_addresses:
            self.logger.debug(f"Sample extracted addresses: {extracted_addresses[:2]}")
        address_match = self._match_address(declared_address, extracted_addresses)
        if address_match:
            self.logger.info(f"Address match: {address_match.get('status')} (score: {address_match.get('score', 0):.1f}%)")
        else:
            self.logger.info(f"Address matching skipped or no match found (extracted: {len(extracted_addresses)}, declared length: {len(declared_address) if declared_address else 0})")
        
        return EntityMatchResult(
            declared_name=declared_name,
            extracted_names=extracted_names,
            best_match=best_match,
            match_score=match_score,
            match_status=match_status,
            address_match=address_match,
            evidence={
                'match_details': match_details,
                'extraction_sources': self._get_extraction_sources(scan_data),
                'normalized_declared': self._normalize_company_name(declared_name),
            }
        )
    
    def _extract_legal_names(self, scan_data: Dict[str, Any]) -> List[str]:
        """Extract potential legal names from scan data"""
        names = []
        
        # 1. From business_details (already extracted by scan engine)
        business_details = scan_data.get('business_details', {})
        extracted_name = business_details.get('extracted_business_name')
        if extracted_name and extracted_name != 'Not found':
            self.logger.info(f"Extracted name from business_details: {extracted_name}")
            # Clean navigation keywords from extracted business name
            cleaned = self._clean_navigation_keywords(extracted_name)
            if cleaned:
                names.append(cleaned)
        
        # 2. From meta tags
        metadata = scan_data.get('metadata', {})
        og_site_name = metadata.get('og:site_name')
        if og_site_name:
            self.logger.debug(f"Extracted name from og:site_name: {og_site_name}")
            names.append(og_site_name)
        
        # 3. From page title
        title = metadata.get('title', '')
        self.logger.info(f"Title from metadata: '{title}' (exists: {bool(title)})")
        if title:
            self.logger.info(f"Processing page title: {title}")
            # Extract company name from title (often "Company - Tagline")
            title_parts = re.split(r'\s*[-|–]\s*', title)
            if title_parts:
                first_part = title_parts[0].strip()
                self.logger.info(f"Title first part: '{first_part}'")
                
                # Always try to clean navigation keywords from titles first
                # This handles cases like "Kisan Center Home Wallet Coin Login"
                navigation_keywords = ['home', 'login', 'sign', 'cart', 'basket', 'checkout', 
                                     'wallet', 'coin', 'account', 'profile', 'search', 'menu', 'shop', 'track']
                words = first_part.split()
                
                # Check if title contains any navigation keywords
                has_nav_keywords = any(word.lower() in navigation_keywords for word in words)
                self.logger.info(f"Title has nav keywords: {has_nav_keywords}, word count: {len(words)}, condition: {has_nav_keywords and len(words) > 2}")
                
                if has_nav_keywords and len(words) > 2:
                    # Remove navigation keywords from the end first
                    removed_count = 0
                    while words and words[-1].lower() in navigation_keywords:
                        removed = words.pop()
                        removed_count += 1
                        self.logger.debug(f"Removed navigation keyword from end: {removed}")
                    # Also remove from beginning if it's still long and starts with nav keyword
                    if len(words) > 3 and words and words[0].lower() in navigation_keywords:
                        removed = words.pop(0)
                        removed_count += 1
                        self.logger.debug(f"Removed navigation keyword from start: {removed}")
                    if words and len(words) >= 1:
                        cleaned_title = ' '.join(words)
                        self.logger.info(f"Cleaned title from '{first_part}' to '{cleaned_title}' (removed {removed_count} nav keywords)")
                        # Pass cleaned title to _clean_extracted_name for validation
                        final_cleaned = self._clean_extracted_name(cleaned_title)
                        if final_cleaned:
                            self.logger.info(f"Added cleaned title as name: {final_cleaned}")
                            names.append(final_cleaned)
                        else:
                            self.logger.warning(f"Cleaned title '{cleaned_title}' was filtered by _clean_extracted_name")
                    else:
                        self.logger.debug(f"Skipped title (nothing left after removing nav keywords): {first_part}")
                elif not self._is_navigation_text(first_part):
                    # No nav keywords or already clean, validate and add
                    final_cleaned = self._clean_extracted_name(first_part)
                    if final_cleaned:
                        self.logger.debug(f"Added title as name: {final_cleaned}")
                        names.append(final_cleaned)
                    else:
                        self.logger.debug(f"Title '{first_part}' was filtered by _clean_extracted_name")
        
        # 4. Search page content for copyright notices and descriptive patterns
        crawl_summary = scan_data.get('crawl_summary', {})
        page_texts = crawl_summary.get('page_texts', {})
        
        for page_url, page_text in page_texts.items():
            if not page_text:
                continue
            
            # Search for copyright patterns
            for pattern in self.COPYRIGHT_PATTERNS:
                matches = re.findall(pattern, page_text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    clean_name = match.strip()
                    # Remove trailing punctuation
                    clean_name = re.sub(r'\s*[.|,]\s*$', '', clean_name)
                    if len(clean_name) >= 3:
                        # Clean navigation keywords before adding
                        cleaned = self._clean_navigation_keywords(clean_name)
                        if cleaned and cleaned not in names:
                            self.logger.debug(f"Found name from copyright pattern on {page_url}: {cleaned} (original: {clean_name})")
                            names.append(cleaned)
            
            # V2.2.1: Also look for "Company Name is a..." pattern (common in footers/about sections)
            for pattern in self.DESCRIPTIVE_PATTERNS:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    clean_name = match.strip()
                    if len(clean_name) >= 3:
                        # Clean navigation keywords before adding
                        cleaned = self._clean_navigation_keywords(clean_name)
                        if cleaned and cleaned not in names:
                            names.append(cleaned)
            
            # V2.2.2: Extract company names from Contact/About pages (plain display format)
            # Look for patterns like "Company Name Private Limited" on its own line or in "Our Location" sections
            if 'contact' in page_url.lower() or 'about' in page_url.lower():
                # Pattern for standalone company name with legal suffix
                company_name_pattern = r'(?:^|[\n\r])\s*([A-Z][A-Za-z0-9\s&.\'-]*(?:Private\s+Limited|Pvt\.?\s*Ltd\.?|Limited|Ltd\.?|Inc\.?|LLC|LLP))\s*(?:[\n\r]|$)'
                matches = re.findall(company_name_pattern, page_text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    clean_name = match.strip()
                    # Filter out very short matches or common words
                    if len(clean_name) >= 5 and clean_name.lower() not in ['all rights reserved', 'private limited']:
                        if clean_name not in names:
                            names.append(clean_name)
                
                # Pattern for "Our Location" or similar section headers followed by company name
                location_pattern = r'(?:Our\s+Location|Company\s+Name|Registered\s+Name)[\s:]*\n?\s*([A-Z][A-Za-z0-9\s&.\'-]*(?:Private\s+Limited|Pvt\.?\s*Ltd\.?|Limited|Ltd\.?|Inc\.?|LLC|LLP))'
                matches = re.findall(location_pattern, page_text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    clean_name = match.strip()
                    if len(clean_name) >= 5 and clean_name not in names:
                        names.append(clean_name)
        
        # 5. Look in footer specifically
        footer_text = scan_data.get('footer_text', '')
        if footer_text:
            self.logger.debug(f"Checking footer text (length: {len(footer_text)})")
            for pattern in self.COPYRIGHT_PATTERNS:
                matches = re.findall(pattern, footer_text, re.IGNORECASE | re.MULTILINE)
                if matches:
                    self.logger.debug(f"Found {len(matches)} copyright matches in footer with pattern: {pattern[:50]}...")
                for match in matches:
                    clean_name = match.strip()
                    clean_name = re.sub(r'\s*[.|,]\s*$', '', clean_name)
                    if len(clean_name) >= 3:
                        # Clean navigation keywords before adding
                        cleaned = self._clean_navigation_keywords(clean_name)
                        if cleaned and cleaned not in names:
                            self.logger.debug(f"Added name from footer copyright: {cleaned} (original: {clean_name})")
                            names.append(cleaned)
            # Also check descriptive patterns in footer
            for pattern in self.DESCRIPTIVE_PATTERNS:
                matches = re.findall(pattern, footer_text, re.IGNORECASE)
                for match in matches:
                    clean_name = match.strip()
                    if len(clean_name) >= 3:
                        # Clean navigation keywords before adding
                        cleaned = self._clean_navigation_keywords(clean_name)
                        if cleaned and cleaned not in names:
                            self.logger.debug(f"Added name from footer descriptive pattern: {cleaned} (original: {clean_name})")
                            names.append(cleaned)
        else:
            self.logger.debug("No footer text found in scan_data")
        
        # 6. From Terms & Conditions page
        policy_details = scan_data.get('policy_details', {})
        terms_page = policy_details.get('terms_condition', {})
        if terms_page.get('found'):
            terms_content = terms_page.get('content', '')
            if terms_content:
                # Look for "operated by", "provided by", "owned by" patterns
                operated_patterns = [
                    r'(?:operated|provided|owned|run)\s+by\s+([A-Z][A-Za-z0-9\s&,.\'-]+?)(?:\.|,|\s*\()',
                    r'(?:company|entity|organization)\s+name[:\s]+([A-Z][A-Za-z0-9\s&,.\'-]+?)(?:\.|,)',
                ]
                for pattern in operated_patterns:
                    matches = re.findall(pattern, terms_content, re.IGNORECASE)
                    for match in matches:
                        clean_name = match.strip()
                        if len(clean_name) >= 3 and clean_name not in names:
                            names.append(clean_name)
        
        # Deduplicate and clean, filtering out navigation text
        if names:
            self.logger.info(f"Raw extracted names before cleaning ({len(names)}): {names[:5]}")
        cleaned_names = []
        navigation_keywords = [
            'home', 'login', 'sign in', 'register', 'cart', 'basket', 'checkout',
            'wallet', 'coin', 'account', 'profile', 'search', 'menu', 'shop',
            'products', 'categories', 'blog', 'about us', 'contact us', 'faq'
        ]
        
        for name in names:
            cleaned = self._clean_extracted_name(name)
            if not cleaned:
                self.logger.warning(f"Name '{name}' was filtered out by _clean_extracted_name")
                continue
            
            # Filter out names that are clearly navigation menus
            cleaned_lower = cleaned.lower()
            
            # Skip if it contains multiple navigation keywords (likely a menu)
            nav_keyword_count = sum(1 for keyword in navigation_keywords if keyword in cleaned_lower)
            if nav_keyword_count >= 2:
                self.logger.warning(f"Filtered out navigation text as name (has {nav_keyword_count} nav keywords): {cleaned}")
                continue
            
            # Skip if name starts with navigation keywords
            if any(cleaned_lower.startswith(kw + ' ') or cleaned_lower == kw for kw in navigation_keywords):
                self.logger.warning(f"Filtered out name starting with navigation keyword: {cleaned}")
                continue
            
            # Skip very long names that look like concatenated menu items
            words = cleaned.split()
            if len(words) > 5:  # Company names rarely have more than 5 words
                # Check if it contains navigation keywords in the middle/end
                if any(kw in cleaned_lower for kw in navigation_keywords):
                    self.logger.warning(f"Filtered out long name with navigation keywords: {cleaned}")
                    continue
            
            if cleaned not in cleaned_names:
                self.logger.info(f"Added cleaned name to final list: '{cleaned}'")
                cleaned_names.append(cleaned)
        
        # Always log what we found (even if empty)
        if cleaned_names:
            self.logger.info(f"Extracted {len(cleaned_names)} legal names after filtering: {cleaned_names[:5]}")
        else:
            self.logger.warning(f"Extracted 0 legal names after filtering. Raw names were: {names[:10]}")
            # Try to identify why names were filtered
            if names:
                self.logger.warning(f"Names were extracted but filtered out. Sample raw names: {names[:5]}")
                # Check first few names to see why they were filtered
                for name in names[:3]:
                    cleaned = self._clean_extracted_name(name)
                    if not cleaned:
                        self.logger.warning(f"  '{name}' was filtered by _clean_extracted_name")
                    elif self._is_navigation_text(cleaned):
                        self.logger.warning(f"  '{name}' -> '{cleaned}' was filtered as navigation text")
        return cleaned_names[:10]  # Limit to 10 names
    
    def _extract_addresses(self, scan_data: Dict[str, Any]) -> List[str]:
        """Extract addresses from scan data"""
        self.logger.info("Starting address extraction...")
        addresses = []
        
        # From business_details
        business_details = scan_data.get('business_details', {})
        contact_info = business_details.get('contact_info', {})
        address = contact_info.get('address')
        if address and address != 'Not found':
            addresses.append(address)
            self.logger.debug(f"Extracted address from business_details: {address[:50]}...")
        
        # Search page content
        crawl_summary = scan_data.get('crawl_summary', {})
        page_texts = crawl_summary.get('page_texts', {})
        
        # Limit page text size to avoid processing huge pages (performance optimization)
        # Take first 20KB of each page (reduced from 50KB) to speed up processing
        MAX_PAGE_TEXT_SIZE = 20000
        limited_page_texts = {}
        for page_url, page_text in page_texts.items():
            if page_text and len(page_text) > MAX_PAGE_TEXT_SIZE:
                limited_page_texts[page_url] = page_text[:MAX_PAGE_TEXT_SIZE]
                self.logger.debug(f"Truncated page text for {page_url} from {len(page_text)} to {MAX_PAGE_TEXT_SIZE} chars")
            else:
                limited_page_texts[page_url] = page_text
        
        page_texts = limited_page_texts
        
        # Prioritize contact and about pages - ONLY process these for pattern matching
        priority_pages = ['contact', 'about']
        
        # First, separate priority pages from others
        priority_page_list = []
        other_pages = []
        
        for page_url, page_text in page_texts.items():
            if not page_text:
                continue
            page_lower = page_url.lower()
            if any(priority in page_lower for priority in priority_pages):
                priority_page_list.append((page_url, page_text))
            else:
                other_pages.append((page_url, page_text))
        
        # ONLY process priority pages with regex patterns (skip others to save time)
        # Process max 3 priority pages
        # SKIP if we already found address from business_details (saves time)
        if len(addresses) == 0:  # Only do regex if we don't have any addresses yet
            for page_url, page_text in priority_page_list[:3]:
                # Use simpler, faster pattern matching - limit to first 10KB of text
                text_to_search = page_text[:10000] if len(page_text) > 10000 else page_text
                
                # Only use the most common patterns (skip complex ones)
                simple_patterns = [
                    self.ADDRESS_PATTERNS[0],  # Indian address format
                    self.ADDRESS_PATTERNS[3],  # Indian address with PIN code pattern
                ]
                
                for pattern in simple_patterns:
                    try:
                        matches = re.findall(pattern, text_to_search, re.IGNORECASE)
                        for match in matches:
                            clean_addr = match.strip()
                            # Quick validation - must have PIN code
                            if len(clean_addr) >= 25 and len(clean_addr) <= 250:
                                if re.search(r'\b\d{5,6}\b', clean_addr):  # Must have PIN
                                    if clean_addr not in addresses:
                                        addresses.append(clean_addr)
                                        self.logger.debug(f"Extracted address from {page_url}: {clean_addr[:50]}...")
                                        if len(addresses) >= 3:  # Stop after 3 addresses
                                            break
                    except Exception as e:
                        self.logger.debug(f"Pattern error on {page_url}: {e}")
                        continue
                    if len(addresses) >= 3:
                        break
                if len(addresses) >= 3:
                    break
        else:
            self.logger.debug("Skipping regex pattern matching - already have address from business_details")
        
        # Skip other pages pattern matching entirely - go straight to loose pattern matching
        # This saves a lot of time since regex on large pages is slow
        
        # V2.2.2: Also look for addresses in Contact/About pages without strict patterns
        # Many sites just display addresses as plain text
        # Common navigation/UI words to exclude
        nav_exclusion_keywords = [
            'view more', 'shop by', 'all category', 'home', 'search', 'cart', 'wish',
            'subscribe', 'newsletter', 'follow us', 'social media', 'menu', 'navigation',
            'login', 'sign in', 'register', 'account', 'checkout', 'basket', 'bag',
            'filter', 'sort', 'price', 'add to cart', 'buy now', 'categories', 'products',
            'blog', 'about us', 'contact us', 'faq', 'help', 'terms', 'privacy', 'policy'
        ]
        
        # Limit number of pages processed to avoid hanging
        # Prioritize contact/about pages first
        contact_about_pages = []
        other_pages_limited = []
        
        for page_url, page_text in page_texts.items():
            if not page_text:
                continue
            page_lower = page_url.lower()
            if 'contact' in page_lower or 'about' in page_lower:
                contact_about_pages.append((page_url, page_text))
            else:
                other_pages_limited.append((page_url, page_text))
        
        # Process contact/about pages first (most likely to have addresses)
        # Balanced: Process enough pages to find addresses but limit to avoid delays
        # Process up to 3 contact/about pages (more likely to have addresses) + 2 others
        pages_to_process = contact_about_pages[:3] + other_pages_limited[:2]  # Max 3 contact/about + 2 others
        self.logger.info(f"Processing {len(pages_to_process)} pages for address extraction ({len(contact_about_pages)} contact/about available, {len(other_pages_limited)} others available)")
        
        for page_url, page_text in pages_to_process:
            # Early exit if we already found enough addresses
            if len(addresses) >= 5:
                self.logger.info(f"Found {len(addresses)} addresses, stopping extraction")
                break
            
            page_lower = page_url.lower()
            is_contact_about = 'contact' in page_lower or 'about' in page_lower
            
            if is_contact_about:
                # Look for lines that look like addresses (contain location keywords + PIN/state)
                # Address-specific keywords (more specific)
                address_keywords = ['road', 'street', 'avenue', 'lane', 'nagar', 'colony', 
                                   'sector', 'phase', 'district', 'pincode', 'pin code', 
                                   'postal', 'zip', 'khasra', 'plot', 'building', 'flat',
                                   'shop no', 'shop number', 'office no', 'office number',
                                   'behind', 'near', 'opposite', 'area', 'locality']
                
                # Indian states
                indian_states = [
                    'uttarakhand', 'delhi', 'mumbai', 'bangalore', 'kolkata', 'chennai',
                    'hyderabad', 'pune', 'ahmedabad', 'jaipur', 'lucknow', 'ghaziabad',
                    'noida', 'gurgaon', 'gurugram', 'faridabad', 'mumbai', 'pune',
                    'nagpur', 'aurangabad', 'nashik', 'karnataka', 'maharashtra',
                    'tamil nadu', 'west bengal', 'gujarat', 'rajasthan', 'uttar pradesh',
                    'punjab', 'haryana', 'himachal', 'bihar', 'jharkhand', 'odisha'
                ]
                
                # Limit number of lines processed to avoid hanging on huge pages
                # Balanced: Check more lines for contact/about pages (addresses usually in middle/end)
                # For contact/about pages, check first 100 lines (addresses might not be at top)
                # For other pages, check first 50 lines
                lines = page_text.split('\n')
                max_lines = 100 if is_contact_about else 50  # More lines for contact/about pages
                if len(lines) > max_lines:
                    lines = lines[:max_lines]
                    self.logger.debug(f"Processing first {max_lines} lines from {page_url} ({len(page_text.split(chr(10)))} total)")
                
                # For contact/about pages, also try searching from the END (addresses often in footer)
                if is_contact_about and len(page_text.split('\n')) > max_lines:
                    # Get last 50 lines too (addresses are often in footer)
                    all_lines = page_text.split('\n')
                    if len(all_lines) > 150:  # If page is long, also check footer
                        footer_lines = all_lines[-50:]
                        # Combine: first 100 + last 50, but avoid duplicates
                        combined_lines = lines + [line for line in footer_lines if line not in lines]
                        lines = combined_lines[:150]  # Max 150 lines total
                        self.logger.debug(f"Also checking footer lines from {page_url} (total: {len(lines)} lines to process)")
                
                # Limit address candidates per page to avoid excessive processing
                max_addresses_per_page = 3 if is_contact_about else 2  # More for contact/about pages
                addresses_from_page = 0
                
                for line_num, line in enumerate(lines):
                    if addresses_from_page >= max_addresses_per_page:
                        self.logger.debug(f"Found {max_addresses_per_page} addresses from {page_url}, stopping")
                        break  # Stop processing this page after finding enough candidates
                    
                    # Early exit if we already have enough addresses total
                    if len(addresses) >= 5:
                        break
                    line = line.strip()
                    
                    # Skip if line is too short or too long (likely not an address)
                    if len(line) < 25 or len(line) > 200:
                        continue
                    
                    # Skip if it contains navigation keywords
                    line_lower = line.lower()
                    if any(nav_kw in line_lower for nav_kw in nav_exclusion_keywords):
                        continue
                    
                    # Skip if it's mostly uppercase (likely a header)
                    if len(line) > 10 and line.isupper() and ' ' not in line:
                        continue
                    
                    # Must have at least one address-specific keyword
                    has_address_keyword = any(kw in line_lower for kw in address_keywords)
                    if not has_address_keyword:
                        continue
                    
                    # Must have either PIN code or state name
                    has_pin = bool(re.search(r'\b\d{5,6}\b', line))  # PIN code
                    has_state = any(state in line_lower for state in indian_states)
                    
                    # Must have multiple address indicators (not just one)
                    # Count indicators: keywords, numbers (house/plot numbers), PIN, state
                    indicator_count = 0
                    if has_address_keyword:
                        indicator_count += 1
                    if has_pin:
                        indicator_count += 1
                    if has_state:
                        indicator_count += 1
                    if re.search(r'\b\d+\b', line):  # Has numbers (house/plot numbers)
                        indicator_count += 1
                    
                    # Require at least 2 indicators to be considered an address
                    if indicator_count >= 2 and (has_pin or has_state):
                        # Additional validation: should not be a common page element
                        if not any(skip in line_lower for skip in ['copyright', '©', 'all rights reserved', 'powered by']):
                            # Final validation using helper method
                            if self._is_valid_address(line):
                                if line not in addresses:
                                    addresses.append(line)
                                    addresses_from_page += 1
                                    self.logger.debug(f"Extracted address from {page_url} (loose pattern): {line[:80]}...")
                                    if addresses_from_page >= max_addresses_per_page:
                                        break  # Found enough addresses from this page
                            else:
                                self.logger.debug(f"Filtered out invalid address candidate: {line[:50]}...")
        
        # Filter out addresses that are not valid addresses
        filtered_addresses = []
        for addr in addresses:
            # Use validation helper to check if it's a real address
            if self._is_valid_address(addr):
                filtered_addresses.append(addr)
            else:
                self.logger.debug(f"Filtered out invalid address: {addr[:60]}...")
        
        self.logger.info(f"Address extraction complete: {len(filtered_addresses)} addresses found (after filtering from {len(pages_to_process)} pages processed)")
        if filtered_addresses:
            self.logger.info(f"Sample addresses: {[a[:60] + '...' for a in filtered_addresses[:3]]}")
        else:
            self.logger.info("No valid addresses extracted from website")
        
        return filtered_addresses[:5]  # Limit to 5 addresses
    
    def _match_names(
        self,
        declared: str,
        extracted: List[str]
    ) -> Tuple[Optional[str], float, Dict[str, Any]]:
        """
        Match declared name against extracted names.
        
        Returns:
            Tuple of (best_match, score, details)
        """
        if not extracted:
            return None, 0.0, {'reason': 'No names extracted from website'}
        
        # Normalize declared name
        declared_normalized = self._normalize_company_name(declared)
        
        if RAPIDFUZZ_AVAILABLE:
            # Use rapidfuzz for fuzzy matching
            results = []
            for ext_name in extracted:
                ext_normalized = self._normalize_company_name(ext_name)
                
                # Calculate multiple similarity scores
                ratio = fuzz.ratio(declared_normalized, ext_normalized)
                partial_ratio = fuzz.partial_ratio(declared_normalized, ext_normalized)
                token_sort = fuzz.token_sort_ratio(declared_normalized, ext_normalized)
                token_set = fuzz.token_set_ratio(declared_normalized, ext_normalized)
                
                # Weighted average (token_set is best for company names)
                weighted_score = (ratio * 0.2 + partial_ratio * 0.2 + 
                                token_sort * 0.3 + token_set * 0.3)
                
                results.append({
                    'original': ext_name,
                    'normalized': ext_normalized,
                    'score': weighted_score,
                    'breakdown': {
                        'ratio': ratio,
                        'partial_ratio': partial_ratio,
                        'token_sort': token_sort,
                        'token_set': token_set,
                    }
                })
            
            # Sort by score
            results.sort(key=lambda x: x['score'], reverse=True)
            
            best = results[0] if results else None
            if best:
                return best['original'], best['score'], {
                    'method': 'rapidfuzz',
                    'top_matches': results[:3],
                    'declared_normalized': declared_normalized,
                }
        else:
            # Fallback to basic matching
            best_match = None
            best_score = 0.0
            
            for ext_name in extracted:
                ext_normalized = self._normalize_company_name(ext_name)
                score = self._basic_similarity(declared_normalized, ext_normalized)
                
                if score > best_score:
                    best_score = score
                    best_match = ext_name
            
            return best_match, best_score, {
                'method': 'basic',
                'declared_normalized': declared_normalized,
            }
        
        return None, 0.0, {'reason': 'Matching failed'}
    
    # V2.2.1: Placeholder values that indicate no address was provided
    ADDRESS_PLACEHOLDER_VALUES = {
        'address not provided',
        'not provided',
        'n/a',
        'na',
        'none',
        'test address',
        'address',
        '',
    }
    
    def _match_address(
        self,
        declared: str,
        extracted: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Match declared address against extracted addresses"""
        if not extracted or not declared:
            return None
        
        # V2.2.1: Skip address matching if declared address is a placeholder
        # This prevents false ADDRESS_MISMATCH when user doesn't provide an address
        declared_lower = declared.lower().strip()
        if declared_lower in self.ADDRESS_PLACEHOLDER_VALUES:
            return None
        
        # Also check for common placeholder patterns
        if len(declared_lower) < 15 or declared_lower.startswith('test'):
            return None
        
        declared_normalized = self._normalize_address(declared)
        
        best_match = None
        best_score = 0.0
        
        for ext_addr in extracted:
            ext_normalized = self._normalize_address(ext_addr)
            
            if RAPIDFUZZ_AVAILABLE:
                score = fuzz.token_set_ratio(declared_normalized, ext_normalized)
            else:
                score = self._basic_similarity(declared_normalized, ext_normalized)
            
            if score > best_score:
                best_score = score
                best_match = ext_addr
        
        if best_score >= self.MATCH_THRESHOLD:
            status = 'MATCH'
        elif best_score >= self.PARTIAL_MATCH_THRESHOLD:
            status = 'PARTIAL_MATCH'
        else:
            status = 'MISMATCH'
        
        return {
            'declared': declared,
            'best_match': best_match,
            'score': best_score,
            'status': status,
        }
    
    def _normalize_company_name(self, name: str) -> str:
        """Normalize company name for comparison"""
        if not name:
            return ''
        
        # Convert to lowercase
        normalized = name.lower().strip()
        
        # Remove common suffixes
        for suffix in sorted(self.COMPANY_SUFFIXES, key=len, reverse=True):
            normalized = re.sub(
                r'\s*' + re.escape(suffix) + r'\s*$',
                '',
                normalized,
                flags=re.IGNORECASE
            )
        
        # Remove special characters except spaces
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        
        # Normalize whitespace
        normalized = ' '.join(normalized.split())
        
        return normalized
    
    def _is_navigation_text(self, text: str) -> bool:
        """
        Check if extracted text is navigation menu text (not a company name).
        
        Returns True if text appears to be navigation/menu items.
        """
        if not text or len(text) < 3:
            return False
        
        text_lower = text.lower()
        
        # Common navigation keywords
        navigation_keywords = [
            'home', 'login', 'sign in', 'register', 'cart', 'basket', 'checkout',
            'wallet', 'coin', 'account', 'profile', 'search', 'menu', 'shop',
            'products', 'categories', 'blog', 'about us', 'contact us', 'faq',
            'help', 'support', 'terms', 'privacy', 'policy', 'sign out', 'logout'
        ]
        
        # Check if text contains multiple navigation keywords (likely a menu)
        nav_count = sum(1 for keyword in navigation_keywords if keyword in text_lower)
        if nav_count >= 2:
            return True
        
        # Check if text starts with navigation keyword
        words = text_lower.split()
        if words and any(word in navigation_keywords for word in words[:2]):
            return True
        
        # Check if it's a concatenated menu (multiple capitalized words that are navigation items)
        if len(text.split()) > 3:
            all_words_are_nav = all(word.lower() in navigation_keywords for word in text.split())
            if all_words_are_nav:
                return True
        
        return False
    
    def _is_valid_address(self, text: str) -> bool:
        """
        Validate if extracted text is actually an address (not navigation/UI text).
        
        Returns True if text appears to be a real address.
        """
        if not text or len(text) < 25 or len(text) > 300:
            return False
        
        text_lower = text.lower()
        
        # Must not contain navigation/UI keywords
        nav_keywords = [
            'view more', 'shop by', 'all category', 'categories', 'products',
            'home', 'search', 'cart', 'wish', 'subscribe', 'newsletter',
            'follow us', 'social media', 'menu', 'navigation', 'login',
            'sign in', 'register', 'account', 'checkout', 'basket', 'bag',
            'filter', 'sort', 'price', 'add to cart', 'buy now', 'blog',
            'about us', 'contact us', 'faq', 'help', 'terms', 'privacy'
        ]
        
        nav_score = sum(1 for nav in nav_keywords if nav in text_lower)
        if nav_score >= 2:  # Too many navigation keywords
            return False
        
        # Must contain address-like indicators
        address_indicators = [
            'road', 'street', 'st', 'avenue', 'ave', 'lane', 'nagar', 'colony',
            'sector', 'phase', 'district', 'pincode', 'pin code', 'postal', 'zip',
            'khasra', 'plot', 'building', 'flat', 'shop no', 'shop number',
            'office no', 'office number', 'behind', 'near', 'opposite', 'area',
            'locality', 'city', 'state', 'india', 'in '
        ]
        
        has_address_indicator = any(ind in text_lower for ind in address_indicators)
        if not has_address_indicator:
            return False
        
        # Should have numbers (house/plot numbers or PIN codes)
        has_numbers = bool(re.search(r'\d+', text))
        if not has_numbers:
            return False
        
        # Should have PIN code or state name for Indian addresses
        has_pin = bool(re.search(r'\b\d{5,6}\b', text))
        indian_states = ['uttarakhand', 'delhi', 'maharashtra', 'karnataka', 'tamil nadu',
                        'west bengal', 'gujarat', 'rajasthan', 'uttar pradesh', 'punjab',
                        'haryana', 'himachal', 'bihar', 'jharkhand', 'odisha', 'ghaziabad',
                        'mumbai', 'bangalore', 'kolkata', 'chennai', 'hyderabad', 'pune']
        has_state = any(state in text_lower for state in indian_states)
        
        if not (has_pin or has_state):
            return False
        
        # Should not be all uppercase single words (likely headers)
        words = text.split()
        if len(words) <= 3 and text.isupper():
            return False
        
        return True
    
    def _normalize_address(self, address: str) -> str:
        """Normalize address for comparison"""
        if not address:
            return ''
        
        # Convert to lowercase
        normalized = address.lower().strip()
        
        # Standardize common abbreviations
        replacements = {
            r'\bstreet\b': 'st',
            r'\bst\.?\b': 'st',
            r'\bavenue\b': 'ave',
            r'\bave\.?\b': 'ave',
            r'\broad\b': 'rd',
            r'\brd\.?\b': 'rd',
            r'\bboulevard\b': 'blvd',
            r'\bblvd\.?\b': 'blvd',
            r'\bdrive\b': 'dr',
            r'\bdr\.?\b': 'dr',
            r'\blane\b': 'ln',
            r'\bln\.?\b': 'ln',
            r'\bapartment\b': 'apt',
            r'\bapt\.?\b': 'apt',
            r'\bsuite\b': 'ste',
            r'\bste\.?\b': 'ste',
            r'\bfloor\b': 'fl',
            r'\bfl\.?\b': 'fl',
        }
        
        for pattern, replacement in replacements.items():
            normalized = re.sub(pattern, replacement, normalized)
        
        # Remove extra punctuation
        normalized = re.sub(r'[,.]', ' ', normalized)
        
        # Normalize whitespace
        normalized = ' '.join(normalized.split())
        
        return normalized
    
    def _clean_navigation_keywords(self, name: str) -> Optional[str]:
        """Remove navigation keywords from extracted name (e.g., 'Home Wallet Coin Login')"""
        if not name:
            return None
        
        navigation_keywords = ['home', 'login', 'sign', 'cart', 'basket', 'checkout', 
                             'wallet', 'coin', 'account', 'profile', 'search', 'menu', 'shop', 'track']
        words = name.split()
        has_nav_keywords = any(word.lower() in navigation_keywords for word in words)
        
        # Only clean if name has nav keywords and is long enough (> 2 words)
        if has_nav_keywords and len(words) > 2:
            cleaned_words = words.copy()
            removed_count = 0
            # Remove navigation keywords from the end first
            while cleaned_words and cleaned_words[-1].lower() in navigation_keywords:
                cleaned_words.pop()
                removed_count += 1
            # Also remove from beginning if it's still long and starts with nav keyword
            if len(cleaned_words) > 3 and cleaned_words and cleaned_words[0].lower() in navigation_keywords:
                cleaned_words.pop(0)
                removed_count += 1
            if cleaned_words and len(cleaned_words) >= 1:
                cleaned_name = ' '.join(cleaned_words)
                self.logger.info(f"Cleaned nav keywords from '{name}' to '{cleaned_name}' (removed {removed_count} keywords)")
                return cleaned_name
            else:
                self.logger.debug(f"Removed all words from '{name}' after cleaning nav keywords")
                return None
        
        # No nav keywords or already clean, return as-is
        return name
    
    def _clean_extracted_name(self, name: str) -> Optional[str]:
        """Clean and validate extracted company name"""
        if not name:
            return None

        # Check if it's navigation text first (before cleaning)
        # But allow short names (1-2 words) even if they might match nav keywords
        # because company names can sometimes match (e.g., "Home Depot")
        if len(name.split()) > 2 and self._is_navigation_text(name):
            return None
        
        # Remove leading/trailing whitespace
        cleaned = name.strip()
        
        # V2.2.1: Remove common noise prefixes like "us", "at", "about"
        # These get captured when pattern matches text like "About us COMPANY NAME is..."
        words = cleaned.split()
        while words and words[0].lower() in self.NOISE_PREFIXES:
            words.pop(0)
        if not words:
            return None
        cleaned = ' '.join(words)
        
        # Remove "All Rights Reserved" etc.
        cleaned = re.sub(r'\s*All\s+Rights\s+Reserved.*$', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s*\d{4}\s*[-–]?\s*\d{4}', '', cleaned)  # Remove year ranges
        
        # V2.2.1: Remove if too short (5 chars min for meaningful company name) or too long
        if len(cleaned) < 5 or len(cleaned) > 100:
            return None
        
        # V2.2.1: Single-word names without legal suffixes are likely incomplete/false positives
        # Valid: "CELESTIA INNO PRIVATE LIMITED", "TechCorp Inc"
        # Invalid: "CELESTIA" alone (likely a brand name, not legal entity)
        words = cleaned.split()
        legal_suffixes = {'ltd', 'limited', 'inc', 'llc', 'llp', 'corp', 'corporation', 
                         'pvt', 'private', 'company', 'co', 'gmbh', 'sa', 'ag'}
        has_legal_suffix = any(w.lower().rstrip('.') in legal_suffixes for w in words)
        
        if len(words) == 1 and not has_legal_suffix:
            # Single word without legal suffix - too ambiguous to be a legal entity name
            return None
        
        # Remove if it's just numbers or common words
        if re.match(r'^[\d\s]+$', cleaned):
            return None
        
        # V2.2.1: Expanded list of common false positive words
        common_words = ['home', 'about', 'contact', 'privacy', 'terms', 'blog', 'news',
                       'shop', 'store', 'products', 'services', 'solutions', 'welcome',
                       'copyright', 'reserved', 'rights', 'policy', 'legal']
        if cleaned.lower() in common_words:
            return None
        
        return cleaned.strip()
    
    def _basic_similarity(self, s1: str, s2: str) -> float:
        """
        Basic string similarity when rapidfuzz is not available.
        
        V2.2.1: Enhanced to penalize:
        - Single word matches (not meaningful for company names)
        - Large word count differences (likely unrelated entities)
        """
        if not s1 or not s2:
            return 0.0
        
        # Simple approach: word overlap
        words1 = set(s1.lower().split())
        words2 = set(s2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        # V2.2.1: Single word matches are not meaningful for company names
        # e.g., "CELESTIA" matching "CELESTIA INNO PRIVATE LIMITED" should score low
        if len(intersection) == 1 and (len(words1) > 2 or len(words2) > 2):
            # Only 1 word matches but one side has 3+ words - likely coincidental
            return 20.0  # Low score, will be MISMATCH
        
        # V2.2.1: Penalize if word counts are very different
        # e.g., extracted "CELESTIA" (1 word) vs declared "CELESTIA INNO PRIVATE LIMITED" (4 words)
        len_ratio = min(len(words1), len(words2)) / max(len(words1), len(words2))
        if len_ratio < 0.5:
            # One side has less than half the words of the other - penalize
            base_jaccard = (len(intersection) / len(union)) * 100
            return base_jaccard * len_ratio  # Heavily penalized
        
        # Standard Jaccard similarity * 100
        return (len(intersection) / len(union)) * 100
    
    def _get_extraction_sources(self, scan_data: Dict[str, Any]) -> List[str]:
        """Get list of sources used for extraction"""
        sources = []
        
        business_details = scan_data.get('business_details', {})
        if business_details.get('extracted_business_name') and business_details.get('extracted_business_name') != 'Not found':
            sources.append('business_details')
        
        metadata = scan_data.get('metadata', {})
        if metadata.get('og:site_name'):
            sources.append('meta_og_site_name')
        if metadata.get('title'):
            sources.append('page_title')
        
        if scan_data.get('footer_text'):
            sources.append('footer_copyright')
        
        policy_details = scan_data.get('policy_details', {})
        if policy_details.get('terms_condition', {}).get('found'):
            sources.append('terms_conditions')
        if policy_details.get('about_us', {}).get('found'):
            sources.append('about_page')
        
        return sources

