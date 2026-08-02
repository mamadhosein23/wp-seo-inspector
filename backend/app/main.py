import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.analyzer import analyze_url
from app.http_client import FetchError
from app.schemas import AuditRequest, AuditResponse
from app.security import UnsafeUrlError

APP_NAME = "WP SEO Inspector API"
APP_VERSION = "1.1.0"
APP_DESCRIPTION = "Technical SEO audit API for web pages and WordPress sites."

logger = logging.getLogger(__name__)


def get_allowed_origins() -> list[str]:
    raw_origins = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    )
    return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("%s v%s is starting...", APP_NAME, APP_VERSION)
    yield
    logger.info("%s is shutting down...", APP_NAME)


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.exception_handler(UnsafeUrlError)
async def unsafe_url_exception_handler(request: Request, exc: UnsafeUrlError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": {
                "type": "unsafe_url",
                "message": str(exc),
            }
        },
    )


@app.exception_handler(FetchError)
async def fetch_error_exception_handler(request: Request, exc: FetchError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "type": "fetch_error",
                "message": str(exc),
            }
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error while processing request: %s", request.url.path)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": "internal_server_error",
                "message": "An unexpected error occurred while auditing the page.",
            }
        },
    )


@app.get(
    "/",
    tags=["System"],
    summary="Root endpoint",
)
def root():
    return {
        "message": f"{APP_NAME} is running",
        "version": APP_VERSION,
        "docs": "/docs",
    }


@app.get(
    "/health",
    tags=["System"],
    summary="Health check",
)
def health_check():
    return {
        "status": "ok",
        "service": APP_NAME,
        "version": APP_VERSION,
    }


@app.post(
    "/api/audit",
    response_model=AuditResponse,
    status_code=status.HTTP_200_OK,
    tags=["Audit"],
    summary="Audit a web page",
    description="Fetches a target URL and returns a structured technical SEO audit report.",
)
def audit_page(payload: AuditRequest):
    return analyze_url(str(payload.url))
