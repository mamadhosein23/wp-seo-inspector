im
import asyncio
from app.security import get_safe_ip

MAX_SIZE = 5 * 1024 * 1024  # 5MB

async def fetch_html(url: str) -> str:
    parsed = urlparse(url)
    safe_ip = get_safe_ip(parsed.hostname)
    
    # برای جلوگیری از DNS Rebinding، به IP ثابت کانکت می‌شویم
    host_header = parsed.hostname
    target_url = f"{parsed.scheme}://{safe_ip}{parsed.path}"
    
    async with httpx.AsyncClient(timeout=httpx.Timeout(5.0, connect=10.0)) as client:
        response = await client.get(
            target_url, 
            headers={"Host": host_header, "User-Agent": "WPSEOInspector/2.0"},
            follow_redirects=True
        )
        
        if response.status_code != 200:
            raise Exception(f"HTTP Error: {response.status_code}")
            
        if int(response.headers.get("Content-Length", 0)) > MAX_SIZE:
            raise Exception("Page too large")
            
        return response.text
