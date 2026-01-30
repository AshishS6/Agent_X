"""
Robots.txt Parser Module
Fetch and parse robots.txt rules
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from urllib.parse import urlparse, urljoin

import aiohttp


@dataclass
class RobotsRules:
    """Container for parsed robots.txt rules"""
    disallow_patterns: Dict[str, List[str]] = field(default_factory=dict)  # user-agent -> patterns
    allow_patterns: Dict[str, List[str]] = field(default_factory=dict)
    sitemaps: List[str] = field(default_factory=list)
    crawl_delay: Optional[float] = None
    raw_content: str = ""
    found: bool = False
    
    def is_allowed(self, path: str, user_agent: str = '*') -> bool:
        """
        Check if a path is allowed for crawling.
        
        Args:
            path: URL path to check (e.g., /privacy)
            user_agent: User agent to check rules for
            
        Returns:
            True if allowed, False if disallowed
        """
        # Normalize path
        path = path.lower()
        if not path.startswith('/'):
            path = '/' + path
        
        # Get rules for user agent (fallback to *)
        disallows = self.disallow_patterns.get(user_agent.lower(), [])
        if not disallows:
            disallows = self.disallow_patterns.get('*', [])
        
        allows = self.allow_patterns.get(user_agent.lower(), [])
        if not allows:
            allows = self.allow_patterns.get('*', [])
        
        # Check if path matches any allow pattern (allows take precedence)
        for pattern in allows:
            if self._matches_pattern(path, pattern):
                return True
        
        # Check if path matches any disallow pattern
        for pattern in disallows:
            if self._matches_pattern(path, pattern):
                return False
        
        # Default: allowed
        return True
    
    def _matches_pattern(self, path: str, pattern: str) -> bool:
        """Check if path matches robots.txt pattern"""
        if not pattern:
            return False
        
        pattern = pattern.lower()
        
        # Handle wildcard patterns
        if '*' in pattern:
            import re
            # Convert robots.txt pattern to regex
            regex = pattern.replace('*', '.*')
            if pattern.endswith('$'):
                regex = regex[:-1] + '$'
            else:
                regex = regex + '.*'
            try:
                return bool(re.match(regex, path))
            except Exception:
                return False
        
        # Simple prefix match
        return path.startswith(pattern)


class RobotsTxtParser:
    """Parse robots.txt files"""
    
    USER_AGENT = 'Agent_X_CrawlOrchestrator/1.0'
    TIMEOUT = 3  # seconds
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    async def fetch_and_parse(
        self,
        base_url: str,
        session: Optional[aiohttp.ClientSession] = None
    ) -> RobotsRules:
        """
        Fetch and parse robots.txt from a website.
        
        Args:
            base_url: Base URL of the website
            session: Optional aiohttp session to reuse
            
        Returns:
            RobotsRules object with parsed rules
        """
        parsed = urlparse(base_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        
        rules = RobotsRules()
        
        try:
            close_session = False
            if session is None:
                session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=self.TIMEOUT),
                    headers={'User-Agent': self.USER_AGENT}
                )
                close_session = True
            
            try:
                async with session.get(robots_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        rules = self._parse_content(content)
                        rules.found = True
                        self.logger.info(f"[CRAWL] Robots.txt found at {robots_url}")
                    else:
                        self.logger.info(f"[CRAWL] No robots.txt (status {response.status})")
            finally:
                if close_session:
                    await session.close()
                    
        except asyncio.TimeoutError:
            self.logger.warning(f"[CRAWL] Robots.txt timeout: {robots_url}")
        except Exception as e:
            self.logger.warning(f"[CRAWL] Robots.txt error: {e}")
        
        return rules
    
    def _parse_content(self, content: str) -> RobotsRules:
        """Parse robots.txt content"""
        rules = RobotsRules(raw_content=content)
        
        current_agents: List[str] = []
        
        for line in content.split('\n'):
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Parse directive
            if ':' in line:
                directive, value = line.split(':', 1)
                directive = directive.strip().lower()
                value = value.strip()
                
                if directive == 'user-agent':
                    current_agents = [value.lower()]
                elif directive == 'disallow' and current_agents:
                    for agent in current_agents:
                        if agent not in rules.disallow_patterns:
                            rules.disallow_patterns[agent] = []
                        if value:  # Empty disallow means allow all
                            rules.disallow_patterns[agent].append(value)
                elif directive == 'allow' and current_agents:
                    for agent in current_agents:
                        if agent not in rules.allow_patterns:
                            rules.allow_patterns[agent] = []
                        if value:
                            rules.allow_patterns[agent].append(value)
                elif directive == 'sitemap':
                    rules.sitemaps.append(value)
                elif directive == 'crawl-delay' and current_agents:
                    try:
                        rules.crawl_delay = float(value)
                    except ValueError:
                        pass
        
        return rules
