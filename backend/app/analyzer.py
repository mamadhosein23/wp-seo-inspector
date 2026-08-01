# backend/app/analyzer.py

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.http_client import fetch_html
from app.schemas import AuditResponse, CheckItem
from app.scorer import calculate_score
from app.utils import is_internal_link


def get_text_content(soup: BeautifulSoup) -> str:
    for element in soup(["script", "style", "noscript", "svg"]):
        element.decompose()

    return " ".join(soup.get_text(" ", strip=True).split())


def detect_wordpress(soup: BeautifulSoup, html: str) -> bool:
    generator = soup.find("meta", attrs={"name": "generator"})
    generator_content = generator.get("content", "").lower() if generator else ""

    wordpress_signals = [
        "wordpress" in generator_content,
        "/wp-content/" in html.lower(),
        "/wp-includes/" in html.lower(),
    ]

    return any(wordpress_signals)


def analyze_url(url: str) -> AuditResponse:
    fetch_result = fetch_html(url)

    soup = BeautifulSoup(fetch_result.html, "lxml")
    checks: list[CheckItem] = []

    # ---------- Metadata ----------
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else None
    title_length = len(title) if title else 0

    meta_description_tag = soup.find(
        "meta",
        attrs={"name": re.compile(r"^description$", re.IGNORECASE)},
    )
    meta_description = (
        meta_description_tag.get("content", "").strip()
        if meta_description_tag
        else None
    )
    meta_description_length = len(meta_description) if meta_description else 0

    canonical_tag = soup.find(
        "link",
        attrs={"rel": lambda value: value and "canonical" in value},
    )
    canonical = (
        urljoin(fetch_result.final_url, canonical_tag.get("href", ""))
        if canonical_tag and canonical_tag.get("href")
        else None
    )

    robots_tag = soup.find(
        "meta",
        attrs={"name": re.compile(r"^robots$", re.IGNORECASE)},
    )
    robots_meta = robots_tag.get("content", "").strip() if robots_tag else None

    # ---------- Content ----------
    h1_count = len(soup.find_all("h1"))
    h2_count = len(soup.find_all("h2"))

    text_content = get_text_content(soup)
    word_count = len(re.findall(r"\b[\w'-]+\b", text_content))

    # ---------- Images ----------
    images = soup.find_all("img")
    total_images = len(images)
    images_without_alt = sum(
        1
        for image in images
        if image.get("alt") is None or not image.get("alt", "").strip()
    )

    # ---------- Links ----------
    internal_links = 0
    external_links = 0

    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()

        if href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue

        if is_internal_link(href, fetch_result.final_url):
            internal_links += 1
        else:
            external_links += 1

    # ---------- Open Graph and structured data ----------
    has_open_graph = bool(
        soup.find("meta", attrs={"property": re.compile(r"^og:", re.IGNORECASE)})
    )

    has_structured_data = bool(
        soup.find("script", attrs={"type": "application/ld+json"})
    )

    is_wordpress = detect_wordpress(soup, fetch_result.html)

    # ---------- Audit Rules ----------
    if not title:
        checks.append(
            CheckItem(
                key="title",
                label="Title Tag",
                status="error",
                value=None,
                message="The page does not contain a title tag.",
                recommendation="Add a unique and descriptive title tag.",
            )
        )
    elif 30 <= title_length <= 60:
        checks.append(
            CheckItem(
                key="title",
                label="Title Tag Length",
                status="success",
                value=f"{title_length} characters",
                message="The title length is within the recommended range.",
            )
        )
    else:
        checks.append(
            CheckItem(
                key="title",
                label="Title Tag Length",
                status="warning",
                value=f"{title_length} characters",
                message="The title length is outside the recommended 30–60 character range.",
                recommendation="Keep the title between 30 and 60 characters.",
            )
        )

    if not meta_description:
        checks.append(
            CheckItem(
                key="meta_description",
                label="Meta Description",
                status="warning",
                value=None,
                message="No meta description was found.",
                recommendation="Add a compelling meta description between 70 and 160 characters.",
            )
        )
    elif 70 <= meta_description_length <= 160:
        checks.append(
            CheckItem(
                key="meta_description",
                label="Meta Description Length",
                status="success",
                value=f"{meta_description_length} characters",
                message="The meta description length is optimized.",
            )
        )
    else:
        checks.append(
            CheckItem(
                key="meta_description",
                label="Meta Description Length",
                status="warning",
                value=f"{meta_description_length} characters",
                message="The meta description length is outside the recommended 70–160 character range.",
                recommendation="Keep the meta description between 70 and 160 characters.",
            )
        )

    if h1_count == 1:
        checks.append(
            CheckItem(
                key="h1_count",
                label="H1 Heading",
                status="success",
                value=h1_count,
                message="Exactly one H1 heading was found.",
            )
        )
    elif h1_count == 0:
        checks.append(
            CheckItem(
                key="h1_count",
                label="H1 Heading",
                status="error",
                value=h1_count,
                message="No H1 heading was found.",
                recommendation="Add exactly one descriptive H1 heading.",
            )
        )
    else:
        checks.append(
            CheckItem(
                key="h1_count",
                label="H1 Heading",
                status="warning",
                value=h1_count,
                message=f"{h1_count} H1 headings were found.",
                recommendation="Use exactly one primary H1 heading per page.",
            )
        )

    if word_count < 150:
        checks.append(
            CheckItem(
                key="word_count",
                label="Content Length",
                status="warning",
                value=f"{word_count} words",
                message="The page has relatively thin textual content.",
                recommendation="Add useful, original, and topic-focused content.",
            )
        )
    else:
        checks.append(
            CheckItem(
                key="word_count",
                label="Content Length",
                status="success",
                value=f"{word_count} words",
                message="The page contains a reasonable amount of textual content.",
            )
        )

    if images_without_alt > 0:
        checks.append(
            CheckItem(
                key="image_alt",
                label="Image Alt Attributes",
                status="warning",
                value=f"{images_without_alt} of {total_images} missing",
                message="One or more images have missing or empty alt attributes.",
                recommendation="Add descriptive alt text to meaningful images.",
            )
        )
    else:
        checks.append(
            CheckItem(
                key="image_alt",
                label="Image Alt Attributes",
                status="success",
                value=f"{total_images} images checked",
                message="All detected images include alt attributes.",
            )
        )

    if not canonical:
        checks.append(
            CheckItem(
                key="canonical",
                label="Canonical URL",
                status="warning",
                value=None,
                message="No canonical URL was detected.",
                recommendation="Add a self-referencing canonical link element.",
            )
        )
    else:
        checks.append(
            CheckItem(
                key="canonical",
                label="Canonical URL",
                status="success",
                value=canonical,
                message="A canonical URL was detected.",
            )
        )

    robots_value = (robots_meta or "").lower()
    if "noindex" in robots_value:
        checks.append(
            CheckItem(
                key="robots",
                label="Robots Meta Tag",
                status="error",
                value=robots_meta,
                message="The page contains a noindex directive.",
                recommendation="Remove noindex if this page should appear in search results.",
            )
        )
    else:
        checks.append(
            CheckItem(
                key="robots",
                label="Robots Meta Tag",
                status="info",
                value=robots_meta or "Not specified",
                message="No noindex directive was detected.",
            )
        )

    checks.append(
        CheckItem(
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
    )

    checks.append(
        CheckItem(
            key="structured_data",
            label="Structured Data",
            status="success" if has_structured_data else "warning",
            value=has_structured_data,
            message=(
                "JSON-LD structured data was detected."
                if has_structured_data
                else "No JSON-LD structured data was detected."
            ),
            recommendation=(
                None
                if has_structured_data
                else "Add valid schema markup relevant to the page content."
            ),
        )
    )

    checks.append(
        CheckItem(
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
