"""
SEO Analyzer Module
Handles lightweight SEO analysis
"""

import requests
from typing import Dict, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


class SEOAnalyzer:
    """Analyzes SEO fundamentals"""
    
    @staticmethod
    def analyze_seo(soup: BeautifulSoup, url: str) -> Dict[str, any]:
        """
        Perform lightweight SEO analysis
        
        Args:
            soup: BeautifulSoup object
            url: Page URL
            
        Returns:
            Dict with SEO analysis
        """
        seo_data = {
            "title": SEOAnalyzer._analyze_title(soup),
            "meta_description": SEOAnalyzer._analyze_meta_description(soup),
            "h1_count": SEOAnalyzer._count_h1(soup),
            "canonical": SEOAnalyzer._get_canonical(soup, url),
            "indexable": SEOAnalyzer._check_indexable(soup),
            "sitemap_found": SEOAnalyzer._check_sitemap(url),
            "robots_txt_found": SEOAnalyzer._check_robots_txt(url),
            "seo_score": 0  # Will be calculated
        }
        
        # Calculate SEO score
        score = 0
        
        # Title (20 points)
        if seo_data["title"]["present"]:
            score += 10
            if 30 <= seo_data["title"]["length"] <= 60:
                score += 10
        
        # Meta description (20 points)
        if seo_data["meta_description"]["present"]:
            score += 10
            if 120 <= seo_data["meta_description"]["length"] <= 160:
                score += 10
        
        # H1 count (15 points)
        if seo_data["h1_count"] == 1:
            score += 15
        elif seo_data["h1_count"] > 0:
            score += 5
        
        # Canonical (10 points)
        if seo_data["canonical"]:
            score += 10
        
        # Indexable (15 points)
        if seo_data["indexable"]:
            score += 15
        
        # Sitemap (10 points)
        if seo_data["sitemap_found"]:
            score += 10
        
        # Robots.txt (10 points)
        if seo_data["robots_txt_found"]:
            score += 10
        
        seo_data["seo_score"] = score
        
        return seo_data
    
    @staticmethod
    def _analyze_title(soup: BeautifulSoup) -> Dict[str, any]:
        """Analyze title tag"""
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            title_text = title_tag.string.strip()
            return {
                "present": True,
                "length": len(title_text),
                "text": title_text
            }
        return {
            "present": False,
            "length": 0,
            "text": ""
        }
    
    @staticmethod
    def _analyze_meta_description(soup: BeautifulSoup) -> Dict[str, any]:
        """Analyze meta description"""
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            desc_text = meta_desc["content"].strip()
            return {
                "present": True,
                "length": len(desc_text),
                "text": desc_text
            }
        return {
            "present": False,
            "length": 0,
            "text": ""
        }
    
    @staticmethod
    def _count_h1(soup: BeautifulSoup) -> int:
        """Count H1 tags"""
        return len(soup.find_all("h1"))
    
    @staticmethod
    def _get_canonical(soup: BeautifulSoup, url: str) -> Optional[str]:
        """Get canonical URL"""
        canonical = soup.find("link", attrs={"rel": "canonical"})
        if canonical and canonical.get("href"):
            return canonical["href"]
        return None
    
    @staticmethod
    def _check_indexable(soup: BeautifulSoup) -> bool:
        """Check if page is indexable"""
        robots_meta = soup.find("meta", attrs={"name": "robots"})
        if robots_meta:
            content = robots_meta.get("content", "").lower()
            if "noindex" in content:
                return False
        return True
    
    @staticmethod
    def _check_sitemap(url: str) -> bool:
        """Check if sitemap.xml exists"""
        parsed = urlparse(url)
        sitemap_url = f"{parsed.scheme}://{parsed.netloc}/sitemap.xml"
        
        try:
            response = requests.head(sitemap_url, timeout=5, allow_redirects=True)
            return response.status_code == 200
        except:
            return False
    
    @staticmethod
    def _check_robots_txt(url: str) -> bool:
        """Check if robots.txt exists"""
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        
        try:
            response = requests.head(robots_url, timeout=5, allow_redirects=True)
            return response.status_code == 200
        except:
            return False
