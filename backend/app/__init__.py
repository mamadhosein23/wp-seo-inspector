"""""""
WP SEO Inspector - High-Performance Technical SEO Audit Engine.

A specialized auditing backend designed to dissect web pages, parse DOM trees,
and evaluate technical SEO health via heuristic deductive scoring.
"""""""

from typing import Final, Tuple
import logging

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

__version_info__: Final[Tuple[int, int, int]] = (1, 0, 0)

# ---------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------
# Set up default package-level logger to avoid 'No handler found' warnings
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# ---------------------------------------------------------
# Public API Exposures (Selective imports to maintain clean namespace)
# ---------------------------------------------------------
try:
    from app.http_client import FetcherClient, fetch_url
    from app.analyzer import SEOAnalyzer
    from app.scorer import SEOScorer
    from app.schemas import (
        AuditRequest,
        AuditResponse,
        SEOReport,
        ScoreBreakdown,
    )

    __all__: Tuple[str, ...] = (
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
    )

except ImportError:
    # Graceful degradation during package builds or isolated schema generations
    __all__ = (
        "__title__",
        "__version__",
        "__version_info__",
    )
