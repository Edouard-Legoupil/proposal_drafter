import uuid

from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

from backend.api import users
from backend.core.security import get_current_user, is_system_admin
from backend.main import app


def _settings_engine(user_id, approved_team_id):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE users (
                    id TEXT PRIMARY KEY,
                    geographic_coverage_type TEXT,
                    geographic_coverage_region TEXT,
                    geographic_coverage_country TEXT
                )
                """
            )
        )
        connection.execute(text("INSERT INTO users (id) VALUES (:id)"), {"id": user_id})
        connection.execute(
            text("CREATE TABLE user_roles (user_id TEXT, role_id INTEGER, PRIMARY KEY (user_id, role_id))")
        )
        connection.execute(text("INSERT INTO user_roles VALUES (:id, 1)"), {"id": user_id})
        connection.execute(
            text("CREATE TABLE user_role_requests (user_id TEXT, role_id INTEGER, PRIMARY KEY (user_id, role_id))")
        )
        connection.execute(text("CREATE TABLE user_donor_groups (user_id TEXT, donor_group TEXT)"))
        connection.execute(text("CREATE TABLE user_donors (user_id TEXT, donor_id TEXT)"))
        connection.execute(text("CREATE TABLE user_outcomes (user_id TEXT, outcome_id TEXT)"))
        connection.execute(text("CREATE TABLE user_field_contexts (user_id TEXT, field_context_id TEXT)"))
        connection.execute(
            text("CREATE TABLE team_members (user_id TEXT, team_id TEXT, PRIMARY KEY (user_id, team_id))")
        )
        connection.execute(
            text("INSERT INTO team_members VALUES (:user_id, :team_id)"),
            {"user_id": user_id, "team_id": approved_team_id},
        )
        connection.execute(
            text(
                """
                CREATE TABLE user_settings_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, setting_type TEXT,
                    setting_value TEXT, status TEXT DEFAULT 'pending'
                )
                """
            )
        )
    return engine


def test_self_service_update_preserves_approved_roles_and_memberships(client, monkeypatch):
    user_id = str(uuid.uuid4())
    approved_team_id = str(uuid.uuid4())
    attacker_team_id = str(uuid.uuid4())
    engine = _settings_engine(user_id, approved_team_id)
    monkeypatch.setattr(users, "get_engine", lambda: engine)
    app.dependency_overrides[get_current_user] = lambda: {"user_id": user_id, "roles": ["proposal writer"]}

    try:
        response = client.put(
            "/api/users/me/settings",
            headers={"host": "localhost"},
            json={
                "geographic_coverage_type": "regional",
                "roles": [6],
                "team_memberships": [attacker_team_id],
                "requested_team_memberships": [attacker_team_id],
            },
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 204
    with engine.connect() as connection:
        roles = (
            connection.execute(text("SELECT role_id FROM user_roles WHERE user_id = :user_id"), {"user_id": user_id})
            .scalars()
            .all()
        )
        teams = (
            connection.execute(text("SELECT team_id FROM team_members WHERE user_id = :user_id"), {"user_id": user_id})
            .scalars()
            .all()
        )
        pending_teams = (
            connection.execute(
                text(
                    "SELECT setting_value FROM user_settings_requests "
                    "WHERE user_id = :user_id AND setting_type = 'team_membership'"
                ),
                {"user_id": user_id},
            )
            .scalars()
            .all()
        )

    assert roles == [1]
    assert teams == [approved_team_id]
    assert pending_teams == [attacker_team_id]


def test_self_service_rejects_legacy_direct_role_requests(client):
    user_id = str(uuid.uuid4())
    app.dependency_overrides[get_current_user] = lambda: {"user_id": user_id, "roles": []}
    try:
        response = client.put(
            "/api/users/me/settings",
            headers={"host": "localhost"},
            json={"requested_roles": [2]},
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 410
    assert "team" in response.json()["detail"].lower()


def test_admin_settings_rejects_legacy_direct_role_assignment(client):
    app.dependency_overrides[is_system_admin] = lambda: {"user_id": str(uuid.uuid4()), "is_admin": True}
    try:
        response = client.put(
            f"/api/admin/users/{uuid.uuid4()}/settings",
            headers={"host": "localhost"},
            json={"role_ids": [2]},
        )
    finally:
        app.dependency_overrides.pop(is_system_admin, None)

    assert response.status_code == 410
    assert "team" in response.json()["detail"].lower()
