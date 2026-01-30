"""
Fetchers Module
Provides pluggable page fetching backends:
- HttpFetcher: fast path using aiohttp (current behavior)
- JsFetcher: optional Playwright-based renderer for SPAs / JS-heavy sites

Per plan: enable coverage-first crawling with render gating + budgets, while preserving
determinism and provenance metadata (detection_method, render_type, timings).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import aiohttp


@dataclass
class FetchOutput:
    url: str
    final_url: str
    status: int
    content_type: str
    html: str
    headers: Dict[str, str] = field(default_factory=dict)
    fetch_type: str = "http"  # "http" | "js"
    fetch_metadata: Dict[str, Any] = field(default_factory=dict)


class HttpFetcher:
    """HTTP fetcher using aiohttp session (no JS execution)."""

    def __init__(self, user_agent: str, logger=None):
        self.user_agent = user_agent
        self.logger = logger

    async def fetch(self, session: aiohttp.ClientSession, url: str) -> FetchOutput:
        start = time.monotonic()
        async with session.get(url, allow_redirects=True) as response:
            content_type = response.headers.get("Content-Type", "") or ""
            status = response.status
            final_url = str(response.url)

            html = ""
            if "text/html" in content_type.lower():
                html = await response.text()
            else:
                # Drain body to avoid connection leaks
                try:
                    await response.read()
                except Exception:
                    pass

            duration_ms = int((time.monotonic() - start) * 1000)
            return FetchOutput(
                url=url,
                final_url=final_url,
                status=status,
                content_type=content_type,
                html=html,
                headers={k: v for k, v in response.headers.items()},
                fetch_type="http",
                fetch_metadata={
                    "duration_ms": duration_ms,
                    "redirected": final_url != url,
                },
            )


class JsFetcher:
    """
    Playwright-based renderer for SPA / JS-heavy pages.

    Notes:
    - Import is optional; if Playwright isn't installed, we raise ImportError.
    - Designed to be used under a small concurrency limit (separate semaphore).
    """

    def __init__(
        self,
        user_agent: str,
        logger=None,
        navigation_timeout_ms: int = 15000,
        wait_until: str = "networkidle",
        viewport: Optional[Dict[str, int]] = None,
    ):
        self.user_agent = user_agent
        self.logger = logger
        self.navigation_timeout_ms = navigation_timeout_ms
        self.wait_until = wait_until
        self.viewport = viewport or {"width": 1365, "height": 768}

    async def fetch(self, url: str) -> FetchOutput:
        start = time.monotonic()

        try:
            from playwright.async_api import async_playwright  # type: ignore
        except Exception as e:  # pragma: no cover
            raise ImportError(
                "Playwright is required for JS rendering. Install with `pip install playwright` "
                "and run `playwright install`."
            ) from e

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=self.user_agent,
                viewport=self.viewport,
                java_script_enabled=True,
            )
            page = await context.new_page()

            status = 0
            content_type = "text/html; charset=utf-8"
            final_url = url
            try:
                resp = await page.goto(
                    url,
                    wait_until=self.wait_until,
                    timeout=self.navigation_timeout_ms,
                )
                if resp:
                    status = resp.status
                    final_url = page.url
                    try:
                        headers = await resp.all_headers()
                    except Exception:
                        headers = {}
                    content_type = headers.get("content-type", content_type) if isinstance(headers, dict) else content_type
                else:
                    headers = {}

                # Stabilize: stop animations/timers (best effort)
                try:
                    await page.add_style_tag(content="*{animation:none!important;transition:none!important}")
                except Exception:
                    pass

                html = await page.content()
            finally:
                try:
                    await context.close()
                except Exception:
                    pass
                try:
                    await browser.close()
                except Exception:
                    pass

        duration_ms = int((time.monotonic() - start) * 1000)
        return FetchOutput(
            url=url,
            final_url=final_url,
            status=status,
            content_type=content_type,
            html=html,
            headers=headers if isinstance(headers, dict) else {},
            fetch_type="js",
            fetch_metadata={
                "duration_ms": duration_ms,
                "wait_until": self.wait_until,
                "navigation_timeout_ms": self.navigation_timeout_ms,
            },
        )

