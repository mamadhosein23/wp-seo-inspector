"""
WP SEO Inspector - DOM Parsing & Extraction Engine.

Dissects raw HTML documents using BeautifulSoup4 (lxml engine) to extract
20+ technical SEO signals, metadata, heading trees, and semantic structure.
"""

from __future__ import annotations

import json
import re
from typing import Any, Final, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Comment, NavigableString, Tag

from app.schemas import AuditReportData, CheckItem, HeadingStructure, LinkMetrics, MediaMetrics
from app.utils import is_internal_link

# ---------------------------------------------------------
# CONSTANTS & SEO BENCHMARKS
# ---------------------------------------------------------
TITLE_MIN_LENGTH: Final[int] = 30
TITLE_MAX_LENGTH: Final[int] = 60

META_DESC_MIN_LENGTH: Final[int] = 70
META_DESC_MAX_LENGTH: Final[int] = 160

MIN_WORD_COUNT: Final[int] = 300

IGNORED_LINK_SCHEMES: Final[Tuple[str, ...]] = (
    "#",
    "mailto:",
    "tel:",
    "javascript:",
    "data:",
    "whatsapp:",
)

NON_CONTENT_TAGS: Final[Set[str]] = {
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

# Regex for Persian / Arabic / Latin word counting
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
    def _normalize_space(text: Optional[str]) -> str:
        if not text:
            return ""
        return " ".join(text.split())

    @staticmethod
    def _get_attr(tag: Optional[Tag], attr: str) -> Optional[str]:
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
    def extract_title(self) -> Optional[str]:
        title_tag = self.soup.find("title")
        if not title_tag:
            return None
        title_text = self._normalize_space(title_tag.get_text())
        return title_text or None

    def extract_meta_content(self, name_or_prop: str, is_property: bool = False) -> Optional[str]:
        attr_key = "property" if is_property else "name"
        tag = self.soup.find(
            "meta",
            attrs={attr_key: re.compile(rf"^{re.escape(name_or_prop)}$", re.IGNORECASE)},
        )
        content = self._get_attr(tag, "content")
        return self._normalize_space(content) or None

    def extract_canonical(self) -> Optional[str]:
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
        if not href:
            return None
        return urljoin(self.base_url, href)

    # -----------------------------------------------------
    # Structure & Content
    # -----------------------------------------------------
    def extract_headings(self) -> HeadingStructure:
        h1_tags = [self._normalize_space(t.get_text()) for t in self.soup.find_all("h1")]
        h2_tags = [self._normalize_space(t.get_text()) for t in self.soup.find_all("h2")]
        h3_tags = [self._normalize_space(t.get_text()) for t in self.soup.find_all("h3")]
        h4_tags = [self._normalize_space(t.get_text()) for t in self.soup.find_all("h4")]
        h5_tags = [self._normalize_space(t.get_text()) for t in self.soup.find_all("h5")]
        h6_tags = [self._normalize_space(t.get_text()) for t in self.soup.find_all("h6")]

        return HeadingStructure(
            h1_count=len(h1_tags),
            h2_count=len(h2_tags),
            h3_count=len(h3_tags),
            h4_count=len(h4_tags),
            h5_count=len(h5_tags),
            h6_count=len(h6_tags),
            h1_contents=h1_tags,
        )

    def extract_text_and_word_count(self) -> Tuple[str, int]:
        # Shallow copy or selective traversal without mutating soup
        visible_chunks: List[str] = []
        for element in self.soup.find_all(string=True):
            if isinstance(element, Comment):
                continue
            parent = element.parent
            if parent and parent.name and parent.name.lower() in NON_CONTENT_TAGS:
                continue
            cleaned = str(element).strip()
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
        total = len(images)
        missing_alt = 0
        empty_alt = 0

        for img in images:
            alt = img.get("alt")
            if alt is None:
                missing_alt += 1
            elif not str(alt).strip():
                empty_alt += 1

        return MediaMetrics(
            total_images=total,
            missing_alt=missing_alt,
            empty_alt=empty_alt,
        )

    def extract_links(self) -> LinkMetrics:
        internal_count = 0
        external_count = 0
        nofollow_count = 0
        unique_links: Set[str] = set()

        for anchor in self.soup.find_all("a", href=True):
            raw_href = anchor["href"].strip()
            if not raw_href or raw_href.lower().startswith(IGNORED_LINK_SCHEMES):
                continue

            abs_url = urljoin(self.base_url, raw_href)
            if abs_url in unique_links:
                continue
            unique_links.add(abs_url)

            rel_list = anchor.get("rel", [])
            if isinstance(rel_list, str):
                rel_list = rel_list.split()
            if "nofollow" in [r.lower() for r in rel_list]:
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

    def extract_json_ld_schemas(self) -> List[dict[str, Any]]:
        schemas: List[dict[str, Any]] = []
        script_tags = self.soup.find_all(
            "script",
            attrs={"type": lambda v: v and str(v).lower().strip() == "application/ld+json"},
        )
        for script in script_tags:
            content = script.string or script.get_text(strip=True)
            if not content:
                continue
            try:
                parsed = json.loads(content)
                if isinstance(parsed, dict):
                    schemas.append(parsed)
                elif isinstance(parsed, list):
                    schemas.extend([item for item in parsed if isinstance(item, dict)])
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
        title = self.extract_title()
        meta_description = self.extract_meta_content("description")
        canonical = self.extract_canonical()
        robots_meta = self.extract_meta_content("robots")

        headings = self.extract_headings()
        _, word_count = self.extract_text_and_word_count()
        media = self.extract_media()
        links = self.extract_links()
        social = self.extract_social_graph()
        schemas = self.extract_json_ld_schemas()
        is_wp = self.detect_wordpress()

        return AuditReportData(
            title=title,
            meta_description=meta_description,
            canonical=canonical,
            robots_meta=robots_meta,
            headings=headings,
            word_count=word_count,
            media=media,
            links=links,
            has_open_graph=social["has_open_graph"],
            has_twitter_card=social["has_twitter_card"],
            has_structured_data=bool(schemas),
            structured_data_types=[s.get("@type", "Unknown") for s in schemas if "@type" in s],
            is_wordpress=is_wp,
        )
