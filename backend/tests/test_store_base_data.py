import pytest
from httpx import AsyncClient
from backend.main import app
from httpx import AsyncClient
from httpx import ASGITransport

@pytest.mark.asyncio
async def test_store_base_data():
    # transport = ASGITransport(app=app)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "form_data": {
                "Project title": "Migration Support",
                "Project type": "Humanitarian Aid"
            },
            "project_description": "A test description for unit testing."
        }

        response = await ac.post("/api/store_base_data", json=payload)
        json_response = response.json()

    assert response.status_code == 200
    assert "session_id" in json_response
    assert json_response["message"] == "Base data stored successfully"
    assert isinstance(json_response["session_id"], str)
