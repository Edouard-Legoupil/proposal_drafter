import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy import JSON, bindparam, text

from backend.api import knowledge, proposals
from backend.core.authorization import check_object_access
from backend.core.security import get_current_user
from backend.main import app


def _seed_object_scope(
    test_engine,
    *,
    membership=True,
    role=True,
    role_key="proposal writer",
    team_grant=True,
    user_grant=False,
    permissions=None,
):
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
                "VALUES (1, :role_key, :role_key, 'ProposalWorkspace')"
            ),
            {"role_key": role_key},
        )
        if membership:
            connection.execute(
                text("INSERT INTO team_members (team_id, user_id, status) " "VALUES (:team, :user, 'ACTIVE')"),
                ids,
            )
        if role:
            connection.execute(
                text("INSERT INTO team_roles (team_id, role_id, role_key) VALUES (:team, 1, :role_key)"),
                {**ids, "role_key": role_key},
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
                    "permissions": permissions or ["read"],
                },
            )
    return ids


def _current_user(ids, *, roles=None, settings=None):
    return {
        "user_id": ids["user"],
        "is_admin": False,
        "active_team": {"id": ids["team"], "name": "Team One"},
        "roles": roles or ["proposal writer"],
        "settings": settings or {},
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


@pytest.mark.asyncio
async def test_proposal_reviewer_cannot_edit_or_delete(test_engine):
    ids = _seed_object_scope(
        test_engine,
        role_key="project reviewer",
        permissions=["read", "edit", "delete"],
    )
    current_user = _current_user(ids, roles=["project reviewer"])

    assert await check_object_access("proposal", ids["proposal"], current_user, "read") is True
    for permission in ("edit", "delete"):
        with pytest.raises(HTTPException) as exc:
            await check_object_access("proposal", ids["proposal"], current_user, permission)
        assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_scoped_setting_filters_proposal_objects(test_engine):
    ids = _seed_object_scope(test_engine)
    with test_engine.begin() as connection:
        connection.execute(text("INSERT INTO donors (id, name) VALUES ('donor-1', 'Donor One')"))
        connection.execute(
            text("INSERT INTO proposal_donors (proposal_id, donor_id) VALUES (:proposal, 'donor-1')"),
            ids,
        )

    denied_user = _current_user(ids, settings={"proposal writer": {"donor": "donor-2"}})
    with pytest.raises(HTTPException) as exc:
        await check_object_access("proposal", ids["proposal"], denied_user, "read")
    assert exc.value.status_code == 403

    allowed_user = _current_user(ids, settings={"proposal writer": {"donor": "donor-1"}})
    assert await check_object_access("proposal", ids["proposal"], allowed_user, "read") is True


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        (
            "post",
            "/api/regenerate_section/proposal-1",
            {
                "section": "Summary",
                "concise_input": "Shorten it",
                "form_data": {},
                "project_description": "Description",
            },
        ),
        (
            "post",
            "/api/update-section-content",
            {
                "proposal_id": "00000000-0000-0000-0000-000000000001",
                "section": "Summary",
                "content": "Updated",
            },
        ),
        ("post", "/api/proposals/00000000-0000-0000-0000-000000000001/submit", None),
    ],
)
def test_proposal_mutations_call_strict_object_policy(client, monkeypatch, method, path, payload):
    async def deny(*_args, **_kwargs):
        raise HTTPException(status_code=403, detail="strict policy denial")

    monkeypatch.setattr(proposals, "check_object_access", deny)
    app.dependency_overrides[get_current_user] = lambda: {
        "user_id": "user-1",
        "active_team": {"id": "team-1"},
        "roles": ["proposal writer"],
        "is_admin": False,
    }
    try:
        response = getattr(client, method)(path, json=payload) if payload is not None else getattr(client, method)(path)
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 403
    assert response.json()["detail"] == "strict policy denial"


def test_knowledge_history_calls_strict_object_policy(client, monkeypatch):
    async def deny(*_args, **_kwargs):
        raise HTTPException(status_code=403, detail="strict policy denial")

    monkeypatch.setattr(knowledge, "check_object_access", deny)
    app.dependency_overrides[get_current_user] = lambda: {
        "user_id": "user-1",
        "active_team": {"id": "team-1"},
        "roles": ["knowledge manager donors"],
        "is_admin": False,
    }
    try:
        response = client.get("/api/knowledge-cards/00000000-0000-0000-0000-000000000001/history")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 403
    assert response.json()["detail"] == "strict policy denial"


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("post", "/api/create-session", {"form_data": {}, "project_description": "Description"}),
        ("get", "/api/templates/", None),
        ("get", "/api/knowledge-cards", None),
    ],
)
def test_component_entry_points_require_active_team_role(client, method, path, payload):
    app.dependency_overrides[get_current_user] = lambda: {
        "user_id": "user-1",
        "active_team": {"id": "team-1"},
        "roles": [],
        "is_admin": False,
    }
    try:
        response = getattr(client, method)(path, json=payload) if payload is not None else getattr(client, method)(path)
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 403
