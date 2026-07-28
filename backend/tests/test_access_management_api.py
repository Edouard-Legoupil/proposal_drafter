import pytest
from sqlalchemy import text

from backend.core.security import get_current_user
from backend.main import app


CANONICAL_ROUTES = [
    ("POST", "/api/teams", {"name": "Operations"}),
    ("GET", "/api/teams", None),
    ("PATCH", "/api/teams/team-1", {"name": "Operations"}),
    ("DELETE", "/api/teams/team-1", None),
    ("GET", "/api/teams/team-1/members", None),
    ("POST", "/api/teams/team-1/members/user-1", None),
    ("DELETE", "/api/teams/team-1/members/user-1", None),
    ("POST", "/api/teams/team-1/join", None),
    ("GET", "/api/teams/team-1/requests", None),
    ("POST", "/api/teams/team-1/approve/user-1", None),
    ("POST", "/api/teams/team-1/reject/user-1", None),
    ("PUT", "/api/teams/team-1/leaders/user-1", None),
    ("DELETE", "/api/teams/team-1/leaders/user-1", None),
    ("GET", "/api/roles", None),
    ("GET", "/api/teams/team-1/roles", None),
    ("POST", "/api/teams/team-1/roles", {"role_key": "proposal writer"}),
    ("DELETE", "/api/teams/team-1/roles/proposal%20writer", None),
]


@pytest.fixture(autouse=True)
def _clear_authentication_override():
    app.dependency_overrides.pop(get_current_user, None)
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.parametrize(("method", "path", "body"), CANONICAL_ROUTES)
def test_every_access_management_route_requires_authentication(client, method, path, body):
    response = client.request(method, path, json=body)

    assert response.status_code == 401


def _actor(user_id="admin-1", *, is_admin=False, leader_team=None):
    return {
        "user_id": user_id,
        "name": user_id,
        "email": f"{user_id}@example.com",
        "is_admin": is_admin,
        "roles": [],
        "active_team": {"id": leader_team, "name": leader_team} if leader_team else None,
        "team_leadership": leader_team is not None,
    }


def _authenticate(actor):
    app.dependency_overrides[get_current_user] = lambda: actor


def _seed_users_and_roles(test_engine):
    with test_engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO users (id, email, password, name) VALUES "
                "('admin-1', 'admin@example.com', 'x', 'Admin'), "
                "('leader-1', 'leader@example.com', 'x', 'Leader'), "
                "('user-1', 'user@example.com', 'x', 'User')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO roles (id, name, role_key, component) VALUES "
                "(1, 'proposal writer', 'proposal writer', 'ProposalWorkspace'), "
                "(2, 'system admin', 'system admin', NULL), "
                "(3, 'TEAM_LEADER', 'TEAM_LEADER', NULL)"
            )
        )


def test_system_admin_can_create_list_and_update_a_team(client, test_engine):
    _seed_users_and_roles(test_engine)
    _authenticate(_actor(is_admin=True))

    created = client.post("/api/teams", json={"name": "Operations", "description": "Field operations"})
    assert created.status_code == 201
    team_id = created.json()["id"]

    listed = client.get("/api/teams")
    assert listed.status_code == 200
    assert listed.json() == {
        "teams": [
            {
                "id": team_id,
                "name": "Operations",
                "description": "Field operations",
            }
        ]
    }

    updated = client.patch(f"/api/teams/{team_id}", json={"name": "Response Operations"})
    assert updated.status_code == 200
    assert updated.json()["name"] == "Response Operations"

    deleted = client.delete(f"/api/teams/{team_id}")
    assert deleted.status_code == 204

    with test_engine.connect() as connection:
        actions = connection.execute(
            text("SELECT action FROM resource_access_audit WHERE resource_type = 'team' ORDER BY created_at, action")
        ).scalars()
        assert set(actions) == {"team.created", "team.updated", "team.deleted"}
        assert connection.execute(text("SELECT COUNT(*) FROM teams WHERE id = :id"), {"id": team_id}).scalar() == 0


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("POST", "/api/teams", {"name": "Forbidden"}),
        ("PATCH", "/api/teams/team-1", {"name": "Forbidden"}),
        ("DELETE", "/api/teams/team-1", None),
        ("POST", "/api/teams/team-1/members/user-1", None),
        ("DELETE", "/api/teams/team-1/members/user-1", None),
        ("PUT", "/api/teams/team-1/leaders/user-1", None),
        ("DELETE", "/api/teams/team-1/leaders/user-1", None),
        ("POST", "/api/teams/team-1/roles", {"role_key": "proposal writer"}),
        ("DELETE", "/api/teams/team-1/roles/proposal%20writer", None),
    ],
)
def test_admin_only_mutations_reject_ordinary_users(client, method, path, body):
    _authenticate(_actor(user_id="user-1"))

    response = client.request(method, path, json=body)

    assert response.status_code == 403


