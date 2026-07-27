from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.core import authorization
from backend.core.security import get_current_user
from backend.models.user import User
from backend.utils import auth_helpers


@pytest.mark.asyncio
@pytest.mark.parametrize("membership_status", ["PENDING", "REJECTED"])
async def test_verify_team_membership_rejects_inactive_rows(test_engine, monkeypatch, membership_status):
    with test_engine.begin() as connection:
        connection.execute(text("INSERT INTO teams (id, name) VALUES ('team-1', 'Team 1')"))
        connection.execute(
            text("INSERT INTO users (id, email, password) VALUES ('user-1', 'user@example.org', 'secret')")
        )
        connection.execute(
            text("INSERT INTO team_members (team_id, user_id, status) " "VALUES ('team-1', 'user-1', :status)"),
            {"status": membership_status},
        )

    monkeypatch.setattr(authorization, "get_db_connection", test_engine.connect)

    with pytest.raises(HTTPException) as exc_info:
        await authorization.verify_team_membership("team-1", {"user_id": "user-1"})

    assert exc_info.value.status_code == 403


@pytest.mark.parametrize("membership_status", ["PENDING", "REJECTED"])
def test_auth_helper_rejects_inactive_membership(test_engine, membership_status):
    with test_engine.begin() as connection:
        connection.execute(text("INSERT INTO teams (id, name) VALUES ('team-1', 'Team 1')"))
        connection.execute(
            text("INSERT INTO users (id, email, password) VALUES ('user-1', 'user@example.org', 'secret')")
        )
        connection.execute(
            text("INSERT INTO team_members (team_id, user_id, status) " "VALUES ('team-1', 'user-1', :status)"),
            {"status": membership_status},
        )

    with Session(test_engine) as session:
        assert auth_helpers.is_team_member("user-1", "team-1", session) is False


def test_auth_helper_enumerates_only_active_teams(test_engine):
    with test_engine.begin() as connection:
        connection.execute(
            text("INSERT INTO teams (id, name) VALUES ('active-team', 'Active'), ('pending-team', 'Pending')")
        )
        connection.execute(
            text("INSERT INTO users (id, email, password) VALUES ('user-1', 'user@example.org', 'secret')")
        )
        connection.execute(
            text(
                "INSERT INTO team_members (team_id, user_id, status) VALUES "
                "('active-team', 'user-1', 'ACTIVE'), "
                "('pending-team', 'user-1', 'PENDING')"
            )
        )

    with Session(test_engine) as session:
        assert auth_helpers.get_user_team_ids("user-1", session) == ["active-team"]


def test_resource_access_rejects_inactive_team_membership(test_engine):
    with test_engine.begin() as connection:
        connection.execute(text("INSERT INTO teams (id, name) VALUES ('team-1', 'Team 1')"))
        connection.execute(
            text("INSERT INTO users (id, email, password) VALUES ('user-1', 'user@example.org', 'secret')")
        )
        connection.execute(
            text("INSERT INTO team_members (team_id, user_id, status) " "VALUES ('team-1', 'user-1', 'PENDING')")
        )

    resource = SimpleNamespace(user_id="owner-1", team_id="team-1", donor_id=None)

    with test_engine.connect() as connection:

        class ResourceSession:
            def get(self, _model, _resource_id):
                return resource

            def execute(self, statement, parameters):
                return connection.execute(statement, parameters)

        assert auth_helpers.has_resource_access("proposal", "proposal-1", "user-1", ResourceSession()) is False


def test_user_model_membership_helpers_return_only_active_teams(test_engine):
    with test_engine.begin() as connection:
        connection.execute(
            text("INSERT INTO teams (id, name) VALUES ('active-team', 'Active'), ('rejected-team', 'Rejected')")
        )
        connection.execute(
            text("INSERT INTO users (id, email, password) VALUES ('user-1', 'user@example.org', 'secret')")
        )
        connection.execute(
            text(
                "INSERT INTO team_members (team_id, user_id, status) VALUES "
                "('active-team', 'user-1', 'ACTIVE'), "
                "('rejected-team', 'user-1', 'REJECTED')"
            )
        )

    with Session(test_engine) as session:
        user = session.get(User, "user-1")
        assert user is not None
        assert user.is_team_member("rejected-team", session) is False
        assert user.get_team_ids(session) == ["active-team"]


def test_available_team_settings_excludes_only_active_or_pending_memberships(authenticated_client, db_session):
    user_id = authenticated_client.app.dependency_overrides[get_current_user]()["user_id"]
    db_session.execute(
        text(
            "INSERT INTO teams (id, name) VALUES "
            "('active-team', 'Active'), "
            "('rejected-team', 'Rejected'), "
            "('available-team', 'Available')"
        )
    )
    db_session.execute(
        text(
            "INSERT INTO team_members (team_id, user_id, status) VALUES "
            "('active-team', :user_id, 'ACTIVE'), "
            "('rejected-team', :user_id, 'REJECTED')"
        ),
        {"user_id": user_id},
    )
    db_session.execute(
        text(
            "INSERT INTO user_settings_requests (user_id, setting_type, setting_value, status) "
            "VALUES (:user_id, 'team_membership', 'rejected-team', 'approved')"
        ),
        {"user_id": user_id},
    )
    db_session.commit()

    response = authenticated_client.get("/api/settings/requests")

    assert response.status_code == 200
    available_team_ids = {team["id"] for team in response.json()["available_settings"]["team_membership"]}
    assert "active-team" not in available_team_ids
    assert {"rejected-team", "available-team"} <= available_team_ids
