import uuid

from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

from backend.api import auth


def _engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE roles (id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL)"))
        connection.execute(text("INSERT INTO roles (id, name) VALUES (1, 'proposal writer'), (6, 'system admin')"))
        connection.execute(text("CREATE TABLE teams (id TEXT PRIMARY KEY, name TEXT UNIQUE NOT NULL)"))
        connection.execute(
            text(
                """
                CREATE TABLE users (
                    id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, name TEXT,
                    team_id TEXT, password TEXT NOT NULL, security_questions TEXT,
                    geographic_coverage_type TEXT, geographic_coverage_region TEXT,
                    geographic_coverage_country TEXT
                )
                """
            )
        )
        connection.execute(
            text(
                "CREATE TABLE user_roles "
                "(user_id TEXT NOT NULL, role_id INTEGER NOT NULL, PRIMARY KEY (user_id, role_id))"
            )
        )
    return engine


def test_signup_ignores_client_supplied_roles(client, monkeypatch):
    engine = _engine()

    async def no_rate_limit(*_args, **_kwargs):
        return None

    monkeypatch.setattr(auth, "get_engine", lambda: engine)
    monkeypatch.setattr(auth, "check_api_rate_limit", no_rate_limit)

    response = client.post(
        "/api/signup",
        headers={"host": "localhost"},
        json={
            "username": "New User",
            "email": "new@example.com",
            "password": "strong-password",
            "team_id": str(uuid.uuid4()),
            "security_question": "First pet?",
            "security_answer": "Otter",
            "settings": {
                "roles": [6],
                "geographic_coverage_type": "global",
            },
        },
    )

    assert response.status_code == 201
    with engine.connect() as connection:
        assigned_roles = (
            connection.execute(
                text(
                    """
                SELECT r.name FROM roles r
                JOIN user_roles ur ON ur.role_id = r.id
                JOIN users u ON u.id = ur.user_id
                WHERE u.email = :email
                """
                ),
                {"email": "new@example.com"},
            )
            .scalars()
            .all()
        )

    assert assigned_roles == ["proposal writer"]


def test_signup_is_not_available_when_local_authentication_is_disabled(client, monkeypatch):
    monkeypatch.setattr(auth, "local_authentication_enabled", lambda: False)

    response = client.post("/api/signup", headers={"host": "localhost"}, json={})

    assert response.status_code == 404
    assert response.json() == {"detail": "Not found."}
