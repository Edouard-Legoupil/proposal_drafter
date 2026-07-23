import json
import uuid

from backend.core.redis import redis_client


def test_get_base_data(authenticated_client):
    client = authenticated_client
    payload = {
        "form_data": {
            "Project title": "Health Access Project",
            "Project type": "Development Aid",
        },
        "project_description": "A testing project.",
        "template_name": "proposal_template_unhcr.json",
    }

    post_response = client.post("/api/store_base_data", json=payload, headers={"host": "localhost"})
    assert post_response.status_code == 200
    session_id = post_response.json()["session_id"]

    get_response = client.get(f"/api/get_base_data/{session_id}", headers={"host": "localhost"})
    data = get_response.json()

    assert get_response.status_code == 200
    assert data["form_data"] == payload["form_data"]
    assert data["project_description"] == payload["project_description"]


def test_get_base_data_rejects_session_owned_by_another_user(authenticated_client):
    session_id = str(uuid.uuid4())
    redis_client.setex(
        session_id,
        3600,
        json.dumps(
            {
                "form_data": {"Project title": "Private project"},
                "project_description": "Private proposal data",
                "user_id": "another-user",
            }
        ),
    )

    try:
        response = authenticated_client.get(
            f"/api/get_base_data/{session_id}", headers={"host": "localhost"}
        )
    finally:
        redis_client.delete(session_id)

    assert response.status_code == 403
