"""WP SEO Inspector - FastAPI Application Entry Point.

Orchestrates HTTP fetching, DOM parsing, heuristic scoring, and REST responses.
"""

from __future__ import annotations

import logging
import os
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Final

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.analyzer import SEOAnalyzer
from app.http_client import SafeAsyncCrawler
from app.schemas import (
    AuditErrorDetail,
    AuditErrorResponse,
    AuditRequest,
    AuditResponse,
    HealthResponse,
)
from app.scorer import SEOScorer
from app.security import (
    InvalidTargetURLError,
    PayloadTooLargeError,
    SSRFDetectedError,
)

# ---------------------------------------------------------
# CONSTANTS & CONFIGURATION
# ---------------------------------------------------------
APP_NAME: Final[str] = "WP SEO Inspector API"
APP_VERSION: Final[str] = "1.2.0"
APP_DESCRIPTION: Final[str] = (
    "High-Performance Technical SEO Audit & Heuristic Scoring Engine"
)

DEFAULT_ALLOWED_ORIGINS: Final[tuple[str, ...]] = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
)

# ---------------------------------------------------------
# LOGGING
# ---------------------------------------------------------
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("wp_seo_inspector")


def get_allowed_origins() -> list[str]:
    """Parses and validates comma-separated CORS origins."""
    raw_origins = os.getenv("ALLOWED_ORIGINS")

    if raw_origins is None:
        return list(DEFAULT_ALLOWED_ORIGINS)

    return [
        origin.strip().rstrip("/")
        for origin in raw_origins.split(",")
        if origin.strip()
    ]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Creates shared application resources and closes them on shutdown."""
    logger.info("Initializing %s v%s...", APP_NAME, APP_VERSION)

    crawler = SafeAsyncCrawler()
    app.state.crawler = crawler

    try:
        yield
    finally:
        logger.info("Gracefully shutting down %s...", APP_NAME)
        await crawler.close()
        logger.info("HTTP crawler closed successfully.")


# ---------------------------------------------------------
# FASTAPI APPLICATION
# ---------------------------------------------------------
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# ERROR RESPONSE HELPERS
# ---------------------------------------------------------
def build_error_response(
    error_type: str,
    message: str,
    status_code: int,
) -> JSONResponse:
    """Builds a consistent API error response."""
    payload = AuditErrorResponse(
        error=AuditErrorDetail(
            type=error_type,
            message=message,
        )
    )

    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump(),
    )


# ---------------------------------------------------------
# EXCEPTION HANDLERS
# ---------------------------------------------------------
@app.exception_handler(SSRFDetectedError)
@app.exception_handler(InvalidTargetURLError)
async def security_url_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.warning(
        "Security rejection on %s: %s",
        request.url.path,
        str(exc),
    )

    return build_error_response(
        error_type="security_violation",
        message=str(exc),
        status_code=status.HTTP_400_BAD_REQUEST,
    )


@app.exception_handler(PayloadTooLargeError)
async def payload_size_exception_handler(
    request: Request,
    exc: PayloadTooLargeError,
) -> JSONResponse:
    logger.warning(
        "Payload exceeded cap on %s: %s",
        request.url.path,
        str(exc),
    )

    return build_error_response(
        error_type="payload_too_large",
        message=str(exc),
        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.exception(
        "Unhandled runtime error during %s %s",
        request.method,
        request.url.path,
    )

    return build_error_response(
        error_type="internal_server_error",
        message=(
            "An unexpected error occurred during the technical SEO audit."
        ),
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


# ---------------------------------------------------------
# ENDPOINTS
# ---------------------------------------------------------
@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Service Health Check",
)
async def health_check() -> HealthResponse:
    """Verifies service availability."""
    return HealthResponse(
        status="healthy",
        service=APP_NAME,
        version=APP_VERSION,
    )


@app.post(
    "/api/audit",
    response_model=AuditResponse,
    status_code=status.HTTP_200_OK,
    tags=["Audit Engine"],
    summary="Execute Technical SEO Audit",
    description=(
        "Asynchronously crawls target URL, parses DOM elements, "
        "and computes heuristic scores."
    ),
)
async def audit_page(
    payload: AuditRequest,
    request: Request,
) -> AuditResponse:
    """
    Executes the complete technical SEO audit lifecycle:

    1. Secure asynchronous network fetch.
    2. DOM parsing via BeautifulSoup and lxml.
    3. Heuristic SEO scoring.
    4. Response serialization according to the API schema.
    """
    target_url = str(payload.url)

    crawler: SafeAsyncCrawler = request.app.state.crawler

    # -----------------------------------------------------
    # Step 1: Secure HTTP Fetch
    # -----------------------------------------------------
    fetch_result = await crawler.fetch(target_url)

    # -----------------------------------------------------
    # Step 2: DOM Analysis
    # -----------------------------------------------------
    analyzer = SEOAnalyzer(
        html=fetch_result.html,
        base_url=fetch_result.final_url,
    )
    report_data = analyzer.analyze()

    # -----------------------------------------------------
    # Step 3: Heuristic Scoring
    # -----------------------------------------------------
    scorer = SEOScorer(
        report_data=report_data,
        fetch_result=fetch_result,
    )
    score_result = scorer.calculate()

    # -----------------------------------------------------
    # Step 4: API Response
    # -----------------------------------------------------
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
