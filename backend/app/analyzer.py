import json
import re

from typing import Any, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup, Comment, NavigableString, Tag
from app.http_client import fetch_html
from app.schemas import AuditResponse, CheckItem
from app.scorer import calculate_score
from app.utils import is_internal_link


TITLE_MIN_LENGTH = 30
TITLE_MAX_LENGTH = 60

META_DESCRIPTION_MIN_LENGTH = 70
META_DESCRIPTION_MAX_LENGTH = 160

MIN_WORD_COUNT = 150

IGNORED_LINK_PREFIXES = ("#", "mailto:", "tel:", "javascript:")

TEXT_EXCLUDED_PARENTS = {
    "script",
    "style",
    "noscript",
    "svg",
    "template",
    "iframe",
}


WORD_PATTERN = re.compile(
    r"[\w\u0600-\u06FF]+(?:[-'’][\w\u0600-\u06FF]+)*",
    re.UNICODE,
)


def normalize_space(value: str) -> str:
    return " ".join(value.split())


def get_attr(tag: Optional[Tag], attr: str, default: Optional[str] = None) -> Optional[str]:
    if not tag:
        return default

    value = tag.get(attr)

    if value is None:
        return default

    if isinstance(value, list):
        value = " ".join(str(item) for item in value)

    return str(value).strip()


def get_meta_content(soup: BeautifulSoup, name: str) -> Optional[str]:
    tag = soup.find(
        "meta",
        attrs={"name": re.compile(rf"^{re.escape(name)}$", re.IGNORECASE)},
    )

    content = get_attr(tag, "content")

    return content or None


def get_title(soup: BeautifulSoup) -> Optional[str]:
    title_tag = soup.find("title")

    if not title_tag:
        return None

    title = normalize_space(title_tag.get_text(" ", strip=True))

    return title or None


def get_canonical_url(soup: BeautifulSoup, base_url: str) -> Optional[str]:
    canonical_tag = soup.find(
        "link",
        attrs={
            "rel": lambda value: value
            and any(str(item).lower() == "canonical" for item in value)
            if isinstance(value, list)
            else str(value).lower() == "canonical"
        },
    )

    href = get_attr(canonical_tag, "href")

    if not href:
        return None

    return urljoin(base_url, href)


def is_visible_text_node(node: NavigableString) -> bool:
    if isinstance(node, Comment):
        return False

    parent = node.parent

    if not parent:
        return False

    if parent.name and parent.name.lower() in TEXT_EXCLUDED_PARENTS:
        return False

    text = str(node).strip()

    return bool(text)


def get_text_content(soup: BeautifulSoup) -> str:
    """
    Extract visible textual content without mutating the original soup.

    مهم:
    این تابع نباید script/style را از soup اصلی حذف کند،
    چون بعداً برای JSON-LD و سایر بررسی‌ها به آن‌ها نیاز داریم.
    """
    text_nodes = soup.find_all(string=True)
    visible_texts = [str(node) for node in text_nodes if is_visible_text_node(node)]

    return normalize_space(" ".join(visible_texts))


def count_words(text: str) -> int:
    return len(WORD_PATTERN.findall(text))


def detect_wordpress(soup: BeautifulSoup, html: str) -> bool:
    html_lower = html.lower()

    generator_content = get_meta_content(soup, "generator") or ""
    generator_content = generator_content.lower()

    wordpress_signals = [
        "wordpress" in generator_content,
        "/wp-content/" in html_lower,
        "/wp-includes/" in html_lower,
        "wp-json" in html_lower,
        "wp-emoji" in html_lower,
        "wp-block-library" in html_lower,
    ]

    return any(wordpress_signals)


def has_open_graph_metadata(soup: BeautifulSoup) -> bool:
    return bool(
        soup.find(
            "meta",
            attrs={"property": re.compile(r"^og:", re.IGNORECASE)},
        )
    )


def has_valid_json_ld(soup: BeautifulSoup) -> bool:
    scripts = soup.find_all(
        "script",
        attrs={
            "type": lambda value: value
            and str(value).lower().strip() == "application/ld+json"
        },
    )

    for script in scripts:
        raw_json = script.string or script.get_text(strip=True)

        if not raw_json:
            continue

        try:
            json.loads(raw_json)
            return True
        except json.JSONDecodeError:
            continue

    return False


def get_heading_counts(soup: BeautifulSoup) -> tuple[int, int]:
    return len(soup.find_all("h1")), len(soup.find_all("h2"))


def analyze_images(soup: BeautifulSoup) -> tuple[int, int]:
    images = soup.find_all("img")
    total_images = len(images)

    images_without_alt = 0

    for image in images:
        alt = image.get("alt")

        if alt is None or not str(alt).strip():
            images_without_alt += 1

    return total_images, images_without_alt


def analyze_links(soup: BeautifulSoup, final_url: str) -> tuple[int, int]:
    internal_links = 0
    external_links = 0

    seen_links: set[str] = set()

    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()

        if not href:
            continue

        if href.lower().startswith(IGNORED_LINK_PREFIXES):
            continue

        absolute_url = urljoin(final_url, href)

        if absolute_url in seen_links:
            continue

        seen_links.add(absolute_url)

        if is_internal_link(absolute_url, final_url):
            internal_links += 1
        else:
            external_links += 1

    return internal_links, external_links


