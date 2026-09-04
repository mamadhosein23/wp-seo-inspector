"""WP SEO Inspector - Hardened Async HTTP Crawler.

Handles secure fetching, SSRF mitigation, DNS pinning/rebinding defense,
streaming payload limits, and latency profiling.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Final

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
    redirect_history: list[str]


class SafeAsyncCrawler:
    """SSRF-hardened async crawler with persistent connection pooling and streaming chunk protection."""

    def __init__(
        self,
        max_payload_size: int = MAX_PAYLOAD_BYTES,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        max_redirects: int = MAX_REDIRECTS,
    ) -> None:
        self.max_payload_size = max_payload_size
        self.max_redirects = max_redirects
        self.timeout = httpx.Timeout(timeout, connect=5.0, read=timeout, write=5.0)
        self.transport = DNSRebindingTransport()
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                transport=self.transport,
                timeout=self.timeout,
                headers=DEFAULT_HEADERS,
                follow_redirects=False,
                verify=True,
            )
        return self._client

    async def close(self) -> None:
        """Closes the underlying HTTP client session."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()

    async def __aenter__(self) -> SafeAsyncCrawler:
        return self

    async def __aexit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: object) -> None:
        await self.close()

    async def fetch(self, raw_url: str) -> FetchResult:
        """
        Executes a secure fetch lifecycle.
        Validates schemes, tracks manual redirects to enforce SSRF guards on every hop,
        and streams content to cap memory overhead.
        """
        current_url = validate_target_url(raw_url)
        redirect_chain: list[str] = []
        hops = 0

        client = self._get_client()
        start_time = time.perf_counter()

        while hops <= self.max_redirects:
            validate_target_url(current_url)

            try:
                request = client.build_request("GET", current_url)
                response = await client.send(request, stream=True)
            except httpx.RequestError as exc:
                raise InvalidTargetURLError(f"Connection failed to {current_url}: {exc}") from exc

            # Manually trace redirects to validate intermediate IPs against SSRF
            if response.is_redirect:
                redirect_chain.append(current_url)
                location = response.headers.get("Location")
                await response.aclose()

                if not location:
                    raise InvalidTargetURLError("Redirect response missing 'Location' header.")

                current_url = str(response.url.join(location))
                hops += 1
                continue

            # Fail-fast on Content-Length header before consuming stream
            content_length = response.headers.get("Content-Length")
            if content_length and content_length.isdigit():
                if int(content_length) > self.max_payload_size:
                    await response.aclose()
                    raise PayloadTooLargeError(
                        f"Response header exceeded {self.max_payload_size // (1024 * 1024)}MB cap."
                    )

            content_type = response.headers.get("Content-Type", "").lower()
            body_chunks: list[bytes] = []
            bytes_received = 0

            try:
                async for chunk in response.aiter_bytes():
                    bytes_received += len(chunk)
                    if bytes_received > self.max_payload_size:
                        raise PayloadTooLargeError(
                            f"Response stream exceeded {self.max_payload_size // (1024 * 1024)}MB cap."
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


# Reusable default crawler instance
_default_crawler = SafeAsyncCrawler()


async def fetch_html(url: str) -> FetchResult:
    """Top-level convenience fetcher using the persistent connection pool."""
    return await _default_crawler.fetch(url)
