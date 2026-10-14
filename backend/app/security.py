from __future__ import annotations

import asyncio
import ipaddress
import re
import socket
import time
from dataclasses import dataclass, field
from typing import Final
from urllib.parse import urlparse

import httpx

from app.security import InvalidTargetURLError, PayloadTooLargeError, SSRFDetectedError

MAX_CONTENT_BYTES: Final[int] = 5 * 1024 * 1024  # 5 MB
DEFAULT_TIMEOUT_SEC: Final[float] = 8.0
MAX_REDIRECTS: Final[int] = 5

# Allow only HTML-ish types
_HTML_MIME_RE: Final[re.Pattern[str]] = re.compile(
    r"^\s*(text/html|application/xhtml\+xml)\b", re.IGNORECASE
)


@dataclass(slots=True)
class FetchResult:
    html: str
    final_url: str
    status_code: int
    response_time_ms: int
    content_type: str
    redirect_history: list[str] = field(default_factory=list)


def _is_special_use_ipv4(ip: ipaddress.IPv4Address) -> bool:
    # RFC 6598 CGNAT, RFC 2544 benchmarking, TEST-NETs
    special_nets = [
        ipaddress.ip_network("100.64.0.0/10"),
        ipaddress.ip_network("198.18.0.0/15"),
        ipaddress.ip_network("192.0.2.0/24"),
        ipaddress.ip_network("198.51.100.0/24"),
        ipaddress.ip_network("203.0.113.0/24"),
    ]
    return any(ip in net for net in special_nets)


def is_ip_safe(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped

    if isinstance(ip, ipaddress.IPv4Address) and _is_special_use_ipv4(ip):
        return False

    return not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


class SSRFSafeTransport(httpx.AsyncHTTPTransport):
    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        url = request.url
        hostname = url.host
        port = url.port or (443 if url.scheme == "https" else 80)

        loop = asyncio.get_running_loop()
        try:
            addr_info = await loop.getaddrinfo(
                hostname,
                port,
                family=socket.AF_UNSPEC,
                type=socket.SOCK_STREAM,
            )
        except socket.gaierror as err:
            raise InvalidTargetURLError(
                f"DNS resolution failed for '{hostname}': {err}"
            ) from err

        resolved: list[ipaddress.IPv4Address | ipaddress.IPv6Address] = []
        for item in addr_info:
            raw_ip = item[4][0]
            try:
                resolved.append(ipaddress.ip_address(raw_ip))
            except ValueError as err:
                raise SSRFDetectedError(f"Malformed IP returned by DNS: {raw_ip}") from err

        if not resolved:
            raise InvalidTargetURLError(f"Hostname '{hostname}' resolved to no records.")

        for ip in resolved:
            if not is_ip_safe(ip):
                raise SSRFDetectedError(
                    f"Forbidden connection target: '{hostname}' resolved to restricted IP: {ip}"
                )

        return await super().handle_async_request(request)


class SafeAsyncCrawler:
    def __init__(
        self,
        timeout_sec: float = DEFAULT_TIMEOUT_SEC,
        user_agent: str = "WP-SEO-Inspector/1.2 (+https://github.com/mamadhosein23)",
    ) -> None:
        self.timeout_sec = timeout_sec
        self.headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.1",
            "Accept-Encoding": "gzip, deflate",
        }
        self._transport = SSRFSafeTransport(verify=True)
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            timeout = httpx.Timeout(
                timeout=self.timeout_sec,
                connect=4.0,
                read=self.timeout_sec,
                write=self.timeout_sec,
                pool=2.0,
            )
            limits = httpx.Limits(max_connections=50, max_keepalive_connections=20)
            self._client = httpx.AsyncClient(
                transport=self._transport,
                timeout=timeout,
                limits=limits,
                follow_redirects=False,
                headers=self.headers,
                http2=False,
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def _validate_initial_url(self, url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise InvalidTargetURLError(
                f"Unsupported protocol scheme '{parsed.scheme}'. Only HTTP/HTTPS permitted."
            )
        if not parsed.hostname:
            raise InvalidTargetURLError("Missing host component in target URL.")

    async def fetch(self, url: str) -> FetchResult:
        self._validate_initial_url(url)
        client = self._get_client()

        current_url = url
        redirect_chain: list[str] = [url]
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

            if response.is_redirect:
                location = response.headers.get("Location")
                await response.aclose()

                if not location:
                    raise InvalidTargetURLError("Redirect response returned without Location header.")

                current_url = str(response.url.join(location))
                self._validate_initial_url(current_url)
                redirect_chain.append(current_url)
                continue

            content_type = response.headers.get("Content-Type", "")
            if not _HTML_MIME_RE.match(content_type):
                await response.aclose()
                raise InvalidTargetURLError(
                    f"Unsupported Content-Type '{content_type}'. Only HTML is allowed."
                )

            buf = bytearray()
            try:
                async for chunk in response.aiter_bytes():
                    buf.extend(chunk)
                    if len(buf) > MAX_CONTENT_BYTES:
                        raise PayloadTooLargeError(
                            f"Response entity exceeded maximum allowable limit ({MAX_CONTENT_BYTES} bytes)."
                        )
            finally:
                await response.aclose()

            encoding = response.encoding or "utf-8"
            html_text = bytes(buf).decode(encoding, errors="replace")
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)

            return FetchResult(
                html=html_text,
                final_url=str(response.url),
                status_code=response.status_code,
                response_time_ms=elapsed_ms,
                content_type=content_type.lower(),
                redirect_history=redirect_chain[:-1], 
            )

        raise InvalidTargetURLError(f"Exceeded maximum redirect depth of {MAX_REDIRECTS} hops.")
