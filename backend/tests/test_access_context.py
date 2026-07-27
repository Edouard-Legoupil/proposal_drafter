import jwt
import pytest
from fastapi import HTTPException
from sqlalchemy import text
from starlette.requests import Request

from backend.core import authorization, security
from backend.services.access_management_service import AccessManagementService


@pytest.fixture
def access_data(test_engine):
    with test_engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO roles (id, name, role_key, component) VALUES "
                "(1, 'direct ordinary', 'direct ordinary', 'Legacy'), "
                "(2, 'access metrics', 'access metrics', 'Metrics'), "
                "(3, 'access template', 'access template', 'Templates'), "
                "(4, 'TEAM_LEADER', 'TEAM_LEADER', NULL), "
                "(5, 'system admin', 'system admin', NULL), "
                "(6, 'non component', 'non component', NULL)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO teams (id, name) VALUES "
                "('team-a', 'Team A'), ('team-b', 'Team B'), "
                "('team-pending', 'Pending'), ('team-rejected', 'Rejected')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO users (id, email, password, name) VALUES "
                "('user-1', 'user@example.org', 'secret', 'User'), "
                "('admin-1', 'admin@example.org', 'secret', 'Admin')"
            )
        )
        connection.execute(
            text("INSERT INTO user_roles (user_id, role_id) VALUES " "('user-1', 1), ('admin-1', 1), ('admin-1', 5)")
        )
        connection.execute(
            text(
                "INSERT INTO team_members (team_id, user_id, status) VALUES "
                "('team-a', 'user-1', 'ACTIVE'), "
                "('team-b', 'user-1', 'ACTIVE'), "
                "('team-pending', 'user-1', 'PENDING'), "
                "('team-rejected', 'user-1', 'REJECTED')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO team_roles (team_id, role_id, role_key) VALUES "
                "('team-a', 2, 'access metrics'), "
                "('team-a', 6, 'non component'), "
                "('team-b', 3, 'access template'), "
                "('team-pending', 3, 'access template'), "
                "('team-rejected', 3, 'access template')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO team_member_roles (team_id, user_id, role_key, assigned_by) "
                "VALUES ('team-a', 'user-1', 'TEAM_LEADER', 'admin-1')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO access_settings "
                "(user_id, team_id, role_key, key, value, created_by) VALUES "
                "('user-1', 'team-a', 'access metrics', 'region', '\"east\"', 'admin-1'), "
                "('user-1', 'team-a', 'access template', 'hidden', 'true', 'admin-1'), "
                "('user-1', 'team-b', 'access template', 'format', '\"docx\"', 'admin-1')"
            )
        )
    return test_engine


def _service(engine):
    return AccessManagementService(engine)


def test_context_ignores_direct_ordinary_roles_and_scopes_roles_to_selected_team(access_data):
    with _service(access_data) as service:
        team_a = service.resolve_context("user-1", "team-a")
        team_b = service.resolve_context("user-1", "team-b")

    assert team_a.roles == {"access metrics"}
    assert team_b.roles == {"access template"}
    assert "direct ordinary" not in team_a.roles | team_b.roles


def test_context_exposes_only_active_memberships_and_uses_safe_deterministic_fallback(access_data):
    with _service(access_data) as service:
        context = service.resolve_context("user-1")

    assert [membership["id"] for membership in context.memberships] == ["team-a", "team-b"]
    assert context.active_team == {"id": "team-a", "name": "Team A"}


@pytest.mark.parametrize("team_id", ["team-pending", "team-rejected", "missing-team"])
def test_context_rejects_selected_team_without_active_membership(access_data, team_id):
    with _service(access_data) as service, pytest.raises(HTTPException) as exc_info:
        service.resolve_context("user-1", team_id)

    assert exc_info.value.status_code == 403


def test_context_scopes_leadership_and_settings_after_team_role(access_data):
    with _service(access_data) as service:
        team_a = service.resolve_context("user-1", "team-a")
        team_b = service.resolve_context("user-1", "team-b")

    assert team_a.team_leadership is True
    assert team_b.team_leadership is False
    assert team_a.settings == {"access metrics": {"region": "east"}}
    assert team_b.settings == {"access template": {"format": "docx"}}


def test_direct_system_admin_is_global_but_does_not_restore_direct_ordinary_roles(access_data):
    with _service(access_data) as service:
        context = service.resolve_context("admin-1")

    assert context.is_admin is True
    assert context.active_team is None
    assert context.roles == set()


def test_get_current_user_uses_requested_active_team_context(access_data, monkeypatch):
    token = jwt.encode({"email": "user@example.org"}, str(security.SECRET_KEY), algorithm="HS256")
    request = Request(
        {
            "type": "http",
            "headers": [
                (b"cookie", f"auth_token={token}".encode()),
                (b"x-team-id", b"team-b"),
            ],
        }
    )
    monkeypatch.setattr(security, "get_engine", lambda: access_data)
    monkeypatch.setattr(security, "is_session_token_active", lambda _user_id, _token: True)

    current_user = security.get_current_user(request)

    assert current_user["active_team"] == {"id": "team-b", "name": "Team B"}
    assert current_user["roles"] == ["access template"]
    assert current_user["all_roles"] == ["access template"]
    assert current_user["team_leadership"] is False
    assert current_user["settings"] == {"access template": {"format": "docx"}}


def test_role_helpers_ignore_legacy_all_roles_and_use_scoped_roles():
    current_user = {
        "roles": ["access metrics"],
        "all_roles": ["access metrics", "access template"],
        "is_admin": False,
    }

    assert authorization.get_user_roles_with_inheritance(current_user) == ["access metrics"]
    assert authorization.has_permission(current_user, "access template") is False

    dependency = security.require_any_role("access template")
    with pytest.raises(HTTPException) as exc_info:
        dependency(current_user=current_user)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_team_membership_helper_uses_only_active_team_context():
    current_user = {
        "user_id": "user-1",
        "active_team": {"id": "team-a", "name": "Team A"},
        "is_admin": False,
    }

    assert await authorization.verify_team_membership("team-a", current_user) is True
    with pytest.raises(HTTPException) as exc_info:
        await authorization.verify_team_membership("team-b", current_user)
    assert exc_info.value.status_code == 403
