import pytest
from fastapi.testclient import TestClient
from backend.main import app

def test_get_base_data(authenticated_client):
    client = authenticated_client
    payload = {
        "form_data": {
            "Project title": "Health Access Project",
            "Project type": "Development Aid"
        },
        "project_description": "A testing project.",
        "template_name": "unhcr_proposal_template.json"
    }

    post_response = client.post("/api/store_base_data", json=payload)
    assert post_response.status_code == 200
    session_id = post_response.json()["session_id"]

    get_response = client.get(f"/api/get_base_data/{session_id}")
    data = get_response.json()

    assert get_response.status_code == 200
    assert data["form_data"] == payload["form_data"]
    assert data["project_description"] == payload["project_description"]