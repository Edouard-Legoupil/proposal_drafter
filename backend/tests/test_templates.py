import pytest
import uuid
from sqlalchemy import text

def test_list_templates(authenticated_client):
    response = authenticated_client.get("/api/templates/")
    assert response.status_code == 200
    data = response.json()
    assert "published" in data
    assert "requests" in data

def test_create_template_request(authenticated_client):
    request_data = {
        "name": "New Donor Template",
        "configuration": {"sections": ["Section 1", "Section 2"]}
    }
    response = authenticated_client.post("/api/templates/request", json=request_data)
    if response.status_code != 200:
        print(response.json())
    assert response.status_code == 200
    assert response.json()["message"] == "Template request submitted successfully."

def test_get_template_request(authenticated_client, db_session):
    request_id = str(uuid.uuid4())
    user_id = authenticated_client.get("/api/profile").json()["user"]["id"]
    
    db_session.execute(
        text("""
            INSERT INTO donor_template_requests (id, name, configuration, created_by, status)
            VALUES (:id, :name, :conf, :uid, 'pending')
        """),
        {"id": request_id, "name": "Test Request", "conf": '{"sections": []}', "uid": user_id}
    )
    db_session.commit()

    response = authenticated_client.get(f"/api/templates/request/{request_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Request"
    assert data["status"] == "pending"

def test_add_comment(authenticated_client, db_session):
    request_id = str(uuid.uuid4())
    user_id = authenticated_client.get("/api/profile").json()["user"]["id"]
    
    db_session.execute(
        text("""
            INSERT INTO donor_template_requests (id, name, configuration, created_by)
            VALUES (:id, :name, :conf, :uid)
        """),
        {"id": request_id, "name": "Comment Test", "conf": '{"sections": []}', "uid": user_id}
    )
    db_session.commit()

    comment_data = {"comment_text": "This is a test comment"}
    response = authenticated_client.post(f"/api/templates/request/{request_id}/comment", json=comment_data)
    assert response.status_code == 200
    
    # Verify comment is returned in detail
    detail_response = authenticated_client.get(f"/api/templates/request/{request_id}")
    assert len(detail_response.json()["comments"]) == 1
    assert detail_response.json()["comments"][0]["text"] == "This is a test comment"

def test_update_status_admin(authenticated_client, db_session):
    request_id = str(uuid.uuid4())
    user_id = authenticated_client.get("/api/profile").json()["user"]["id"]
    
    db_session.execute(
        text("""
            INSERT INTO donor_template_requests (id, name, configuration, created_by, status)
            VALUES (:id, :name, :conf, :uid, 'pending')
        """),
        {"id": request_id, "name": "Status Test", "conf": '{"sections": []}', "uid": user_id}
    )
    db_session.commit()

    response = authenticated_client.put(
        f"/api/templates/request/{request_id}/status", 
        json={"status": "approved"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Status updated to approved."

def test_update_status_unauthorized(client):
    # Test without auth
    response = client.put("/api/templates/request/some-id/status", json={"status": "approved"})
    assert response.status_code == 401
