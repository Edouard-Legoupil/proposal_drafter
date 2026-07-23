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