def test_team_delete_conflicts_with_protected_resources_and_preserves_them(client, test_engine):
    _seed_users_and_roles(test_engine)
    with test_engine.begin() as connection:
        connection.execute(text("INSERT INTO teams (id, name, created_by) VALUES ('team-1', 'Team One', 'admin-1')"))
        connection.execute(
            text(
                "INSERT INTO proposals (id, user_id, project_description, team_id) "
                "VALUES ('proposal-1', 'user-1', 'Protected', 'team-1')"
            )
        )
    _authenticate(_actor(is_admin=True))

    response = client.delete("/api/teams/team-1")

    assert response.status_code == 409
    with test_engine.connect() as connection:
        assert connection.execute(text("SELECT COUNT(*) FROM teams WHERE id = 'team-1'")).scalar() == 1
        assert connection.execute(text("SELECT COUNT(*) FROM proposals WHERE id = 'proposal-1'")).scalar() == 1


def test_admin_team_alias_uses_the_same_creation_contract(client, test_engine):
    _seed_users_and_roles(test_engine)
    _authenticate(_actor(is_admin=True))

    response = client.post("/api/admin/teams", json={"name": "Legacy Admin Team"})

    assert response.status_code == 201
    assert response.json()["team"]["name"] == "Legacy Admin Team"


def test_runtime_role_creation_is_absent(client):
    _authenticate(_actor(is_admin=True))

    response = client.post("/api/admin/roles", json={"name": "runtime role"})

    assert response.status_code == 405


def _seed_teams(test_engine):
    _seed_users_and_roles(test_engine)
    with test_engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO teams (id, name, created_by) VALUES "
                "('team-1', 'Team One', 'admin-1'), ('team-2', 'Team Two', 'admin-1')"
            )
        )


def test_admin_can_add_and_remove_an_active_member(client, test_engine):
    _seed_teams(test_engine)
    _authenticate(_actor(is_admin=True))

    added = client.post("/api/teams/team-1/members/user-1")
    assert added.status_code == 201
    assert added.json()["status"] == "ACTIVE"

    duplicate = client.post("/api/teams/team-1/members/user-1")
    assert duplicate.status_code == 409

    members = client.get("/api/teams/team-1/members")
    assert members.status_code == 200
    assert [member["user_id"] for member in members.json()["members"]] == ["user-1"]

    removed = client.delete("/api/teams/team-1/members/user-1")
    assert removed.status_code == 204
    with test_engine.connect() as connection:
        assert connection.execute(text("SELECT COUNT(*) FROM team_members")).scalar() == 0
        actions = set(connection.execute(text("SELECT action FROM resource_access_audit")).scalars())
    assert {"team_member.added", "team_member.removed"} <= actions


def test_join_request_enforces_membership_state_conflicts(client, test_engine):
    _seed_teams(test_engine)
    _authenticate(_actor(user_id="user-1"))

    requested = client.post("/api/teams/team-1/join")
    assert requested.status_code == 200
    assert requested.json()["status"] == "PENDING"

    duplicate = client.post("/api/teams/team-1/join")
    assert duplicate.status_code == 409

    with test_engine.begin() as connection:
        connection.execute(
            text("UPDATE team_members SET status = 'REJECTED' " "WHERE team_id = 'team-1' AND user_id = 'user-1'")
        )
    rerequested = client.post("/api/teams/team-1/join")
    assert rerequested.status_code == 200
    assert rerequested.json()["status"] == "PENDING"


