import jwt
import pytest
from starlette.requests import Request
from sqlalchemy import text

from backend.core import security


@pytest.mark.parametrize("status", ["PENDING", "REJECTED"])
def test_authenticated_inactive_member_does_not_inherit_team_role(test_engine, monkeypatch, status):
    with test_engine.begin() as connection:
        connection.execute(text("INSERT INTO teams (id, name) VALUES ('team-1', 'Test Team')"))
        connection.execute(
            text("INSERT INTO users (id, email, password) " "VALUES ('user-1', 'pending@example.org', 'secret')")
        )
        connection.execute(
            text(
                "INSERT INTO roles (id, name, role_key, component) "
                "VALUES (1, 'access_metrics', 'access_metrics', 'MetricsDashboard')"
            )
        )
        connection.execute(
            text("INSERT INTO team_members (team_id, user_id, status) " "VALUES ('team-1', 'user-1', :status)"),
            {"status": status},
        )
        connection.execute(
            text("INSERT INTO team_roles (team_id, role_id, role_key) " "VALUES ('team-1', 1, 'access_metrics')")
        )

    token = jwt.encode({"email": "pending@example.org"}, str(security.SECRET_KEY), algorithm="HS256")
    request = Request({"type": "http", "headers": [(b"cookie", f"auth_token={token}".encode())]})
    monkeypatch.setattr(security, "get_engine", lambda: test_engine)
    monkeypatch.setattr(security, "is_session_token_active", lambda _user_id, _token: True)

    current_user = security.get_current_user(request)

    assert "access_metrics" not in current_user["all_roles"]
