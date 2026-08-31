"""
Web SEO Inspector — Scoring Engine
====================================
موتور امتیازدهی استاندارد مبتنی بر Deductive Weighting با اعمال سقف دسته‌ای (Category Capping).
امتیاز پایه = ۱۰۰ و کسر امتیازها در چارچوب حداکثر تأثیر هر دسته انجام می‌شود.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum

from app.schemas import CheckCategory, CheckItem


# ---------------------------------------------------------------------------
# ۱) سطوح شدت و سقف جریمه دسته‌بندی‌ها
# ---------------------------------------------------------------------------

class Severity(IntEnum):
    """سطح جریمه پیش‌فرض به ازای هر خطا."""
    CRITICAL = 30   # خطای مسدودکننده (e.g. 5xx, noindex)
    HIGH     = 20   # خطای ساختاری حاد (e.g. missing title/h1)
    MEDIUM   = 10   # خطای سئو تکنیکال سطح دو (e.g. canonical, meta desc)
    LOW      = 5    # بهینه‌سازی‌های جزئی (e.g. alt, og tags)


# سقف مجاز کسر امتیاز به تفکیک دسته‌بندی مطابق جدول README
CATEGORY_MAX_IMPACT: dict[CheckCategory, int] = {
    "indexability":  40,
    "structure":     20,
    "metadata":      25,
    "accessibility": 15,
    "social":        10,
}


# ---------------------------------------------------------------------------
# ۲) ثبت قوانین پیش‌فرض (Registry)
# ---------------------------------------------------------------------------

CHECK_RULES: dict[str, int] = {
    # --- Indexability (Max 40) ---
    "http_error":         Severity.CRITICAL,
    "robots_noindex":     Severity.CRITICAL,
    "status_code_failed": Severity.HIGH,

    # --- Structure (Max 20) ---
    "h1_missing":         Severity.HIGH,
    "h1_multiple":        Severity.MEDIUM,
    "heading_hierarchy":  Severity.LOW,

    # --- Metadata (Max 25) ---
    "title_missing":      Severity.HIGH,
    "title_length":       Severity.LOW,
    "meta_desc_missing":  Severity.MEDIUM,
    "meta_desc_length":   Severity.LOW,
    "canonical_missing":  Severity.MEDIUM,

    # --- Accessibility (Max 15) ---
    "images_without_alt": Severity.LOW,
    "link_descriptors":   Severity.LOW,

    # --- Social Graph (Max 10) ---
    "og_tags_missing":    Severity.LOW,
    "twitter_missing":    Severity.LOW,
    "schema_missing":     Severity.LOW,
}


# ---------------------------------------------------------------------------
# ۳) مدل‌های خروجی و گزارش
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class PenaltyBreakdown:
    key: str
    label: str
    category: CheckCategory
    message: str
    severity: int
    applied_penalty: int
    rule_penalty: int


@dataclass(slots=True)
class ScoreReport:
    total_score: int
    max_score: int = 100
    total_penalty: int = 0
    items_checked: int = 0
    issues_found: int = 0
    category_penalties: dict[CheckCategory, int] = field(default_factory=dict)
    penalties: list[PenaltyBreakdown] = field(default_factory=list)

    @property
    def percent(self) -> float:
        if self.max_score <= 0:
            return 0.0
        return round((self.total_score / self.max_score) * 100, 2)


# ---------------------------------------------------------------------------
# ۴) موتور محاسبه با Group Capping
# ---------------------------------------------------------------------------

def calculate_seo_score(checks: list[CheckItem]) -> ScoreReport:
    """
    محاسبه نمره کل با اعمال جریمه‌های تفکیک‌شده و محدودسازی بر اساس سقف هر Category.
    """
    raw_category_penalties: dict[CheckCategory, int] = {
        cat: 0 for cat in CATEGORY_MAX_IMPACT
    }
    penalties_list: list[PenaltyBreakdown] = []
    items_checked = len(checks)
    issues_found = 0

    for check in checks:
        # آیتم‌های موفق یا صرفاً اطلاع‌رسانی جریمه ندارند
        if check.status in ("success", "info"):
            continue

        base_penalty = CHECK_RULES.get(check.key, Severity.LOW)

        # اگر Analyzer جریمه اختصاصی داده باشد اولویت دارد؛ در غیر اینصورت وضعیت warning تخفیف ۵۰٪ می‌گیرد
        if check.penalty > 0:
            applied = check.penalty
        elif check.status == "warning":
            applied = max(1, base_penalty // 2)
        else:
            applied = base_penalty

        applied = max(1, min(Severity.CRITICAL, applied))

        category = check.category
        if category in raw_category_penalties:
            raw_category_penalties[category] += applied

        issues_found += 1
        penalties_list.append(
            PenaltyBreakdown(
                key=check.key,
                label=check.label,
                category=category,
                message=check.message,
                severity=base_penalty,
                applied_penalty=applied,
                rule_penalty=base_penalty,
            )
        )

    # اعمال سقف مجاز جریمه روی هر دسته (Capping)
    final_category_penalties: dict[CheckCategory, int] = {}
    total_deductions = 0

    for cat, raw_pen in raw_category_penalties.items():
        max_allowed = CATEGORY_MAX_IMPACT[cat]
        effective_penalty = min(raw_pen, max_allowed)
        final_category_penalties[cat] = effective_penalty
        total_deductions += effective_penalty

    final_score = max(0, min(100, 100 - total_deductions))

    return ScoreReport(
        total_score=final_score,
        total_penalty=total_deductions,
        items_checked=items_checked,
        issues_found=issues_found,
        category_penalties=final_category_penalties,
        penalties=penalties_list,
    )


# ---------------------------------------------------------------------------
# ۵) توابع کمکی
# ---------------------------------------------------------------------------

def score_only(checks: list[CheckItem]) -> int:
    """محاسبه سریع صرفاً مقدار عددی نمره نهایی."""
    return calculate_seo_score(checks).total_score


def summarize(checks: list[CheckItem]) -> dict[str, int]:
    """خلاصه تجمیعی برای گزارش‌گیری سریع یا لاگ."""
    report = calculate_seo_score(checks)
    return {
        "score": report.total_score,
        "total_penalty": report.total_penalty,
        "issues": report.issues_found,
        "checked": report.items_checked,
    }
