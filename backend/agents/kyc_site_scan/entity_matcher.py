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
        # With year and optional separator (|, -, –, or whitespace)
        # Greedy capture for company name, terminated by ". All" or "All Rights"
        r'©\s*\d{4}\s*[-|–]?\s*([A-Z][A-Za-z0-9\s&,\'-]+(?:Private\s+Limited|Pvt\.?\s*Ltd\.?|Limited|Ltd\.?|Inc\.?|LLC|LLP)?)\s*\.?\s*(?:All\s*[Rr]ights|$)',
        r'\(c\)\s*\d{4}\s*[-|–]?\s*([A-Z][A-Za-z0-9\s&,\'-]+(?:Private\s+Limited|Pvt\.?\s*Ltd\.?|Limited|Ltd\.?|Inc\.?|LLC|LLP)?)\s*\.?\s*(?:All\s*[Rr]ights|$)',
        r'[Cc]opyright\s*(?:©|\(c\))?\s*\d{4}\s*[-|–]?\s*([A-Z][A-Za-z0-9\s&,\'-]+(?:Private\s+Limited|Pvt\.?\s*Ltd\.?|Limited|Ltd\.?|Inc\.?|LLC|LLP)?)\s*\.?\s*(?:All\s*[Rr]ights|$)',
        # Without year
        r'©\s+([A-Z][A-Za-z0-9\s&,\'-]+(?:Private\s+Limited|Pvt\.?\s*Ltd\.?|Limited|Ltd\.?|Inc\.?|LLC|LLP)?)\s*\.?\s*(?:All\s*[Rr]ights|$)',
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
    
    # Patterns for extracting addresses
    ADDRESS_PATTERNS = [
        # Indian address format
        r'(?:address|office|headquarter|location)[\s:]+(.{20,200}?(?:India|IN|\d{6}))',
        # US address format
        r'(\d+\s+[\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Way)[,\s]+[\w\s]+[,\s]+[A-Z]{2}\s+\d{5}(?:-\d{4})?)',
        # UK address format
        r'(\d+\s+[\w\s]+[,\s]+[\w\s]+[,\s]+[\w\s]+[,\s]+[A-Z]{1,2}\d{1,2}\s*\d[A-Z]{2})',
        # Generic with PIN code
        r'(?:registered\s+(?:office|address)|head\s*office)[\s:]+(.{20,200}?\d{5,6})',
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
        extracted_names = self._extract_legal_names(scan_data)
        
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
        address_match = self._match_address(declared_address, extracted_addresses)
        
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
            names.append(extracted_name)
        
        # 2. From meta tags
        metadata = scan_data.get('metadata', {})
        og_site_name = metadata.get('og:site_name')
        if og_site_name:
            names.append(og_site_name)
        
        # 3. From page title
        title = metadata.get('title', '')
        if title:
            # Extract company name from title (often "Company - Tagline")
            title_parts = re.split(r'\s*[-|–]\s*', title)
            if title_parts:
                names.append(title_parts[0].strip())
        
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
                    if len(clean_name) >= 3 and clean_name not in names:
                        names.append(clean_name)
            
            # V2.2.1: Also look for "Company Name is a..." pattern (common in footers/about sections)
            for pattern in self.DESCRIPTIVE_PATTERNS:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    clean_name = match.strip()
                    if len(clean_name) >= 3 and clean_name not in names:
                        names.append(clean_name)
        
        # 5. Look in footer specifically
        footer_text = scan_data.get('footer_text', '')
        if footer_text:
            for pattern in self.COPYRIGHT_PATTERNS:
                matches = re.findall(pattern, footer_text, re.IGNORECASE)
                for match in matches:
                    clean_name = match.strip()
                    clean_name = re.sub(r'\s*[.|,]\s*$', '', clean_name)
                    if len(clean_name) >= 3 and clean_name not in names:
                        names.append(clean_name)
            # Also check descriptive patterns in footer
            for pattern in self.DESCRIPTIVE_PATTERNS:
                matches = re.findall(pattern, footer_text, re.IGNORECASE)
                for match in matches:
                    clean_name = match.strip()
                    if len(clean_name) >= 3 and clean_name not in names:
                        names.append(clean_name)
        
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
        
        # Deduplicate and clean
        cleaned_names = []
        for name in names:
            cleaned = self._clean_extracted_name(name)
            if cleaned and cleaned not in cleaned_names:
                cleaned_names.append(cleaned)
        
        return cleaned_names[:10]  # Limit to 10 names
    
    def _extract_addresses(self, scan_data: Dict[str, Any]) -> List[str]:
        """Extract addresses from scan data"""
        addresses = []
        
        # From business_details
        business_details = scan_data.get('business_details', {})
        contact_info = business_details.get('contact_info', {})
        address = contact_info.get('address')
        if address and address != 'Not found':
            addresses.append(address)
        
        # Search page content
        crawl_summary = scan_data.get('crawl_summary', {})
        page_texts = crawl_summary.get('page_texts', {})
        
        for page_url, page_text in page_texts.items():
            if not page_text:
                continue
            
            for pattern in self.ADDRESS_PATTERNS:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    clean_addr = match.strip()
                    if len(clean_addr) >= 20 and clean_addr not in addresses:
                        addresses.append(clean_addr)
        
        return addresses[:5]  # Limit to 5 addresses
    
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
    
    def _clean_extracted_name(self, name: str) -> Optional[str]:
        """Clean an extracted name"""
        if not name:
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

