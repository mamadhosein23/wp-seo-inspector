from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

CheckStatus = Literal["success", "warning", "error", "info"]
CheckCategory = Literal[
    "indexability", "structure", "metadata", "accessibility", "social"
]


class AuditRequest(BaseModel):
    url: HttpUrl = Field(
        ...,
        description="Target URL to run technical SEO audit on",
        examples=["https://example.com"],
    )


class CheckItem(BaseModel):
    key: str = Field(..., description="Unique machine-readable identifier")
    label: str = Field(..., description="Human-readable title")
    category: CheckCategory = Field(
        ..., description="Metric category for UI grouping"
    )
    status: CheckStatus
    value: Any | None = Field(
        default=None, description="Extracted dynamic value"
    )
    message: str = Field(..., description="Diagnostic summary")
    recommendation: str | None = Field(
        default=None, description="Actionable fix recommendation"
    )
    penalty: int = Field(
        default=0, ge=0, description="Deducted points from overall score"
    )


class MetaInfo(BaseModel):
    title: str | None = None
    title_length: int = Field(default=0, ge=0)
    meta_description: str | None = None
    description_length: int = Field(default=0, ge=0)
    canonical_url: str | None = None
    robots_meta: str | None = None
    has_viewport: bool = False
    charset: str | None = None


class SocialGraphInfo(BaseModel):
    has_open_graph: bool = False
    og_title: str | None = None
    og_description: str | None = None
    og_image: str | None = None
    has_twitter_card: bool = False
    twitter_card_type: str | None = None


class ContentStats(BaseModel):
    h1_count: int = Field(default=0, ge=0)
    h2_count: int = Field(default=0, ge=0)
    h3_count: int = Field(default=0, ge=0)
    h1_contents: list[str] = Field(default_factory=list)
    word_count: int = Field(default=0, ge=0)


class ImageStats(BaseModel):
    total_images: int = Field(default=0, ge=0)
    images_without_alt: int = Field(default=0, ge=0)
    images_missing_dimensions: int = Field(default=0, ge=0)


class LinkStats(BaseModel):
    internal_links: int = Field(default=0, ge=0)
    external_links: int = Field(default=0, ge=0)
    broken_links_detected: int = Field(default=0, ge=0)


class TechnicalSignals(BaseModel):
    is_wordpress: bool = False
    has_structured_data: bool = False
    structured_data_types: list[str] = Field(default_factory=list)
    is_https: bool = True
    content_encoding: str | None = None


class AuditResponse(BaseModel):
    model_config = ConfigDict(ser_json_timedelta="iso8601")

    url: str = Field(..., description="Original requested URL")
    final_url: str = Field(..., description="Resolved destination URL")

    score: int = Field(ge=0, le=100, description="Deductive SEO health score")

    http_status_code: int = Field(..., ge=100, le=599)
    response_time_ms: int = Field(
        ..., ge=0, description="Server response latency in milliseconds"
    )
    content_type: str

    meta: MetaInfo
    social: SocialGraphInfo
    content: ContentStats
    images: ImageStats
    links: LinkStats
    technical: TechnicalSignals

    checks: list[CheckItem] = Field(default_factory=list)

    checked_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Audit execution timestamp in UTC",
    )
