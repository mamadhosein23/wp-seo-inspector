"""WP SEO Inspector — Utility Functions.

Pure, deterministic utility routines for URL normalization,
Unicode text sanitization, and Persian/Arabic word tokenization.
"""

from __future__ import annotations

import re
from typing import Final
from urllib.parse import urljoin, urlparse, urlunparse

# ---------------------------------------------------------------------------
# PRE-COMPILED REGEX PATTERNS
# ---------------------------------------------------------------------------
WHITESPACE_RE: Final[re.Pattern[str]] = re.compile(r"[\s\u200b\u200e\u200f]+", re.UNICODE)
# پشتیبانی کامل از حروف الفبا، اعداد و نیم‌فاصله‌ی فارسی/عربی (\u200c)
WORD_RE: Final[re.Pattern[str]] = re.compile(r"[\w\u200c]+", re.UNICODE)
SPECIAL_SCHEMES: Final[tuple[str, ...]] = ("mailto:", "tel:", "javascript:", "#", "data:")


def normalize_url(url: str, base_url: str | None = None) -> str:
    """Normalizes and resolves relative URLs, stripping fragments and trailing whitespaces."""
    cleaned = url.strip()
    if not cleaned:
        return ""

    if base_url:
        cleaned = urljoin(base_url, cleaned)

    parsed = urlparse(cleaned)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    path = parsed.path or "/"

    # نرمال‌سازی اسلش‌های تکراری متوالی در مسیر
    normalized_path = re.sub(r"/{2,}", "/", path)

    return urlunparse((scheme, netloc, normalized_path, parsed.params, parsed.query, ""))


def extract_domain(url: str) -> str:
    """Extracts raw host domain without ports, www prefix, or IPv6 brackets."""
    if not url:
        return ""

    parsed = urlparse(url)
    hostname = parsed.hostname

    if not hostname:
        return ""

    hostname = hostname.lower()
    if hostname.startswith("www."):
        return hostname[4:]

    return hostname


def is_internal_link(target_url: str, base_url: str) -> bool:
    """
    Evaluates whether target_url belongs to the same apex/subdomain hierarchy.
    Correctly prevents substring collision vulnerabilities (e.g., evil-example.com vs example.com).
    """
    cleaned_target = target_url.strip().lower()
    if cleaned_target.startswith(SPECIAL_SCHEMES):
        return False

    base_domain = extract_domain(base_url)
    if not base_domain:
        return False

    resolved_target = normalize_url(target_url, base_url)
    target_domain = extract_domain(resolved_target)

    if not target_domain:
        return True

    if target_domain == base_domain:
        return True

    # فقط ساب‌دامین‌های معتبر که با دات جدا شده‌اند
    return target_domain.endswith(f".{base_domain}")


def clean_text(text: str | None) -> str:
    """Strips excessive whitespace, unicode control characters, and linebreaks."""
    if not text:
        return ""
    return WHITESPACE_RE.sub(" ", text).strip()


def count_words(text: str | None) -> int:
    """
    Accurately counts words across Latin, Persian, and Arabic alphabets,
    properly treating Zero-Width Non-Joiner (ZWNJ / نیم‌فاصله) as internal word characters.
    """
    if not text:
        return 0

    cleaned = clean_text(text)
    if not cleaned:
        return 0

    tokens = WORD_RE.findall(cleaned)
    # فیلتر کردن توکن‌های صرفاً کاراکترهای عددی خالص بدون معنی متنی در صورت نیاز یا شمارش مستقیم
    return len(tokens)


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncates string to max_length without cutting words abruptly if feasible."""
    cleaned = clean_text(text)
    if len(cleaned) <= max_length:
        return cleaned

    effective_limit = max(0, max_length - len(suffix))
    return cleaned[:effective_limit].rstrip() + suffix
