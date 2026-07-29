"""Bounded public-web ingestion helpers."""

import io
import ipaddress
import logging
import os
import socket
from collections.abc import Callable
from urllib.parse import ParseResult, parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

from backend.core.config import SCRAPER_ALLOWED_SCHEMES

logger = logging.getLogger(__name__)

MAX_RESPONSE_BYTES = int(os.getenv("SCRAPER_MAX_RESPONSE_BYTES", str(10 * 1024 * 1024)))
MAX_REDIRECTS = int(os.getenv("SCRAPER_MAX_REDIRECTS", "5"))
MAX_PDF_PAGES = int(os.getenv("SCRAPER_MAX_PDF_PAGES", "100"))
MAX_RECURSION_DEPTH = 1
REQUEST_TIMEOUT = (5, 20)
REDIRECT_STATUSES = {301, 302, 303, 307, 308}


class UnsafeUrlError(ValueError):
    """Raised when a remote URL could reach a non-public destination."""


def validate_remote_url_syntax(url: str) -> ParseResult:
    """Validate remote URL syntax without performing network resolution."""
    try:
        parsed = urlparse(url)
        _ = parsed.port
    except ValueError as exc:
        raise UnsafeUrlError("URL authority is invalid") from exc
    if parsed.scheme.lower() not in SCRAPER_ALLOWED_SCHEMES:
        raise UnsafeUrlError("URL scheme is not allowed")
    if not parsed.hostname:
        raise UnsafeUrlError("URL hostname is required")
    if parsed.username is not None or parsed.password is not None:
        raise UnsafeUrlError("Embedded URL credentials are not allowed")
    return parsed


def validate_public_url(
    url: str,
    *,
    resolver: Callable[..., list[tuple]] = socket.getaddrinfo,
) -> ParseResult:
    """Validate the URL scheme, authority, and every resolved address."""
    parsed = validate_remote_url_syntax(url)
    port = parsed.port

    service_port = port or (443 if parsed.scheme.lower() == "https" else 80)
    try:
        answers = resolver(parsed.hostname, service_port, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise UnsafeUrlError("URL hostname could not be resolved") from exc
    if not answers:
        raise UnsafeUrlError("URL hostname could not be resolved")

    for answer in answers:
        address = ipaddress.ip_address(answer[4][0])
        if not address.is_global:
            raise UnsafeUrlError("URL must resolve only to public addresses")
    return parsed


def _headers_for_url(url: str) -> dict[str, str]:
    """Return host-specific headers without forwarding credentials on redirects."""
    if urlparse(url).hostname != "www.unhcr.org":
        return {}
    client_id = os.getenv("cfAccessClientId")
    client_secret = os.getenv("cfAccessClientSecret")
    if not client_id or not client_secret:
        return {}
    return {
        "Authorization": f"Bearer {client_id}:{client_secret}",
        "CF-Access-Client-Id": client_id,
    }


def _read_bounded_response(response) -> bytes:
    content = bytearray()
    for chunk in response.iter_content(chunk_size=64 * 1024):
        if not chunk:
            continue
        content.extend(chunk)
        if len(content) > MAX_RESPONSE_BYTES:
            raise UnsafeUrlError("Remote response exceeds the configured size limit")
    return bytes(content)


def _fetch(url: str) -> tuple[str, str, bytes]:
    current_url = url
    for redirect_count in range(MAX_REDIRECTS + 1):
        validate_public_url(current_url)
        response = requests.get(
            current_url,
            timeout=REQUEST_TIMEOUT,
            headers=_headers_for_url(current_url),
            allow_redirects=False,
            stream=True,
        )
        try:
            if response.status_code in REDIRECT_STATUSES:
                location = response.headers.get("Location")
                if not location:
                    raise UnsafeUrlError("Remote redirect is missing a target")
                if redirect_count >= MAX_REDIRECTS:
                    raise UnsafeUrlError("Remote response exceeded the redirect limit")
                target = urljoin(current_url, location)
                validate_public_url(target)
                current_url = target
                continue

            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "").lower()
            return current_url, content_type, _read_bounded_response(response)
        finally:
            response.close()
    raise UnsafeUrlError("Remote response exceeded the redirect limit")


def _extract_pdf(content: bytes) -> str | None:
    reader = PdfReader(io.BytesIO(content))
    if len(reader.pages) > MAX_PDF_PAGES:
        raise UnsafeUrlError("PDF exceeds the configured page limit")
    chunks = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text:
            chunks.append(text)
    extracted = "\n".join(chunks).strip()
    return extracted or None


def scrape_url(url: str, *, _depth: int = 0) -> str | None:
    """Extract bounded text from a public HTML or PDF URL."""
    try:
        parsed = validate_public_url(url)
        if parsed.hostname == "www.unhcr.org" and "/media/" in parsed.path:
            file_param = parse_qs(parsed.query).get("file", [None])[0]
            if file_param:
                url = urljoin(url, file_param)

        final_url, content_type, content = _fetch(url)
        if "application/pdf" in content_type or final_url.lower().endswith(".pdf"):
            return _extract_pdf(content)

        soup = BeautifulSoup(content, "html.parser")
        if _depth < MAX_RECURSION_DEPTH and ("pdf.js" in soup.get_text().lower() or "viewer.html" in final_url):
            for link in soup.find_all("a", href=True):
                href = link.get("href")
                if isinstance(href, str) and href.lower().endswith(".pdf"):
                    return scrape_url(urljoin(final_url, href), _depth=_depth + 1)

        paragraphs = [paragraph.get_text(strip=True) for paragraph in soup.find_all("p")]
        extracted = "\n".join(text for text in paragraphs if text).strip()
        return extracted or soup.get_text(separator="\n", strip=True) or None
    except UnsafeUrlError as exc:
        logger.warning("Rejected remote content: %s", exc)
        return None
    except requests.exceptions.Timeout:
        logger.warning("Remote content request timed out")
        return None
    except requests.exceptions.RequestException as exc:
        logger.warning("Remote content request failed: %s", type(exc).__name__)
        return None
    except Exception:
        logger.exception("Remote content processing failed")
        return None
