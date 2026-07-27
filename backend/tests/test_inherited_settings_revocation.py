import asyncio

from sqlalchemy import text

from backend.api import team_settings as team_settings_api
from backend.core.security import get_current_user


def _approved_settings(client):
    response = client.get("/api/users/me/approved-settings")
    assert response.status_code == 200
    return {(setting["setting_type"], setting["setting_value"]) for setting in response.json()["approved_settings"]}


def test_system_inherited_setting_requires_a_current_active_matching_team(authenticated_client, db_session):
    user_id = authenticated_client.app.dependency_overrides[get_current_user]()["user_id"]
    db_session.execute(text("INSERT INTO teams (id, name) VALUES ('team-1', 'Team 1'), ('team-2', 'Team 2')"))
    db_session.execute(
        text(
            "INSERT INTO team_members (team_id, user_id, status) VALUES "
            "('team-1', :user_id, 'ACTIVE'), ('team-2', :user_id, 'ACTIVE')"
        ),
        {"user_id": user_id},
    )
    db_session.execute(
        text(
            "INSERT INTO team_settings (team_id, setting_type, setting_value) VALUES "
            "('team-1', ' DONOR_FOCAL ', 'donor-1'), "
            "('team-2', 'donor_focal', ' DONOR-1 ')"
        )
    )
    db_session.execute(
        text(
            "INSERT INTO user_settings_requests "
            "(user_id, setting_type, setting_value, status, approved_by) "
            "VALUES (:user_id, 'donor_focal', 'donor-1', 'approved', NULL)"
        ),
        {"user_id": user_id},
    )
    db_session.commit()

    assert ("donor_focal", "donor-1") in _approved_settings(authenticated_client)

    with db_session.begin():
        db_session.execute(text("UPDATE team_members SET status = 'REJECTED' WHERE team_id = 'team-1'"))
    assert ("donor_focal", "donor-1") in _approved_settings(authenticated_client)

    with db_session.begin():
        db_session.execute(text("UPDATE team_members SET status = 'REJECTED' WHERE team_id = 'team-2'"))
    assert ("donor_focal", "donor-1") not in _approved_settings(authenticated_client)

    with db_session.begin():
        audit_row_count = db_session.execute(
            text("SELECT COUNT(*) FROM user_settings_requests " "WHERE user_id = :user_id AND approved_by IS NULL"),
            {"user_id": user_id},
        ).scalar_one()
    assert audit_row_count == 1


def test_admin_approved_setting_remains_effective_without_active_team(authenticated_client, db_session):
    user_id = authenticated_client.app.dependency_overrides[get_current_user]()["user_id"]
    db_session.execute(
        text(
            "INSERT INTO users (id, email, name, password) "
            "VALUES ('admin-1', 'admin@example.org', 'Admin', 'secret')"
        )
    )
    db_session.execute(
        text(
            "INSERT INTO user_settings_requests "
            "(user_id, setting_type, setting_value, status, approved_by) "
            "VALUES (:user_id, 'outcome_focal', 'outcome-1', 'approved', 'admin-1')"
        ),
        {"user_id": user_id},
    )
    db_session.commit()

    assert ("outcome_focal", "outcome-1") in _approved_settings(authenticated_client)


def test_revoked_system_inherited_setting_becomes_requestable(authenticated_client, db_session):
    user_id = authenticated_client.app.dependency_overrides[get_current_user]()["user_id"]
    db_session.execute(text("INSERT INTO donors (id, name) VALUES ('donor-1', 'Donor 1')"))
    db_session.execute(
        text(
            "INSERT INTO user_settings_requests "
            "(user_id, setting_type, setting_value, status, approved_by) "
            "VALUES (:user_id, 'donor_focal', 'donor-1', 'approved', NULL)"
        ),
        {"user_id": user_id},
    )
    db_session.commit()

    response = authenticated_client.get("/api/settings/requests")

    assert response.status_code == 200
    available_donors = response.json()["available_settings"]["donor_focal"]
    assert {donor["id"] for donor in available_donors} >= {"donor-1"}


def test_removing_one_team_grant_preserves_inherited_audit_row_and_other_active_grant(
    authenticated_client, db_session, monkeypatch
):
    user_id = authenticated_client.app.dependency_overrides[get_current_user]()["user_id"]
    db_session.execute(text("INSERT INTO teams (id, name) VALUES ('team-1', 'Team 1'), ('team-2', 'Team 2')"))
    db_session.execute(
        text(
            "INSERT INTO team_members (team_id, user_id, status) VALUES "
            "('team-1', :user_id, 'ACTIVE'), ('team-2', :user_id, 'ACTIVE')"
        ),
        {"user_id": user_id},
    )
    db_session.execute(
        text(
            "INSERT INTO team_settings (team_id, setting_type, setting_value) VALUES "
            "('team-1', 'donor_focal', 'donor-1'), ('team-2', 'donor_focal', 'donor-1')"
        )
    )
    db_session.execute(
        text(
            "INSERT INTO user_settings_requests "
            "(user_id, setting_type, setting_value, status, approved_by) "
            "VALUES (:user_id, 'donor_focal', 'donor-1', 'approved', NULL)"
        ),
        {"user_id": user_id},
    )
    setting_id = db_session.execute(text("SELECT id FROM team_settings WHERE team_id = 'team-1'")).scalar_one()
    db_session.commit()

    monkeypatch.setattr(team_settings_api, "get_engine", lambda: db_session.engine)
    result = asyncio.run(team_settings_api.remove_team_setting(setting_id, admin={"user_id": "admin-1"}))

    assert result["message"] == "Team setting removed successfully"
    assert ("donor_focal", "donor-1") in _approved_settings(authenticated_client)
    with db_session.begin():
        remaining_grants = db_session.execute(
            text(
                "SELECT team_id, COUNT(*) FROM team_settings "
                "WHERE setting_type = 'donor_focal' AND setting_value = 'donor-1' GROUP BY team_id"
            )
        ).all()
        audit_rows = db_session.execute(
            text("SELECT COUNT(*) FROM user_settings_requests " "WHERE user_id = :user_id AND approved_by IS NULL"),
            {"user_id": user_id},
        ).scalar_one()
    assert remaining_grants == [("team-2", 1)]
    assert audit_rows == 1
