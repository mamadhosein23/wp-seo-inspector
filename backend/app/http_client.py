# backend/app/http_client.py

import time
from dataclasses import dataclass

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.security import validate_safe_url


DEFAULT_TIMEOUT = 15
MAX_HTML_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


@dataclass
class FetchResult:
    requested_url: str
    final_url: str
    html: str
    status_code: int
    content_type: str
    response_time_ms: int


class FetchError(Exception):
    """Raised when a remote page cannot be fetched safely."""


def create_http_session() -> requests.Session:
    retry_config = Retry(
        total=2,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )

    adapter = HTTPAdapter(max_retries=retry_config)

    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (compatible; WPSEOInspector/1.0; "
                "+https://github.com/mamadhosein23/wp-seo-inspector)"
            ),
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        }
    )

    return session


def fetch_html(url: str) -> FetchResult:
    validate_safe_url(url)

    session = create_http_session()
    started_at = time.perf_counter()

    try:
        response = session.get(
            url,
            timeout=DEFAULT_TIMEOUT,
            allow_redirects=True,
            stream=True,
        )
    except requests.RequestException as error:
        raise FetchError(
            "Unable to fetch the target URL. The website may be unavailable, "
            "blocking requests, or taking too long to respond."
        ) from error

    response_time_ms = round((time.perf_counter() - started_at) * 1000)

    # URL after redirects must be validated too.
    validate_safe_url(response.url)

    content_type = response.headers.get("Content-Type", "").lower()

    if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
        raise FetchError(
            f"Unsupported content type: '{content_type or 'unknown'}'. "
            "Only HTML pages can be audited."
        )

    if response.status_code >= 400:
        raise FetchError(
            f"The target website returned HTTP status code {response.status_code}."
        )

    content_length = response.headers.get("Content-Length")
    if content_length and int(content_length) > MAX_HTML_SIZE_BYTES:
        raise FetchError("The HTML document is larger than the 5 MB audit limit.")

    downloaded_chunks: list[bytes] = []
    downloaded_size = 0

    for chunk in response.iter_content(chunk_size=8192):
        if not chunk:
            continue

        downloaded_size += len(chunk)

        if downloaded_size > MAX_HTML_SIZE_BYTES:
            raise FetchError("The HTML document exceeded the 5 MB audit limit.")

        downloaded_chunks.append(chunk)

    raw_html = b"".join(downloaded_chunks)
    encoding = response.encoding or "utf-8"
    html = raw_html.decode(encoding, errors="replace")

    return FetchResult(
        requested_url=url,
        final_url=response.url,
        html=html,
        status_code=response.status_code,
        content_type=content_type,
        response_time_ms=response_time_ms,
    )
