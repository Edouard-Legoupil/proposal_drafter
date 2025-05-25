import pytest
from httpx import AsyncClient
from main import app, redis_client, SECTIONS
from httpx import ASGITransport
import os
import json
from httpx import AsyncClient
from httpx import ASGITransport
from main import app

@pytest.mark.asyncio
async def test_generate_document():
    # Step 1: Store base data to get a session ID
    # transport = ASGITransport(app=app)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "form_data": {"Project title": "Disaster Relief"},
            "project_description": "Testing document generation."
        }
        post_response = await ac.post("/api/store_base_data", json=payload)
        session_id = post_response.json()["session_id"]

    # Step 2: Add dummy generated_sections data into Redis
    session_data = {
        "form_data": {"Project title": "Disaster Relief"},
        "project_description": "Testing document generation.",
        "generated_sections": {section: f"Sample content for {section}" for section in SECTIONS}
    }
    redis_client.set(session_id, json.dumps(session_data))

    # Step 3: Call generate-document endpoint
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(f"/api/generate-document/{session_id}")
        data = response.json()

    # Step 4: Assertions
    assert response.status_code == 200
    assert "file_path" in data
    assert os.path.exists(data["file_path"])

    # ✅ Clean up generated file after test
    os.remove(data["file_path"])
