"""WP SEO Inspector - DOM Parsing & Extraction Engine.

Dissects raw HTML documents using BeautifulSoup4 (lxml engine) to extract
20+ technical SEO signals, metadata, heading trees, and semantic structure.
"""

from __future__ import annotations

import json
import re
from typing import Any, Final
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Comment, Tag

from app.schemas import AuditReportData, HeadingStructure, LinkMetrics, MediaMetrics
from app.utils import is_internal_link

# ---------------------------------------------------------
# CONSTANTS & SEO BENCHMARKS
# ---------------------------------------------------------
TITLE_MIN_LENGTH: Final[int] = 30
TITLE_MAX_LENGTH: Final[int] = 60

META_DESC_MIN_LENGTH: Final[int] = 70
META_DESC_MAX_LENGTH: Final[int] = 160

MIN_WORD_COUNT: Final[int] = 300

IGNORED_LINK_SCHEMES: Final[tuple[str, ...]] = (
    "#",
    "mailto:",
    "tel:",
    "javascript:",
    "data:",
    "whatsapp:",
)

NON_CONTENT_TAGS: Final[set[str]] = {
    "script",
    "style",
    "noscript",
    "svg",
    "template",
    "iframe",
    "header",
    "footer",
    "nav",
}

WORD_REGEX: Final[re.Pattern[str]] = re.compile(
    r"[\w\u0600-\u06FF]+(?:[-'’][\w\u0600-\u06FF]+)*",
    re.UNICODE,
)


