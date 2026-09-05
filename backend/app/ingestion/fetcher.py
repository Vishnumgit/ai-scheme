"""
Fetcher — rate-limited, retry-aware HTTP fetcher with content-hash caching.

Respects:
  - Per-source rate limits (requests per second + crawl delay)
  - robots.txt (for HTML sources)
  - Retry with exponential backoff (tenacity)
  - Content-hash to detect changes (only reprocess on change)
  - Configurable timeouts
"""
import asyncio
import hashlib
import logging
import time
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser

import aiohttp
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

logger = logging.getLogger(__name__)

# Per-domain last-fetch timestamps for rate limiting
_last_fetch: Dict[str, float] = {}


def _compute_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


async def _wait_for_rate_limit(domain: str, crawl_delay: float) -> None:
    """Enforce per-domain crawl delay."""
    now = time.monotonic()
    last = _last_fetch.get(domain, 0.0)
    wait = crawl_delay - (now - last)
    if wait > 0:
        await asyncio.sleep(wait)
    _last_fetch[domain] = time.monotonic()


class FetchResult:
    __slots__ = ("url", "status", "content", "content_type", "content_hash", "error")

    def __init__(
        self,
        url: str,
        status: int,
        content: Optional[bytes] = None,
        content_type: str = "",
        content_hash: str = "",
        error: Optional[str] = None,
    ):
        self.url = url
        self.status = status
        self.content = content
        self.content_type = content_type
        self.content_hash = content_hash
        self.error = error

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300 and self.error is None

    @property
    def text(self) -> Optional[str]:
        if self.content is None:
            return None
        try:
            return self.content.decode("utf-8", errors="replace")
        except Exception:
            return None


class RateLimitedFetcher:
    """
    Async HTTP fetcher with:
      - Per-source rate limiting
      - Content-hash caching (skip if unchanged)
      - Robots.txt checking (HTML sources)
      - Retry with exponential backoff
    """

    USER_AGENT = "SchemeDiscovery-Bot/1.0 (government scheme discovery; contact: admin@example.com)"
    TIMEOUT_S = 30
    _robots_cache: Dict[str, RobotFileParser] = {}

    def __init__(self, session: aiohttp.ClientSession):
        self._session = session

    @classmethod
    async def create(cls) -> "RateLimitedFetcher":
        session = aiohttp.ClientSession(
            headers={"User-Agent": cls.USER_AGENT},
            timeout=aiohttp.ClientTimeout(total=cls.TIMEOUT_S),
        )
        return cls(session)

    async def close(self) -> None:
        await self._session.close()

    def _get_domain(self, url: str) -> str:
        return urlparse(url).netloc

    async def _check_robots(self, url: str) -> bool:
        """Return True if fetching this URL is allowed by robots.txt."""
        parsed = urlparse(url)
        domain = parsed.netloc
        robots_url = f"{parsed.scheme}://{domain}/robots.txt"

        if domain not in self._robots_cache:
            rp = RobotFileParser()
            rp.set_url(robots_url)
            try:
                async with self._session.get(robots_url, allow_redirects=True) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        rp.parse(text.splitlines())
                    else:
                        # No robots.txt — assume allowed
                        rp.parse([])
            except Exception:
                rp.parse([])
            self._robots_cache[domain] = rp

        return self._robots_cache[domain].can_fetch(self.USER_AGENT, url)

    async def fetch(
        self,
        url: str,
        source_config: Dict[str, Any],
        known_hash: Optional[str] = None,
        check_robots: bool = True,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> FetchResult:
        """
        Fetch a URL respecting rate limits and robots.txt.

        Args:
            url: URL to fetch
            source_config: Source registry entry (for rate limits, auth)
            known_hash: If provided and response hash matches, returns None content (no change)
            check_robots: Whether to check robots.txt (False for APIs)
            headers: Extra HTTP headers (auth tokens etc.)
            params: Query parameters

        Returns:
            FetchResult with status, content, and hash
        """
        domain = self._get_domain(url)
        crawl_delay = source_config.get("crawl_delay_s", 1.0)

        # robots.txt check for HTML sources
        if check_robots and source_config.get("type") == "html":
            allowed = await self._check_robots(url)
            if not allowed:
                logger.warning("robots.txt disallows fetch: %s", url)
                return FetchResult(url=url, status=403, error="Disallowed by robots.txt")

        # Auth header injection
        request_headers = dict(headers or {})
        auth_env_key = source_config.get("auth_env_key")
        if auth_env_key:
            import os
            api_key = os.environ.get(auth_env_key)
            if api_key:
                request_headers["Authorization"] = f"Bearer {api_key}"

        # Rate limiting
        await _wait_for_rate_limit(domain, crawl_delay)

        return await self._fetch_with_retry(url, request_headers, params, known_hash)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    async def _fetch_with_retry(
        self,
        url: str,
        headers: Dict[str, str],
        params: Optional[Dict[str, Any]],
        known_hash: Optional[str],
    ) -> FetchResult:
        try:
            async with self._session.get(url, headers=headers, params=params, allow_redirects=True) as resp:
                if resp.status >= 400:
                    return FetchResult(url=url, status=resp.status, error=f"HTTP {resp.status}")

                content = await resp.read()
                content_type = resp.content_type or ""
                content_hash = _compute_hash(content)

                # Skip processing if content hasn't changed
                if known_hash and known_hash == content_hash:
                    logger.debug("No change detected for %s (hash match)", url)
                    return FetchResult(url=url, status=resp.status, content=None, content_hash=content_hash)

                return FetchResult(
                    url=url,
                    status=resp.status,
                    content=content,
                    content_type=content_type,
                    content_hash=content_hash,
                )
        except asyncio.TimeoutError:
            logger.error("Timeout fetching %s", url)
            raise
        except aiohttp.ClientError as e:
            logger.error("Client error fetching %s: %s", url, e)
            raise

    async def check_url_liveness(self, url: str) -> Tuple[int, str]:
        """
        Check if a URL is live (HEAD request).
        Returns (http_status, redirect_url_if_any).
        """
        try:
            async with self._session.head(url, allow_redirects=True, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                final_url = str(resp.url)
                return resp.status, final_url
        except Exception as e:
            return 0, str(e)
