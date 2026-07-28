import pytest
from redis.exceptions import RedisError  # type: ignore[import-untyped]
from sqlalchemy import text

from backend.core.redis import redis_client
from backend.core.security import get_current_user
from backend.main import app


@pytest.fixture(autouse=True)
def _clear_authentication_override():
    app.dependency_overrides.pop(get_current_user, None)
    for user_id in ("user-1", "admin-1"):
        redis_client.delete(f"active_team:{user_id}")
    yield
    app.dependency_overrides.pop(get_current_user, None)
    for user_id in ("user-1", "admin-1"):
        redis_client.delete(f"active_team:{user_id}")


def _seed_team_context(test_engine):
    with test_engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO users (id, email, password, name) VALUES "
                "('user-1', 'user@example.com', 'x', 'User'), "
                "('admin-1', 'admin@example.com', 'x', 'Admin')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO teams (id, name, created_by) VALUES "
                "('team-1', 'Team One', 'admin-1'), "
                "('team-2', 'Team Two', 'admin-1'), "
                "('team-3', 'Team Three', 'admin-1')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO team_members (team_id, user_id, status) VALUES "
                "('team-1', 'user-1', 'ACTIVE'), "
                "('team-2', 'user-1', 'ACTIVE'), "
                "('team-3', 'user-1', 'PENDING')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO roles (id, name, role_key, component) VALUES "
                "(1, 'access_metrics', 'access_metrics', 'MetricsDashboard'), "
                "(2, 'access_template', 'access_template', 'TemplateLibrary')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO team_roles (team_id, role_id, role_key) VALUES "
                "('team-1', 1, 'access_metrics'), "
                "('team-2', 2, 'access_template')"
            )
        )


def _authenticate():
    app.dependency_overrides[get_current_user] = lambda: {
        "user_id": "user-1",
        "name": "User",
        "email": "user@example.com",
        "is_admin": False,
        "memberships": [
            {"id": "team-1", "name": "Team One"},
            {"id": "team-2", "name": "Team Two"},
        ],
        "active_team": {"id": "team-1", "name": "Team One"},
        "roles": ["access_metrics"],
    }


def test_switching_active_team_replaces_scoped_roles_and_persists_selection(client, test_engine):
    _seed_team_context(test_engine)
    _authenticate()

    response = client.put("/api/profile/active-team", json={"team_id": "team-2"})

    assert response.status_code == 200
    assert response.json()["active_team"] == {"id": "team-2", "name": "Team Two"}
    assert response.json()["roles"] == ["access_template"]
    assert "access_metrics" not in response.json()["roles"]
    assert redis_client.get("active_team:user-1") == "team-2"


def test_switching_active_team_succeeds_when_redis_is_unavailable(client, test_engine, monkeypatch):
    _seed_team_context(test_engine)
    _authenticate()
    monkeypatch.setattr(redis_client, "setex", lambda *_args, **_kwargs: (_ for _ in ()).throw(RedisError("down")))

    response = client.put("/api/profile/active-team", json={"team_id": "team-2"})

    assert response.status_code == 200
    assert response.json()["active_team"] == {"id": "team-2", "name": "Team Two"}


@pytest.mark.parametrize("team_id", ["team-3", "missing-team"])
def test_switching_rejects_pending_or_missing_membership(client, test_engine, team_id):
    _seed_team_context(test_engine)
    _authenticate()

    response = client.put("/api/profile/active-team", json={"team_id": team_id})

    assert response.status_code == 403
    assert redis_client.get("active_team:user-1") is None
