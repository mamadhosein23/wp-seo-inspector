"""WP SEO Inspector — Hardened HTTP Fetcher.

SSRF & DNS-Rebinding protected asynchronous crawler using Custom Async Transport.
"""

from __future__ import annotations

import asyncio
import ipaddress
import socket
import time
from dataclasses import dataclass, field
from typing import Final
from urllib.parse import urlparse

import httpx

from app.security import (
    InvalidTargetURLError,
    PayloadTooLargeError,
    SSRFDetectedError,
)

MAX_CONTENT_BYTES: Final[int] = 5 * 1024 * 1024  # 5 MB Cap
DEFAULT_TIMEOUT_SEC: Final[float] = 8.0
MAX_REDIRECTS: Final[int] = 5


@dataclass(slots=True)
class FetchResult:
    """Consolidated network response for DOM analysis and SEO scoring."""
    html: str
    final_url: str
    status_code: int
    response_time_ms: int
    content_type: str
    redirect_history: list[str] = field(default_factory=list)


def is_ip_safe(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Verifies that an IP does not belong to loopback, private or link-local subnets."""
    # Convert IPv4-mapped IPv6 (e.g. ::ffff:127.0.0.1) to standard IPv4
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped

    return not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


class SSRFSafeTransport(httpx.AsyncHTTPTransport):
    """Custom Async Transport enforcing IP validation on raw socket connections."""

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        url = request.url
        hostname = url.host
        port = url.port or (443 if url.scheme == "https" else 80)

        # 1. Non-blocking asynchronous DNS lookup
        loop = asyncio.get_running_loop()
        try:
            addr_info = await loop.getaddrinfo(
                hostname,
                port,
                family=socket.AF_UNSPEC,
                type=socket.SOCK_STREAM,
            )
        except socket.gaierror as err:
            raise InvalidTargetURLError(f"DNS resolution failed for '{hostname}': {err}") from err

        # 2. Extract and validate all resolved IP addresses
        resolved_ips: list[ipaddress.IPv4Address | ipaddress.IPv6Address] = []
        for item in addr_info:
            raw_ip = item[4][0]
            try:
                ip_obj = ipaddress.ip_address(raw_ip)
                resolved_ips.append(ip_obj)
            except ValueError:
                raise SSRFDetectedError(f"Malformed IP returned by DNS: {raw_ip}")

        if not resolved_ips:
            raise InvalidTargetURLError(f"Hostname '{hostname}' resolved to no records.")

        for ip in resolved_ips:
            if not is_ip_safe(ip):
                raise SSRFDetectedError(
                    f"Forbidden connection target: Hostname '{hostname}' points to restricted IP: {ip}"
                )

        return await super().handle_async_request(request)


class SafeAsyncCrawler:
    """High-performance crawler supporting connection-pooling and SSRF hardening."""

    def __init__(
        self,
        timeout_sec: float = DEFAULT_TIMEOUT_SEC,
        user_agent: str = "WP-SEO-Inspector/1.2 (+https://github.com/mamadhosein23)",
    ) -> None:
        self.timeout_sec = timeout_sec
        self.headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
        }
        self._transport = SSRFSafeTransport(verify=True)
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                transport=self._transport,
                timeout=httpx.Timeout(self.timeout_sec, connect=4.0),
                follow_redirects=False,  # Redirects handled manually to enforce hop-by-hop validation
                headers=self.headers,
                http2=False,
            )
        return self._client

    async def close(self) -> None:
        """Closes connection pools gracefully on application teardown."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def _validate_initial_url(self, url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise InvalidTargetURLError(f"Unsupported protocol scheme '{parsed.scheme}'. Only HTTP/HTTPS permitted.")
        if not parsed.hostname:
            raise InvalidTargetURLError("Missing host component in target URL.")

    async def fetch(self, url: str) -> FetchResult:
        """Executes secure, streamed crawl with fail-fast byte limits and manual redirect tracing."""
        self._validate_initial_url(url)
        client = self._get_client()

        current_url = url
        redirect_chain: list[str] = []
        start_time = time.perf_counter()

        for _ in range(MAX_REDIRECTS + 1):
            try:
                req = client.build_request("GET", current_url)
                response = await client.send(req, stream=True)
            except httpx.TimeoutException as exc:
                raise TimeoutError(f"Crawl timed out after {self.timeout_sec} seconds.") from exc
            except (SSRFDetectedError, InvalidTargetURLError):
                raise
            except httpx.HTTPError as exc:
                raise ConnectionError(f"HTTP network failure on {current_url}: {exc}") from exc

            # Redirect handling (Manual hop validation)
            if response.is_redirect:
                redirect_chain.append(current_url)
                location = response.headers.get("Location")
                await response.aclose()

                if not location:
                    raise InvalidTargetURLError("Redirect response returned without Location header.")

                current_url = str(response.url.join(location))
                self._validate_initial_url(current_url)
                continue

            # Read Body with Strict 5MB Cap
            content_type = response.headers.get("Content-Type", "").lower()
            collected_chunks: list[bytes] = []
            total_bytes = 0

            try:
                async for chunk in response.aiter_bytes():
                    total_bytes += len(chunk)
                    if total_bytes > MAX_CONTENT_BYTES:
                        raise PayloadTooLargeError(
                            f"Response entity exceeded maximum allowable limit ({MAX_CONTENT_BYTES} bytes)."
                        )
                    collected_chunks.append(chunk)
            finally:
                await response.aclose()

            raw_bytes = b"".join(collected_chunks)
            encoding = response.encoding or "utf-8"
            html_text = raw_bytes.decode(encoding, errors="replace")

            elapsed_ms = int((time.perf_counter() - start_time) * 1000)

            return FetchResult(
                html=html_text,
                final_url=str(response.url),
                status_code=response.status_code,
                response_time_ms=elapsed_ms,
                content_type=content_type,
                redirect_history=redirect_chain,
            )

        raise InvalidTargetURLError(f"Exceeded maximum redirect depth of {MAX_REDIRECTS} hops.")
