import pytest
from httpx import AsyncClient
from backend.main import app
from httpx import AsyncClient
from httpx import ASGITransport

@pytest.mark.asyncio
async def test_get_base_data():
    # transport = ASGITransport(app=app)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "form_data": {
                "Project title": "Health Access Project",
                "Project type": "Development Aid"
            },
            "project_description": "A testing project."
        }

        post_response = await ac.post("/api/store_base_data", json=payload)
        session_id = post_response.json()["session_id"]

        get_response = await ac.get(f"/api/get_base_data/{session_id}")
        data = get_response.json()

    assert get_response.status_code == 200
    assert data["form_data"] == payload["form_data"]
    assert data["project_description"] == payload["project_description"]