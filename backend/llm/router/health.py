"""
Health Checker - Provider availability and health monitoring

This module checks the health of LLM providers:
- Ollama availability
- OpenAI API key validity
- Anthropic API key validity
- Provider reachability
"""

import os
import asyncio
import logging
from typing import Dict, Optional
from enum import Enum
import httpx

logger = logging.getLogger(__name__)


class ProviderStatus(str, Enum):
    """Provider health status"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthChecker:
    """
    Checks health of LLM providers
    
    Provides:
    - Ollama availability checks
    - API key validation (basic)
    - Provider status caching
    """
    
    def __init__(self):
        self._status_cache: Dict[str, ProviderStatus] = {}
        self._cache_ttl = 60  # Cache status for 60 seconds
        self._last_check: Dict[str, float] = {}
    
    async def check_ollama(self, base_url: Optional[str] = None) -> ProviderStatus:
        """
        Check if Ollama is available
        
        Args:
            base_url: Ollama base URL (defaults to env var or localhost)
            
        Returns:
            ProviderStatus
        """
        base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        cache_key = f"ollama:{base_url}"
        
        # Check cache
        if self._is_cache_valid(cache_key):
            return self._status_cache.get(cache_key, ProviderStatus.UNKNOWN)
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{base_url}/api/tags")
                if response.status_code == 200:
                    status = ProviderStatus.HEALTHY
                else:
                    status = ProviderStatus.UNHEALTHY
        except Exception as e:
            logger.debug(f"Ollama health check failed: {e}")
            status = ProviderStatus.UNHEALTHY
        
        # Update cache
        self._status_cache[cache_key] = status
        self._last_check[cache_key] = asyncio.get_event_loop().time()
        
        return status
    
    def check_openai_key(self) -> ProviderStatus:
        """
        Check if OpenAI API key is configured
        
        Note: This is a basic check (key presence), not validity
        """
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key or api_key == "your-openai-api-key":
            return ProviderStatus.UNHEALTHY
        return ProviderStatus.HEALTHY
    
    def check_anthropic_key(self) -> ProviderStatus:
        """
        Check if Anthropic API key is configured
        
        Note: This is a basic check (key presence), not validity
        """
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            return ProviderStatus.UNHEALTHY
        return ProviderStatus.HEALTHY
    
    def get_provider_status(self, provider: str, base_url: Optional[str] = None) -> ProviderStatus:
        """
        Get status for a provider (synchronous)
        
        Args:
            provider: Provider name (ollama, openai, anthropic)
            base_url: Optional base URL for Ollama
            
        Returns:
            ProviderStatus
        """
        provider_lower = provider.lower()
        
        if provider_lower == "ollama":
            # For Ollama, we need async check, so return cached or unknown
            cache_key = f"ollama:{base_url or os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')}"
            return self._status_cache.get(cache_key, ProviderStatus.UNKNOWN)
        elif provider_lower == "openai":
            return self.check_openai_key()
        elif provider_lower == "anthropic":
            return self.check_anthropic_key()
        else:
            return ProviderStatus.UNKNOWN
    
    async def get_provider_status_async(self, provider: str, base_url: Optional[str] = None) -> ProviderStatus:
        """
        Get status for a provider (async, can check Ollama)
        
        Args:
            provider: Provider name (ollama, openai, anthropic)
            base_url: Optional base URL for Ollama
            
        Returns:
            ProviderStatus
        """
        provider_lower = provider.lower()
        
        if provider_lower == "ollama":
            return await self.check_ollama(base_url)
        elif provider_lower == "openai":
            return self.check_openai_key()
        elif provider_lower == "anthropic":
            return self.check_anthropic_key()
        else:
            return ProviderStatus.UNKNOWN
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached status is still valid"""
        if cache_key not in self._status_cache:
            return False
        
        if cache_key not in self._last_check:
            return False
        
        elapsed = asyncio.get_event_loop().time() - self._last_check[cache_key]
        return elapsed < self._cache_ttl
    
    def clear_cache(self):
        """Clear status cache"""
        self._status_cache.clear()
        self._last_check.clear()


# Global health checker instance
_health_checker: Optional[HealthChecker] = None


def get_health_checker() -> HealthChecker:
    """Get the global health checker instance"""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker
