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
            
            # Skip invalid link types that can't be fetched
            if href.startswith('#') or href.startswith('javascript:') or \
               href.startswith('mailto:') or href.startswith('tel:') or \
               href.startswith('data:') or not href.strip():
                continue
            
            full_url = urljoin(base_url, href)
            
            # Skip if urljoin produced an invalid URL (e.g., javascript:void(0) stays as-is)
            if not full_url.startswith(('http://', 'https://')):
                continue
            
            link_text = a.get_text(strip=True).lower()
            
            all_links.append({
                'url': full_url,
                'text': link_text
            })
        
        return all_links
