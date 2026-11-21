"""WP SEO Inspector - DOM Parsing & Extraction Engine.

Dissects raw HTML documents using BeautifulSoup4 (lxml engine) to extract
technical SEO signals, metadata, heading trees, and semantic structure.
"""

from __future__ import annotations

import json
import re
from typing import Any, Final
from urllib.parse import urldefrag, urljoin, urlsplit

from bs4 import BeautifulSoup, Tag

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
    "mailto",
    "tel",
    "javascript",
    "data",
    "whatsapp",
    "sms",
    "blob",
    "about",
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
    "aside",
}

WORD_REGEX: Final[re.Pattern[str]] = re.compile(
    r"[\w\u0600-\u06FF\u200c]+(?:[-'’][\w\u0600-\u06FF\u200c]+)*",
    re.UNICODE,
)

JSON_LD_COMMENT_REGEX: Final[re.Pattern[str]] = re.compile(
    r"^\s*(?:<!--|/\*|//)?\s*|\s*(?:-->|\\*/)\s*$",
    re.MULTILINE,
)


class SEOAnalyzer:
    """DOM analysis engine for technical SEO signals."""

    def __init__(self, html: str, base_url: str) -> None:
        self.raw_html = html
        self.base_url = base_url
        self.soup = BeautifulSoup(html, "lxml")

    # -----------------------------------------------------
    # Utility Helpers
    # -----------------------------------------------------
    @staticmethod
    def _normalize_space(text: str | None) -> str:
        return " ".join(text.split()) if text else ""

    @staticmethod
    def _get_attr(tag: Tag | None, attr: str) -> str | None:
        if tag is None:
            return None

        value = tag.get(attr)
        if value is None:
            return None

        if isinstance(value, list):
            return " ".join(str(item) for item in value).strip()

        return str(value).strip()

    @staticmethod
    def _get_rel_values(tag: Tag) -> set[str]:
        """Returns normalized link-rel tokens."""
        rel = tag.get("rel", [])

        if isinstance(rel, str):
            return {item.lower() for item in rel.split() if item}

        if isinstance(rel, list):
            return {str(item).lower() for item in rel if str(item).strip()}

        return set()

    def _normalize_link_url(self, raw_href: str) -> str | None:
        """Resolve a link and remove its fragment for unique-link metrics."""
        href = raw_href.strip()

        if not href or href.startswith("#"):
            return None

        parsed = urlsplit(href)
        if parsed.scheme.lower() in IGNORED_LINK_SCHEMES:
            return None

        absolute_url = urljoin(self.base_url, href)
        absolute_parts = urlsplit(absolute_url)

        # Links such as ftp:, file:, or malformed relative values are not crawlable
        # web links for this audit.
        if absolute_parts.scheme.lower() not in {"http", "https"}:
            return None

        normalized_url, _ = urldefrag(absolute_url)
        return normalized_url

    # -----------------------------------------------------
    # Metadata Extractors
    # -----------------------------------------------------
    def extract_title(self) -> str | None:
        title_tag = self.soup.find("title")
        if title_tag is None:
            return None

        title = self._normalize_space(title_tag.get_text(" ", strip=True))
        return title or None

    def extract_meta_content(
        self,
        name_or_prop: str,
        *,
        is_property: bool = False,
    ) -> str | None:
        attr_key = "property" if is_property else "name"

        tag = self.soup.find(
            "meta",
            attrs={
                attr_key: re.compile(
                    rf"^{re.escape(name_or_prop)}$",
                    re.IGNORECASE,
                )
            },
        )

        content = self._get_attr(tag, "content")
        return self._normalize_space(content) or None

    def extract_canonical(self) -> str | None:
        for link_tag in self.soup.find_all("link", href=True):
            if "canonical" not in self._get_rel_values(link_tag):
                continue

            href = self._get_attr(link_tag, "href")
            if href:
                return urljoin(self.base_url, href)

        return None

    # -----------------------------------------------------
    # Structure & Content
    # -----------------------------------------------------
    def extract_headings(self) -> HeadingStructure:
        headings_map: dict[str, list[str]] = {
            f"h{level}": [] for level in range(1, 7)
        }

        for tag in self.soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
            tag_name = (tag.name or "").lower()
            if tag_name not in headings_map:
                continue

            headings_map[tag_name].append(
                self._normalize_space(tag.get_text(" ", strip=True))
            )

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
        """Extract visible page text without mutating the original DOM."""
        body = self.soup.body or self.soup
        content_soup = BeautifulSoup(str(body), "lxml")

        for tag in content_soup.find_all(NON_CONTENT_TAGS):
            tag.decompose()

        text = content_soup.get_text(separator=" ", strip=True)
        normalized_text = self._normalize_space(text)

        return normalized_text, len(WORD_REGEX.findall(normalized_text))

    # -----------------------------------------------------
    # Media & Links
    # -----------------------------------------------------
    def extract_media(self) -> MediaMetrics:
        images = self.soup.find_all("img")
        missing_alt = 0
        empty_alt = 0

        for image in images:
            alt = image.get("alt")

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
            raw_href = str(anchor["href"])
            absolute_url = self._normalize_link_url(raw_href)

            if absolute_url is None or absolute_url in unique_links:
                continue

            unique_links.add(absolute_url)

            if "nofollow" in self._get_rel_values(anchor):
                nofollow_count += 1

            if is_internal_link(absolute_url, self.base_url):
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
        og_description = self.extract_meta_content(
            "og:description",
            is_property=True,
        )
        og_image = self.extract_meta_content("og:image", is_property=True)

        # In the wild, Twitter tags appear both as name= and property=.
        twitter_card = (
            self.extract_meta_content("twitter:card")
            or self.extract_meta_content("twitter:card", is_property=True)
        )

        return {
            "has_open_graph": bool(og_title or og_description or og_image),
            "has_twitter_card": bool(twitter_card),
        }

    @staticmethod
    def _clean_json_ld(content: str) -> str:
        """Remove common HTML/comment wrappers around JSON-LD blocks."""
        cleaned = content.strip()

        if cleaned.startswith("<!--"):
            cleaned = cleaned[4:]
        if cleaned.endswith("-->"):
            cleaned = cleaned[:-3]

        if cleaned.startswith("<![CDATA["):
            cleaned = cleaned[9:]
        if cleaned.endswith("]]>"):
            cleaned = cleaned[:-3]

        return cleaned.strip()

    def extract_json_ld_schemas(self) -> list[dict[str, Any]]:
        schemas: list[dict[str, Any]] = []

        script_tags = self.soup.find_all(
            "script",
            attrs={
                "type": lambda value: bool(
                    value
                    and str(value).lower().strip() == "application/ld+json"
                )
            },
        )

        for script in script_tags:
            raw_content = script.string or script.get_text()
            if not raw_content:
                continue

            try:
                parsed = json.loads(self._clean_json_ld(str(raw_content)))
            except (json.JSONDecodeError, TypeError):
                continue

            if isinstance(parsed, dict):
                graph = parsed.get("@graph")
                if isinstance(graph, list):
                    schemas.extend(item for item in graph if isinstance(item, dict))
                else:
                    schemas.append(parsed)

            elif isinstance(parsed, list):
                schemas.extend(item for item in parsed if isinstance(item, dict))

        return schemas

    def detect_wordpress(self) -> bool:
        html_lower = self.raw_html.lower()
        generator = (self.extract_meta_content("generator") or "").lower()

        return any(
            (
                "wordpress" in generator,
                "/wp-content/" in html_lower,
                "/wp-includes/" in html_lower,
                "wp-json" in html_lower,
                "wp-emoji" in html_lower,
                "wp-block-library" in html_lower,
            )
        )

    # -----------------------------------------------------
    # Main Execution Method
    # -----------------------------------------------------
    def analyze(self) -> AuditReportData:
        """Execute full DOM parsing and return structured SEO metrics."""
        schemas = self.extract_json_ld_schemas()
        social = self.extract_social_graph()
        _, word_count = self.extract_text_and_word_count()

        schema_types: list[str] = []
        seen_schema_types: set[str] = set()

        for schema in schemas:
            raw_type = schema.get("@type")

            if isinstance(raw_type, str):
                types = [raw_type]
            elif isinstance(raw_type, list):
                types = [item for item in raw_type if isinstance(item, str)]
            else:
                types = []

            for schema_type in types:
                if schema_type not in seen_schema_types:
                    seen_schema_types.add(schema_type)
                    schema_types.append(schema_type)

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
