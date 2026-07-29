import socket
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from backend.api.knowledge import KnowledgeCardReferenceIn
from backend.utils import scraper


def _dns(*addresses):
    return [
        (socket.AF_INET6 if ":" in address else socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, 443))
        for address in addresses
    ]


def test_rejects_unsupported_url_scheme():
    with pytest.raises(scraper.UnsafeUrlError, match="scheme"):
        scraper.validate_public_url("file:///etc/passwd", resolver=lambda *_args, **_kwargs: [])


def test_rejects_embedded_url_credentials():
    with pytest.raises(scraper.UnsafeUrlError, match="credentials"):
        scraper.validate_public_url(
            "https://user:password@example.org/report",
            resolver=lambda *_args, **_kwargs: _dns("93.184.216.34"),
        )


@pytest.mark.parametrize(
    "address",
    ["127.0.0.1", "10.0.0.1", "169.254.169.254", "0.0.0.0", "::1", "fc00::1", "fe80::1"],
)
def test_rejects_non_public_resolved_addresses(address):
    with pytest.raises(scraper.UnsafeUrlError, match="public"):
        scraper.validate_public_url(
            "https://example.org/report",
            resolver=lambda *_args, **_kwargs: _dns(address),
        )


def test_rejects_hostname_with_mixed_public_and_private_answers():
    with pytest.raises(scraper.UnsafeUrlError, match="public"):
        scraper.validate_public_url(
            "https://example.org/report",
            resolver=lambda *_args, **_kwargs: _dns("93.184.216.34", "127.0.0.1"),
        )


def test_accepts_http_and_https_public_urls():
    def resolver(*_args, **_kwargs):
        return _dns("93.184.216.34")

    assert scraper.validate_public_url("http://example.org/report", resolver=resolver).scheme == "http"
    assert scraper.validate_public_url("https://example.org/report", resolver=resolver).scheme == "https"


def test_stored_reference_rejects_unsafe_url_syntax():
    with pytest.raises(ValidationError, match="scheme"):
        KnowledgeCardReferenceIn(url="file:///etc/passwd", reference_type="source")


def test_redirect_target_is_validated_before_second_request(monkeypatch):
    redirect = Mock(
        status_code=302,
        headers={"Location": "http://127.0.0.1/admin"},
        close=Mock(),
    )
    request = Mock(return_value=redirect)
    monkeypatch.setattr(scraper.requests, "get", request)
    monkeypatch.setattr(
        scraper.socket,
        "getaddrinfo",
        lambda host, *_args, **_kwargs: _dns("93.184.216.34" if host == "example.org" else "127.0.0.1"),
    )

    assert scraper.scrape_url("https://example.org/start") is None
    assert request.call_count == 1


def test_oversized_response_is_rejected(monkeypatch):
    response = Mock(
        status_code=200,
        headers={"Content-Type": "text/html"},
        iter_content=Mock(return_value=[b"a" * 6, b"b" * 6]),
        raise_for_status=Mock(),
        close=Mock(),
    )
    monkeypatch.setattr(scraper, "MAX_RESPONSE_BYTES", 10)
    monkeypatch.setattr(scraper.requests, "get", Mock(return_value=response))
    monkeypatch.setattr(scraper.socket, "getaddrinfo", lambda *_args, **_kwargs: _dns("93.184.216.34"))

    assert scraper.scrape_url("https://example.org/report") is None
    response.close.assert_called_once()
