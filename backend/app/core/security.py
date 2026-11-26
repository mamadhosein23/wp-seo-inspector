import ipaddress
import socket
from urllib.parse import urlparse
from fastapi import HTTPException

def validate_target_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail="Invalid protocol. Only HTTP/HTTPS allowed.")
    
    hostname = parsed.hostname
    if not hostname:
        raise HTTPException(status_code=400, detail="Missing hostname.")

    try:
        ip_list = socket.getaddrinfo(hostname, None)
        for entry in ip_list:
            ip = ipaddress.ip_address(entry[4][0])
            if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local:
                raise HTTPException(status_code=403, detail="SSRF protection: Private addresses forbidden.")
    except socket.gaierror:
        raise HTTPException(status_code=400, detail="Domain name resolution failed.")
        
    return url
