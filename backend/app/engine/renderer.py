import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

class HybridRenderer:
    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self.headers = {"User-Agent": "WP-SEO-Inspector-Bot/2.0 (+https://inspector.dev/bot)"}

    async def fetch(self, url: str) -> tuple[str, int, dict]:
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True, headers=self.headers) as client:
            resp = await client.get(url)
            html = resp.text
            status = resp.status_code
            headers = dict(resp.headers)

        # تشخیص نیاز به رندر JS (صفحات خالی SPA/React/Headless WP)
        soup = BeautifulSoup(html, "lxml")
        has_heavy_js = bool(soup.find(id="__next") or soup.find(id="root")) and len(soup.get_text(strip=True)) < 150

        if has_heavy_js:
            html = await self._render_headless(url)

        return html, status, headers

    async def _render_headless(self, url: str) -> str:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
            page = await browser.new_page(user_agent=self.headers["User-Agent"])
            await page.goto(url, wait_until="networkidle", timeout=int(self.timeout * 1000))
            content = await page.content()
            await browser.close()
            return content
