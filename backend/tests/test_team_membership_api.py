from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

from backend.api import team_membership
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
            text(
                """
                CREATE TABLE team_members (
                    team_id TEXT, user_id TEXT, status TEXT,
                    PRIMARY KEY (team_id, user_id)
                )
                """
            )
        )
        connection.execute(text("INSERT INTO teams VALUES ('team-1', 'Team One')"))
        connection.execute(text("INSERT INTO users VALUES ('user-1', 'User One', 'user@example.com')"))
    return engine


def test_join_request_is_committed(client, monkeypatch):
    engine = _engine()
    monkeypatch.setattr(team_membership, "get_engine", lambda: engine)
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
    monkeypatch.setattr(team_membership, "get_engine", lambda: engine)
    app.dependency_overrides[get_current_user] = lambda: {"user_id": "user-1"}
    try:
        response = client.get(
            "/api/teams/team-1/requests",
            headers={"host": "localhost"},
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 403
