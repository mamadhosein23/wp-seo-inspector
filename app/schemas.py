from datetime import datet

from typing import Literal

from pydantic import BaseModel, Field, HttpUrl

CheckStatus = Literal["success", "warning", "error", "info"]


class AuditRequest(BaseModel):
    url: HttpUrl


class CheckItem(BaseModel):
    key: str
    label: str
    status: CheckStatus
    value: str | int | bool | None = None
    message: str
    recommendation: str | None = None


class MetaInfo(BaseModel):
    """اطلاعات متا و تگ‌های SEO"""

    title: str | None
    meta_description: str | None
    canonical: str | None
    robots_meta: str | None


class ContentStats(BaseModel):
    """آمار محتوای صفحه"""

    h1_count: int
    h2_count: int
    word_count: int


class ImageStats(BaseModel):
    """آمار تصاویر"""

    total_images: int
    images_without_alt: int


class LinkStats(BaseModel):
    """آمار لینک‌ها"""

    internal_links: int
    external_links: int


class AuditResponse(BaseModel):
    """پاسخ کامل آنالیز SEO"""

    url: HttpUrl
    final_url: HttpUrl

    score: int = Field(ge=0, le=100, description="امتیاز کلی SEO از 0 تا 100")

    http_status_code: int
    response_time_ms: int
    content_type: str

    meta: MetaInfo
    content: ContentStats
    images: ImageStats
    links: LinkStats

    has_open_graph: bool
    has_structured_data: bool
    is_wordpress: bool

    checks: list[CheckItem]

    checked_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="زمان اجرای audit به UTC",
    )
