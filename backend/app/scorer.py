"""Web SEO Inspector — Scoring & Heuristic Engine.

Deductive Category-Capped scoring model.
Translates DOM audit signals & network metrics into structured checks and weighted scores.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Final

from app.http_client import FetchResult
from app.schemas import (
    AuditReportData,
    CheckCategory,
    CheckItem,
    CheckStatus,
    ScoreBreakdown,
    ScoreResult,
)

# ---------------------------------------------------------------------------
# ۱) سطوح شدت و سقف جریمه دسته‌بندی‌ها (مجموع دقیق = ۱۰۰)
# ---------------------------------------------------------------------------

class Severity(IntEnum):
    """جریمه‌های استاندارد بر اساس سطح اهمیت خطای تکنیکال."""
    CRITICAL = 30
    HIGH = 20
    MEDIUM = 10
    LOW = 5


CATEGORY_MAX_IMPACT: Final[dict[CheckCategory, int]] = {
    CheckCategory.INDEXABILITY: 35,
    CheckCategory.METADATA: 25,
    CheckCategory.STRUCTURE: 20,
    CheckCategory.ACCESSIBILITY: 10,
    CheckCategory.SOCIAL: 10,
}


# ---------------------------------------------------------------------------
# ۲) کلاس اصلی SEOScorer هماهنگ با FastAPI Entry Point
# ---------------------------------------------------------------------------

class SEOScorer:
    """Evaluates raw audit metrics and produces normalized weighted scores."""

    def __init__(self, report_data: AuditReportData, fetch_result: FetchResult) -> None:
        self.data = report_data
        self.fetch = fetch_result
        self.checks: list[CheckItem] = []

    def _add_check(
        self,
        key: str,
        label: str,
        category: CheckCategory,
        status: CheckStatus,
        message: str,
        penalty: int = 0,
    ) -> None:
        self.checks.append(
            CheckItem(
                key=key,
                label=label,
                category=category,
                status=status,
                message=message,
                penalty=penalty,
            )
        )

    # -----------------------------------------------------
    # ارزیابی تک‌تک سیگنال‌ها (Heuristic Rules)
    # -----------------------------------------------------
    def _evaluate_indexability(self) -> None:
        # ۱. وضعیت HTTP Status
        if self.fetch.status_code >= 400:
            self._add_check(
                key="http_error",
                label="HTTP Response Status",
                category=CheckCategory.INDEXABILITY,
                status=CheckStatus.ERROR,
                message=f"Server returned HTTP {self.fetch.status_code}",
                penalty=Severity.CRITICAL,
            )
        else:
            self._add_check(
                key="http_error",
                label="HTTP Response Status",
                category=CheckCategory.INDEXABILITY,
                status=CheckStatus.SUCCESS,
                message=f"Page is reachable (HTTP {self.fetch.status_code})",
            )

        # ۲. متا تگ Robots / Noindex
        robots = (self.data.robots_meta or "").lower()
        if "noindex" in robots:
            self._add_check(
                key="robots_noindex",
                label="Robots Meta Directive",
                category=CheckCategory.INDEXABILITY,
                status=CheckStatus.ERROR,
                message="Page contains 'noindex' directive blocking search engines.",
                penalty=Severity.CRITICAL,
            )

        # ۳. آدرس کانونیکال (Canonical)
        if not self.data.canonical:
            self._add_check(
                key="canonical_missing",
                label="Canonical URL",
                category=CheckCategory.INDEXABILITY,
                status=CheckStatus.WARNING,
                message="Canonical tag is missing.",
                penalty=Severity.LOW,
            )
        else:
            self._add_check(
                key="canonical_missing",
                label="Canonical URL",
                category=CheckCategory.INDEXABILITY,
                status=CheckStatus.SUCCESS,
                message=f"Canonical link tag exists ({self.data.canonical}).",
            )

    def _evaluate_metadata(self) -> None:
        # Title
        if not self.data.title:
            self._add_check(
                key="title_missing",
                label="Page Title",
                category=CheckCategory.METADATA,
                status=CheckStatus.ERROR,
                message="Document has no <title> tag.",
                penalty=Severity.HIGH,
            )
        else:
            t_len = len(self.data.title)
            if t_len < 30 or t_len > 60:
                self._add_check(
                    key="title_length",
                    label="Page Title Length",
                    category=CheckCategory.METADATA,
                    status=CheckStatus.WARNING,
                    message=f"Title length ({t_len} chars) is outside optimal 30-60 char range.",
                    penalty=Severity.LOW,
                )

        # Meta Description
        if not self.data.meta_description:
            self._add_check(
                key="meta_desc_missing",
                label="Meta Description",
                category=CheckCategory.METADATA,
                status=CheckStatus.WARNING,
                message="Meta description is missing.",
                penalty=Severity.MEDIUM,
            )
        else:
            d_len = len(self.data.meta_description)
            if d_len < 70 or d_len > 160:
                self._add_check(
                    key="meta_desc_length",
                    label="Meta Description Length",
                    category=CheckCategory.METADATA,
                    status=CheckStatus.WARNING,
                    message=f"Meta description length ({d_len} chars) is outside optimal 70-160 range.",
                    penalty=Severity.LOW,
                )

    def _evaluate_structure(self) -> None:
        # H1 Checks
        h1_count = self.data.headings.h1_count
        if h1_count == 0:
            self._add_check(
                key="h1_missing",
                label="Primary Heading (H1)",
                category=CheckCategory.STRUCTURE,
                status=CheckStatus.ERROR,
                message="Document has no <h1> heading tag.",
                penalty=Severity.HIGH,
            )
        elif h1_count > 1:
            self._add_check(
                key="h1_multiple",
                label="Primary Heading (H1)",
                category=CheckCategory.STRUCTURE,
                status=CheckStatus.WARNING,
                message=f"Document contains {h1_count} H1 headings (recommended: exactly 1).",
                penalty=Severity.LOW,
            )

        # Word Count
        if self.data.word_count < 300:
            self._add_check(
                key="word_count_low",
                label="Content Thinness",
                category=CheckCategory.STRUCTURE,
                status=CheckStatus.WARNING,
                message=f"Thin content detected ({self.data.word_count} words). Recommended >= 300.",
                penalty=Severity.MEDIUM,
            )

    def _evaluate_accessibility(self) -> None:
        media = self.data.media
        if media.total_images > 0:
            unlabeled = media.missing_alt + media.empty_alt
            if unlabeled > 0:
                ratio = round((unlabeled / media.total_images) * 100)
                self._add_check(
                    key="images_without_alt",
                    label="Image Alt Attributes",
                    category=CheckCategory.ACCESSIBILITY,
                    status=CheckStatus.WARNING if ratio < 50 else CheckStatus.ERROR,
                    message=f"{unlabeled} of {media.total_images} images lack descriptive alt tags ({ratio}%).",
                    penalty=Severity.MEDIUM if ratio >= 50 else Severity.LOW,
                )

    def _evaluate_social_and_rich(self) -> None:
        if not self.data.has_open_graph:
            self._add_check(
                key="og_tags_missing",
                label="Open Graph Protocol",
                category=CheckCategory.SOCIAL,
                status=CheckStatus.WARNING,
                message="Open Graph metadata tags are missing.",
                penalty=Severity.LOW,
            )

        if not self.data.has_structured_data:
            self._add_check(
                key="schema_missing",
                label="Structured Data (JSON-LD)",
                category=CheckCategory.SOCIAL,
                status=CheckStatus.WARNING,
                message="No structured schema data found in page markup.",
                penalty=Severity.LOW,
            )

    # -----------------------------------------------------
    # محاسبه نهایی امتیاز با اعمال Group Capping
    # -----------------------------------------------------
    def calculate(self) -> ScoreResult:
        # ۱. اجرای تمام ارزیابی‌ها
        self._evaluate_indexability()
        self._evaluate_metadata()
        self._evaluate_structure()
        self._evaluate_accessibility()
        self._evaluate_social_and_rich()

        # ۲. جمع‌آوری و کسر با Group Capping
        raw_penalties: dict[CheckCategory, int] = {cat: 0 for cat in CATEGORY_MAX_IMPACT}

        for check in self.checks:
            if check.status in (CheckStatus.SUCCESS, CheckStatus.INFO):
                continue
            if check.category in raw_penalties:
                raw_penalties[check.category] += check.penalty

        # ۳. محاسبه نمرات دسته‌ای و کل
        breakdown_dict: dict[str, int] = {}
        total_deductions = 0

        for cat, max_impact in CATEGORY_MAX_IMPACT.items():
            applied_penalty = min(raw_penalties[cat], max_impact)
            # نمره باقی‌مانده از سقف دسته
            category_score = max_impact - applied_penalty
            breakdown_dict[cat.value] = category_score
            total_deductions += applied_penalty

        final_total_score = max(0, 100 - total_deductions)

        score_breakdown = ScoreBreakdown(
            indexability=breakdown_dict[CheckCategory.INDEXABILITY.value],
            metadata=breakdown_dict[CheckCategory.METADATA.value],
            structure=breakdown_dict[CheckCategory.STRUCTURE.value],
            accessibility=breakdown_dict[CheckCategory.ACCESSIBILITY.value],
            social=breakdown_dict[CheckCategory.SOCIAL.value],
        )

        return ScoreResult(
            total_score=final_total_score,
            breakdown=score_breakdown,
            checks=self.checks,
        )
