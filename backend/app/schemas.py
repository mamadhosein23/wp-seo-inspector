from datetime import datetime, timezone
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
    penalty: int = 0


class MetaInfo(BaseModel):
    title: str | None = None
    meta_description: str | None = None
    canonical: str | None = None
    robots_meta: str | None = None


class ContentStats(BaseModel):
    h1_count: int = 0
    h2_count: int = 0
    word_count: int = 0


class ImageStats(BaseModel):
    total_images: int = 0
    images_without_alt: int = 0


class LinkStats(BaseModel):
    internal_links: int = 0
    external_links: int = 0


class AuditResponse(BaseModel):
    url: HttpUrl
    final_url: HttpUrl

    score: int = Field(ge=0, le=100, description="SEO score from 0 to 100")

    http_status_code: int
    response_time_ms: int
    content_type: str

    meta: MetaInfo
    content: ContentStats
    images: ImageStats
    links: LinkStats

    has_open_graph: bool = False
    has_structured_data: bool = False
    is_wordpress: bool = False

    checks: list[CheckItem] = Field(default_factory=list)

    checked_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Audit execution time in UTC",
    )
