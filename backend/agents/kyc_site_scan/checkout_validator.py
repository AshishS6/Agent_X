"""
Checkout Flow Validator
Browser-based validation of checkout flows using Playwright

Per PRD Section 6.3: Checkout & Payment Flow Simulation
- Product pricing visible
- "Buy / Subscribe / Checkout" CTA present
- Cart or checkout page reachable
- No real payment execution
"""

import asyncio
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse, urljoin

try:
    from .models.output_schema import CheckoutFlowResult
except ImportError:
    from models.output_schema import CheckoutFlowResult


class CheckoutValidator:
    """
    Validates checkout flows on websites using browser automation.
    
    Detection targets:
    1. "Buy Now" / "Add to Cart" / "Subscribe" / "Checkout" CTAs
    2. Pricing visibility (actual prices, not placeholders)
    3. Cart/checkout page reachability
    4. Form fields presence (no actual payment execution)
    """
    
    # CTA patterns to look for
    CTA_PATTERNS = [
        # Buy patterns
        r'\bbuy\s*now\b',
        r'\bbuy\s*it\s*now\b',
        r'\bpurchase\b',
        r'\border\s*now\b',
        r'\bget\s*started\b',
        r'\bget\s*it\s*now\b',
        # Cart patterns
        r'\badd\s*to\s*cart\b',
        r'\badd\s*to\s*bag\b',
        r'\badd\s*to\s*basket\b',
        # Subscribe patterns
        r'\bsubscribe\b',
        r'\bsign\s*up\b',
        r'\bstart\s*free\b',
        r'\bstart\s*trial\b',
        r'\btry\s*free\b',
        r'\btry\s*now\b',
        r'\btry\s*it\s*free\b',
        # Checkout patterns
        r'\bcheckout\b',
        r'\bproceed\s*to\s*checkout\b',
        r'\bproceed\s*to\s*payment\b',
        r'\bcomplete\s*order\b',
        r'\bplace\s*order\b',
        # Pricing patterns
        r'\bview\s*pricing\b',
        r'\bsee\s*pricing\b',
        r'\bpricing\s*plans\b',
        r'\bget\s*quote\b',
        r'\brequest\s*quote\b',
        r'\bcontact\s*sales\b',
    ]
    
    # Price patterns (various currencies)
    PRICE_PATTERNS = [
        r'\$\s*\d+(?:[.,]\d{2})?',           # $99.99 or $99
        r'₹\s*\d+(?:[.,]\d{2})?',            # ₹999
        r'€\s*\d+(?:[.,]\d{2})?',            # €99.99
        r'£\s*\d+(?:[.,]\d{2})?',            # £99.99
        r'\d+(?:[.,]\d{2})?\s*(?:USD|EUR|GBP|INR)',  # 99.99 USD
        r'(?:USD|EUR|GBP|INR)\s*\d+(?:[.,]\d{2})?',  # USD 99.99
        r'\d+\s*/\s*(?:mo|month|yr|year)',   # 99/mo, 99/year
        r'(?:per|/)\s*(?:month|year|user)',  # per month, /user
    ]
    
    # Checkout page indicators
    CHECKOUT_PAGE_PATTERNS = [
        r'\bcheckout\b',
        r'\bcart\b',
        r'\bbag\b',
        r'\bbasket\b',
        r'\bpayment\b',
        r'\bbilling\b',
        r'\bshipping\b',
        r'\border\s*summary\b',
        r'\border\s*details\b',
    ]
    
    # Form field selectors for checkout detection
    CHECKOUT_FORM_SELECTORS = [
        'input[name*="card"]',
        'input[name*="credit"]',
        'input[name*="payment"]',
        'input[name*="billing"]',
        'input[name*="shipping"]',
        'input[name*="address"]',
        'input[name*="email"]',
        'input[type="email"]',
        'input[name*="phone"]',
        'input[type="tel"]',
        '[data-stripe]',
        '[data-razorpay]',
        '.stripe-element',
        '.card-element',
        'iframe[src*="stripe"]',
        'iframe[src*="paypal"]',
        'iframe[src*="razorpay"]',
    ]
    
    # Placeholder/dummy price indicators
    PLACEHOLDER_INDICATORS = [
        r'\$0\.00',
        r'\$X+',
        r'XX\.XX',
        r'lorem',
        r'ipsum',
        r'TBD',
        r'coming\s*soon',
        r'price\s*on\s*request',
        r'contact\s*for\s*price',
    ]
    
    def __init__(self, logger: Optional[logging.Logger] = None, timeout: int = 30000):
        self.logger = logger or logging.getLogger(__name__)
        self.timeout = timeout  # milliseconds
        self._playwright = None
        self._browser = None
    
    async def validate(
        self,
        url: str,
        scan_data: Dict[str, Any],
        scan_id: str
    ) -> CheckoutFlowResult:
        """
        Validate checkout flow on a website.
        
        Args:
            url: Website URL to validate
            scan_data: Existing scan data from ModularScanEngine
            scan_id: Scan ID for logging
            
        Returns:
            CheckoutFlowResult with validation results
        """
        self.logger.info(f"[CHECKOUT][{scan_id}] Starting checkout validation for: {url}")
        
        # First, try to use existing scan data for basic detection
        basic_result = self._analyze_scan_data(scan_data)
        
        # If basic detection found no CTAs, try browser automation
        if not basic_result.has_cta:
            self.logger.info(f"[CHECKOUT][{scan_id}] No CTAs in scan data, trying browser automation")
            try:
                browser_result = await self._validate_with_browser(url, scan_id)
                return browser_result
            except Exception as e:
                self.logger.warning(f"[CHECKOUT][{scan_id}] Browser validation failed: {e}")
                return basic_result
        
        # If we found CTAs, validate they're clickable with browser
        if basic_result.has_cta:
            try:
                browser_result = await self._validate_ctas_with_browser(
                    url, scan_data, scan_id
                )
                # Merge results
                return CheckoutFlowResult(
                    has_cta=True,
                    cta_clickable=browser_result.cta_clickable,
                    checkout_reachable=browser_result.checkout_reachable,
                    pricing_visible=basic_result.pricing_visible or browser_result.pricing_visible,
                    form_fields_present=browser_result.form_fields_present,
                    dead_ctas=browser_result.dead_ctas,
                    evidence=browser_result.evidence,
                )
            except Exception as e:
                self.logger.warning(f"[CHECKOUT][{scan_id}] CTA validation failed: {e}")
                return basic_result
        
        return basic_result
    
    def _analyze_scan_data(self, scan_data: Dict[str, Any]) -> CheckoutFlowResult:
        """Analyze existing scan data for checkout indicators"""
        product_details = scan_data.get('product_details', {})
        
        # Check for CTAs from product indicators
        has_cart = product_details.get('has_cart', False)
        has_pricing = product_details.get('has_pricing', False)
        
        # Check crawled pages for CTA text
        crawl_summary = scan_data.get('crawl_summary', {})
        page_texts = crawl_summary.get('page_texts', {})
        
        ctas_found = []
        prices_found = []
        
        # Search through available page content
        for page_url, page_text in page_texts.items():
            if not page_text:
                continue
                
            page_text_lower = page_text.lower() if isinstance(page_text, str) else ''
            
            # Find CTAs
            for pattern in self.CTA_PATTERNS:
                if re.search(pattern, page_text_lower, re.IGNORECASE):
                    ctas_found.append((pattern, page_url))
            
            # Find prices
            for pattern in self.PRICE_PATTERNS:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    # Check if it's a placeholder
                    is_placeholder = any(
                        re.search(p, match, re.IGNORECASE)
                        for p in self.PLACEHOLDER_INDICATORS
                    )
                    if not is_placeholder:
                        prices_found.append((match, page_url))
        
        # Also check policy pages for pricing
        policy_details = scan_data.get('policy_details', {})
        pricing_page = policy_details.get('pricing', {})
        if pricing_page.get('found'):
            has_pricing = True
        
        return CheckoutFlowResult(
            has_cta=has_cart or len(ctas_found) > 0,
            cta_clickable=False,  # Unknown without browser
            checkout_reachable=False,  # Unknown without browser
            pricing_visible=has_pricing or len(prices_found) > 0,
            form_fields_present=False,  # Unknown without browser
            dead_ctas=[],
            evidence={
                'ctas_found': ctas_found[:5],  # Limit for output
                'prices_found': prices_found[:5],
                'source': 'scan_data_analysis'
            }
        )
    
    async def _validate_with_browser(
        self,
        url: str,
        scan_id: str
    ) -> CheckoutFlowResult:
        """Full browser-based validation"""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            self.logger.warning("Playwright not installed, falling back to basic detection")
            return CheckoutFlowResult(
                has_cta=False,
                cta_clickable=False,
                checkout_reachable=False,
                pricing_visible=False,
                form_fields_present=False,
                evidence={'error': 'Playwright not installed'}
            )
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            try:
                # Navigate to the page
                await page.goto(url, wait_until='networkidle', timeout=self.timeout)
                await page.wait_for_timeout(2000)  # Wait for dynamic content
                
                # Get page content
                page_content = await page.content()
                page_text = await page.evaluate('() => document.body.innerText')
                
                # Find CTAs
                ctas_found = await self._find_ctas(page, page_text)
                has_cta = len(ctas_found) > 0
                
                # Find prices
                prices_found = self._find_prices(page_text)
                pricing_visible = len(prices_found) > 0
                
                # Test CTA clickability
                cta_clickable = False
                checkout_reachable = False
                dead_ctas = []
                form_fields_present = False
                
                if ctas_found:
                    cta_clickable, checkout_reachable, dead_ctas, form_fields_present = \
                        await self._test_ctas(page, ctas_found, scan_id)
                
                return CheckoutFlowResult(
                    has_cta=has_cta,
                    cta_clickable=cta_clickable,
                    checkout_reachable=checkout_reachable,
                    pricing_visible=pricing_visible,
                    form_fields_present=form_fields_present,
                    dead_ctas=dead_ctas,
                    evidence={
                        'ctas_found': [c[0] for c in ctas_found[:5]],
                        'prices_found': prices_found[:5],
                        'source': 'browser_automation'
                    }
                )
                
            finally:
                await browser.close()
    
    async def _validate_ctas_with_browser(
        self,
        url: str,
        scan_data: Dict[str, Any],
        scan_id: str
    ) -> CheckoutFlowResult:
        """Validate CTAs found in scan data using browser"""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return CheckoutFlowResult(
                has_cta=True,
                cta_clickable=False,
                checkout_reachable=False,
                pricing_visible=False,
                form_fields_present=False,
            )
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            try:
                await page.goto(url, wait_until='networkidle', timeout=self.timeout)
                await page.wait_for_timeout(2000)
                
                # Find CTAs in the page
                page_text = await page.evaluate('() => document.body.innerText')
                ctas_found = await self._find_ctas(page, page_text)
                
                # Find prices
                prices_found = self._find_prices(page_text)
                
                # Test CTA clickability
                cta_clickable, checkout_reachable, dead_ctas, form_fields_present = \
                    await self._test_ctas(page, ctas_found, scan_id)
                
                return CheckoutFlowResult(
                    has_cta=len(ctas_found) > 0,
                    cta_clickable=cta_clickable,
                    checkout_reachable=checkout_reachable,
                    pricing_visible=len(prices_found) > 0,
                    form_fields_present=form_fields_present,
                    dead_ctas=dead_ctas,
                    evidence={
                        'tested_ctas': len(ctas_found),
                        'source': 'browser_cta_validation'
                    }
                )
                
            finally:
                await browser.close()
    
    async def _find_ctas(self, page, page_text: str) -> List[Tuple[str, Any]]:
        """Find CTA buttons/links in the page"""
        ctas_found = []
        
        # Check page text for CTA patterns
        for pattern in self.CTA_PATTERNS:
            if re.search(pattern, page_text.lower(), re.IGNORECASE):
                # Try to find the actual element
                try:
                    # Build selector for this CTA text
                    selector = f'button, a, [role="button"], input[type="submit"]'
                    elements = await page.query_selector_all(selector)
                    
                    for element in elements:
                        try:
                            text = await element.inner_text()
                            if re.search(pattern, text.lower(), re.IGNORECASE):
                                is_visible = await element.is_visible()
                                if is_visible:
                                    ctas_found.append((text.strip(), element))
                        except:
                            continue
                except:
                    pass
        
        return ctas_found[:10]  # Limit to 10 CTAs
    
    def _find_prices(self, page_text: str) -> List[str]:
        """Find prices in page text"""
        prices = []
        
        for pattern in self.PRICE_PATTERNS:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            for match in matches:
                # Filter out placeholders
                is_placeholder = any(
                    re.search(p, match, re.IGNORECASE)
                    for p in self.PLACEHOLDER_INDICATORS
                )
                if not is_placeholder and match not in prices:
                    prices.append(match)
        
        return prices
    
    async def _test_ctas(
        self,
        page,
        ctas: List[Tuple[str, Any]],
        scan_id: str
    ) -> Tuple[bool, bool, List[str], bool]:
        """
        Test CTA clickability and checkout reachability.
        
        Returns:
            Tuple of (cta_clickable, checkout_reachable, dead_ctas, form_fields_present)
        """
        cta_clickable = False
        checkout_reachable = False
        dead_ctas = []
        form_fields_present = False
        
        original_url = page.url
        
        for cta_text, element in ctas[:3]:  # Test first 3 CTAs only
            try:
                self.logger.debug(f"[CHECKOUT][{scan_id}] Testing CTA: {cta_text}")
                
                # Check if element is clickable
                is_enabled = await element.is_enabled()
                if not is_enabled:
                    dead_ctas.append(cta_text)
                    continue
                
                # Click the CTA
                try:
                    await element.click(timeout=5000)
                    cta_clickable = True
                    
                    # Wait for navigation
                    await page.wait_for_timeout(2000)
                    
                    # Check if we're on a checkout page
                    new_url = page.url
                    new_text = await page.evaluate('() => document.body.innerText')
                    
                    is_checkout = self._is_checkout_page(new_url, new_text)
                    if is_checkout:
                        checkout_reachable = True
                        
                        # Check for form fields
                        form_fields_present = await self._check_form_fields(page)
                        
                        self.logger.info(
                            f"[CHECKOUT][{scan_id}] Checkout page found: {new_url}"
                        )
                        break
                    
                    # Go back to original page for next CTA test
                    if new_url != original_url:
                        await page.goto(original_url, wait_until='networkidle', timeout=self.timeout)
                        await page.wait_for_timeout(1000)
                        
                except Exception as e:
                    self.logger.debug(f"[CHECKOUT][{scan_id}] CTA click failed: {e}")
                    dead_ctas.append(cta_text)
                    
            except Exception as e:
                self.logger.debug(f"[CHECKOUT][{scan_id}] CTA test error: {e}")
                continue
        
        return cta_clickable, checkout_reachable, dead_ctas, form_fields_present
    
    def _is_checkout_page(self, url: str, page_text: str) -> bool:
        """Check if current page is a checkout/cart page"""
        url_lower = url.lower()
        text_lower = page_text.lower()
        
        # Check URL
        for pattern in self.CHECKOUT_PAGE_PATTERNS:
            if re.search(pattern, url_lower):
                return True
        
        # Check page content (multiple indicators required)
        checkout_indicators = 0
        for pattern in self.CHECKOUT_PAGE_PATTERNS:
            if re.search(pattern, text_lower):
                checkout_indicators += 1
        
        # Also check for order/cart summary
        if re.search(r'order\s*total|subtotal|grand\s*total', text_lower):
            checkout_indicators += 1
        
        return checkout_indicators >= 2
    
    async def _check_form_fields(self, page) -> bool:
        """Check if checkout form fields are present"""
        for selector in self.CHECKOUT_FORM_SELECTORS:
            try:
                elements = await page.query_selector_all(selector)
                if elements and len(elements) > 0:
                    return True
            except:
                continue
        
        return False

