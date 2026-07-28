import pytest
from sqlalchemy import text

from backend.core.security import get_current_user
from backend.main import app


@pytest.fixture(autouse=True)
def _clear_authentication_override():
    app.dependency_overrides.pop(get_current_user, None)
    yield
    app.dependency_overrides.pop(get_current_user, None)


def _actor(user_id: str, *, is_admin: bool = False, team_id: str | None = None):
    return {
        "user_id": user_id,
        "name": user_id,
        "email": f"{user_id}@example.com",
        "is_admin": is_admin,
        "roles": ["access_template"] if team_id else [],
        "role_keys": ["access_template"] if team_id else [],
        "active_team": {"id": team_id, "name": "Team One"} if team_id else None,
        "team_leadership": False,
    }


def _authenticate(actor):
    app.dependency_overrides[get_current_user] = lambda: actor


def _seed_access_scope(test_engine):
    with test_engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO users (id, email, password, name) VALUES "
                "('admin-1', 'admin@example.com', 'x', 'Admin'), "
                "('user-1', 'user@example.com', 'x', 'User'), "
                "('outsider-1', 'outsider@example.com', 'x', 'Outsider')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO roles (id, name, role_key, component) VALUES "
                "(1, 'access_template', 'access_template', 'TemplateWorkspace'), "
                "(2, 'access_metrics', 'access_metrics', 'MetricsDashboard')"
            )
        )
        connection.execute(text("INSERT INTO teams (id, name, created_by) VALUES ('team-1', 'Team One', 'admin-1')"))
        connection.execute(
            text("INSERT INTO team_members (team_id, user_id, status) " "VALUES ('team-1', 'user-1', 'ACTIVE')")
        )
        connection.execute(
            text("INSERT INTO team_roles (team_id, role_id, role_key) " "VALUES ('team-1', 1, 'access_template')")
        )


def test_settings_routes_require_authentication(client):
    assert client.get("/api/settings").status_code == 401
    response = client.post(
        "/api/settings",
        json={
            "user_id": "user-1",
            "team_id": "team-1",
            "role_key": "access_template",
            "key": "donor",
            "value": "ECHO",
        },
    )
    assert response.status_code == 401


@pytest.mark.parametrize(
    ("user_id", "role_key"),
    [("outsider-1", "access_template"), ("user-1", "access_metrics")],
)
def test_setting_requires_active_membership_and_assigned_team_role(client, test_engine, user_id, role_key):
    _seed_access_scope(test_engine)
    _authenticate(_actor("admin-1", is_admin=True))

    response = client.post(
        "/api/settings",
        json={
            "user_id": user_id,
            "team_id": "team-1",
            "role_key": role_key,
            "key": "donor",
            "value": "ECHO",
        },
    )

    assert response.status_code == 422


def test_admin_upserts_and_deletes_a_scoped_setting(client, test_engine):
    _seed_access_scope(test_engine)
    _authenticate(_actor("admin-1", is_admin=True))

    created = client.post(
        "/api/settings",
        json={
            "user_id": "user-1",
            "team_id": "team-1",
            "role_key": "access_template",
            "key": "donor",
            "value": ["ECHO"],
        },
    )
    assert created.status_code == 201
    setting_id = created.json()["id"]

    updated = client.post(
        "/api/settings",
        json={
            "user_id": "user-1",
            "team_id": "team-1",
            "role_key": "access_template",
            "key": "donor",
            "value": ["ECHO", "USAID"],
        },
    )
    assert updated.status_code == 200
    assert updated.json()["id"] == setting_id
    assert updated.json()["value"] == ["ECHO", "USAID"]

    deleted = client.delete(f"/api/settings/{setting_id}")
    assert deleted.status_code == 204


def test_current_user_lists_only_active_team_authorized_settings(client, test_engine):
    _seed_access_scope(test_engine)
    with test_engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO access_settings "
                "(user_id, team_id, role_key, key, value, created_by) "
                "VALUES ('user-1', 'team-1', 'access_template', 'donor', :value, 'admin-1')"
            ),
            {"value": '["ECHO"]'},
        )
    _authenticate(_actor("user-1", team_id="team-1"))

    response = client.get("/api/settings")

    assert response.status_code == 200
    assert response.json() == {
        "settings": [
            {
                "id": 1,
                "user_id": "user-1",
                "team_id": "team-1",
                "role_key": "access_template",
                "key": "donor",
                "value": ["ECHO"],
            }
        ]
    }
