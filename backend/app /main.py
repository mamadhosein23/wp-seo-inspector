# backend/app/main.py

from fastapi import FastAPI, HTTPExcep
from fastapi.middleware.cors import CORSMiddleware

from app.analyzer import analyze_url
from app.http_client import FetchError
from app.schemas import AuditRequest, AuditResponse
from app.security import UnsafeUrlError

app = FastAPI(
    title="WP SEO Inspector API",
    version="1.1.0",
    description="Technical SEO audit API for web pages and WordPress sites.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)


@app.get("/")
def health_check():
    return {
        "message": "WP SEO Inspector API is running",
        "version": "1.1.0",
    }


@app.post("/api/audit", response_model=AuditResponse)
def audit_page(payload: AuditRequest):
    try:
        return analyze_url(str(payload.url))

    except UnsafeUrlError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    except FetchError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while auditing the page.",
        )
