"""Web SEO Inspector — Scoring & Heuristic Engine.

Deductive Category-Capped scoring model.
Translates DOM audit signals & network metrics into structured checks and weighted scores.
"""

from __future__ import annotations

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
# ---------------------------------------------------------------------------

class Severity(IntEnum):
پ    CRITICAL = 30
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
                penalty=int(penalty),
            )
        )

    # -----------------------------------------------------
    # Heuristic Rules
    # -----------------------------------------------------
    def _evaluate_indexability(self) -> None:
        # HTTP Status
        if self.fetch.status_code >= 400:
            self._add_check(
                key="http_status",
                label="HTTP Response Status",
                category=CheckCategory.INDEXABILITY,
                status=CheckStatus.ERROR,
                message=f"Server returned HTTP {self.fetch.status_code}.",
                penalty=Severity.CRITICAL,
            )
        else:
            self._add_check(
                key="http_status",
                label="HTTP Response Status",
                category=CheckCategory.INDEXABILITY,
                status=CheckStatus.SUCCESS,
                message=f"Page is reachable (HTTP {self.fetch.status_code}).",
            )

        # Robots Meta / Noindex
        robots = (self.data.robots_meta or "").lower().strip()
        if "noindex" in robots:
            self._add_check(
                key="robots_meta",
                label="Robots Meta Directive",
                category=CheckCategory.INDEXABILITY,
                status=CheckStatus.ERROR,
                message="Page contains 'noindex' directive blocking indexing.",
                penalty=Severity.CRITICAL,
            )
        else:
            self._add_check(
                key="robots_meta",
                label="Robots Meta Directive",
                category=CheckCategory.INDEXABILITY,
                status=CheckStatus.SUCCESS,
                message="No 'noindex' directive detected in robots meta.",
            )

        # Canonical
        if not self.data.canonical:
            self._add_check(
                key="canonical",
                label="Canonical URL",
                category=CheckCategory.INDEXABILITY,
                status=CheckStatus.WARNING,
                message="Canonical tag is missing.",
                penalty=Severity.LOW,
            )
        else:
            self._add_check(
                key="canonical",
                label="Canonical URL",
                category=CheckCategory.INDEXABILITY,
                status=CheckStatus.SUCCESS,
                message=f"Canonical link tag exists ({self.data.canonical}).",
            )

    def _evaluate_metadata(self) -> None:
        # Title
        if not self.data.title:
            self._add_check(
                key="title",
                label="Page Title",
                category=CheckCategory.METADATA,
                status=CheckStatus.ERROR,
                message="Document has no <title> tag.",
                penalty=Severity.HIGH,
            )
        else:
            t_len = len(self.data.title)
            if 30 <= t_len <= 60:
                self._add_check(
                    key="title",
                    label="Page Title",
                    category=CheckCategory.METADATA,
                    status=CheckStatus.SUCCESS,
                    message=f"Title exists and length is OK ({t_len} chars).",
                )
            else:
                self._add_check(
                    key="title",
                    label="Page Title Length",
                    category=CheckCategory.METADATA,
                    status=CheckStatus.WARNING,
                    message=f"Title length ({t_len} chars) is outside optimal 30–60 range.",
                    penalty=Severity.LOW,
                )

        # Meta Description
        if not self.data.meta_description:
            self._add_check(
                key="meta_description",
                label="Meta Description",
                category=CheckCategory.METADATA,
                status=CheckStatus.WARNING,
                message="Meta description is missing.",
                penalty=Severity.MEDIUM,
            )
        else:
            d_len = len(self.data.meta_description)
            if 70 <= d_len <= 160:
                self._add_check(
                    key="meta_description",
                    label="Meta Description",
                    category=CheckCategory.METADATA,
                    status=CheckStatus.SUCCESS,
                    message=f"Meta description exists and length is OK ({d_len} chars).",
                )
            else:
                self._add_check(
                    key="meta_description",
                    label="Meta Description Length",
                    category=CheckCategory.METADATA,
                    status=CheckStatus.WARNING,
                    message=f"Meta description length ({d_len} chars) is outside optimal 70–160 range.",
                    penalty=Severity.LOW,
                )

    def _evaluate_structure(self) -> None:
        # H1 Checks
        h1_count = self.data.headings.h1_count
        if h1_count == 0:
            self._add_check(
                key="h1",
                label="Primary Heading (H1)",
                category=CheckCategory.STRUCTURE,
                status=CheckStatus.ERROR,
                message="Document has no <h1> heading tag.",
                penalty=Severity.HIGH,
            )
        elif h1_count > 1:
            self._add_check(
                key="h1",
                label="Primary Heading (H1)",
                category=CheckCategory.STRUCTURE,
                status=CheckStatus.WARNING,
                message=f"Document contains {h1_count} H1 headings (recommended: exactly 1).",
                penalty=Severity.LOW,
            )
        else:
            self._add_check(
                key="h1",
                label="Primary Heading (H1)",
                category=CheckCategory.STRUCTURE,
                status=CheckStatus.SUCCESS,
                message="Exactly one H1 heading found.",
            )

        # Word Count
        wc = self.data.word_count
        if wc >= 300:
            self._add_check(
                key="word_count",
                label="Content Length",
                category=CheckCategory.STRUCTURE,
                status=CheckStatus.SUCCESS,
                message=f"Word count is sufficient ({wc} words).",
            )
        else:
            self._add_check(
                key="word_count",
                label="Content Thinness",
                category=CheckCategory.STRUCTURE,
                status=CheckStatus.WARNING,
                message=f"Thin content detected ({wc} words). Recommended >= 300.",
                penalty=Severity.MEDIUM,
            )

    def _evaluate_accessibility(self) -> None:
        media = self.data.media
        if media.total_images == 0:
            self._add_check(
                key="image_alt",
                label="Image Alt Attributes",
                category=CheckCategory.ACCESSIBILITY,
                status=CheckStatus.INFO,
                message="No images detected on the page.",
            )
            return

        unlabeled = media.missing_alt + media.empty_alt
        if unlabeled == 0:
            self._add_check(
                key="image_alt",
                label="Image Alt Attributes",
                category=CheckCategory.ACCESSIBILITY,
                status=CheckStatus.SUCCESS,
                message=f"All {media.total_images} images have alt attributes.",
            )
            return

        ratio = round((unlabeled / media.total_images) * 100)
        is_severe = ratio >= 50

        self._add_check(
            key="image_alt",
            label="Image Alt Attributes",
            category=CheckCategory.ACCESSIBILITY,
            status=CheckStatus.ERROR if is_severe else CheckStatus.WARNING,
            message=f"{unlabeled} of {media.total_images} images lack descriptive alt tags ({ratio}%).",
            penalty=Severity.MEDIUM if is_severe else Severity.LOW,
        )

    def _evaluate_social_and_rich(self) -> None:
        # Open Graph
        if self.data.has_open_graph:
            self._add_check(
                key="open_graph",
                label="Open Graph Protocol",
                category=CheckCategory.SOCIAL,
                status=CheckStatus.SUCCESS,
                message="Open Graph metadata detected.",
            )
        else:
            self._add_check(
                key="open_graph",
                label="Open Graph Protocol",
                category=CheckCategory.SOCIAL,
                status=CheckStatus.WARNING,
                message="Open Graph metadata tags are missing.",
                penalty=Severity.LOW,
            )

        # Structured Data
        if self.data.has_structured_data:
            types = ", ".join(self.data.structured_data_types) if self.data.structured_data_types else "unknown"
            self._add_check(
                key="structured_data",
                label="Structured Data (JSON-LD)",
                category=CheckCategory.SOCIAL,
                status=CheckStatus.SUCCESS,
                message=f"Structured data detected (types: {types}).",
            )
        else:
            self._add_check(
                key="structured_data",
                label="Structured Data (JSON-LD)",
                category=CheckCategory.SOCIAL,
                status=CheckStatus.WARNING,
                message="No structured schema data found in page markup.",
                penalty=Severity.LOW,
            )

    # -----------------------------------------------------
    # Final Scoring with Category Capping
    # -----------------------------------------------------
    def calculate(self) -> ScoreResult:
        self.checks.clear()

        self._evaluate_indexability()
        self._evaluate_metadata()
        self._evaluate_structure()
        self._evaluate_accessibility()
        self._evaluate_social_and_rich()

        raw_penalties: dict[CheckCategory, int] = {cat: 0 for cat in CATEGORY_MAX_IMPACT}

        for check in self.checks:
            if check.status in (CheckStatus.SUCCESS, CheckStatus.INFO):
                continue
            raw_penalties[check.category] += int(check.penalty)

        applied_indexability = min(raw_penalties[CheckCategory.INDEXABILITY], CATEGORY_MAX_IMPACT[CheckCategory.INDEXABILITY])
        applied_metadata     = min(raw_penalties[CheckCategory.METADATA],     CATEGORY_MAX_IMPACT[CheckCategory.METADATA])
        applied_structure    = min(raw_penalties[CheckCategory.STRUCTURE],    CATEGORY_MAX_IMPACT[CheckCategory.STRUCTURE])
        applied_access       = min(raw_penalties[CheckCategory.ACCESSIBILITY],CATEGORY_MAX_IMPACT[CheckCategory.ACCESSIBILITY])
        applied_social       = min(raw_penalties[CheckCategory.SOCIAL],       CATEGORY_MAX_IMPACT[CheckCategory.SOCIAL])

        total_deductions = applied_indexability + applied_metadata + applied_structure + applied_access + applied_social
        total_score = max(0, 100 - total_deductions)

        breakdown = ScoreBreakdown(
            indexability=CATEGORY_MAX_IMPACT[CheckCategory.INDEXABILITY] - applied_indexability,
            metadata=CATEGORY_MAX_IMPACT[CheckCategory.METADATA] - applied_metadata,
            structure=CATEGORY_MAX_IMPACT[CheckCategory.STRUCTURE] - applied_structure,
            accessibility=CATEGORY_MAX_IMPACT[CheckCategory.ACCESSIBILITY] - applied_access,
            social=CATEGORY_MAX_IMPACT[CheckCategory.SOCIAL] - applied_social,
        )

        return ScoreResult(
            total_score=total_score,
            breakdown=breakdown,
            checks=self.checks,
        )