def test_team_leader_can_manage_pending_requests_only_in_active_team(client, test_engine):
    _seed_teams(test_engine)
    with test_engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO team_members (team_id, user_id, status) VALUES "
                "('team-1', 'leader-1', 'ACTIVE'), "
                "('team-1', 'user-1', 'PENDING'), "
                "('team-2', 'user-1', 'PENDING')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO team_member_roles (team_id, user_id, role_key, assigned_by) "
                "VALUES ('team-1', 'leader-1', 'TEAM_LEADER', 'admin-1')"
            )
        )
    _authenticate(_actor(user_id="leader-1", leader_team="team-1"))

    pending = client.get("/api/teams/team-1/requests")
    assert pending.status_code == 200
    assert [request["user_id"] for request in pending.json()["pending_requests"]] == ["user-1"]
    assert client.get("/api/teams/team-2/requests").status_code == 403

    approved = client.post("/api/teams/team-1/approve/user-1")
    assert approved.status_code == 200
    assert approved.json()["status"] == "ACTIVE"
    assert client.post("/api/teams/team-1/approve/user-1").status_code == 409
    assert client.post("/api/teams/team-2/reject/user-1").status_code == 403


def test_admin_can_reject_a_pending_request(client, test_engine):
    _seed_teams(test_engine)
    with test_engine.begin() as connection:
        connection.execute(text("INSERT INTO team_members VALUES ('team-1', 'user-1', 'PENDING', CURRENT_TIMESTAMP)"))
    _authenticate(_actor(is_admin=True))

    response = client.post("/api/teams/team-1/reject/user-1")

    assert response.status_code == 200
    assert response.json()["status"] == "REJECTED"


def test_admin_assigns_leadership_only_to_active_members(client, test_engine):
    _seed_teams(test_engine)
    with test_engine.begin() as connection:
        connection.execute(text("INSERT INTO team_members VALUES ('team-1', 'user-1', 'PENDING', CURRENT_TIMESTAMP)"))
    _authenticate(_actor(is_admin=True))

    assert client.put("/api/teams/team-1/leaders/user-1").status_code == 409
    with test_engine.begin() as connection:
        connection.execute(
            text("UPDATE team_members SET status = 'ACTIVE' " "WHERE team_id = 'team-1' AND user_id = 'user-1'")
        )

    assigned = client.put("/api/teams/team-1/leaders/user-1")
    assert assigned.status_code == 200
    assert assigned.json()["role_key"] == "TEAM_LEADER"
    assert client.put("/api/teams/team-1/leaders/user-1").status_code == 409
    assert client.delete("/api/teams/team-1/leaders/user-1").status_code == 204


def test_static_component_roles_are_listed_and_assigned_by_role_key(client, test_engine):
    _seed_teams(test_engine)
    _authenticate(_actor(is_admin=True))

    roles = client.get("/api/roles")
    assert roles.status_code == 200
    assert {role["role_key"]: role["component"] for role in roles.json()["roles"]} == {
        "proposal writer": "ProposalWorkspace",
        "system admin": None,
        "TEAM_LEADER": None,
    }

    assigned = client.post("/api/teams/team-1/roles", json={"role_key": "proposal writer"})
    assert assigned.status_code == 201
    assert assigned.json()["role_key"] == "proposal writer"
    assert client.post("/api/teams/team-1/roles", json={"role_key": "proposal writer"}).status_code == 409
    assert client.post("/api/teams/team-1/roles", json={"role_key": "TEAM_LEADER"}).status_code == 422

    listed = client.get("/api/teams/team-1/roles")
    assert listed.status_code == 200
    assert [role["role_key"] for role in listed.json()["roles"]] == ["proposal writer"]
    assert listed.json()["roles"][0]["role_id"] == 1
    assert listed.json()["roles"][0]["role_name"] == "proposal writer"

    removed = client.delete("/api/teams/team-1/roles/proposal%20writer")
    assert removed.status_code == 204

    legacy_assigned = client.post("/api/teams/team-1/roles", json={"role_id": 1})
    assert legacy_assigned.status_code == 201
    assert legacy_assigned.json()["role_key"] == "proposal writer"
    assert client.delete("/api/teams/team-1/roles/1").status_code == 204
