"""
Tech Stack Detector Module
Detects CMS, analytics, payment gateways, frameworks, and hosting
"""

import re
from typing import Dict, List, Optional
from bs4 import BeautifulSoup


class TechDetector:
    """Detects technology stack from website"""
    
    # CMS signatures
    CMS_SIGNATURES = {
        "WordPress": {
            "meta": [("name", "generator", r"WordPress")],
            "scripts": [r"wp-content", r"wp-includes"],
            "html": [r"wp-json"]
        },
        "Shopify": {
            "meta": [("name", "shopify", None)],
            "scripts": [r"cdn\.shopify\.com"],
            "html": [r"Shopify\."]
        },
        "Wix": {
            "meta": [("name", "generator", r"Wix")],
            "scripts": [r"static\.wixstatic\.com"],
            "html": []
        },
        "Squarespace": {
            "meta": [("name", "generator", r"Squarespace")],
            "scripts": [r"squarespace"],
            "html": []
        },
        "Webflow": {
            "meta": [("name", "generator", r"Webflow")],
            "scripts": [r"webflow"],
            "html": []
        },
        "Drupal": {
            "meta": [("name", "generator", r"Drupal")],
            "scripts": [r"/sites/default", r"drupal"],
            "html": []
        },
        "Joomla": {
            "meta": [("name", "generator", r"Joomla")],
            "scripts": [r"joomla"],
            "html": []
        }
    }
    
    # Analytics signatures
    ANALYTICS_SIGNATURES = {
        "Google Analytics": [r"google-analytics\.com/analytics\.js", r"googletagmanager\.com/gtag"],
        "Google Tag Manager": [r"googletagmanager\.com/gtm\.js"],
        "Facebook Pixel": [r"connect\.facebook\.net/.*fbevents\.js"],
        "Hotjar": [r"static\.hotjar\.com"],
        "Mixpanel": [r"cdn\.mxpnl\.com"],
        "Segment": [r"cdn\.segment\.com"]
    }
    
    # Payment gateway signatures
    PAYMENT_SIGNATURES = {
        "Razorpay": [r"checkout\.razorpay\.com", r"razorpay"],
        "Stripe": [r"js\.stripe\.com", r"stripe"],
        "PayPal": [r"paypal\.com/sdk", r"paypal"],
        "Paytm": [r"paytm", r"securegw\.paytm"],
        "PhonePe": [r"phonepe"],
        "PayU": [r"payu"]
    }
    
    # JS Framework signatures
    FRAMEWORK_SIGNATURES = {
        "React": [r"react", r"_react"],
        "Vue": [r"vue\.js", r"vue\.min\.js"],
        "Angular": [r"angular", r"ng-"],
        "Next.js": [r"_next/", r"__NEXT_DATA__"],
        "Nuxt": [r"_nuxt/"],
        "Svelte": [r"svelte"]
    }
    
    # Hosting/CDN signatures
    HOSTING_SIGNATURES = {
        "Cloudflare": [r"cloudflare"],
        "AWS": [r"amazonaws\.com", r"cloudfront"],
        "Vercel": [r"vercel"],
        "Netlify": [r"netlify"],
        "Google Cloud": [r"googleapis\.com"],
        "Azure": [r"azure"]
    }
    
    @staticmethod
    def detect_cms(soup: BeautifulSoup, html_text: str) -> Optional[str]:
        """
        Detect CMS platform
        
        Args:
            soup: BeautifulSoup object
            html_text: Raw HTML text
            
        Returns:
            CMS name or None
        """
        for cms_name, signatures in TechDetector.CMS_SIGNATURES.items():
            # Check meta tags
            for attr_name, attr_value, pattern in signatures["meta"]:
                meta = soup.find("meta", attrs={attr_name: attr_value})
                if meta:
                    content = meta.get("content", "")
                    if pattern and re.search(pattern, content, re.I):
                        return cms_name
                    elif not pattern:
                        return cms_name
            
            # Check scripts
            for script_pattern in signatures["scripts"]:
                scripts = soup.find_all("script", src=True)
                for script in scripts:
                    if re.search(script_pattern, script['src'], re.I):
                        return cms_name
            
            # Check HTML content
            for html_pattern in signatures["html"]:
                if re.search(html_pattern, html_text, re.I):
                    return cms_name
        
        return "Custom"
    
    @staticmethod
    def detect_analytics(soup: BeautifulSoup, html_text: str) -> List[str]:
        """
        Detect analytics tools
        
        Args:
            soup: BeautifulSoup object
            html_text: Raw HTML text
            
        Returns:
            List of detected analytics tools
        """
        detected = []
        
        scripts = soup.find_all("script", src=True)
        script_srcs = " ".join([s.get('src', '') for s in scripts])
        
        # Also check inline scripts
        inline_scripts = soup.find_all("script")
        inline_content = " ".join([s.string or '' for s in inline_scripts])
        
        all_script_content = script_srcs + " " + inline_content + " " + html_text
        
        for tool_name, patterns in TechDetector.ANALYTICS_SIGNATURES.items():
            for pattern in patterns:
                if re.search(pattern, all_script_content, re.I):
                    if tool_name not in detected:
                        detected.append(tool_name)
                    break
        
        return detected
    
    @staticmethod
    def detect_payments(soup: BeautifulSoup, html_text: str) -> List[str]:
        """
        Detect payment gateways
        
        Args:
            soup: BeautifulSoup object
            html_text: Raw HTML text
            
        Returns:
            List of detected payment gateways
        """
        detected = []
        
        scripts = soup.find_all("script", src=True)
        script_srcs = " ".join([s.get('src', '') for s in scripts])
        all_content = script_srcs + " " + html_text
        
        for gateway_name, patterns in TechDetector.PAYMENT_SIGNATURES.items():
            for pattern in patterns:
                if re.search(pattern, all_content, re.I):
                    if gateway_name not in detected:
                        detected.append(gateway_name)
                    break
        
        return detected
    
    @staticmethod
    def detect_frameworks(soup: BeautifulSoup, html_text: str) -> List[str]:
        """
        Detect JS frameworks
        
        Args:
            soup: BeautifulSoup object
            html_text: Raw HTML text
            
        Returns:
            List of detected frameworks
        """
        detected = []
        
        scripts = soup.find_all("script", src=True)
        script_srcs = " ".join([s.get('src', '') for s in scripts])
        all_content = script_srcs + " " + html_text
        
        for framework_name, patterns in TechDetector.FRAMEWORK_SIGNATURES.items():
            for pattern in patterns:
                if re.search(pattern, all_content, re.I):
                    if framework_name not in detected:
                        detected.append(framework_name)
                    break
        
        return detected
    
    @staticmethod
    def detect_hosting(soup: BeautifulSoup, html_text: str, headers: Dict[str, str]) -> Optional[str]:
        """
        Detect hosting/CDN provider
        
        Args:
            soup: BeautifulSoup object
            html_text: Raw HTML text
            headers: HTTP response headers
            
        Returns:
            Hosting provider name or None
        """
        # Check headers first
        server_header = headers.get('server', '').lower()
        cf_ray = headers.get('cf-ray', '')
        
        if cf_ray or 'cloudflare' in server_header:
            return "Cloudflare"
        
        # Check HTML content
        all_content = html_text.lower()
        
        for provider_name, patterns in TechDetector.HOSTING_SIGNATURES.items():
            for pattern in patterns:
                if re.search(pattern, all_content, re.I):
                    return provider_name
        
        return None
    
    @staticmethod
    def detect_all(soup: BeautifulSoup, html_text: str, headers: Dict[str, str] = None) -> Dict[str, any]:
        """
        Detect all tech stack components
        
        Args:
            soup: BeautifulSoup object
            html_text: Raw HTML text
            headers: HTTP response headers (optional)
            
        Returns:
            Dict with all detected technologies
        """
        if headers is None:
            headers = {}
        
        return {
            "cms": TechDetector.detect_cms(soup, html_text),
            "analytics": TechDetector.detect_analytics(soup, html_text),
            "payments": TechDetector.detect_payments(soup, html_text),
            "frameworks": TechDetector.detect_frameworks(soup, html_text),
            "hosting": TechDetector.detect_hosting(soup, html_text, headers)
        }
