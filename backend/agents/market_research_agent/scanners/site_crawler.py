"""
Site Crawler Module
Handles URL crawling and page fetching
"""

import requests
from typing import Dict, Any, Optional
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup


class SiteCrawler:
    """Handles website crawling operations"""
    
    def __init__(self, timeout: int = 10, user_agent: str = 'Agent_X_ComplianceScanner/1.0'):
        self.timeout = timeout
        self.headers = {'User-Agent': user_agent}
    
    def fetch_page(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a page and return response data
        
        Args:
            url: URL to fetch
            
        Returns:
            Dict with response data or None on failure
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout, allow_redirects=True)
            
            return {
                'url': url,
                'final_url': response.url,
                'status_code': response.status_code,
                'content': response.content,
                'text': response.text,
                'headers': dict(response.headers),
                'redirect_count': len(response.history),
                'success': response.status_code == 200
            }
        except Exception as e:
            return {
                'url': url,
                'error': str(e),
                'success': False
            }
    
    def parse_html(self, html_content: str) -> BeautifulSoup:
        """
        Parse HTML content into BeautifulSoup object
        
        Args:
            html_content: HTML string to parse
            
        Returns:
            BeautifulSoup object
        """
        return BeautifulSoup(html_content, 'html.parser')
