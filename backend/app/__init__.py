from __future__ import annotations

import logging
from typing import Final

from app.analyzer import SEOAnalyzer
from app.http_client import FetcherClient, fetch_url
from app.scorer import SEOScorer
from app.schemas import AuditRequest, AuditResponse, SEOReport, ScoreBreakdown


__title__: Final[str] = "wp-seo-inspector"
__description__: Final[str] = (
    "A High-Performance Technical SEO Audit Engine & Analytics Interface"
)
__version__: Final[str] = "1.0.0"
__version_info__: Final[tuple[int, int, int]] = (1, 0, 0)
__author__: Final[str] = "WP SEO Inspector Core Team"
__license__: Final[str] = "MIT"

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

__all__: tuple[str, ...] = (
    "__title__",
    "__description__",
    "__version__",
    "__version_info__",
    "__author__",
    "__license__",
    "FetcherClient",
    "fetch_url",
    "SEOAnalyzer",
    "SEOScorer",
    "AuditRequest",
    "AuditResponse",
    "SEOReport",
    "ScoreBreakdown",
)