def robots_contains_directive(robots_meta: Optional[str], directive: str) -> bool:
    if not robots_meta:
        return False

    directives = {
        item.strip().lower()
        for item in robots_meta.split(",")
        if item.strip()
    }

    return directive.lower() in directives


def make_check(
    *,
    key: str,
    label: str,
    status: str,
    value: Any = None,
    message: str,
    recommendation: Optional[str] = None,
) -> CheckItem:
    return CheckItem(
        key=key,
        label=label,
        status=status,
        value=value,
        message=message,
        recommendation=recommendation,
    )


def check_title(title: Optional[str]) -> CheckItem:
    if not title:
        return make_check(
            key="title",
            label="Title Tag",
            status="error",
            value=None,
            message="The page does not contain a title tag.",
            recommendation="Add a unique and descriptive title tag.",
        )

    title_length = len(title)

    if TITLE_MIN_LENGTH <= title_length <= TITLE_MAX_LENGTH:
        return make_check(
            key="title",
            label="Title Tag Length",
            status="success",
            value=f"{title_length} characters",
            message="The title length is within the recommended range.",
        )

    return make_check(
        key="title",
        label="Title Tag Length",
        status="warning",
        value=f"{title_length} characters",
        message=(
            f"The title length is outside the recommended "
            f"{TITLE_MIN_LENGTH}–{TITLE_MAX_LENGTH} character range."
        ),
        recommendation=(
            f"Keep the title between {TITLE_MIN_LENGTH} and "
            f"{TITLE_MAX_LENGTH} characters."
        ),
    )


def check_meta_description(meta_description: Optional[str]) -> CheckItem:
    if not meta_description:
        return make_check(
            key="meta_description",
            label="Meta Description",
            status="warning",
            value=None,
            message="No meta description was found.",
            recommendation=(
                f"Add a compelling meta description between "
                f"{META_DESCRIPTION_MIN_LENGTH} and "
                f"{META_DESCRIPTION_MAX_LENGTH} characters."
            ),
        )

    meta_description_length = len(meta_description)

    if META_DESCRIPTION_MIN_LENGTH <= meta_description_length <= META_DESCRIPTION_MAX_LENGTH:
        return make_check(
            key="meta_description",
            label="Meta Description Length",
            status="success",
            value=f"{meta_description_length} characters",
            message="The meta description length is optimized.",
        )

    return make_check(
        key="meta_description",
        label="Meta Description Length",
        status="warning",
        value=f"{meta_description_length} characters",
        message=(
            f"The meta description length is outside the recommended "
            f"{META_DESCRIPTION_MIN_LENGTH}–{META_DESCRIPTION_MAX_LENGTH} "
            f"character range."
        ),
        recommendation=(
            f"Keep the meta description between "
            f"{META_DESCRIPTION_MIN_LENGTH} and "
            f"{META_DESCRIPTION_MAX_LENGTH} characters."
        ),
    )


def check_h1_count(h1_count: int) -> CheckItem:
    if h1_count == 1:
        return make_check(
            key="h1_count",
            label="H1 Heading",
            status="success",
            value=h1_count,
            message="Exactly one H1 heading was found.",
        )

    if h1_count == 0:
        return make_check(
            key="h1_count",
            label="H1 Heading",
            status="error",
            value=h1_count,
            message="No H1 heading was found.",
            recommendation="Add exactly one descriptive H1 heading.",
        )

    return make_check(
        key="h1_count",
        label="H1 Heading",
        status="warning",
        value=h1_count,
        message=f"{h1_count} H1 headings were found.",
        recommendation="Use exactly one primary H1 heading per page.",
    )


def check_word_count(word_count: int) -> CheckItem:
    if word_count < MIN_WORD_COUNT:
        return make_check(
            key="word_count",
            label="Content Length",
            status="warning",
            value=f"{word_count} words",
            message="The page has relatively thin textual content.",
            recommendation="Add useful, original, and topic-focused content.",
        )

    return make_check(
        key="word_count",
        label="Content Length",
        status="success",
        value=f"{word_count} words",
        message="The page contains a reasonable amount of textual content.",
    )


def check_image_alt(total_images: int, images_without_alt: int) -> CheckItem:
    if total_images == 0:
        return make_check(
            key="image_alt",
            label="Image Alt Attributes",
            status="info",
            value="No images found",
            message="No images were detected on the page.",
        )

    if images_without_alt > 0:
        return make_check(
            key="image_alt",
            label="Image Alt Attributes",
            status="warning",
            value=f"{images_without_alt} of {total_images} missing",
            message="One or more images have missing or empty alt attributes.",
            recommendation="Add descriptive alt text to meaningful images.",
        )

    return make_check(
        key="image_alt",
        label="Image Alt Attributes",
        status="success",
        value=f"{total_images} images checked",
        message="All detected images include alt attributes.",
    )


