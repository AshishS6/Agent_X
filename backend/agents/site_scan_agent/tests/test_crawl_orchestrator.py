"""
Unit Tests for Crawl Orchestrator Components
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio

# Import components to test
from crawlers.url_utils import URLNormalizer, PageClassifier
from crawlers.page_graph import PageData, CrawlError, NormalizedPageGraph, CrawlMetadata


class TestURLNormalizer:
    """Tests for URL normalization"""
    
    def test_normalize_removes_fragments(self):
        """URL fragments should be removed"""
        url = "https://example.com/page#section"
        normalized = URLNormalizer.normalize(url)
        assert "#section" not in normalized
        assert normalized == "https://example.com/page"
    
    def test_normalize_removes_trailing_slash(self):
        """Trailing slashes should be removed (except for root)"""
        url = "https://example.com/about/"
        normalized = URLNormalizer.normalize(url)
        assert normalized == "https://example.com/about"
    
    def test_normalize_preserves_root_slash(self):
        """Root path should keep its slash"""
        url = "https://example.com/"
        normalized = URLNormalizer.normalize(url)
        assert normalized == "https://example.com/"
    
    def test_normalize_lowercases_domain(self):
        """Domain should be lowercased"""
        url = "https://EXAMPLE.COM/About"
        normalized = URLNormalizer.normalize(url)
        assert "example.com" in normalized
    
    def test_is_internal_same_domain(self):
        """Same domain should be internal"""
        assert URLNormalizer.is_internal(
            "https://example.com/about",
            "example.com"
        ) is True
    
    def test_is_internal_www_prefix(self):
        """www prefix should be handled"""
        assert URLNormalizer.is_internal(
            "https://www.example.com/about",
            "example.com"
        ) is True
    
    def test_is_internal_different_domain(self):
        """Different domain should not be internal"""
        assert URLNormalizer.is_internal(
            "https://other.com/about",
            "example.com"
        ) is False
    
    def test_is_internal_subdomain(self):
        """Subdomains should be internal"""
        assert URLNormalizer.is_internal(
            "https://blog.example.com/post",
            "example.com"
        ) is True


class TestPageClassifier:
    """Tests for page classification"""
    
    def test_classify_privacy_policy_url(self):
        """Privacy policy URL should classify correctly"""
        result = PageClassifier.classify("https://example.com/privacy-policy")
        assert result["type"] == "privacy_policy"
        assert result["confidence"] >= 0.9
    
    def test_classify_privacy_short_url(self):
        """Short privacy URL should classify correctly"""
        result = PageClassifier.classify("https://example.com/privacy")
        assert result["type"] == "privacy_policy"
        assert result["confidence"] >= 0.8
    
    def test_classify_terms_url(self):
        """Terms URL should classify correctly"""
        result = PageClassifier.classify("https://example.com/terms-of-service")
        assert result["type"] == "terms_conditions"
        assert result["confidence"] >= 0.9
    
    def test_classify_terms_and_conditions(self):
        """Terms and conditions URL should classify correctly"""
        result = PageClassifier.classify("https://example.com/terms-and-conditions")
        assert result["type"] == "terms_conditions"
        assert result["confidence"] >= 0.9
    
    def test_classify_about_url(self):
        """About URL should classify correctly"""
        result = PageClassifier.classify("https://example.com/about-us")
        assert result["type"] == "about"
        assert result["confidence"] >= 0.9
    
    def test_classify_pricing_url(self):
        """Pricing URL should classify correctly"""
        result = PageClassifier.classify("https://example.com/pricing")
        assert result["type"] == "pricing"
        assert result["confidence"] >= 0.9
    
    def test_classify_returns_confidence(self):
        """Classification should always return confidence score"""
        result = PageClassifier.classify("https://example.com/some-random-page")
        assert "type" in result
        assert "confidence" in result
        assert 0.0 <= result["confidence"] <= 1.0
    
    def test_classify_anchor_text_boost(self):
        """Anchor text should boost confidence"""
        result_url_only = PageClassifier.classify("https://example.com/legal")
        result_with_anchor = PageClassifier.classify(
            "https://example.com/legal",
            anchor_text="Privacy Policy"
        )
        # Anchor text should boost confidence for privacy_policy
        assert result_with_anchor["type"] == "privacy_policy"
    
    def test_classify_skip_pdf(self):
        """PDF files should be skipped"""
        result = PageClassifier.classify("https://example.com/document.pdf")
        assert result["type"] == "skip"
    
    def test_classify_skip_javascript(self):
        """JavaScript links should be skipped"""
        result = PageClassifier.classify("javascript:void(0)")
        assert result["type"] == "skip"
    
    def test_get_priority_score(self):
        """Priority scores should be sensible"""
        assert PageClassifier.get_priority_score("home") > PageClassifier.get_priority_score("blog")
        assert PageClassifier.get_priority_score("privacy_policy") > PageClassifier.get_priority_score("docs")


class TestCrawlError:
    """Tests for crawl error classification"""
    
    def test_timeout_classification(self):
        """Timeout errors should be classified correctly"""
        error = CrawlError.from_exception(Exception("Request timeout exceeded"))
        assert error.type == "timeout"
    
    def test_ssl_classification(self):
        """SSL errors should be classified correctly"""
        error = CrawlError.from_exception(Exception("SSL certificate verify failed"))
        assert error.type == "ssl"
    
    def test_dns_classification(self):
        """DNS errors should be classified correctly"""
        error = CrawlError.from_exception(Exception("nodename nor servname provided"))
        assert error.type == "dns"
    
    def test_blocked_classification(self):
        """403 errors should be classified as blocked"""
        error = CrawlError.from_exception(Exception("Forbidden"), status_code=403)
        assert error.type == "blocked"
    
    def test_http_error_classification(self):
        """Other HTTP errors should be classified correctly"""
        error = CrawlError.from_exception(Exception("Not Found"), status_code=404)
        assert error.type == "http_error"


class TestPageData:
    """Tests for page data"""
    
    def test_content_hash_computed(self):
        """Content hash should be computed on creation"""
        page = PageData(
            url="https://example.com",
            final_url="https://example.com",
            status=200,
            content_type="text/html",
            html="<html><body>Hello World</body></html>",
            source="root",
            page_type="home",
            classification_confidence=1.0
        )
        assert page.content_hash is not None
        assert len(page.content_hash) == 64  # SHA-256 hex length
    
    def test_content_hash_deterministic(self):
        """Same content should produce same hash"""
        html = "<html><body>Test</body></html>"
        page1 = PageData(
            url="https://example.com",
            final_url="https://example.com",
            status=200,
            content_type="text/html",
            html=html,
            source="root",
            page_type="home",
            classification_confidence=1.0
        )
        page2 = PageData(
            url="https://example.com/other",
            final_url="https://example.com/other",
            status=200,
            content_type="text/html",
            html=html,
            source="sitemap",
            page_type="about",
            classification_confidence=0.9
        )
        assert page1.content_hash == page2.content_hash
    
    def test_get_soup(self):
        """get_soup should return BeautifulSoup object"""
        page = PageData(
            url="https://example.com",
            final_url="https://example.com",
            status=200,
            content_type="text/html",
            html="<html><body><h1>Title</h1></body></html>",
            source="root",
            page_type="home",
            classification_confidence=1.0
        )
        soup = page.get_soup()
        assert soup is not None
        assert soup.find("h1").text == "Title"


class TestNormalizedPageGraph:
    """Tests for normalized page graph"""
    
    def test_add_page(self):
        """Pages can be added to graph"""
        graph = NormalizedPageGraph("https://example.com")
        page = PageData(
            url="https://example.com",
            final_url="https://example.com",
            status=200,
            content_type="text/html",
            html="<html></html>",
            source="root",
            page_type="home",
            classification_confidence=1.0
        )
        result = graph.add_page(page)
        assert result is True
        assert graph.get_page_by_type("home") is page
    
    def test_duplicate_canonical_rejected(self):
        """Pages with same canonical URL should be rejected"""
        graph = NormalizedPageGraph("https://example.com")
        page1 = PageData(
            url="https://example.com/about",
            final_url="https://example.com/about",
            canonical_url="https://example.com/about-us",
            status=200,
            content_type="text/html",
            html="<html></html>",
            source="root",
            page_type="about",
            classification_confidence=0.9
        )
        page2 = PageData(
            url="https://example.com/about-us",
            final_url="https://example.com/about-us",
            canonical_url="https://example.com/about-us",
            status=200,
            content_type="text/html",
            html="<html></html>",
            source="sitemap",
            page_type="about",
            classification_confidence=0.95
        )
        graph.add_page(page1)
        result = graph.add_page(page2)
        assert result is False  # Duplicate canonical
    
    def test_has_required_pages(self):
        """has_required_pages should check privacy and terms"""
        graph = NormalizedPageGraph("https://example.com")
        assert graph.has_required_pages() is False
        
        # Add privacy policy
        graph.add_page(PageData(
            url="https://example.com/privacy",
            final_url="https://example.com/privacy",
            status=200,
            content_type="text/html",
            html="<html></html>",
            source="sitemap",
            page_type="privacy_policy",
            classification_confidence=0.9
        ))
        assert graph.has_required_pages() is False  # Still missing terms
        
        # Add terms
        graph.add_page(PageData(
            url="https://example.com/terms",
            final_url="https://example.com/terms",
            status=200,
            content_type="text/html",
            html="<html></html>",
            source="sitemap",
            page_type="terms_conditions",
            classification_confidence=0.9
        ))
        assert graph.has_required_pages() is True
    
    def test_get_all_links(self):
        """get_all_links should extract links from home page"""
        graph = NormalizedPageGraph("https://example.com")
        graph.add_page(PageData(
            url="https://example.com",
            final_url="https://example.com",
            status=200,
            content_type="text/html",
            html='<html><body><a href="/about">About</a><a href="/contact">Contact</a></body></html>',
            source="root",
            page_type="home",
            classification_confidence=1.0
        ))
        links = graph.get_all_links()
        assert len(links) == 2
        assert any("about" in link["url"] for link in links)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