class SEOAnalyzer:
    """High-performance DOM analysis engine."""

    def __init__(self, html: str, base_url: str) -> None:
        self.raw_html: str = html
        self.base_url: str = base_url
        self.soup: BeautifulSoup = BeautifulSoup(html, "lxml")

    # -----------------------------------------------------
    # Utility Helpers
    # -----------------------------------------------------
    @staticmethod
    def _normalize_space(text: str | None) -> str:
        return " ".join(text.split()) if text else ""

    @staticmethod
    def _get_attr(tag: Tag | None, attr: str) -> str | None:
        if not tag:
            return None
        val = tag.get(attr)
        if val is None:
            return None
        if isinstance(val, list):
            return " ".join(str(item) for item in val).strip()
        return str(val).strip()

    # -----------------------------------------------------
    # Metadata Extractors
    # -----------------------------------------------------
    def extract_title(self) -> str | None:
        title_tag = self.soup.find("title")
        if not title_tag:
            return None
        title_text = self._normalize_space(title_tag.get_text())
        return title_text or None

    def extract_meta_content(self, name_or_prop: str, is_property: bool = False) -> str | None:
        attr_key = "property" if is_property else "name"
        tag = self.soup.find(
            "meta",
            attrs={attr_key: re.compile(rf"^{re.escape(name_or_prop)}$", re.IGNORECASE)},
        )
        content = self._get_attr(tag, "content")
        return self._normalize_space(content) or None

    def extract_canonical(self) -> str | None:
        link_tag = self.soup.find(
            "link",
            attrs={
                "rel": lambda val: (
                    any(str(item).lower() == "canonical" for item in val)
                    if isinstance(val, list)
                    else str(val).lower() == "canonical"
                )
            },
        )
        href = self._get_attr(link_tag, "href")
        return urljoin(self.base_url, href) if href else None

    # -----------------------------------------------------
    # Structure & Content
    # -----------------------------------------------------
    def extract_headings(self) -> HeadingStructure:
        headings_map: dict[str, list[str]] = {f"h{i}": [] for i in range(1, 7)}

        for tag in self.soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
            text = self._normalize_space(tag.get_text())
            headings_map[tag.name.lower()].append(text)

        return HeadingStructure(
            h1_count=len(headings_map["h1"]),
            h2_count=len(headings_map["h2"]),
            h3_count=len(headings_map["h3"]),
            h4_count=len(headings_map["h4"]),
            h5_count=len(headings_map["h5"]),
            h6_count=len(headings_map["h6"]),
            h1_contents=headings_map["h1"],
        )

    def extract_text_and_word_count(self) -> tuple[str, int]:
        # استخراج کل استرینگ‌ها با حذف کامل تمام اجداد نامربوط (نه فقط والد مستقیم)
        visible_chunks: list[str] = []

        for element in self.soup.find_all(string=True):
            if isinstance(element, Comment):
                continue
            # بررسی کل زنجیره والدین برای تضمین عدم وجود در هدر، فوتر، اسکریپت و...
            parent_names = {parent.name.lower() for parent in element.parents if parent and parent.name}
            if parent_names.intersection(NON_CONTENT_TAGS):
                continue

            cleaned = element.strip()
            if cleaned:
                visible_chunks.append(cleaned)

        raw_text = " ".join(visible_chunks)
        normalized_text = self._normalize_space(raw_text)
        word_count = len(WORD_REGEX.findall(normalized_text))
        return normalized_text, word_count

    # -----------------------------------------------------
    # Media & Links
    # -----------------------------------------------------
    def extract_media(self) -> MediaMetrics:
        images = self.soup.find_all("img")
        missing_alt = 0
        empty_alt = 0

        for img in images:
            alt = img.get("alt")
            if alt is None:
                missing_alt += 1
            elif not str(alt).strip():
                empty_alt += 1

        return MediaMetrics(
            total_images=len(images),
            missing_alt=missing_alt,
            empty_alt=empty_alt,
        )

    def extract_links(self) -> LinkMetrics:
        internal_count = 0
        external_count = 0
        nofollow_count = 0
        unique_links: set[str] = set()

        for anchor in self.soup.find_all("a", href=True):
            raw_href = anchor["href"].strip()
            if not raw_href or raw_href.lower().startswith(IGNORED_LINK_SCHEMES):
                continue

            abs_url = urljoin(self.base_url, raw_href)
            if abs_url in unique_links:
                continue
            unique_links.add(abs_url)

            rel_attr = anchor.get("rel", [])
            rel_list = rel_attr if isinstance(rel_attr, list) else rel_attr.split()
            if any(str(r).lower() == "nofollow" for r in rel_list):
                nofollow_count += 1

            if is_internal_link(abs_url, self.base_url):
                internal_count += 1
            else:
                external_count += 1

        return LinkMetrics(
            internal_links=internal_count,
            external_links=external_count,
            nofollow_links=nofollow_count,
            total_unique_links=len(unique_links),
        )

    # -----------------------------------------------------
    # Technical & Advanced Signals
    # -----------------------------------------------------
    def extract_social_graph(self) -> dict[str, bool]:
        og_title = self.extract_meta_content("og:title", is_property=True)
        og_desc = self.extract_meta_content("og:description", is_property=True)
        og_image = self.extract_meta_content("og:image", is_property=True)
        tw_card = self.extract_meta_content("twitter:card")

        return {
            "has_open_graph": bool(og_title or og_desc or og_image),
            "has_twitter_card": bool(tw_card),
        }

    def extract_json_ld_schemas(self) -> list[dict[str, Any]]:
        schemas: list[dict[str, Any]] = []
        script_tags = self.soup.find_all(
            "script",
            attrs={"type": lambda v: bool(v and str(v).lower().strip() == "application/ld+json")},
        )
        for script in script_tags:
            content = script.string or script.get_text(strip=True)
            if not content:
                continue
            try:
                parsed = json.loads(content)
                if isinstance(parsed, dict):
                    # مدیریت اسکیماهای تو در تو و ساختار Yoast / RankMath
                    if "@graph" in parsed and isinstance(parsed["@graph"], list):
                        schemas.extend(item for item in parsed["@graph"] if isinstance(item, dict))
                    else:
                        schemas.append(parsed)
                elif isinstance(parsed, list):
                    schemas.extend(item for item in parsed if isinstance(item, dict))
            except (json.JSONDecodeError, TypeError):
                continue
        return schemas

    def detect_wordpress(self) -> bool:
        html_lower = self.raw_html.lower()
        generator = (self.extract_meta_content("generator") or "").lower()

        signals = [
            "wordpress" in generator,
            "/wp-content/" in html_lower,
            "/wp-includes/" in html_lower,
            "wp-json" in html_lower,
            "wp-emoji" in html_lower,
            "wp-block-library" in html_lower,
        ]
        return any(signals)

    # -----------------------------------------------------
    # Main Execution Method
    # -----------------------------------------------------
    def analyze(self) -> AuditReportData:
        """Executes full DOM parsing and returns structured metrics."""
        schemas = self.extract_json_ld_schemas()
        social = self.extract_social_graph()
        _, word_count = self.extract_text_and_word_count()

        # استخراج ساختاریافته تایپ‌های JSON-LD
        schema_types: list[str] = []
        for s in schemas:
            schema_type = s.get("@type")
            if isinstance(schema_type, str):
                schema_types.append(schema_type)
            elif isinstance(schema_type, list):
                schema_types.extend(str(t) for t in schema_type)

        return AuditReportData(
            title=self.extract_title(),
            meta_description=self.extract_meta_content("description"),
            canonical=self.extract_canonical(),
            robots_meta=self.extract_meta_content("robots"),
            headings=self.extract_headings(),
            word_count=word_count,
            media=self.extract_media(),
            links=self.extract_links(),
            has_open_graph=social["has_open_graph"],
            has_twitter_card=social["has_twitter_card"],
            has_structured_data=bool(schemas),
            structured_data_types=schema_types,
            is_wordpress=self.detect_wordpress(),
        )
