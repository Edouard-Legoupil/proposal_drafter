import pytest
from httpx import AsyncClient
from backend.main import app
from backend.core.storage import storage_client
from backend.core.config import SECTIONS
from httpx import ASGITransport
import os
import json
from unittest.mock import MagicMock

@pytest.mark.asyncio
async def test_generate_document(mocker):
    # Step 1: Create a mock proposal in the database
    proposal_id = "test-proposal-id"
    user_id = "test-user-id"
    form_data = {"Project title": "Disaster Relief"}
    project_description = "Testing document generation."
    generated_sections = {section: f"Sample content for {section}" for section in SECTIONS}

    # Mock the database query
    mock_connection = MagicMock()
    mock_result = MagicMock()
    mock_result.fetchone.return_value = (
        json.dumps(form_data),
        project_description,
        json.dumps(generated_sections),
    )
    mock_connection.execute.return_value = mock_result
    mocker.patch("backend.api.documents.engine.connect").return_value.__enter__.return_value = mock_connection

    # Step 2: Call generate-document endpoint
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/api/generate-document/{proposal_id}")

    # Step 3: Assertions
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    # The test doesn't check the file content, so we don't need to save and remove it.
    # The FileResponse will be cleaned up automatically.
