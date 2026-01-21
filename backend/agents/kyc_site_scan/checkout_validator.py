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
    
    # Checkout page indicators (strong signals)
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
        r'route=checkout',  # For route-based URLs like index.php?route=checkout/checkout
        r'route=cart',      # For route-based URLs
        r'route=payment',   # For route-based URLs
    ]
    
    # Strong checkout page indicators (high confidence)
    STRONG_CHECKOUT_INDICATORS = [
        r'order\s*total|subtotal|grand\s*total|total\s*amount',
        r'payment\s*method|payment\s*information',
        r'credit\s*card|debit\s*card|card\s*number',
        r'billing\s*address|shipping\s*address',
        r'place\s*order|complete\s*purchase|confirm\s*order',
        r'cart\s*summary|order\s*summary|review\s*order',
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
        'iframe[src*="braintree"]',
        'iframe[src*="square"]',
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
            CheckoutFlowResult with validation results including checkout_url
        """
        self.logger.info(f"[CHECKOUT][{scan_id}] Starting checkout validation for: {url}")
        
        # First, try to use existing scan data for basic detection
        basic_result = self._analyze_scan_data(scan_data)
        self.logger.info(
            f"[CHECKOUT][{scan_id}] Basic analysis: has_cta={basic_result.has_cta}, "
            f"pricing_visible={basic_result.pricing_visible}, "
            f"ctas_found={len(basic_result.evidence.get('ctas_found', []) if basic_result.evidence else [])}"
        )
        
        # Always try browser automation for reliable validation
        # Even if basic detection found CTAs, we need to verify they work
        try:
            self.logger.info(f"[CHECKOUT][{scan_id}] Starting browser-based validation")
            browser_result = await self._validate_with_browser(url, scan_id, scan_data)
            
            # Merge with basic results
            final_result = CheckoutFlowResult(
                has_cta=browser_result.has_cta or basic_result.has_cta,
                cta_clickable=browser_result.cta_clickable,
                checkout_reachable=browser_result.checkout_reachable,
                checkout_url=browser_result.checkout_url,
                checkout_confidence=browser_result.checkout_confidence,
                pricing_visible=browser_result.pricing_visible or basic_result.pricing_visible,
                form_fields_present=browser_result.form_fields_present,
                dead_ctas=browser_result.dead_ctas,
                evidence={
                    **(browser_result.evidence or {}),
                    **(basic_result.evidence or {}),
                    'validation_method': 'browser_automation'
                }
            )
            
            self.logger.info(
                f"[CHECKOUT][{scan_id}] Validation complete: "
                f"checkout_reachable={final_result.checkout_reachable}, "
                f"checkout_url={final_result.checkout_url}, "
                f"confidence={final_result.checkout_confidence:.2f}"
            )
            
            return final_result
            
        except Exception as e:
            self.logger.error(
                f"[CHECKOUT][{scan_id}] Browser validation failed: {e}", 
                exc_info=True
            )
            # Try direct checkout URL check as fallback
            try:
                fallback_result = await self._check_direct_checkout_urls(url, scan_id, None, scan_data)
                if fallback_result and fallback_result.get('checkout_reachable'):
                    self.logger.info(f"[CHECKOUT][{scan_id}] Fallback: Found checkout via direct URL check")
                    return CheckoutFlowResult(
                        has_cta=basic_result.has_cta,
                        cta_clickable=False,
                        checkout_reachable=True,
                        checkout_url=fallback_result['checkout_url'],
                        checkout_confidence=fallback_result['checkout_confidence'],
                        pricing_visible=basic_result.pricing_visible,
                        form_fields_present=fallback_result['form_fields_present'],
                        evidence={'source': 'direct_url_fallback', **fallback_result}
                    )
            except Exception as fallback_error:
                self.logger.warning(f"[CHECKOUT][{scan_id}] Fallback check also failed: {fallback_error}")
            
            # Return basic result if all browser attempts fail
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
            checkout_url=None,
            checkout_confidence=0.0,
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
        scan_id: str,
        scan_data: Optional[Dict[str, Any]] = None
    ) -> CheckoutFlowResult:
        """Full browser-based validation"""
        try:
            from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
        except ImportError:
            self.logger.warning("Playwright not installed, falling back to basic detection")
            return CheckoutFlowResult(
                has_cta=False,
                cta_clickable=False,
                checkout_reachable=False,
                checkout_url=None,
                checkout_confidence=0.0,
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
                # Navigate to the page with better error handling
                try:
                    await page.goto(url, wait_until='domcontentloaded', timeout=self.timeout)
                    # Wait for dynamic content with multiple strategies
                    await self._wait_for_page_ready(page)
                except PlaywrightTimeoutError as e:
                    self.logger.warning(f"[CHECKOUT][{scan_id}] Page load timeout: {e}")
                    # Try to continue with what we have
                except Exception as e:
                    self.logger.warning(f"[CHECKOUT][{scan_id}] Navigation error: {e}")
                    raise
                
                # Get page content
                page_content = await page.content()
                page_text = await page.evaluate('() => document.body.innerText')
                self.logger.debug(f"[CHECKOUT][{scan_id}] Page loaded, content length: {len(page_text)} chars")
                
                # Find CTAs
                ctas_found = await self._find_ctas(page, page_text)
                has_cta = len(ctas_found) > 0
                self.logger.info(f"[CHECKOUT][{scan_id}] Found {len(ctas_found)} CTAs: {[c[0][:50] for c in ctas_found[:3]]}")
                
                # Find prices
                prices_found = self._find_prices(page_text)
                pricing_visible = len(prices_found) > 0
                self.logger.info(f"[CHECKOUT][{scan_id}] Found {len(prices_found)} prices: {prices_found[:3]}")
                
                # Test CTA clickability
                cta_clickable = False
                checkout_reachable = False
                checkout_url = None
                checkout_confidence = 0.0
                dead_ctas = []
                form_fields_present = False
                
                if ctas_found:
                    self.logger.info(f"[CHECKOUT][{scan_id}] Testing {len(ctas_found)} CTAs...")
                    result = await self._test_ctas(page, ctas_found, scan_id, url)
                    cta_clickable = result['cta_clickable']
                    checkout_reachable = result['checkout_reachable']
                    checkout_url = result['checkout_url']
                    checkout_confidence = result['checkout_confidence']
                    dead_ctas = result['dead_ctas']
                    form_fields_present = result['form_fields_present']
                    
                    self.logger.info(
                        f"[CHECKOUT][{scan_id}] CTA testing complete: "
                        f"clickable={cta_clickable}, reachable={checkout_reachable}, "
                        f"url={checkout_url}, confidence={checkout_confidence:.2f}"
                    )
                    
                    # If CTAs didn't lead to checkout, try direct URL fallback
                    if not checkout_reachable:
                        self.logger.info(f"[CHECKOUT][{scan_id}] CTAs didn't lead to checkout, trying direct URL fallback...")
                        try:
                            direct_check = await self._check_direct_checkout_urls(url, scan_id, page, scan_data)
                            if direct_check and direct_check.get('checkout_reachable'):
                                checkout_reachable = direct_check['checkout_reachable']
                                checkout_url = direct_check['checkout_url']
                                checkout_confidence = direct_check['checkout_confidence']
                                form_fields_present = direct_check['form_fields_present']
                                self.logger.info(f"[CHECKOUT][{scan_id}] Found checkout via direct URL fallback: {checkout_url}")
                        except Exception as fallback_error:
                            self.logger.debug(f"[CHECKOUT][{scan_id}] Direct URL fallback failed: {fallback_error}")
                elif not ctas_found:
                    self.logger.warning(f"[CHECKOUT][{scan_id}] No CTAs found on page, trying direct checkout URL check")
                    # Try direct checkout URL check as fallback
                    direct_check = await self._check_direct_checkout_urls(url, scan_id, page, scan_data)
                    if direct_check and direct_check.get('checkout_reachable'):
                        checkout_reachable = direct_check['checkout_reachable']
                        checkout_url = direct_check['checkout_url']
                        checkout_confidence = direct_check['checkout_confidence']
                        form_fields_present = direct_check['form_fields_present']
                        self.logger.info(f"[CHECKOUT][{scan_id}] Found checkout via direct URL: {checkout_url}")
                
                return CheckoutFlowResult(
                    has_cta=has_cta,
                    cta_clickable=cta_clickable,
                    checkout_reachable=checkout_reachable,
                    checkout_url=checkout_url,
                    checkout_confidence=checkout_confidence,
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
                try:
                    await browser.close()
                except Exception as e:
                    self.logger.debug(f"[CHECKOUT][{scan_id}] Error closing browser: {e}")
    
    async def _validate_ctas_with_browser(
        self,
        url: str,
        scan_data: Dict[str, Any],
        scan_id: str
    ) -> CheckoutFlowResult:
        """Validate CTAs found in scan data using browser"""
        try:
            from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
        except ImportError:
            return CheckoutFlowResult(
                has_cta=True,
                cta_clickable=False,
                checkout_reachable=False,
                checkout_url=None,
                checkout_confidence=0.0,
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
                try:
                    await page.goto(url, wait_until='domcontentloaded', timeout=self.timeout)
                    await self._wait_for_page_ready(page)
                except PlaywrightTimeoutError as e:
                    self.logger.warning(f"[CHECKOUT][{scan_id}] Page load timeout: {e}")
                except Exception as e:
                    self.logger.warning(f"[CHECKOUT][{scan_id}] Navigation error: {e}")
                    raise
                
                # Find CTAs in the page
                page_text = await page.evaluate('() => document.body.innerText')
                ctas_found = await self._find_ctas(page, page_text)
                
                # Find prices
                prices_found = self._find_prices(page_text)
                
                # Test CTA clickability
                result = await self._test_ctas(page, ctas_found, scan_id, url)
                
                return CheckoutFlowResult(
                    has_cta=len(ctas_found) > 0,
                    cta_clickable=result['cta_clickable'],
                    checkout_reachable=result['checkout_reachable'],
                    checkout_url=result['checkout_url'],
                    checkout_confidence=result['checkout_confidence'],
                    pricing_visible=len(prices_found) > 0,
                    form_fields_present=result['form_fields_present'],
                    dead_ctas=result['dead_ctas'],
                    evidence={
                        'tested_ctas': len(ctas_found),
                        'source': 'browser_cta_validation'
                    }
                )
                
            finally:
                await browser.close()
    
    async def _wait_for_page_ready(self, page, max_wait: int = 5000):
        """
        Wait for page to be ready with multiple strategies for SPAs.
        
        Strategies:
        1. Wait for network idle (if possible)
        2. Wait for common loading indicators to disappear
        3. Wait for key elements to be visible
        
        Returns True if page is ready, False if timeout or login required
        """
        try:
            # Strategy 1: Wait for network to be relatively idle (with shorter timeout)
            await page.wait_for_load_state('networkidle', timeout=2000)
        except Exception:
            # If networkidle times out, continue
            pass
        
        # Check if we're on a login/signin page (don't wait forever)
        current_url = page.url.lower()
        page_text = await page.evaluate('() => document.body.innerText') if hasattr(page, 'evaluate') else ''
        
        login_indicators = ['sign in', 'signin', 'login', 'log in', 'authenticate', 'password', 'email']
        if any(indicator in current_url or indicator in page_text.lower()[:500] for indicator in login_indicators):
            # Likely redirected to login - return early
            return False
        
        # Strategy 2: Wait for common loading indicators to disappear (with shorter timeout)
        loading_selectors = [
            '.loading', '.spinner', '[data-loading]', '.loader',
            '.skeleton', '.shimmer', '[aria-busy="true"]'
        ]
        
        for selector in loading_selectors:
            try:
                await page.wait_for_selector(
                    selector,
                    state='hidden',
                    timeout=500  # Reduced timeout
                )
            except Exception:
                continue
        
        # Strategy 3: Wait a bit for dynamic content (reduced wait)
        await page.wait_for_timeout(1000)  # Reduced from 1500ms
        
        return True
    
    async def _find_ctas(self, page, page_text: str) -> List[Tuple[str, Any]]:
        """Find CTA buttons/links in the page"""
        ctas_found = []
        
        # Check page text for CTA patterns
        for pattern in self.CTA_PATTERNS:
            if re.search(pattern, page_text.lower(), re.IGNORECASE):
                # Try to find the actual element
                try:
                    # Build selector for this CTA text
                    selector = 'button, a, [role="button"], input[type="submit"], input[type="button"]'
                    elements = await page.query_selector_all(selector)
                    
                    for element in elements:
                        try:
                            text = await element.inner_text()
                            if text and re.search(pattern, text.lower(), re.IGNORECASE):
                                is_visible = await element.is_visible()
                                if is_visible:
                                    ctas_found.append((text.strip(), element))
                        except Exception as e:
                            # Element might be detached or not accessible
                            self.logger.debug(f"Error reading element text: {e}")
                            continue
                except Exception as e:
                    self.logger.debug(f"Error querying CTA elements: {e}")
                    continue
        
        # Remove duplicates based on text
        seen_texts = set()
        unique_ctas = []
        for text, element in ctas_found:
            if text.lower() not in seen_texts:
                seen_texts.add(text.lower())
                unique_ctas.append((text, element))
        
        return unique_ctas[:10]  # Limit to 10 CTAs
    
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
        scan_id: str,
        original_url: str
    ) -> Dict[str, Any]:
        """
        Test CTA clickability and checkout reachability.
        
        Returns:
            Dict with: cta_clickable, checkout_reachable, checkout_url, 
                      checkout_confidence, dead_ctas, form_fields_present
        """
        from playwright.async_api import TimeoutError as PlaywrightTimeoutError
        
        cta_clickable = False
        checkout_reachable = False
        checkout_url = None
        checkout_confidence = 0.0
        dead_ctas = []
        form_fields_present = False
        
        base_url = original_url
        
        for cta_text, element in ctas[:5]:  # Test first 5 CTAs
            try:
                self.logger.debug(f"[CHECKOUT][{scan_id}] Testing CTA: {cta_text}")
                
                # Check if element is still attached and visible
                try:
                    is_visible = await element.is_visible()
                    is_enabled = await element.is_enabled()
                except Exception as e:
                    self.logger.debug(f"[CHECKOUT][{scan_id}] Element check failed: {e}")
                    dead_ctas.append(f"{cta_text} (element detached)")
                    continue
                
                if not is_visible or not is_enabled:
                    dead_ctas.append(f"{cta_text} (not visible/enabled)")
                    continue
                
                # Scroll element into view
                try:
                    await element.scroll_into_view_if_needed()
                    await page.wait_for_timeout(500)  # Wait for scroll
                except Exception as e:
                    self.logger.debug(f"[CHECKOUT][{scan_id}] Scroll failed: {e}")
                
                # Click the CTA
                try:
                    await element.click(timeout=5000)
                    cta_clickable = True
                    
                    # Wait for navigation or page changes
                    try:
                        # Wait for URL change or network activity
                        await page.wait_for_timeout(2000)
                        
                        # Check if URL changed
                        new_url = page.url
                        url_changed = new_url != base_url
                        
                        # Wait a bit more for dynamic content
                        await page.wait_for_timeout(1500)
                        
                        # Get updated page content
                        new_text = await page.evaluate('() => document.body.innerText')
                        
                        self.logger.debug(
                            f"[CHECKOUT][{scan_id}] After clicking '{cta_text}': "
                            f"URL={new_url}, text_length={len(new_text)}"
                        )
                        
                        # Validate if this is a checkout page (async version)
                        validation_result = await self._validate_checkout_page_async(
                            new_url, new_text, page, base_url
                        )
                        
                        self.logger.debug(
                            f"[CHECKOUT][{scan_id}] Validation result: "
                            f"is_checkout={validation_result['is_checkout']}, "
                            f"confidence={validation_result['confidence']:.2f}, "
                            f"indicators={validation_result.get('indicators', [])[:3]}"
                        )
                        
                        if validation_result['is_checkout']:
                            checkout_reachable = True
                            checkout_url = new_url
                            checkout_confidence = validation_result['confidence']
                            form_fields_present = validation_result['form_fields_present']
                            
                            self.logger.info(
                                f"[CHECKOUT][{scan_id}] Checkout page found: {new_url} "
                                f"(confidence: {checkout_confidence:.2f})"
                            )
                            break  # Found checkout, no need to test more CTAs
                        
                        # If URL changed but not checkout, go back
                        if url_changed and new_url != base_url:
                            try:
                                await page.goto(base_url, wait_until='domcontentloaded', timeout=self.timeout)
                                await self._wait_for_page_ready(page)
                            except Exception as e:
                                self.logger.debug(f"[CHECKOUT][{scan_id}] Failed to return to base URL: {e}")
                                # Continue with current page
                                base_url = new_url
                                
                    except Exception as e:
                        self.logger.debug(f"[CHECKOUT][{scan_id}] Post-click validation failed: {e}")
                        # CTA was clickable but didn't lead to checkout
                        continue
                        
                except PlaywrightTimeoutError:
                    self.logger.debug(f"[CHECKOUT][{scan_id}] CTA click timeout: {cta_text}")
                    dead_ctas.append(f"{cta_text} (click timeout)")
                except Exception as e:
                    self.logger.debug(f"[CHECKOUT][{scan_id}] CTA click failed: {e}")
                    dead_ctas.append(f"{cta_text} (click error)")
                    
            except Exception as e:
                self.logger.debug(f"[CHECKOUT][{scan_id}] CTA test error: {e}")
                continue
        
        return {
            'cta_clickable': cta_clickable,
            'checkout_reachable': checkout_reachable,
            'checkout_url': checkout_url,
            'checkout_confidence': checkout_confidence,
            'dead_ctas': dead_ctas,
            'form_fields_present': form_fields_present
        }
    
    def _validate_checkout_page(
        self,
        url: str,
        page_text: str,
        page,
        base_url: str
    ) -> Dict[str, Any]:
        """
        Validate if a page is a checkout page using multiple factors.
        
        Returns:
            Dict with: is_checkout (bool), confidence (float 0-1), form_fields_present (bool)
        """
        url_lower = url.lower()
        text_lower = page_text.lower()
        
        confidence_score = 0.0
        indicators_found = []
        
        # Factor 1: URL patterns (strong signal)
        url_checkout_score = 0.0
        for pattern in self.CHECKOUT_PAGE_PATTERNS:
            if re.search(pattern, url_lower):
                url_checkout_score += 0.15
                indicators_found.append(f"url_pattern:{pattern}")
        
        # Special handling for route-based URLs (e.g., index.php?route=checkout/checkout)
        if 'route=checkout' in url_lower or 'route=cart' in url_lower or 'route=payment' in url_lower:
            url_checkout_score += 0.2  # Extra boost for explicit checkout routes
            indicators_found.append("route_based_checkout")
        
        # URL should not be the same as base (unless it's a modal/SPA)
        if url != base_url:
            url_checkout_score += 0.1
        
        confidence_score += min(url_checkout_score, 0.4)  # Increased cap to 0.4
        
        # Factor 2: Strong checkout indicators in content (very strong signal)
        strong_indicators_count = 0
        for pattern in self.STRONG_CHECKOUT_INDICATORS:
            if re.search(pattern, text_lower):
                strong_indicators_count += 1
                indicators_found.append(f"strong_indicator:{pattern}")
        
        # Each strong indicator adds significant confidence
        confidence_score += min(strong_indicators_count * 0.2, 0.5)  # Cap at 0.5
        
        # Factor 3: Multiple checkout page patterns (moderate signal)
        pattern_matches = 0
        for pattern in self.CHECKOUT_PAGE_PATTERNS:
            if re.search(pattern, text_lower):
                pattern_matches += 1
                indicators_found.append(f"content_pattern:{pattern}")
        
        # Require at least 2 patterns for moderate confidence
        if pattern_matches >= 2:
            confidence_score += 0.15
        elif pattern_matches >= 1:
            confidence_score += 0.05
        
        # Factor 4: Form fields presence (strong signal)
        form_fields_present = False
        try:
            # Use synchronous check since we can't await here
            # This will be checked properly in async context
            form_fields_present = False  # Will be set by async check
        except Exception:
            pass
        
        # Factor 5: Negative indicators (reduce confidence)
        # If page has product listing indicators, it's probably not checkout
        product_listing_indicators = [
            r'add\s*to\s*cart',  # Multiple add to cart buttons = product listing
            r'view\s*all\s*products',
            r'shop\s*now',
            r'browse\s*products',
        ]
        
        negative_score = 0.0
        for pattern in product_listing_indicators:
            matches = len(re.findall(pattern, text_lower))
            if matches > 2:  # Multiple instances suggest product listing
                negative_score += 0.1
                indicators_found.append(f"negative:{pattern}")
        
        confidence_score = max(0.0, confidence_score - negative_score)
        
        # Minimum threshold: need at least 0.25 confidence to be considered checkout
        # Lowered from 0.4 to be more lenient and catch more checkout pages
        is_checkout = confidence_score >= 0.25
        
        return {
            'is_checkout': is_checkout,
            'confidence': min(confidence_score, 1.0),
            'form_fields_present': form_fields_present,
            'indicators': indicators_found
        }
    
    async def _check_form_fields(self, page) -> bool:
        """Check if checkout form fields are present"""
        for selector in self.CHECKOUT_FORM_SELECTORS:
            try:
                elements = await page.query_selector_all(selector)
                if elements and len(elements) > 0:
                    # Verify at least one is visible
                    for element in elements[:3]:  # Check first 3
                        try:
                            if await element.is_visible():
                                return True
                        except Exception:
                            continue
            except Exception as e:
                self.logger.debug(f"Error checking form selector {selector}: {e}")
                continue
        
        return False
    
    async def _check_direct_checkout_urls(
        self,
        base_url: str,
        scan_id: str,
        page = None,
        scan_data: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Fallback: Check common checkout URLs directly.
        This is useful when CTAs aren't found or don't work.
        Also checks URLs found in scan_data.
        """
        from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
        from urllib.parse import urljoin, urlparse
        
        # First, check if scan_data has checkout-related URLs
        urls_to_check = []
        if scan_data:
            crawl_summary = scan_data.get('crawl_summary', {})
            urls_visited = crawl_summary.get('urls_visited', [])
            page_graph = scan_data.get('page_graph', {})
            
            # Look for checkout-related URLs in visited URLs
            checkout_keywords = ['checkout', 'cart', 'basket', 'order', 'payment']
            for visited_url in urls_visited:
                url_lower = visited_url.lower()
                if any(keyword in url_lower for keyword in checkout_keywords):
                    urls_to_check.append(visited_url)
                    self.logger.debug(f"[CHECKOUT][{scan_id}] Found potential checkout URL from scan: {visited_url}")
        
        # Add common checkout paths
        common_checkout_paths = [
            '/checkout',
            '/checkout/',
            '/cart',
            '/cart/',
            '/basket',
            '/basket/',
            '/shopping-cart',
            '/shopping-cart/',
            '/order',
            '/order/',
        ]
        
        # Add common paths to check list
        for path in common_checkout_paths:
            full_url = urljoin(base_url, path)
            if full_url not in urls_to_check:
                urls_to_check.append(full_url)
        
        # If page is provided, use it; otherwise create a new one
        if page is None:
            # Create a new browser context for direct URL checking
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    context = await browser.new_context(
                        viewport={'width': 1920, 'height': 1080},
                        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    )
                    page = await context.new_page()
                    
                    # Check all checkout URLs (with timeout per URL)
                    for checkout_url in urls_to_check:
                        try:
                            self.logger.debug(f"[CHECKOUT][{scan_id}] Checking direct URL: {checkout_url}")
                            # Use shorter timeout to avoid hanging on login pages
                            await page.goto(checkout_url, wait_until='domcontentloaded', timeout=8000)
                            
                            # Check if redirected to login/signin
                            current_url = page.url.lower()
                            if 'signin' in current_url or 'login' in current_url or 'sign-in' in current_url:
                                self.logger.debug(f"[CHECKOUT][{scan_id}] Checkout requires login: {checkout_url}")
                                continue  # Skip this URL if it requires login
                            
                            page_ready = await self._wait_for_page_ready(page)
                            if not page_ready:
                                self.logger.debug(f"[CHECKOUT][{scan_id}] Page not ready or requires login: {checkout_url}")
                                continue
                            
                            # Get page content
                            page_text = await page.evaluate('() => document.body.innerText')
                            current_url = page.url
                            
                            # Validate if this is a checkout page
                            validation_result = await self._validate_checkout_page_async(
                                current_url, page_text, page, base_url
                            )
                            
                            if validation_result['is_checkout']:
                                # Boost confidence if form fields are present
                                final_confidence = validation_result['confidence']
                                if validation_result['form_fields_present']:
                                    final_confidence = min(final_confidence + 0.15, 1.0)
                                
                                self.logger.info(
                                    f"[CHECKOUT][{scan_id}] Found checkout via direct URL: {checkout_url} "
                                    f"(confidence: {final_confidence:.2f}, form_fields={validation_result['form_fields_present']})"
                                )
                                await browser.close()
                                return {
                                    'checkout_reachable': True,
                                    'checkout_url': current_url,
                                    'checkout_confidence': final_confidence,
                                    'form_fields_present': validation_result['form_fields_present']
                                }
                            
                        except PlaywrightTimeoutError:
                            self.logger.debug(f"[CHECKOUT][{scan_id}] Timeout checking {checkout_url}")
                            continue
                        except Exception as e:
                            self.logger.debug(f"[CHECKOUT][{scan_id}] Error checking {checkout_url}: {e}")
                            continue
                    
                    await browser.close()
                    return None
                    
            except Exception as e:
                self.logger.warning(f"[CHECKOUT][{scan_id}] Could not create browser for direct URL check: {e}")
                return None
        else:
            # Use provided page to check URLs
            for checkout_url in urls_to_check:
                try:
                    self.logger.debug(f"[CHECKOUT][{scan_id}] Checking direct URL: {checkout_url}")
                    # Use shorter timeout to avoid hanging on login pages
                    await page.goto(checkout_url, wait_until='domcontentloaded', timeout=8000)
                    
                    # Check if redirected to login/signin
                    current_url = page.url.lower()
                    if 'signin' in current_url or 'login' in current_url or 'sign-in' in current_url:
                        self.logger.debug(f"[CHECKOUT][{scan_id}] Checkout requires login: {checkout_url}")
                        continue  # Skip this URL if it requires login
                    
                    page_ready = await self._wait_for_page_ready(page)
                    if not page_ready:
                        self.logger.debug(f"[CHECKOUT][{scan_id}] Page not ready or requires login: {checkout_url}")
                        continue
                    
                    # Get page content
                    page_text = await page.evaluate('() => document.body.innerText')
                    current_url = page.url
                    
                    # Validate if this is a checkout page
                    validation_result = await self._validate_checkout_page_async(
                        current_url, page_text, page, base_url
                    )
                    
                    if validation_result['is_checkout']:
                        # Boost confidence if form fields are present
                        final_confidence = validation_result['confidence']
                        if validation_result['form_fields_present']:
                            final_confidence = min(final_confidence + 0.15, 1.0)
                        
                        self.logger.info(
                            f"[CHECKOUT][{scan_id}] Found checkout via direct URL: {checkout_url} "
                            f"(confidence: {final_confidence:.2f}, form_fields={validation_result['form_fields_present']})"
                        )
                        return {
                            'checkout_reachable': True,
                            'checkout_url': current_url,
                            'checkout_confidence': final_confidence,
                            'form_fields_present': validation_result['form_fields_present']
                        }
                    
                except PlaywrightTimeoutError:
                    self.logger.debug(f"[CHECKOUT][{scan_id}] Timeout checking {checkout_url}")
                    continue
                except Exception as e:
                    self.logger.debug(f"[CHECKOUT][{scan_id}] Error checking {checkout_url}: {e}")
                    continue
            
            return None
    
    async def _validate_checkout_page_async(
        self,
        url: str,
        page_text: str,
        page,
        base_url: str
    ) -> Dict[str, Any]:
        """
        Async version of checkout page validation that can check form fields.
        """
        # Get base validation
        result = self._validate_checkout_page(url, page_text, page, base_url)
        
        # Check form fields asynchronously
        if result['is_checkout']:
            form_fields_present = await self._check_form_fields(page)
            result['form_fields_present'] = form_fields_present
            
            # Boost confidence if form fields are present
            if form_fields_present:
                result['confidence'] = min(result['confidence'] + 0.1, 1.0)
        
        return result
