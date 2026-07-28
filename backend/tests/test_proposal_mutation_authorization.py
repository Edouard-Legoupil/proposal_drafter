import uuid
from pathlib import Path

from sqlalchemy import text


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


def test_submit_does_not_mutate_a_foreign_proposal(authenticated_client, db_session):
    foreign_owner = _insert_user(db_session, email="foreign-owner@example.com")
    proposal_id = _insert_proposal(db_session, foreign_owner)

    response = authenticated_client.post(f"/api/proposals/{proposal_id}/submit")

    assert response.status_code == 404
    history_count = db_session.execute(
        text("SELECT COUNT(*) FROM proposal_status_history WHERE proposal_id = :proposal_id"),
        {"proposal_id": proposal_id},
    ).scalar_one()
    assert history_count == 0


def test_submit_updates_an_owned_proposal(authenticated_client, db_session):
    owner_id = db_session.execute(text("SELECT id FROM users WHERE email = 'test@example.com'")).scalar_one()
    proposal_id = _insert_proposal(db_session, owner_id)

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
