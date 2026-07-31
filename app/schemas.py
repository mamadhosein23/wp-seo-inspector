from pydantic import BaseModel, HttpUrl
from typing import List, Optional


class AuditRequest(BaseModel):
    url: HttpUrl


class CheckItem(BaseModel):
    key: str
    label: str
    status: str  # success | warning | error | info
    value: Optional[str | int | bool] = None
    message: str
    recommendation: Optional[str] = None


class AuditResponse(BaseModel):
    url: str
    final_url: str
    score: int
    title: Optional[str] = None
    meta_description: Optional[str] = None
    h1_count: int
    h2_count: int
    word_count: int
    total_images: int
    images_without_alt: int
    internal_links: int
    external_links: int
    has_canonical: bool
    has_robots_meta: bool
    has_open_graph: bool
    has_structured_data: bool
    checks: List[CheckItem]
