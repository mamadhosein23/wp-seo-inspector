"""
Web SEO Inspector — Scoring Engine
====================================

موتور امتیازدهی مبتنی بر مدل «Deductive Weighting».
امتیاز پایه = ۱۰۰، و هر مشکل به‌تناسب شدت از آن کم می‌شود.

Why deductive?
- مقیاس ۰ تا ۱۰۰ روی کل سایت: شفاف و قابل تفسیر برای مشتری/داشبورد.
- وزن‌ها جداگانه قابل تنظیم‌اند (fine-tuning بدون دست‌زدن به منطق).
- هر جریمه دارای `reason` است → قابل ممیزی و نمایش در UI.

Design goals:
- Pure / side-effect free → تست‌پذیری آسان (unit-test بدون I/O).
- Deterministic → همان ورودی، همان خروجی.
- Extensible → افزودن rule = یک ورودی در CHECK_RULES.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Dict, List

from app.schemas import CheckItem


# ---------------------------------------------------------------------------
# ۱) سطوح شدت و وزن‌های متناظر
# ---------------------------------------------------------------------------

class Severity(IntEnum):
    """شدت دلخواهِ هر مشکل؛ وزنِ جریمه در CHECK_RULES تعریف می‌شود."""

    CRITICAL = 30   # سایت را عملاً از ایندکس خارج می‌کند (e.g. noindex / 5xx)
    HIGH     = 20   # مشکل ساختار یا ایندکس‌پذیری جدی (e.g. missing H1/title)
    MEDIUM   = 10   # بهینه‌سازی‌های مهمِ ثانویه (canonical, desc …)
    LOW      = 5    # بهبودهای ظریف (alt, OG, schema …)


# ---------------------------------------------------------------------------
# ۲) ثبت‌قوانین (Registry)؛ منبع حقیقتِ امتیازدهی
# ---------------------------------------------------------------------------

# key  →  وزنی که هنگام عدم‌موفقیتِ آن چک اعمال می‌شود
CHECK_RULES: Dict[str, int] = {
    # --- Indexability (Critical) ---
    "http_error":        Severity.CRITICAL,   # 4xx/5xx
    "robots_noindex":    Severity.CRITICAL,   # noindex در meta/headers

    # --- Core structure (High) ---
    "h1_missing":        Severity.HIGH,
    "h1_multiple":       Severity.HIGH,
    "title_missing":     Severity.HIGH,

    # --- Secondary meta (Medium) ---
    "meta_desc_missing": Severity.MEDIUM,
    "canonical_missing": Severity.MEDIUM,
    "og_tags_missing":   Severity.MEDIUM,

    # --- Refinements (Low) ---
    "title_length":      Severity.LOW,
    "meta_desc_length":  Severity.LOW,
    "images_without_alt": Severity.LOW,
    "schema_missing":    Severity.LOW,
}


# ---------------------------------------------------------------------------
# ۳) ساختار خروجیِ امتیاز (برای داشبورد و تست)
# ---------------------------------------------------------------------------

@dataclass
class PenaltyBreakdown:
    """شکستِ دقیقِ جریمه‌ها؛ خروجیِ اصلی همان scan کردن."""
    key: str
    label: str
    message: str
    severity: int            # شدت عددی (برای رنگ‌بندی UI)
    applied_penalty: int     # جریمه‌ای که واقعاً اعمال شد
    rule_penalty: int        # جریمه پیش‌فرض در CHECK_RULES


@dataclass
class ScoreReport:
    """گزارش کامل امتیازدهی؛ چیزی که به Endpoint برمی‌گردد."""
    total_score: int
    max_score: int = 100
    total_penalty: int = 0
    items_checked: int = 0
    issues_found: int = 0
    penalties: List[PenaltyBreakdown] = field(default_factory=list)

    @property
    def percent(self) -> float:
        """درصد امتیاز نرمال‌شده — برای نمودارها."""
        if self.max_score <= 0:
            return 0.0
        return round((self.total_score / self.max_score) * 100, 2)


# ---------------------------------------------------------------------------
# ۴) موتور محاسبه
# ---------------------------------------------------------------------------

def calculate_seo_score(checks: List[CheckItem]) -> ScoreReport:
    """
    محاسبه امتیاز نهایی و شکستِ جریمه‌ها بر اساس چک‌های analyzer.

    Rules of the engine:
      • وضعیت `success` همیشه بی‌جریمه است.
      • اگر `check.penalty` به‌صورت داینامیک توسط analyzer تنظیم شده باشد،
        بر وزنِ پیش‌فرض اولویت دارد (وضعیت‌های «شدیدتر از حد»).
      • امتیاز در بازه [0, 100] clampe می‌شود.
      • چک‌های ناشناخته (خارج از CHECK_RULES) نادیده گرفته می‌شوند،
        نه اینکه سقوط کنند (fail-open، نه fail-closed).
    """
    report = ScoreReport(total_score=100)

    for check in checks:
        report.items_checked += 1

        # جریمه فقط وقتی است که مشکل واقعاً وجود دارد
        if check.status == "success" or check.key not in CHECK_RULES:
            continue

        # شدتِ مشکل برای UI
        severity = CHECK_RULES[check.key]

        # اولویت: جریمه داینامیک analyzer > جریمه پیش‌فرض rule
        applied = check.penalty if check.penalty and check.penalty > 0 else severity

        # در صورت نیاز، جریمه داینامیک را به Severity مقبول clamp کن
        applied = max(1, min(Severity.CRITICAL, applied))

        # اعمال + ثبت
        report.total_penalty += applied
        report.issues_found += 1
        report.total_score -= applied

        report.penalties.append(
            PenaltyBreakdown(
                key=check.key,
                label=check.label,
                message=check.message,
                severity=severity,
                applied_penalty=applied,
                rule_penalty=severity,
            )
        )

    # Clamp به بازه قانونی
    report.total_score = max(0, min(report.max_score, report.total_score))

    return report


# ---------------------------------------------------------------------------
# ۵) APIهای کمکی برای حلقه اصلی (admin / tests)
# ---------------------------------------------------------------------------

def score_only(checks: List[CheckItem]) -> int:
    """فقط عدد امتیاز را برمی‌گرداند — برای ستون‌های کوتاه UI/جداول."""
    return calculate_seo_score(checks).total_score


def summarize(checks: List[CheckItem]) -> dict:
    """خلاصه JSON-friendly برای لاگ یا تست سریع."""
    report = calculate_seo_score(checks)
    return {
        "score": report.total_score,
        "total_penalty": report.total_penalty,
        "issues": report.issues_found,
        "checked": report.items_checked,
    }
