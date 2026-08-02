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


class AuditResponse(BaseModel):
    url: str
    final_url: str

    score: int = Field(ge=0, le=100)

    http_status_code: int
    response_time_ms: int
    content_type: str

    title: str | None
    meta_description: str | None
    canonical: str | None
    robots_meta: str | None

    h1_count: int
    h2_count: int
    word_count: int

    total_images: int
    images_without_alt: int

    internal_links: int
    external_links: int

    has_open_graph: bool
    has_structured_data: bool
    is_wordpress: bool

    checks: list[CheckItem]
