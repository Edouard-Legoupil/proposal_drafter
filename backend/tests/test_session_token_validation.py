from unittest.mock import Mock

from redis.exceptions import RedisError

from backend.core import security
from backend.core.security import is_session_token_active


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


def test_valid_jwt_is_accepted_when_redis_unavailable(monkeypatch):
    monkeypatch.setattr(security, "is_redis_available", lambda: False)
    redis_client = Mock()
    monkeypatch.setattr(security, "redis_client", redis_client)

    assert is_session_token_active("user-1", "presented-token") is True
    redis_client.get.assert_not_called()


def test_redis_error_falls_back_to_valid_jwt(monkeypatch):
    monkeypatch.setattr(security, "is_redis_available", lambda: True)
    monkeypatch.setattr(
        security,
        "redis_client",
        Mock(get=Mock(side_effect=RedisError("redis unavailable"))),
    )

    assert is_session_token_active("user-1", "presented-token") is True
