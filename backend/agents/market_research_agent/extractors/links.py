"""
Link Extractor Module
Handles extraction of links from HTML pages
"""

from typing import List, Dict
from urllib.parse import urljoin
from bs4 import BeautifulSoup


class LinkExtractor:
    """Extracts and processes links from HTML"""
    
    @staticmethod
    def extract_all_links(soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """
        Extract all links from a page
        
        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative links
            
        Returns:
            List of dicts with 'url' and 'text' keys
        """
        all_links = []
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            full_url = urljoin(base_url, href)
            link_text = a.get_text(strip=True).lower()
            
            all_links.append({
                'url': full_url,
                'text': link_text
            })
        
        return all_links
