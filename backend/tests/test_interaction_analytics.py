from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

from backend.core.security import get_current_user
from backend.main import app


def _engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE user_interactions (
                    interaction_type TEXT, session_id TEXT, user_id TEXT,
                    component_name TEXT, was_successful BOOLEAN,
                    interaction_timestamp DATETIME
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE wizard_interactions (
                    feedback_score INTEGER, was_helpful BOOLEAN,
                    search_query TEXT, interaction_timestamp DATETIME
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO user_interactions VALUES
                ('click', 'session-1', 'user-1', 'Wizard', 1, CURRENT_TIMESTAMP),
                ('error', 'session-1', 'user-1', 'Wizard', 0, CURRENT_TIMESTAMP)
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO wizard_interactions VALUES
                (5, 1, 'How do I draft?', CURRENT_TIMESTAMP)
                """
            )
        )
    return engine


def test_interaction_analytics_returns_aggregates_for_authorized_user(client, monkeypatch):
    from backend.api import interaction_analytics

    engine = _engine()
    monkeypatch.setattr(interaction_analytics, "get_engine", lambda: engine)
    app.dependency_overrides[get_current_user] = lambda: {
        "user_id": "admin-1",
        "roles": ["ui_analysis"],
    }

    try:
        response = client.get(
            "/api/interactions/analytics/?date_range=30d",
            headers={"host": "localhost"},
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_interactions"] == 2
    assert payload["total_sessions"] == 1
    assert payload["total_users"] == 1
    assert payload["error_rate"] == 50.0
    assert payload["wizard_usage_stats"]["total_usage"] == 1


def test_interaction_analytics_rejects_user_without_role(client):
    app.dependency_overrides[get_current_user] = lambda: {
        "user_id": "user-1",
        "roles": ["proposal writer"],
    }
    try:
        response = client.get(
            "/api/interactions/analytics/",
            headers={"host": "localhost"},
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 403
