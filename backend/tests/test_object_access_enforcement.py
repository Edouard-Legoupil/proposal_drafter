import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy import JSON, bindparam, text

from backend.core.authorization import check_object_access


def _seed_object_scope(test_engine, *, membership=True, role=True, team_grant=True, user_grant=False):
    ids = {name: str(uuid.uuid4()) for name in ("admin", "user", "team", "proposal", "grant")}
    with test_engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO users (id, email, password, name) VALUES "
                "(:admin, 'admin@example.com', 'x', 'Admin'), "
                "(:user, 'user@example.com', 'x', 'User')"
            ),
            ids,
        )
        connection.execute(text("INSERT INTO teams (id, name, created_by) VALUES (:team, 'Team One', :admin)"), ids)
        connection.execute(
            text(
                "INSERT INTO roles (id, name, role_key, component) "
                "VALUES (1, 'proposal writer', 'proposal writer', 'ProposalWorkspace')"
            )
        )
        if membership:
            connection.execute(
                text("INSERT INTO team_members (team_id, user_id, status) " "VALUES (:team, :user, 'ACTIVE')"),
                ids,
            )
        if role:
            connection.execute(
                text("INSERT INTO team_roles (team_id, role_id, role_key) " "VALUES (:team, 1, 'proposal writer')"),
                ids,
            )
        connection.execute(
            text(
                "INSERT INTO proposals "
                "(id, user_id, team_id, form_data, project_description, status, created_by, updated_by) "
                "VALUES (:proposal, :user, :team, '{}', 'Description', 'draft', :user, :user)"
            ),
            ids,
        )
        if team_grant or user_grant:
            grant_statement = text(
                "INSERT INTO resource_access_grants "
                "(id, resource_type, resource_id, subject_type, subject_id, permissions, created_by) "
                "VALUES (:grant, 'proposals', :proposal, :subject_type, :subject_id, :permissions, :admin)"
            ).bindparams(bindparam("permissions", type_=JSON))
            connection.execute(
                grant_statement,
                {
                    **ids,
                    "subject_type": "team" if team_grant else "user",
                    "subject_id": ids["team"] if team_grant else ids["user"],
                    "permissions": ["read"],
                },
            )
    return ids


def _current_user(ids):
    return {
        "user_id": ids["user"],
        "is_admin": False,
        "active_team": {"id": ids["team"], "name": "Team One"},
        "roles": ["proposal writer"],
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("membership", "role", "team_grant"),
    [(False, True, True), (True, False, True), (True, True, False)],
)
async def test_object_access_requires_membership_role_and_team_grant(test_engine, membership, role, team_grant):
    ids = _seed_object_scope(
        test_engine,
        membership=membership,
        role=role,
        team_grant=team_grant,
    )

    with pytest.raises(HTTPException) as exc:
        await check_object_access("proposal", ids["proposal"], _current_user(ids), "read")

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_owner_and_direct_user_grant_do_not_bypass_team_gates(test_engine):
    ids = _seed_object_scope(test_engine, team_grant=False, user_grant=True)

    with pytest.raises(HTTPException) as exc:
        await check_object_access("proposal", ids["proposal"], _current_user(ids), "read")

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_object_access_succeeds_when_all_three_team_gates_pass(test_engine):
    ids = _seed_object_scope(test_engine)

    assert await check_object_access("proposal", ids["proposal"], _current_user(ids), "read") is True
