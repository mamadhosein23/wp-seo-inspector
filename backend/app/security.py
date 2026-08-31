"""
WP SEO Inspector — Hardened HTTP Fetcher
=========================================
کلاینت ناهمگام ایمن در برابر حملات SSRF و DNS Rebinding.
"""

from __future__ import annotations

import ipaddress
import socket
import time
from typing import NamedTuple
from urllib.parse import urlparse

import httpx


class SecurityAuditError(ValueError):
    """خطای امنیتی ناشی از آدرس‌های غیرمجاز یا ناامن."""
    pass


class FetchResult(NamedTuple):
    response: httpx.Response
    response_time_ms: int
    final_url: str


def is_ip_safe(ip_str: str) -> bool:
    """اعتبارسنجی امنیتی IP برای جلوگیری از اتصال به شبکه‌های داخلی."""
    try:
        ip = ipaddress.ip_address(ip_str)
        # مسدودسازی رنج‌های لوکال، شبکه خصوصی، چندپخشی و کلود متادیتا (169.254.x.x)
        return not (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        )
    except ValueError:
        return False


def validate_hostname_ips(hostname: str, port: int = 80) -> list[str]:
    """Resolve تمامی رکوردهای IPv4 و IPv6 و اعتبارسنجی تک‌تک آدرس‌ها."""
    if not hostname:
        raise SecurityAuditError("Hostname cannot be empty.")

    try:
        # دریافت تمامی آدرس‌ها (IPv4 و IPv6)
        addr_info = socket.getaddrinfo(
            hostname, port, socket.AF_UNSPEC, socket.SOCK_STREAM
        )
    except socket.gaierror as err:
        raise SecurityAuditError(f"DNS resolution failed for {hostname}: {err}") from err

    resolved_ips: set[str] = set()
    for item in addr_info:
        sockaddr = item[4]
        resolved_ips.add(sockaddr[0])

    if not resolved_ips:
        raise SecurityAuditError(f"No IP addresses resolved for {hostname}.")

    for ip in resolved_ips:
        if not is_ip_safe(ip):
            raise SecurityAuditError(
                f"Access denied: Hostname '{hostname}' resolves to restricted IP: {ip}"
            )

    return list(resolved_ips)


def validate_target_url(url: str) -> str:
    """بررسی ساختار، پروتکل و امنیت اولیه آدرس ورودی."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise SecurityAuditError("Only HTTP and HTTPS protocols are supported.")

    hostname = parsed.hostname
    if not hostname:
        raise SecurityAuditError("Invalid URL structure: Missing hostname.")

    # بررسی مستقیم IPهای ورودی یا اعتبارسنجی نام میزبان
    try:
        ip = ipaddress.ip_address(hostname)
        if not is_ip_safe(str(ip)):
            raise SecurityAuditError(f"Target IP {hostname} is non-public/restricted.")
    except ValueError:
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        validate_hostname_ips(hostname, port)

    return url


class SafeRedirectHook:
    """Event Hook برای بررسی امنیتی تک‌تک ریدایرکت‌ها در طول مسیر."""
    def __call__(self, response: httpx.Response) -> None:
        if response.is_redirect:
            next_url = response.headers.get("Location")
            if next_url:
                # تبدیل مسیر نسبی به مطلق در صورت نیاز
                resolved_url = str(response.url.join(next_url))
                validate_target_url(resolved_url)


async def fetch_page(
    url: str,
    timeout_sec: float = 10.0,
    user_agent: str = "WP-SEO-Inspector/1.0 (+https://github.com/mamadhosein23)",
) -> FetchResult:
    """
    دریافت صفحه هدف با کنترل ریدایرکت‌ها، هندل تایم‌اوت و دفاع در برابر SSRF.
    """
    target_url = validate_target_url(url)
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
    }

    start_time = time.perf_counter()

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(timeout_sec, connect=5.0),
        follow_redirects=True,
        max_redirects=5,
        event_hooks={"response": [SafeRedirectHook()]},
        verify=True,
    ) as client:
        try:
            response = await client.get(target_url, headers=headers)
        except httpx.TimeoutException as exc:
            raise TimeoutError(f"Connection timed out after {timeout_sec}s") from exc
        except httpx.HTTPError as exc:
            raise ConnectionError(f"HTTP request failed: {exc}") from exc

    elapsed_ms = int((time.perf_counter() - start_time) * 1000)

    return FetchResult(
        response=response,
        response_time_ms=elapsed_ms,
        final_url=str(response.url),
    )
