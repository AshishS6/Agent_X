"""
Metadata Extractor Module
Handles extraction of business information from websites
"""

import re
from typing import Dict, Optional
from bs4 import BeautifulSoup


class MetadataExtractor:
    """Extracts business metadata from HTML"""
    
    @staticmethod
    def extract_business_name(soup: BeautifulSoup, provided_name: str = "") -> str:
        """
        Extract business name from page
        
        Args:
            soup: BeautifulSoup object
            provided_name: Pre-provided business name (optional)
            
        Returns:
            Extracted or provided business name
        """
        if provided_name:
            return provided_name
        
        business_name = ""
        
        # Try to extract from footer copyright
        footer = soup.find('footer')
        if footer:
            copyright = footer.find(string=re.compile(r'©|\(c\)|copyright', re.I))
            if copyright:
                match = re.search(r'(?:©|\(c\)|copyright)\s*(?:\d{4})?\s*([A-Z][\w\s&,.-]+)', copyright, re.I)
                if match:
                    business_name = match.group(1).strip()
        
        # Fallback: Check title
        if not business_name and soup.title:
            title_parts = soup.title.string.split('-')
            if title_parts:
                business_name = title_parts[0].strip()
        
        # Fallback: Check for meta og:site_name
        if not business_name:
            og_site_name = soup.find("meta", property="og:site_name")
            if og_site_name:
                business_name = og_site_name.get("content", "").strip()
        
        return business_name
    
    @staticmethod
    def extract_contact_info(soup: BeautifulSoup, page_text: str) -> Dict[str, Optional[str]]:
        """
        Extract contact information from page
        
        Args:
            soup: BeautifulSoup object
            page_text: Full page text
            
        Returns:
            Dict with contact information
        """
        contact_info = {
            'email': None,
            'phone': None,
            'address': None
        }
        
        # Extract email (simple pattern)
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', page_text)
        if email_match:
            contact_info['email'] = email_match.group(0)
        
        # Extract phone (simple pattern for Indian/US numbers)
        phone_match = re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', page_text)
        if phone_match:
            contact_info['phone'] = phone_match.group(0)
        
        return contact_info
    
    @staticmethod
    def extract_social_links(soup: BeautifulSoup) -> Dict[str, Optional[str]]:
        """
        Extract social media links
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Dict with social media URLs
        """
        social_links = {
            'facebook': None,
            'twitter': None,
            'linkedin': None,
            'instagram': None
        }
        
        for a in soup.find_all('a', href=True):
            href = a['href'].lower()
            
            if 'facebook.com' in href and not social_links['facebook']:
                social_links['facebook'] = a['href']
            elif 'twitter.com' in href and not social_links['twitter']:
                social_links['twitter'] = a['href']
            elif 'linkedin.com' in href and not social_links['linkedin']:
                social_links['linkedin'] = a['href']
            elif 'instagram.com' in href and not social_links['instagram']:
                social_links['instagram'] = a['href']
        
        return social_links
