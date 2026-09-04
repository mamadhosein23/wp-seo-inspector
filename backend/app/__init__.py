"""WP SEO Inspector - High-Performance Technical SEO Audit Engine.

A specialized auditing backend designed to dissect web pages, parse DOM trees,
and evaluate technical SEO health via heuristic deductive scoring.
"""

from __future__ import annotations

import logging
from typing import Final

# ---------------------------------------------------------
# Application Metadata
# ---------------------------------------------------------
__title__: Final[str] = "wp-seo-inspector"
__description__: Final[str] = (
    "A High-Performance Technical SEO Audit Engine & Analytics Interface"
)
__version__: Final[str] = "1.0.0"
__author__: Final[str] = "WP SEO Inspector Core Team"
__license__: Final[str] = "MIT"

__version_info__: Final[tuple[int, int, int]] = (1, 0, 0)

# ---------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# ---------------------------------------------------------
# Public API Exposures
# ---------------------------------------------------------
from app.analyzer import SEOAnalyzer
from app.http_client import FetcherClient, fetch_url
from app.schemas import (
    AuditRequest,
    AuditResponse,
    ScoreBreakdown,
    SEOReport,
)
from app.scorer import SEOScorer

__all__: list[str] = [
    "__title__",
    "__version__",
    "__version_info__",
    "FetcherClient",
    "fetch_url",
    "SEOAnalyzer",
    "SEOScorer",
    "AuditRequest",
    "AuditResponse",
    "SEOReport",
    "ScoreBreakdown",
]
