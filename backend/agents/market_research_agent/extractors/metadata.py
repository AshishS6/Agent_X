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
            # Get full footer text for more flexible pattern matching
            footer_text = footer.get_text(separator=' ', strip=True)
            
            # V2.2.1: Enhanced patterns to handle various copyright formats
            # Handles: "© 2025 | Company Name", "© 2025 Company Name", "Copyright 2025 - Company Name"
            copyright_patterns = [
                # Pattern with year and optional separator (| , - or nothing)
                r'(?:©|\(c\)|copyright)\s*\d{4}\s*(?:[-|–]?\s*)?([A-Z][A-Za-z0-9\s&,.\'-]+?)(?:\s*\.\s*All|\s*All\s*Rights|$)',
                # Pattern without year
                r'(?:©|\(c\)|copyright)\s+([A-Z][A-Za-z0-9\s&,.\'-]+?)(?:\s*\.\s*All|\s*All\s*Rights|$)',
                # Descriptive pattern: "Company Name is a ..." 
                r'^([A-Z][A-Za-z0-9\s&.\'-]+(?:Private\s+Limited|Pvt\.?\s*Ltd\.?|Ltd\.?|Inc\.?|LLC))\s+is\s+',
            ]
            
            for pattern in copyright_patterns:
                match = re.search(pattern, footer_text, re.IGNORECASE | re.MULTILINE)
                if match:
                    business_name = match.group(1).strip()
                    # Clean up trailing punctuation
                    business_name = re.sub(r'\s*[.|,]\s*$', '', business_name)
                    if len(business_name) >= 3:
                        break
        
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
