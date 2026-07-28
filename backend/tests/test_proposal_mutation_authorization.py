import uuid
from pathlib import Path

from sqlalchemy import JSON, bindparam
from sqlalchemy import text

from backend.core.security import get_current_user


def _insert_user(connection, *, email: str) -> str:
    user_id = str(uuid.uuid4())
    connection.execute(
        text("INSERT INTO users (id, email, password, name) VALUES (:id, :email, 'password', 'Owner')"),
        {"id": user_id, "email": email},
    )
    return user_id


def _insert_proposal(connection, owner_id: str) -> str:
    proposal_id = str(uuid.uuid4())
    connection.execute(
        text(
            "INSERT INTO proposals "
            "(id, user_id, form_data, project_description, generated_sections, status, created_by, updated_by) "
            "VALUES (:id, :owner, '{}', 'Description', '{}', 'draft', :owner, :owner)"
        ),
        {"id": proposal_id, "owner": owner_id},
    )
    return proposal_id


def _grant_proposal_access(authenticated_client, connection, proposal_id: str, owner_id: str) -> None:
    team_id = str(uuid.uuid4())
    grant_id = str(uuid.uuid4())
    connection.execute(text("INSERT INTO teams (id, name) VALUES (:id, 'Proposal Team')"), {"id": team_id})
    connection.execute(
        text("INSERT INTO team_members (team_id, user_id, status) VALUES (:team, :user, 'ACTIVE')"),
        {"team": team_id, "user": owner_id},
    )
    connection.execute(
        text(
            "INSERT INTO roles (id, name, role_key, component) "
            "VALUES (991, 'proposal writer', 'proposal writer', 'ProposalWorkspace')"
        )
    )
    connection.execute(
        text("INSERT INTO team_roles (team_id, role_id, role_key) VALUES (:team, 991, 'proposal writer')"),
        {"team": team_id},
    )
    connection.execute(
        text("UPDATE proposals SET team_id = :team WHERE id = :proposal"),
        {"team": team_id, "proposal": proposal_id},
    )
    statement = text(
        "INSERT INTO resource_access_grants "
        "(id, resource_type, resource_id, subject_type, subject_id, permissions, created_by) "
        "VALUES (:id, 'proposals', :proposal, 'team', :team, :permissions, :user)"
    ).bindparams(bindparam("permissions", type_=JSON))
    connection.execute(
        statement,
        {"id": grant_id, "proposal": proposal_id, "team": team_id, "permissions": ["read", "edit"], "user": owner_id},
    )
    current = authenticated_client.app.dependency_overrides[get_current_user]()
    authenticated_client.app.dependency_overrides[get_current_user] = lambda: {
        **current,
        "active_team": {"id": team_id, "name": "Proposal Team"},
        "roles": ["proposal writer"],
        "settings": {},
    }


def test_submit_does_not_mutate_a_foreign_proposal(authenticated_client, db_session):
    foreign_owner = _insert_user(db_session, email="foreign-owner@example.com")
    proposal_id = _insert_proposal(db_session, foreign_owner)

    response = authenticated_client.post(f"/api/proposals/{proposal_id}/submit")

    assert response.status_code == 403
    history_count = db_session.execute(
        text("SELECT COUNT(*) FROM proposal_status_history WHERE proposal_id = :proposal_id"),
        {"proposal_id": proposal_id},
    ).scalar_one()
    assert history_count == 0


def test_submit_updates_an_owned_proposal(authenticated_client, db_session):
    owner_id = db_session.execute(text("SELECT id FROM users WHERE email = 'test@example.com'")).scalar_one()
    proposal_id = _insert_proposal(db_session, owner_id)
    _grant_proposal_access(authenticated_client, db_session, proposal_id, owner_id)
    db_session.commit()

    response = authenticated_client.post(f"/api/proposals/{proposal_id}/submit")

    assert response.status_code == 200, response.text
    status = db_session.execute(text("SELECT status FROM proposals WHERE id = :id"), {"id": proposal_id}).scalar_one()
    assert status == "submitted"


def test_authorization_queries_use_team_columns_installed_by_access_migration():
    root = Path(__file__).resolve().parents[2]
    authorization = (root / "backend/core/authorization.py").read_text(encoding="utf-8")
    migration = (root / "db/migrations/20260727_access_management_compliance.sql").read_text(encoding="utf-8")
    assert "SELECT id, user_id, team_id FROM proposals" in authorization
    assert "SELECT id, created_by, team_id FROM knowledge_cards" in authorization
    assert "SELECT id, created_by, team_id FROM templates" in authorization
    assert "ALTER TABLE proposals ADD COLUMN IF NOT EXISTS team_id" in migration
    assert "ALTER TABLE knowledge_cards ADD COLUMN IF NOT EXISTS team_id" in migration
    assert "ALTER TABLE templates ADD COLUMN IF NOT EXISTS team_id" in migration
