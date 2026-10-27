"""Application service for executing a single-page SEO audit."""

from __future__ import annotations

import asyncio
from typing import Any

from app.analyzer import SEOAnalyzer
from app.http_client import SafeAsyncCrawler
from app.schemas import AuditResponse
from app.scorer import SEOScorer


def _analyze_and_score(
    html: str,
    base_url: str,
    fetch_result: Any,
) -> tuple[Any, Any]:
    """Run synchronous DOM parsing and scoring outside the event loop."""
    analyzer = SEOAnalyzer(html=html, base_url=base_url)
    report_data = analyzer.analyze()

    scorer = SEOScorer(
        report_data=report_data,
        fetch_result=fetch_result,
    )
    score_result = scorer.calculate()

    return report_data, score_result


class AuditService:
    """Coordinates fetching, analysis, scoring, and response construction."""

    def __init__(self, crawler: SafeAsyncCrawler) -> None:
        self._crawler = crawler

    async def run(self, target_url: str) -> AuditResponse:
        fetch_result = await self._crawler.fetch(target_url)

        report_data, score_result = await asyncio.to_thread(
            _analyze_and_score,
            fetch_result.html,
            fetch_result.final_url,
            fetch_result,
        )

        return AuditResponse(
            url=target_url,
            final_url=fetch_result.final_url,
            status_code=fetch_result.status_code,
            response_time_ms=fetch_result.response_time_ms,
            content_type=fetch_result.content_type,
            redirect_chain=fetch_result.redirect_history,
            score=score_result.total_score,
            score_breakdown=score_result.breakdown,
            checks=score_result.checks,
            data=report_data,
        )
