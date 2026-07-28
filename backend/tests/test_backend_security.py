import uuid

import jwt
import pytest
from sqlalchemy import text

from backend.core import security
from backend.core.security import get_current_user
from backend.main import app


def _token(email):
    return jwt.encode({"email": email}, str(security.SECRET_KEY), algorithm="HS256")


def test_profile_exposes_selected_team_context(client, test_engine, monkeypatch):
    with test_engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO roles (id, name, role_key, component) VALUES "
                "(1, 'access metrics', 'access metrics', 'Metrics'), "
                "(2, 'access template', 'access template', 'Templates'), "
                "(3, 'TEAM_LEADER', 'TEAM_LEADER', NULL)"
            )
        )
        connection.execute(text("INSERT INTO teams (id, name) VALUES ('team-a', 'Team A'), ('team-b', 'Team B')"))
        connection.execute(
            text(
                "INSERT INTO users (id, email, name, password) "
                "VALUES ('user-1', 'profile@example.org', 'Profile User', 'secret')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO team_members (team_id, user_id, status) VALUES "
                "('team-a', 'user-1', 'ACTIVE'), ('team-b', 'user-1', 'ACTIVE')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO team_roles (team_id, role_id, role_key) VALUES "
                "('team-a', 1, 'access metrics'), ('team-b', 2, 'access template')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO team_member_roles (team_id, user_id, role_key, assigned_by) "
                "VALUES ('team-b', 'user-1', 'TEAM_LEADER', 'user-1')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO access_settings (user_id, team_id, role_key, key, value, created_by) "
                "VALUES ('user-1', 'team-b', 'access template', 'format', '\"docx\"', 'user-1')"
            )
        )
    monkeypatch.setattr(security, "is_session_token_active", lambda _user_id, _token: True)

    client.cookies.set("auth_token", _token("profile@example.org"))
    response = client.get("/api/profile", headers={"X-Team-ID": "team-b"})

    assert response.status_code == 200
    user = response.json()["user"]
    assert user["id"] == "user-1"
    assert user["memberships"] == [
        {"id": "team-a", "name": "Team A"},
        {"id": "team-b", "name": "Team B"},
    ]
    assert user["teams"] == user["memberships"]
    assert user["active_team"] == {"id": "team-b", "name": "Team B"}
    assert user["roles"] == ["access template"]
    assert user["team_leadership"] is True
    assert user["settings"] == {"access template": {"format": "docx"}}
    assert user["is_admin"] is False


def test_profile_exposes_global_admin_without_team_or_scoped_roles(client, test_engine, monkeypatch):
    with test_engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO roles (id, name, role_key, component) " "VALUES (1, 'system admin', 'system admin', NULL)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO users (id, email, name, password) "
                "VALUES ('admin-1', 'admin-profile@example.org', 'Admin User', 'secret')"
            )
        )
        connection.execute(text("INSERT INTO user_roles (user_id, role_id) VALUES ('admin-1', 1)"))
    monkeypatch.setattr(security, "is_session_token_active", lambda _user_id, _token: True)

    client.cookies.set("auth_token", _token("admin-profile@example.org"))
    response = client.get("/api/profile")

    assert response.status_code == 200
    user = response.json()["user"]
    assert user["id"] == "admin-1"
    assert user["memberships"] == []
    assert user["teams"] == []
    assert user["active_team"] is None
    assert user["roles"] == []
    assert user["team_leadership"] is False
    assert user["settings"] == {}
    assert user["is_admin"] is True


@pytest.fixture
def global_admin(client):
    app.dependency_overrides[get_current_user] = lambda: {
        "user_id": "admin-1",
        "name": "Admin",
        "email": "admin@example.org",
        "roles": [],
        "all_roles": [],
        "is_admin": True,
    }
    yield client
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def team_a_reviewer(client):
    app.dependency_overrides[get_current_user] = lambda: {
        "user_id": "reviewer-1",
        "name": "Reviewer",
        "email": "reviewer@example.org",
        "roles": ["project reviewer"],
        "all_roles": ["project reviewer"],
        "active_team": {"id": "team-a", "name": "Team A"},
        "is_admin": False,
    }
    yield client
    app.dependency_overrides.pop(get_current_user, None)


def _proposal_for_team(db_session, team_id):
    proposal_id = str(uuid.uuid4())
    db_session.execute(text("INSERT INTO teams (id, name) VALUES ('team-a', 'Team A'), ('team-b', 'Team B')"))
    db_session.execute(
        text(
            "INSERT INTO users (id, email, name, password) VALUES "
            "('reviewer-1', 'reviewer@example.org', 'Reviewer', 'secret'), "
            "('owner-1', 'owner@example.org', 'Owner', 'secret')"
        )
    )
    db_session.execute(
        text(
            "INSERT INTO roles (id, name, role_key, component) "
            "VALUES (1, 'project reviewer', 'project reviewer', 'ReviewWorkspace')"
        )
    )
    db_session.execute(
        text("INSERT INTO team_members (team_id, user_id, status) VALUES ('team-a', 'reviewer-1', 'ACTIVE')")
    )
    db_session.execute(
        text("INSERT INTO team_roles (team_id, role_id, role_key) " "VALUES ('team-a', 1, 'project reviewer')")
    )
    db_session.execute(
        text(
            "INSERT INTO proposals "
            "(id, user_id, team_id, form_data, project_description, status, template_name) "
            "VALUES (:proposal_id, 'owner-1', :team_id, '{}', 'Description', 'draft', "
            "'proposal_template_unhcr.json')"
        ),
        {"proposal_id": proposal_id, "team_id": team_id},
    )
    db_session.execute(
        text(
            "INSERT INTO resource_access_grants "
            "(id, resource_type, resource_id, subject_type, subject_id, permissions, data_scope, created_by) "
            "VALUES (:id, 'proposals', :proposal_id, 'team', :team_id, '[\"read\"]', 'team', 'owner-1')"
        ),
        {"id": str(uuid.uuid4()), "proposal_id": proposal_id, "team_id": team_id},
    )
    db_session.commit()
    return proposal_id


