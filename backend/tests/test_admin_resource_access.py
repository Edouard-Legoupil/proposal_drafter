import uuid

import pytest
from sqlalchemy import text

from backend.core.authorization import _has_explicit_resource_grant
from backend.core.security import get_current_user
from backend.main import app


@pytest.fixture
def admin_client(client):
    admin_id = str(uuid.uuid4())
    app.dependency_overrides[get_current_user] = lambda: {
        "user_id": admin_id,
        "email": "admin@example.com",
        "is_admin": True,
        "roles": ["system admin"],
    }
    yield client, admin_id
    app.dependency_overrides.pop(get_current_user, None)


def _insert_user(connection, *, user_id=None, email="user@example.com", name="User"):
    user_id = user_id or str(uuid.uuid4())
    connection.execute(
        text("INSERT INTO users (id, email, password, name) VALUES (:id, :email, 'password', :name)"),
        {"id": user_id, "email": email, "name": name},
    )
    return user_id


def _insert_proposal(connection, owner_id):
    proposal_id = str(uuid.uuid4())
    connection.execute(
        text(
            "INSERT INTO proposals (id, user_id, form_data, project_description, status, created_by, updated_by) "
            "VALUES (:id, :owner, :form_data, 'Description', 'draft', :owner, :owner)"
        ),
        {"id": proposal_id, "owner": owner_id, "form_data": '{"projectTitle":"Test proposal"}'},
    )
    return proposal_id


def test_admin_can_manage_and_test_proposal_grants(admin_client, db_session):
    client, admin_id = admin_client
    _insert_user(db_session, user_id=admin_id, email="admin@example.com", name="Admin")
    owner_id = _insert_user(db_session, email="owner@example.com", name="Owner")
    subject_id = _insert_user(db_session, email="reader@example.com", name="Reader")
    proposal_id = _insert_proposal(db_session, owner_id)

    grant = client.post(
        f"/api/admin/proposals/{proposal_id}/access",
        json={
            "subjectType": "user",
            "subjectId": subject_id,
            "permissions": ["read"],
            "dataScope": "self",
        },
    )
    assert grant.status_code == 201, grant.text
    grant_id = grant.json()["grant"]["id"]
    assert _has_explicit_resource_grant("proposal", proposal_id, subject_id, "read") is True
    assert _has_explicit_resource_grant("proposal", proposal_id, subject_id, "delete") is False

    access = client.get(f"/api/admin/proposals/{proposal_id}/access")
    assert access.status_code == 200, access.text
    assert access.json()["proposal"]["owner"]["id"] == owner_id
    assert access.json()["grants"][0]["permissions"] == ["read"]

    result = client.post(
        f"/api/admin/proposals/{proposal_id}/access/test",
        json={"subjectType": "user", "subjectId": subject_id, "operation": "GET"},
    )
    assert result.status_code == 200, result.text
    assert result.json()["allowed"] is True

    revoked = client.request(
        "DELETE",
        f"/api/admin/proposals/{proposal_id}/access",
        json={"grant_id": grant_id},
    )
    assert revoked.status_code == 200, revoked.text

    denied = client.post(
        f"/api/admin/proposals/{proposal_id}/access/test",
        json={"subjectType": "user", "subjectId": subject_id, "operation": "GET"},
    )
    assert denied.status_code == 200, denied.text
    assert denied.json()["allowed"] is False


def test_admin_can_transfer_proposal_owner(admin_client, db_session):
    client, admin_id = admin_client
    _insert_user(db_session, user_id=admin_id, email="admin@example.com", name="Admin")
    owner_id = _insert_user(db_session, email="owner@example.com", name="Owner")
    new_owner_id = _insert_user(db_session, email="new-owner@example.com", name="New Owner")
    proposal_id = _insert_proposal(db_session, owner_id)

    response = client.post(
        f"/api/admin/proposals/{proposal_id}/owner",
        json={"owner_id": new_owner_id},
    )
    assert response.status_code == 200, response.text
    actual = db_session.execute(text("SELECT user_id FROM proposals WHERE id = :id"), {"id": proposal_id}).scalar_one()
    assert actual == new_owner_id


def test_grant_rejects_unknown_permissions(admin_client, db_session):
    client, admin_id = admin_client
    _insert_user(db_session, user_id=admin_id, email="admin@example.com", name="Admin")
    owner_id = _insert_user(db_session, email="owner@example.com", name="Owner")
    subject_id = _insert_user(db_session, email="reader@example.com", name="Reader")
    proposal_id = _insert_proposal(db_session, owner_id)

    response = client.post(
        f"/api/admin/proposals/{proposal_id}/access",
        json={"subjectType": "user", "subjectId": subject_id, "permissions": ["superuser"]},
    )
    assert response.status_code == 422


def test_template_visibility_changes_effective_read_access(admin_client, db_session):
    client, admin_id = admin_client
    _insert_user(db_session, user_id=admin_id, email="admin@example.com", name="Admin")
    owner_id = _insert_user(db_session, email="owner@example.com", name="Owner")
    subject_id = _insert_user(db_session, email="reader@example.com", name="Reader")
    template_id = str(uuid.uuid4())
    db_session.execute(
        text(
            "INSERT INTO templates (id, name, filename, template_type, status, created_by, updated_by) "
            "VALUES (:id, 'Template', :filename, 'proposal', 'active', :owner, :owner)"
        ),
        {"id": template_id, "filename": f"{template_id}.json", "owner": owner_id},
    )

    response = client.post(
        f"/api/admin/templates/{template_id}/visibility",
        json={"visibility": "organization"},
    )
    assert response.status_code == 200, response.text

    result = client.post(
        f"/api/admin/templates/{template_id}/access/test",
        json={"subject_type": "user", "subject_id": subject_id, "operation": "view"},
    )
    assert result.status_code == 200, result.text
    assert result.json() == {
        "allowed": True,
        "permission": "read",
        "reason": "organization_visibility",
    }

    access = client.get(f"/api/admin/templates/{template_id}/access")
    assert access.status_code == 200, access.text
    assert access.json()["template"]["visibility"] == "organization"


def test_resource_access_management_requires_system_admin(authenticated_client):
    response = authenticated_client.get(f"/api/admin/proposals/{uuid.uuid4()}/access")
    assert response.status_code == 403
