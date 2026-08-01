from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests

from app.schemas import AuditRequest, AuditResponse
from app.analyzer import analyze_page

app = FastAPI(
    title="WP SEO Inspector API",
    version="1.0.0",
    description="SEO audit API for WordPress pages"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # بعداً محدودش می‌کنیم
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "WP SEO Inspector API is running"
    }


@app.post("/api/audit", response_model=AuditResponse)
def audit_page(payload: AuditRequest):
    try:
        result = analyze_page(str(payload.url))
        return result
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"خطا در دریافت صفحه: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطای داخلی سرور: {str(e)}")
