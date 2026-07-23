from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

from backend.api import proposals
from backend.core.security import get_current_user
from backend.main import app


def _engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE donors (id TEXT PRIMARY KEY, name TEXT, created_by TEXT)"))
        connection.execute(text("CREATE TABLE outcomes (id TEXT PRIMARY KEY, name TEXT, created_by TEXT)"))
        connection.execute(
            text(
                "CREATE TABLE field_contexts "
                "(id TEXT PRIMARY KEY, title TEXT, name TEXT, category TEXT, geographic_coverage TEXT, created_by TEXT)"
            )
        )
    return engine


def _set_user(user):
    app.dependency_overrides[get_current_user] = lambda: user


def test_regular_user_cannot_create_global_knowledge_dimensions(client, monkeypatch):
    monkeypatch.setattr(proposals, "get_engine", _engine)
    _set_user({"user_id": "user-1", "roles": ["proposal writer"]})

    try:
        requests = [
            ("/api/donors", {"name": "Donor"}),
            ("/api/outcomes", {"name": "Outcome"}),
            ("/api/field-contexts", {"name": "Context", "category": "country"}),
        ]
        responses = [client.post(path, headers={"host": "localhost"}, json=body) for path, body in requests]
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert [response.status_code for response in responses] == [403, 403, 403]


def test_matching_knowledge_manager_can_create_dimension(client, monkeypatch):
    engine = _engine()
    monkeypatch.setattr(proposals, "get_engine", lambda: engine)
    _set_user({"user_id": "manager-1", "roles": ["knowledge manager donors"]})

    try:
        response = client.post(
            "/api/donors",
            headers={"host": "localhost"},
            json={"name": "Approved Donor"},
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 201
