"""
WP SEO Inspector - Hardened Async HTTP Crawler.

Handles secure fetching, SSRF mitigation, DNS pinning/rebinding defense,
streaming payload limits, and latency profiling.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Final, List, Optional
from urllib.parse import urlparse

import httpx

from app.security import (
    DNSRebindingTransport,
    InvalidTargetURLError,
    PayloadTooLargeError,
    SSRFDetectedError,
    validate_target_url,
)

# ---------------------------------------------------------
# CRAWLER CONSTANTS
# ---------------------------------------------------------
MAX_PAYLOAD_BYTES: Final[int] = 5 * 1024 * 1024  # 5 MB
DEFAULT_TIMEOUT_SECONDS: Final[float] = 12.0
MAX_REDIRECTS: Final[int] = 5

USER_AGENT: Final[str] = (
    "Mozilla/5.0 (compatible; WPSEOInspector/1.0; +https://github.com/mamadhosein23/wp-seo-inspector)"
)

DEFAULT_HEADERS: Final[dict[str, str]] = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,fa;q=0.8",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}


@dataclass(slots=True, frozen=True)
class FetchResult:
    """Immutable transfer object containing response data and network metrics."""

    url: str
    final_url: str
    status_code: int
    headers: dict[str, str]
    content_type: str
    html: str
    response_time_ms: float
    redirect_history: List[str]


class SafeAsyncCrawler:
    """SSRF-hardened async crawler with streaming chunk protection."""

    def __init__(
        self,
        max_payload_size: int = MAX_PAYLOAD_BYTES,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        max_redirects: int = MAX_REDIRECTS,
    ) -> None:
        self.max_payload_size = max_payload_size
        self.timeout = httpx.Timeout(timeout, connect=5.0, read=timeout, write=5.0)
        self.max_redirects = max_redirects

    async def fetch(self, raw_url: str) -> FetchResult:
        """
        Executes a secure fetch lifecycle.
        Validates schemes, tracks manual redirects to enforce SSRF guards on every hop,
        and streams content to cap memory overhead.
        """
        current_url = validate_target_url(raw_url)
        redirect_chain: List[str] = []
        hops = 0

        start_time = time.perf_counter()

        # Custom transport to pin DNS resolution securely without breaking TLS SNI
        transport = DNSRebindingTransport()

        async with httpx.AsyncClient(
            transport=transport,
            timeout=self.timeout,
            headers=DEFAULT_HEADERS,
            follow_redirects=False,
            verify=True,
        ) as client:
            while hops <= self.max_redirects:
                # Pre-flight check on destination URL prior to connection
                validate_target_url(current_url)

                try:
                    request = client.build_request("GET", current_url)
                    response = await client.send(request, stream=True)
                except httpx.RequestError as exc:
                    raise InvalidTargetURLError(f"Connection failed to {current_url}: {exc}") from exc

                # Check for HTTP redirects manually to validate destination IPs on each hop
                if response.is_redirect:
                    redirect_chain.append(current_url)
                    location = response.headers.get("Location")
                    if not location:
                        raise InvalidTargetURLError("Redirect response missing 'Location' header.")

                    # Resolve relative redirect paths
                    current_url = str(response.url.join(location))
                    await response.aclose()
                    hops += 1
                    continue

                # Stream and enforce payload caps strictly
                content_type = response.headers.get("Content-Type", "").lower()
                body_chunks: List[bytes] = []
                bytes_received = 0

                try:
                    async for chunk in response.aiter_bytes():
                        bytes_received += len(chunk)
                        if bytes_received > self.max_payload_size:
                            raise PayloadTooLargeError(
                                f"Response exceeded {self.max_payload_size // (1024 * 1024)}MB cap."
                            )
                        body_chunks.append(chunk)
                finally:
                    await response.aclose()

                raw_bytes = b"".join(body_chunks)
                encoding = response.encoding or "utf-8"
                html = raw_bytes.decode(encoding, errors="replace")

                latency = round((time.perf_counter() - start_time) * 1000, 2)

                return FetchResult(
                    url=raw_url,
                    final_url=str(response.url),
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    content_type=content_type,
                    html=html,
                    response_time_ms=latency,
                    redirect_history=redirect_chain,
                )

            raise SSRFDetectedError("Too many redirects (potential infinite redirect loop).")


# Singleton-like convenience function
async def fetch_html(url: str) -> FetchResult:
    """Top-level convenience fetcher with default parameters."""
    crawler = SafeAsyncCrawler()
    return await crawler.fetch(url)
