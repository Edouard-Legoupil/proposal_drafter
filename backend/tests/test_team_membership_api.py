from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

from backend.api import access_management
from backend.core.security import get_current_user
from backend.main import app


def _engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE teams (id TEXT PRIMARY KEY, name TEXT)"))
        connection.execute(text("CREATE TABLE users (id TEXT PRIMARY KEY, name TEXT, email TEXT)"))
        connection.execute(text("CREATE TABLE roles (id INTEGER PRIMARY KEY, name TEXT)"))
        connection.execute(text("CREATE TABLE user_roles (user_id TEXT, role_id INTEGER)"))
        connection.execute(text("CREATE TABLE team_roles (team_id TEXT, role_id INTEGER)"))
        connection.execute(
            text("CREATE TABLE team_member_roles (team_id TEXT, user_id TEXT, role_key TEXT, assigned_by TEXT)")
        )
        connection.execute(
            text(
                """
                CREATE TABLE team_members (
                    team_id TEXT, user_id TEXT, status TEXT,
                    PRIMARY KEY (team_id, user_id)
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE resource_access_audit (
                    id TEXT PRIMARY KEY, resource_type TEXT, resource_id TEXT,
                    action TEXT, actor_id TEXT, details TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        connection.execute(text("INSERT INTO teams VALUES ('team-1', 'Team One')"))
        connection.execute(text("INSERT INTO users VALUES ('user-1', 'User One', 'user@example.com')"))
    return engine


def test_join_request_is_committed(client, monkeypatch):
    engine = _engine()
    monkeypatch.setattr(access_management, "get_engine", lambda: engine)
    app.dependency_overrides[get_current_user] = lambda: {"user_id": "user-1"}
    try:
        response = client.post(
            "/api/teams/team-1/join",
            headers={"host": "localhost"},
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    with engine.connect() as connection:
        status = connection.execute(
            text("SELECT status FROM team_members WHERE team_id = 'team-1' AND user_id = 'user-1'")
        ).scalar()
    assert status == "PENDING"


def test_membership_request_listing_preserves_forbidden_response(client, monkeypatch):
    engine = _engine()
    monkeypatch.setattr(access_management, "get_engine", lambda: engine)
    app.dependency_overrides[get_current_user] = lambda: {"user_id": "user-1"}
    try:
        response = client.get(
            "/api/teams/team-1/requests",
            headers={"host": "localhost"},
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 403


def test_team_role_does_not_promote_every_member_to_team_leader(client, monkeypatch):
    engine = _engine()
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO roles VALUES (998, 'TEAM_LEADER')"))
        connection.execute(text("INSERT INTO team_roles VALUES ('team-1', 998)"))
        connection.execute(text("INSERT INTO team_members VALUES ('team-1', 'user-1', 'ACTIVE')"))

    monkeypatch.setattr(access_management, "get_engine", lambda: engine)
    app.dependency_overrides[get_current_user] = lambda: {"user_id": "user-1"}
    try:
        response = client.get("/api/teams/team-1/requests", headers={"host": "localhost"})
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 403


def test_scoped_active_team_leader_can_list_membership_requests(client, monkeypatch):
    engine = _engine()
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO team_members VALUES ('team-1', 'user-1', 'ACTIVE')"))
        connection.execute(text("INSERT INTO team_member_roles VALUES ('team-1', 'user-1', 'TEAM_LEADER', 'user-1')"))

    monkeypatch.setattr(access_management, "get_engine", lambda: engine)
    app.dependency_overrides[get_current_user] = lambda: {
        "user_id": "user-1",
        "active_team": {"id": "team-1", "name": "Team One"},
        "team_leadership": True,
    }
    try:
        response = client.get("/api/teams/team-1/requests", headers={"host": "localhost"})
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200


def test_direct_team_leader_role_does_not_authorize_team_actions(client, monkeypatch):
    engine = _engine()
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO roles VALUES (998, 'TEAM_LEADER')"))
        connection.execute(text("INSERT INTO user_roles VALUES ('user-1', 998)"))
        connection.execute(text("INSERT INTO team_members VALUES ('team-1', 'user-1', 'ACTIVE')"))

    monkeypatch.setattr(access_management, "get_engine", lambda: engine)
    app.dependency_overrides[get_current_user] = lambda: {"user_id": "user-1"}
    try:
        response = client.get("/api/teams/team-1/requests", headers={"host": "localhost"})
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 403
