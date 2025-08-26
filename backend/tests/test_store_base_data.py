import pytest
from fastapi.testclient import TestClient
from backend.main import app

def test_store_base_data(authenticated_client):
    client = authenticated_client
    payload = {
        "form_data": {
            "Project title": "Migration Support",
            "Project type": "Humanitarian Aid"
        },
        "project_description": "A test description for unit testing.",
        "template_name": "unhcr_proposal_template.json"
    }

    response = client.post("/api/store_base_data", json=payload)
    json_response = response.json()

    assert response.status_code == 200
    assert "session_id" in json_response
    assert "message" in json_response