@pytest.mark.parametrize(
    ("path", "denied_status"),
    [
        ("/api/load-draft/{proposal_id}", 403),
        ("/api/proposals/{proposal_id}/peer-reviews", 403),
    ],
)
def test_project_reviewer_cannot_access_known_cross_team_proposal(team_a_reviewer, db_session, path, denied_status):
    proposal_id = _proposal_for_team(db_session, "team-b")

    response = team_a_reviewer.get(path.format(proposal_id=proposal_id))

    assert response.status_code == denied_status


@pytest.mark.parametrize(
    "path",
    [
        "/api/load-draft/{proposal_id}",
        "/api/proposals/{proposal_id}/peer-reviews",
    ],
)
def test_project_reviewer_can_access_same_team_proposal(team_a_reviewer, db_session, path):
    proposal_id = _proposal_for_team(db_session, "team-a")

    response = team_a_reviewer.get(path.format(proposal_id=proposal_id))

    assert response.status_code == 200


def test_global_admin_can_delete_another_users_knowledge_comment(global_admin, db_session):
    card_id = str(uuid.uuid4())
    comment_id = str(uuid.uuid4())
    db_session.execute(
        text(
            "INSERT INTO users (id, email, name, password) VALUES "
            "('admin-1', 'admin@example.org', 'Admin', 'secret'), "
            "('reviewer-1', 'reviewer@example.org', 'Reviewer', 'secret')"
        )
    )
    db_session.execute(
        text(
            "INSERT INTO knowledge_cards (id, summary, created_by, status) "
            "VALUES (:card_id, 'Summary', 'reviewer-1', 'draft')"
        ),
        {"card_id": card_id},
    )
    db_session.execute(
        text(
            "INSERT INTO knowledge_card_reviews (id, knowledge_card_id, reviewer_id) "
            "VALUES (:comment_id, :card_id, 'reviewer-1')"
        ),
        {"comment_id": comment_id, "card_id": card_id},
    )
    db_session.commit()

    response = global_admin.delete(f"/api/knowledge-cards/{card_id}/comment/{comment_id}")

    assert response.status_code == 200


def test_global_admin_can_view_another_users_peer_reviews(global_admin, db_session):
    proposal_id = str(uuid.uuid4())
    db_session.execute(
        text(
            "INSERT INTO users (id, email, name, password) VALUES "
            "('admin-1', 'admin@example.org', 'Admin', 'secret'), "
            "('owner-1', 'owner@example.org', 'Owner', 'secret')"
        )
    )
    db_session.execute(
        text(
            "INSERT INTO proposals (id, user_id, form_data, project_description, status) "
            "VALUES (:proposal_id, 'owner-1', '{}', 'Description', 'draft')"
        ),
        {"proposal_id": proposal_id},
    )
    db_session.commit()

    response = global_admin.get(f"/api/proposals/{proposal_id}/peer-reviews")

    assert response.status_code == 200
    assert response.json() == {"reviews": []}


def test_global_admin_can_load_another_users_draft(global_admin, db_session):
    proposal_id = str(uuid.uuid4())
    db_session.execute(
        text(
            "INSERT INTO users (id, email, name, password) VALUES "
            "('admin-1', 'admin@example.org', 'Admin', 'secret'), "
            "('owner-1', 'owner@example.org', 'Owner', 'secret')"
        )
    )
    db_session.execute(
        text(
            "INSERT INTO proposals "
            "(id, user_id, form_data, project_description, status, template_name) "
            "VALUES (:proposal_id, 'owner-1', '{}', 'Description', 'draft', "
            "'proposal_template_unhcr.json')"
        ),
        {"proposal_id": proposal_id},
    )
    db_session.commit()

    response = global_admin.get(f"/api/load-draft/{proposal_id}")

    assert response.status_code == 200
    assert response.json()["proposal_id"] == proposal_id


def test_global_admin_can_update_template_request_status(global_admin, db_session):
    request_id = str(uuid.uuid4())
    db_session.execute(
        text(
            "INSERT INTO users (id, email, name, password) "
            "VALUES ('admin-1', 'admin@example.org', 'Admin', 'secret')"
        )
    )
    db_session.execute(
        text(
            "INSERT INTO donor_template_requests (id, name, created_by, status) "
            "VALUES (:request_id, 'Template', 'admin-1', 'pending')"
        ),
        {"request_id": request_id},
    )
    db_session.commit()

    response = global_admin.put(
        f"/api/templates/request/{request_id}/status",
        json={"status": "approved"},
    )

    assert response.status_code == 200
