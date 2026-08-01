# backend/app/security.py

import ipaddress
import socket
from urllib.parse import urlparse


class UnsafeUrlError(ValueError):
    """Raised when a target URL is unsafe to fetch."""


def validate_safe_url(url: str) -> None:
    """
    Prevent SSRF by rejecting:
    - Non-HTTP(S) schemes
    - localhost
    - Private, loopback, link-local, multicast, or reserved IP addresses
    """

    parsed = urlparse(url)

    if parsed.scheme not in {"http", "https"}:
        raise UnsafeUrlError("Only HTTP and HTTPS URLs are allowed.")

    if not parsed.hostname:
        raise UnsafeUrlError("The URL must contain a valid hostname.")

    hostname = parsed.hostname.lower()

    blocked_hostnames = {
        "localhost",
        "localhost.localdomain",
        "0.0.0.0",
        "::1",
    }

    if hostname in blocked_hostnames or hostname.endswith(".local"):
        raise UnsafeUrlError("Local or internal hostnames are not allowed.")

    try:
        addresses = socket.getaddrinfo(
            hostname,
            None,
            proto=socket.IPPROTO_TCP,
        )
    except socket.gaierror as error:
        raise UnsafeUrlError(
            "The domain could not be resolved. Check the URL and try again."
        ) from error

    for address_info in addresses:
        ip_string = address_info[4][0]
        ip = ipaddress.ip_address(ip_string)

        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            raise UnsafeUrlError(
                "Private, local, or reserved network addresses cannot be audited."
            )
