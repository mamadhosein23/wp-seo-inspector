"""
WP SEO Inspector — Utility Functions
====================================
توابع کمکی و خالص (Pure Functions) برای نرمال‌سازی URLها،
پردازش رشته‌ها و تمیزکاری داده‌های استخراج‌شده.
"""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse, urlunparse


def normalize_url(url: str, base_url: str | None = None) -> str:
    """
    نرمال‌سازی و تبدیل لینک‌های نسبی به مطلق، حذف Fragment (#) و فضای خالی.
    """
    cleaned = url.strip()
    if base_url:
        cleaned = urljoin(base_url, cleaned)

    parsed = urlparse(cleaned)
    # حذف fragmentها و یکپارچه‌سازی پورت/مسیر
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    path = parsed.path or "/"

    return urlunparse((scheme, netloc, path, parsed.params, parsed.query, ""))


def extract_domain(url: str) -> str:
    """استخراج دامنه خالص (بدون پورت، www و ساب‌فولدر)."""
    netloc = urlparse(url).netloc.lower().split(":")[0]
    if netloc.startswith("www."):
        return netloc[4:]
    return netloc


def is_internal_link(target_url: str, base_url: str) -> bool:
    """
    تشخیص داخلی یا خارجی بودن یک لینک بر اساس دامنه ریشه.
    لینک‌های فاقد پروتکل، tel:، mailto: یا javascript: خارجی تلقی نمی‌شوند.
    """
    if target_url.startswith(("mailto:", "tel:", "javascript:", "#")):
        return False

    target_domain = extract_domain(normalize_url(target_url, base_url))
    base_domain = extract_domain(base_url)

    if not target_domain:
        return True

    return target_domain == base_domain or target_domain.endswith(f".{base_domain}")


def clean_text(text: str | None) -> str:
    """حذف فاصله‌های اضافه، کاراکترهای کنترلی و خطوط خالی متوالی."""
    if not text:
        return ""
    # تبدیل تمام فضاهای سفید چندگانه (شامل \n, \t) به یک فاصله
    return re.sub(r"\s+", " ", text).strip()


def count_words(text: str | None) -> int:
    """
    شمارش دقیق تعداد کلمات متن، با پشتیبانی کامل از زبان‌های لاتین و یونیکد (فارسی/عربی).
    """
    cleaned = clean_text(text)
    if not cleaned:
        return 0
    # الگو منطبق بر کلمات الفبایی-عددی یونیکد
    words = re.findall(r"\b\w+\b", cleaned, flags=re.UNICODE)
    return len(words)


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """برش امن متن طولانی جهت لاگ یا خلاصه در UI."""
    cleaned = clean_text(text)
    if len(cleaned) <= max_length:
        return cleaned
    return cleaned[: max_length - len(suffix)].rstrip() + suffix
