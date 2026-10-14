"""WP SEO Inspector - FastAPI Application Entry Point.

Orchestrates HTTP fetching, DOM parsing, heuristic scoring, and REST responses.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated, Final

from fastapi import Depends, FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.analyzer import SEOAnalyzer
from app.http_client import SafeAsyncCrawler
from app.schemas import (
    AuditErrorDetail,
    AuditErrorResponse,
    AuditReportData,
    AuditRequest,
    AuditResponse,
    HealthResponse,
    ScoreResult,
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
    if not raw_origins:
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
# FASTAPI APPLICATION & MIDDLEWARE
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


def get_crawler(request: Request) -> SafeAsyncCrawler:
    """Dependency provider for the shared network crawler."""
    return request.app.state.crawler


# ---------------------------------------------------------
# ERROR RESPONSE FACTORY & HANDLERS
# ---------------------------------------------------------
def build_error_response(error_type: str, message: str, status_code: int) -> JSONResponse:
    payload = AuditErrorResponse(
        error=AuditErrorDetail(type=error_type, message=message)
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump())


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    error_msgs = "; ".join(f"{err['loc'][-1]}: {err['msg']}" for err in exc.errors())
    logger.warning("Validation rejection on %s: %s", request.url.path, error_msgs)
    return build_error_response("validation_error", error_msgs, status.HTTP_422_UNPROCESSABLE_ENTITY)


@app.exception_handler(SSRFDetectedError)
@app.exception_handler(InvalidTargetURLError)
async def security_url_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.warning("Security rejection on %s: %s", request.url.path, str(exc))
    return build_error_response("security_violation", str(exc), status.HTTP_400_BAD_REQUEST)


@app.exception_handler(PayloadTooLargeError)
async def payload_size_exception_handler(request: Request, exc: PayloadTooLargeError) -> JSONResponse:
    logger.warning("Payload exceeded cap on %s: %s", request.url.path, str(exc))
    return build_error_response("payload_too_large", str(exc), status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled runtime error during %s %s", request.method, request.url.path)
    return build_error_response(
        "internal_server_error",
        "An unexpected error occurred during the technical SEO audit.",
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


# ---------------------------------------------------------
# CPU-BOUND WORKER
# ---------------------------------------------------------
def _process_dom_and_score(html: str, base_url: str, fetch_result: object) -> tuple[AuditReportData, ScoreResult]:
    """Runs synchronous BeautifulSoup and heuristic computations inside worker thread."""
    analyzer = SEOAnalyzer(html=html, base_url=base_url)
    report_data = analyzer.analyze()

    scorer = SEOScorer(report_data=report_data, fetch_result=fetch_result)
    score_result = scorer.calculate()

    return report_data, score_result


# ---------------------------------------------------------
# ENDPOINTS
# ---------------------------------------------------------
@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check() -> HealthResponse:
    return HealthResponse(status="healthy", service=APP_NAME, version=APP_VERSION)


@app.post(
    "/api/audit",
    response_model=AuditResponse,
    status_code=status.HTTP_200_OK,
    tags=["Audit Engine"],
    summary="Execute Technical SEO Audit",
)
async def audit_page(
    payload: AuditRequest,
    crawler: Annotated[SafeAsyncCrawler, Depends(get_crawler)],
) -> AuditResponse:
    target_url = str(payload.url)

    # 1. Non-blocking Network I/O
    fetch_result = await crawler.fetch(target_url)

    # 2 & 3. Offload CPU-bound Parsing & Scoring to Worker Thread
    report_data, score_result = await asyncio.to_thread(
        _process_dom_and_score,
        html=fetch_result.html,
        base_url=fetch_result.final_url,
        fetch_result=fetch_result,
    )

    # 4. API Response Construction
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
