"""WP SEO Inspector - FastAPI application entry point."""

from __future__ import annotations

import logging
import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated, Final

from fastapi import Depends, FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.http_client import SafeAsyncCrawler
from app.schemas import (
    AuditErrorDetail,
    AuditErrorResponse,
    AuditRequest,
    AuditResponse,
    HealthResponse,
)
from app.security import (
    InvalidTargetURLError,
    PayloadTooLargeError,
    SSRFDetectedError,
)
from app.services.audit_service import AuditService


APP_NAME: Final = "WP SEO Inspector API"
APP_VERSION: Final = "1.2.0"
APP_DESCRIPTION: Final = (
    "High-Performance Technical SEO Audit & Heuristic Scoring Engine"
)

DEFAULT_ALLOWED_ORIGINS: Final = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
)


logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("wp_seo_inspector")


def get_allowed_origins() -> list[str]:
    """Read comma-separated CORS origins from the environment."""
    raw = os.getenv("ALLOWED_ORIGINS", "")

    if not raw.strip():
        return list(DEFAULT_ALLOWED_ORIGINS)

    return [
        origin.strip().rstrip("/")
        for origin in raw.split(",")
        if origin.strip()
    ]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Keep one crawler per API process and close it on shutdown."""
    logger.info("Starting %s v%s", APP_NAME, APP_VERSION)

    crawler = SafeAsyncCrawler()
    app.state.crawler = crawler

    try:
        yield
    finally:
        await crawler.close()
        logger.info("HTTP crawler closed")


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
    """Provide the crawler owned by the application lifespan."""
    return request.app.state.crawler


def get_audit_service(
    crawler: Annotated[SafeAsyncCrawler, Depends(get_crawler)],
) -> AuditService:
    """Construct a lightweight service using the shared crawler."""
    return AuditService(crawler)


def build_error_response(
    error_type: str,
    message: str,
    status_code: int,
) -> JSONResponse:
    payload = AuditErrorResponse(
        error=AuditErrorDetail(
            type=error_type,
            message=message,
        )
    )

    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump(mode="json"),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Return validation errors in the project's standard error format."""
    messages = []

    for error in exc.errors():
        location = ".".join(str(part) for part in error["loc"])
        messages.append(f"{location}: {error['msg']}")

    message = "; ".join(messages)

    logger.warning(
        "Validation rejection on %s: %s",
        request.url.path,
        message,
    )

    return build_error_response(
        error_type="validation_error",
        message=message,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


@app.exception_handler(SSRFDetectedError)
@app.exception_handler(InvalidTargetURLError)
async def security_url_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.warning(
        "Rejected target on %s: %s",
        request.url.path,
        exc,
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
        "Payload limit exceeded on %s: %s",
        request.url.path,
        exc,
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
        "Unhandled error during %s %s",
        request.method,
        request.url.path,
    )

    return build_error_response(
        error_type="internal_server_error",
        message="An unexpected error occurred during the technical SEO audit.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Service Health Check",
)
async def health_check() -> HealthResponse:
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
)
async def audit_page(
    payload: AuditRequest,
    service: Annotated[AuditService, Depends(get_audit_service)],
) -> AuditResponse:
    """Execute a single-page audit without changing the existing API."""
    return await service.run(str(payload.url))
