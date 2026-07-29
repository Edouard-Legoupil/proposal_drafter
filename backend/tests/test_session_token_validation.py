from unittest.mock import Mock

import pytest
from redis.exceptions import RedisError  # type: ignore[import-untyped]

from backend.core import security
from fastapi import HTTPException

from backend.core import redis as redis_module
from backend.core.security import is_session_token_active, store_session_token


def test_active_token_is_accepted(monkeypatch):
    monkeypatch.setattr(security, "is_redis_available", lambda: True)
    monkeypatch.setattr(security, "redis_client", Mock(get=Mock(return_value="active-token")))

    assert is_session_token_active("user-1", "active-token") is True


def test_missing_token_is_rejected_when_redis_available(monkeypatch):
    monkeypatch.setattr(security, "is_redis_available", lambda: True)
    monkeypatch.setattr(security, "redis_client", Mock(get=Mock(return_value=None)))

    assert is_session_token_active("user-1", "presented-token") is False


def test_mismatched_token_is_rejected_when_redis_available(monkeypatch):
    monkeypatch.setattr(security, "is_redis_available", lambda: True)
    monkeypatch.setattr(security, "redis_client", Mock(get=Mock(return_value="other-token")))

    assert is_session_token_active("user-1", "presented-token") is False


def test_valid_jwt_is_rejected_when_production_redis_is_unavailable(monkeypatch):
    monkeypatch.setattr(security, "is_redis_available", lambda: False)
    monkeypatch.setattr(security, "shared_session_store_required", lambda: True)
    redis_client = Mock()
    monkeypatch.setattr(security, "redis_client", redis_client)

    with pytest.raises(HTTPException) as exc_info:
        is_session_token_active("user-1", "presented-token")

    assert exc_info.value.status_code == 503
    redis_client.get.assert_not_called()


def test_redis_error_fails_closed_in_production(monkeypatch):
    monkeypatch.setattr(security, "is_redis_available", lambda: True)
    monkeypatch.setattr(security, "shared_session_store_required", lambda: True)
    monkeypatch.setattr(
        security,
        "redis_client",
        Mock(get=Mock(side_effect=RedisError("redis unavailable"))),
    )

    with pytest.raises(HTTPException) as exc_info:
        is_session_token_active("user-1", "presented-token")

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "Session service temporarily unavailable."


def test_local_fallback_accepts_cryptographically_valid_token(monkeypatch):
    monkeypatch.setattr(security, "is_redis_available", lambda: False)
    monkeypatch.setattr(security, "shared_session_store_required", lambda: False)

    assert is_session_token_active("user-1", "presented-token") is True


def test_redis_client_uses_configured_url(monkeypatch):
    expected = Mock()
    from_url = Mock(return_value=expected)
    monkeypatch.setattr(redis_module.redis.Redis, "from_url", from_url)

    client = redis_module.create_redis_client("rediss://cache.example:6380/1")

    assert client is expected
    from_url.assert_called_once_with("rediss://cache.example:6380/1", decode_responses=True)


def test_session_creation_fails_closed_on_production_redis_error(monkeypatch):
    monkeypatch.setattr(security, "shared_session_store_required", lambda: True)
    monkeypatch.setattr(
        security,
        "redis_client",
        Mock(setex=Mock(side_effect=RedisError("redis unavailable"))),
    )

    with pytest.raises(HTTPException) as exc_info:
        store_session_token("user-1", "token")

    assert exc_info.value.status_code == 503


def test_session_creation_uses_eight_hour_ttl(monkeypatch):
    client = Mock()
    monkeypatch.setattr(security, "redis_client", client)

    store_session_token("user-1", "token")

    client.setex.assert_called_once_with("user_session:user-1", 28800, "token")