def check_canonical(canonical: Optional[str]) -> CheckItem:
    if not canonical:
        return make_check(
            key="canonical",
            label="Canonical URL",
            status="warning",
            value=None,
            message="No canonical URL was detected.",
            recommendation="Add a self-referencing canonical link element.",
        )

    return make_check(
        key="canonical",
        label="Canonical URL",
        status="success",
        value=canonical,
        message="A canonical URL was detected.",
    )


def check_robots_meta(robots_meta: Optional[str]) -> CheckItem:
    if robots_contains_directive(robots_meta, "noindex"):
        return make_check(
            key="robots",
            label="Robots Meta Tag",
            status="error",
            value=robots_meta,
            message="The page contains a noindex directive.",
            recommendation="Remove noindex if this page should appear in search results.",
        )

    return make_check(
        key="robots",
        label="Robots Meta Tag",
        status="info",
        value=robots_meta or "Not specified",
        message="No noindex directive was detected.",
    )


def check_open_graph(has_open_graph: bool) -> CheckItem:
    return make_check(
        key="open_graph",
        label="Open Graph Metadata",
        status="success" if has_open_graph else "warning",
        value=has_open_graph,
        message=(
            "Open Graph metadata was detected."
            if has_open_graph
            else "Open Graph metadata was not detected."
        ),
        recommendation=(
            None
            if has_open_graph
            else "Add Open Graph tags to improve social media previews."
        ),
    )


def check_structured_data(has_structured_data: bool) -> CheckItem:
    return make_check(
        key="structured_data",
        label="Structured Data",
        status="success" if has_structured_data else "warning",
        value=has_structured_data,
        message=(
            "Valid JSON-LD structured data was detected."
            if has_structured_data
            else "No valid JSON-LD structured data was detected."
        ),
        recommendation=(
            None
            if has_structured_data
            else "Add valid schema markup relevant to the page content."
        ),
    )


def check_wordpress_detection(is_wordpress: bool) -> CheckItem:
    return make_check(
        key="wordpress_detection",
        label="WordPress Detection",
        status="info",
        value=is_wordpress,
        message=(
            "WordPress indicators were detected."
            if is_wordpress
            else "No clear WordPress indicators were detected."
        ),
    )


def build_checks(
    *,
    title: Optional[str],
    meta_description: Optional[str],
    h1_count: int,
    word_count: int,
    total_images: int,
    images_without_alt: int,
    canonical: Optional[str],
    robots_meta: Optional[str],
    has_open_graph: bool,
    has_structured_data: bool,
    is_wordpress: bool,
) -> list[CheckItem]:
    return [
        check_title(title),
        check_meta_description(meta_description),
        check_h1_count(h1_count),
        check_word_count(word_count),
        check_image_alt(total_images, images_without_alt),
        check_canonical(canonical),
        check_robots_meta(robots_meta),
        check_open_graph(has_open_graph),
        check_structured_data(has_structured_data),
        check_wordpress_detection(is_wordpress),
    ]


def analyze_url(url: str) -> AuditResponse:
    fetch_result = fetch_html(url)

    soup = BeautifulSoup(fetch_result.html, "lxml")

    # ---------- Metadata ----------
    title = get_title(soup)
    meta_description = get_meta_content(soup, "description")
    canonical = get_canonical_url(soup, fetch_result.final_url)
    robots_meta = get_meta_content(soup, "robots")

    # ---------- Content ----------
    h1_count, h2_count = get_heading_counts(soup)
    text_content = get_text_content(soup)
    word_count = count_words(text_content)

    # ---------- Images ----------
    total_images, images_without_alt = analyze_images(soup)

    # ---------- Links ----------
    internal_links, external_links = analyze_links(soup, fetch_result.final_url)

    # ---------- Social / Schema / CMS ----------
    has_open_graph = has_open_graph_metadata(soup)
    has_structured_data = has_valid_json_ld(soup)
    is_wordpress = detect_wordpress(soup, fetch_result.html)

    checks = build_checks(
        title=title,
        meta_description=meta_description,
        h1_count=h1_count,
        word_count=word_count,
        total_images=total_images,
        images_without_alt=images_without_alt,
        canonical=canonical,
        robots_meta=robots_meta,
        has_open_graph=has_open_graph,
        has_structured_data=has_structured_data,
        is_wordpress=is_wordpress,
    )

    score = calculate_score(checks)

    return AuditResponse(
        url=url,
        final_url=fetch_result.final_url,
        score=score,
        http_status_code=fetch_result.status_code,
        response_time_ms=fetch_result.response_time_ms,
        content_type=fetch_result.content_type,
        title=title,
        meta_description=meta_description,
        canonical=canonical,
        robots_meta=robots_meta,
        h1_count=h1_count,
        h2_count=h2_count,
        word_count=word_count,
        total_images=total_images,
        images_without_alt=images_without_alt,
        internal_links=internal_links,
        external_links=external_links,
        has_open_graph=has_open_graph,
        has_structured_data=has_structured_data,
        is_wordpress=is_wordpress,
        checks=checks,
    )
