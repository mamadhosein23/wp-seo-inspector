import tldextract


def normalize_domain(url: str) -> str:
    parsed = urlparse(url)
    extracted = tldextract.extract(parsed.netloc)
    return ".".join(part for part in [extracted.domain, extracted.suffix] if part)


def is_internal_link(base_domain: str, link_url: str) -> bool:
    if not link_url:
        return False

    parsed = urlparse(link_url)

    # لینک نسبی
    if not parsed.netloc:
        return True

    link_domain = normalize_domain(link_url)
    return link_domain == base_domain
