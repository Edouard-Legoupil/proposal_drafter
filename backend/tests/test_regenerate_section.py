import pytest
import uuid
from unittest.mock import MagicMock
from backend.main import app

@pytest.mark.asyncio
async def test_regenerate_section(authenticated_client, mocker):
    client = authenticated_client

    # We patch the `regenerate_section_logic` function directly to isolate the test
    mocker.patch(
        'backend.api.proposals.regenerate_section_logic',
        return_value="Regenerated Content"
    )

    # Mock Redis to return session data
    mocker.patch('backend.api.proposals.redis_client.get', return_value='{"key": "value"}')
    mocker.patch('backend.api.proposals.redis_client.setex')
    # Mock the database check for is_accepted
    mock_engine = MagicMock()
    mock_connection = MagicMock()
    mock_connection.execute.return_value.scalar.return_value = False # Not accepted
    mock_engine.connect.return_value.__enter__.return_value = mock_connection
    mocker.patch('backend.api.proposals.get_engine', return_value=mock_engine)

    # Prepare payload
    session_id = str(uuid.uuid4())
    proposal_id = str(uuid.uuid4())
    regenerate_payload = {
        "section": "Introduction",
        "concise_input": "Make it better.",
        "proposal_id": proposal_id,
        "form_data": {"Project title": "Child Protection"},
        "project_description": "A project for regenerate section test."
    }

    # Make the API call
    response = client.post(f"/api/regenerate_section/{session_id}", json=regenerate_payload)

    # Assert the response
    assert response.status_code == 200
    response_json = response.json()
    assert "Content regenerated for Introduction" in response_json["message"]
    assert "Regenerated Content" in response_json["generated_text"]
