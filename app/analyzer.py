import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from app.schemas import CheckItem, AuditResponse
from app.utils import normalize_domain, is_internal_link
from app.scorer import calculate_score


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    )
}


def get_text_content(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "noscript"]):
        tag.extract()

    text = soup.get_text(separator=" ", strip=True)
    return " ".join(text.split())


def analyze_page(url: str) -> AuditResponse:
    response = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
    response.raise_for_status()

    final_url = response.url
    html = response.text
    soup = BeautifulSoup(html, "lxml")

    base_domain = normalize_domain(final_url)

    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else None

    meta_description_tag = soup.find("meta", attrs={"name": "description"})
    meta_description = (
        meta_description_tag.get("content", "").strip()
        if meta_description_tag and meta_description_tag.get("content")
        else None
    )

    h1_tags = soup.find_all("h1")
    h2_tags = soup.find_all("h2")

    images = soup.find_all("img")
    total_images = len(images)
    images_without_alt = sum(
        1 for img in images if not img.get("alt") or not img.get("alt").strip()
    )

    links = soup.find_all("a", href=True)
    internal_links = 0
    external_links = 0

    for link in links:
        href = link.get("href", "").strip()
        if not href or href.startswith("#") or href.startswith("javascript:"):
            continue

        absolute_url = urljoin(final_url, href)

        if is_internal_link(base_domain, absolute_url):
            internal_links += 1
        else:
            external_links += 1

    canonical_tag = soup.find("link", attrs={"rel": "canonical"})
    has_canonical = canonical_tag is not None and canonical_tag.get("href")

    robots_meta = soup.find("meta", attrs={"name": "robots"})
    has_robots_meta = robots_meta is not None

    open_graph_tags = soup.find_all("meta", attrs={"property": lambda x: x and x.startswith("og:")})
    has_open_graph = len(open_graph_tags) > 0

    json_ld_script = soup.find("script", attrs={"type": "application/ld+json"})
    has_structured_data = json_ld_script is not None

    text_content = get_text_content(soup)
    word_count = len(text_content.split())

    checks = []

    # Title checks
    if not title:
        checks.append(CheckItem(
            key="title_exists",
            label="Title Tag",
            status="error",
            value=False,
            message="تگ title وجود ندارد.",
            recommendation="برای صفحه یک title یکتا و مرتبط تعریف کن."
        ))
    else:
        title_length = len(title)
        if 30 <= title_length <= 60:
            checks.append(CheckItem(
                key="title_length",
                label="Title Length",
                status="success",
                value=title_length,
                message=f"طول title مناسب است ({title_length} کاراکتر)."
            ))
        else:
            checks.append(CheckItem(
                key="title_length",
                label="Title Length",
                status="warning",
                value=title_length,
                message=f"طول title ایده‌آل نیست ({title_length} کاراکتر).",
                recommendation="title را بین 30 تا 60 کاراکتر نگه دار."
            ))

    # Meta description checks
    if not meta_description:
        checks.append(CheckItem(
            key="meta_description_exists",
            label="Meta Description",
            status="error",
            value=False,
            message="Meta description وجود ندارد.",
            recommendation="برای صفحه meta description اختصاصی بنویس."
        ))
    else:
        desc_length = len(meta_description)
        if 70 <= desc_length <= 160:
            checks.append(CheckItem(
                key="meta_description_length",
                label="Meta Description Length",
                status="success",
                value=desc_length,
                message=f"طول meta description مناسب است ({desc_length} کاراکتر)."
            ))
        else:
            checks.append(CheckItem(
                key="meta_description_length",
                label="Meta Description Length",
                status="warning",
                value=desc_length,
                message=f"طول meta description ایده‌آل نیست ({desc_length} کاراکتر).",
                recommendation="توضیحات متا را حدود 70 تا 160 کاراکتر نگه دار."
            ))

    # H1 checks
    if len(h1_tags) == 1:
        checks.append(CheckItem(
            key="h1_count",
            label="H1 Tag",
            status="success",
            value=1,
            message="تعداد H1 مناسب است."
        ))
    elif len(h1_tags) == 0:
        checks.append(CheckItem(
            key="h1_count",
            label="H1 Tag",
            status="error",
            value=0,
            message="هیچ H1ای پیدا نشد.",
            recommendation="برای صفحه دقیقاً یک H1 تعریف کن."
        ))
    else:
        checks.append(CheckItem(
            key="h1_count",
            label="H1 Tag",
            status="warning",
            value=len(h1_tags),
            message=f"{len(h1_tags)} عدد H1 پیدا شد.",
            recommendation="بهتر است فقط یک H1 در صفحه وجود داشته باشد."
        ))

    # Image alt checks
    if total_images == 0:
        checks.append(CheckItem(
            key="images_presence",
            label="Images",
            status="info",
            value=0,
            message="هیچ تصویری در صفحه یافت نشد."
        ))
    elif images_without_alt == 0:
        checks.append(CheckItem(
            key="image_alt_coverage",
            label="Image Alt Coverage",
            status="success",
            value=total_images,
            message="همه تصاویر دارای alt هستند."
        ))
    else:
        checks.append(CheckItem(
            key="image_alt_coverage",
            label="Image Alt Coverage",
            status="warning",
            value=images_without_alt,
            message=f"{images_without_alt} تصویر بدون alt پیدا شد.",
            recommendation="برای همه تصاویر alt توصیفی و مرتبط بنویس."
        ))

    # Canonical
    if has_canonical:
        checks.append(CheckItem(
            key="canonical_tag",
            label="Canonical Tag",
            status="success",
            value=True,
            message="تگ canonical وجود دارد."
        ))
    else:
        checks.append(CheckItem(
            key="canonical_tag",
            label="Canonical Tag",
            status="warning",
            value=False,
            message="تگ canonical پیدا نشد.",
            recommendation="برای جلوگیری از مشکلات محتوای تکراری canonical تعریف کن."
        ))

    # Robots meta
    if has_robots_meta:
        checks.append(CheckItem(
            key="robots_meta",
            label="Robots Meta",
            status="success",
            value=True,
            message="متای robots وجود دارد."
        ))
    else:
        checks.append(CheckItem(
            key="robots_meta",
            label="Robots Meta",
            status="info",
            value=False,
            message="متای robots پیدا نشد."
        ))

    # Open Graph
    if has_open_graph:
        checks.append(CheckItem(
            key="open_graph",
            label="Open Graph Tags",
            status="success",
            value=True,
            message="تگ‌های Open Graph وجود دارند."
        ))
    else:
        checks.append(CheckItem(
            key="open_graph",
            label="Open Graph Tags",
            status="warning",
            value=False,
            message="تگ‌های Open Graph پیدا نشدند.",
            recommendation="برای اشتراک‌گذاری بهتر در شبکه‌های اجتماعی Open Graph اضافه کن."
        ))

    # Structured data
    if has_structured_data:
        checks.append(CheckItem(
            key="structured_data",
            label="Structured Data",
            status="success",
            value=True,
            message="Structured data یافت شد."
        ))
    else:
        checks.append(CheckItem(
            key="structured_data",
            label="Structured Data",
            status="warning",
            value=False,
            message="Structured data پیدا نشد.",
            recommendation="از schema markup مناسب نوع صفحه استفاده کن."
        ))

    score = calculate_score(checks)

    return AuditResponse(
        url=url,
        final_url=final_url,
        score=score,
        title=title,
        meta_description=meta_description,
        h1_count=len(h1_tags),
        h2_count=len(h2_tags),
        word_count=word_count,
        total_images=total_images,
        images_without_alt=images_without_alt,
        internal_links=internal_links,
        external_links=external_links,
        has_canonical=bool(has_canonical),
        has_robots_meta=has_robots_meta,
        has_open_graph=has_open_graph,
        has_structured_data=has_structured_data,
        checks=checks
    )
