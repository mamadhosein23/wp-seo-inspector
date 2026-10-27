# backend/app/services/audit_service.py
from backend.app.http_client import fetch_html
from backend.app.analyzer import analyze_dom
from backend.app.scorer import calculate_score
from backend.app.cache import cache

async def run_full_audit(url: str) -> dict:
    # ۱. بررسی وجود نتیجه در کش Redis
    cache_key = f"seo_audit:{url}"
    cached_result = await cache.get(cache_key)
    if cached_result:
        cached_result["source"] = "cache"
        return cached_result

    # ۲. فچ کردن محتوای صفحه با httpx
    html_content = await fetch_html(url)

    # ۳. استخراج اطلاعات DOM با BeautifulSoup
    extracted_signals = analyze_dom(html_content, url)

    # ۴. محاسبه امتیاز نهایی با موتور امتیازدهی
    audit_score = calculate_score(extracted_signals)

    result = {
        "url": url,
        "signals": extracted_signals,
        "score": audit_score,
        "source": "fresh"
    }

    # ۵. ذخیره در کش با انقضای ۱ ساعته
    await cache.set(cache_key, result, expire_seconds=3600)

    return result
