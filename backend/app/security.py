import ipaddress
import socket
import dns.resolver # نیاز به نصب dnspython داری
from urllib.parse import urlparse

class UnsafeUrlError(ValueError): pass

def get_safe_ip(hostname: str) -> str:
    """Resolve hostname to IP and validate it."""
    try:
        answers = dns.resolver.resolve(hostname, 'A')
        ip_string = str(answers[0])
        ip = ipaddress.ip_address(ip_string)
        
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
            raise UnsafeUrlError(f"Access to internal IP {ip_string} denied.")
        return ip_string
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, Exception) as e:
        raise UnsafeUrlError(f"Could not resolve or validate IP for {hostname}: {e}")

def validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise UnsafeUrlError("Only HTTP/HTTPS allowed.")
    if not parsed.hostname:
        raise UnsafeUrlError("Invalid hostname.")
    
    blocked = {"localhost", "127.0.0.1", "0.0.0.0"}
    if parsed.hostname.lower() in blocked or parsed.hostname.endswith(".local"):
        raise UnsafeUrlError("Localhost is blocked.")
