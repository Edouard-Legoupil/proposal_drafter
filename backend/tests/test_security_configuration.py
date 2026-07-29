import pytest
from starlette.requests import Request

from backend.core import config
from backend.core.middleware import get_cookie_settings


def _request(host="app.example.org", scheme="https"):
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "scheme": scheme,
            "headers": [(b"host", host.encode())],
            "client": ("203.0.113.10", 443),
            "server": (host, 443),
        }
    )


def test_default_jwt_secret_is_rejected_in_production():
    with pytest.raises(ValueError, match="SECRET_KEY"):
        config.validate_secret_key("your_default_dev_secret", environment="production", testing=False)


def test_default_jwt_secret_is_allowed_only_for_local_development():
    config.validate_secret_key("your_default_dev_secret", environment="development", testing=False)


def test_auth_cookie_uses_lax_same_site_policy():
    assert get_cookie_settings(_request()) == {
        "secure": True,
        "samesite": "lax",
        "domain": None,
    }


def test_allowed_hosts_are_hostnames_not_cors_urls():
    assert all("://" not in host for host in config.allowed_hosts)


def test_scraper_schemes_default_to_http_and_https_in_development():
    assert config.parse_scraper_allowed_schemes(None, "development") == frozenset({"http", "https"})


def test_scraper_schemes_are_required_in_production():
    with pytest.raises(ValueError, match="SCRAPER_ALLOWED_SCHEMES"):
        config.parse_scraper_allowed_schemes(None, "production")


@pytest.mark.parametrize("value", ["file", "http,file", "https,gopher", ""])
def test_scraper_schemes_reject_non_http_protocols_in_production(value):
    with pytest.raises(ValueError, match="http and https"):
        config.parse_scraper_allowed_schemes(value, "production")


def test_local_authentication_is_disabled_only_in_production():
    assert config.local_authentication_enabled("development", testing=False) is True
    assert config.local_authentication_enabled("production", testing=False) is False
    assert config.local_authentication_enabled("production", testing=True) is True
