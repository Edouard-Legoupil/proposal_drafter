import uuid
from unittest.mock import MagicMock
import pytest
from backend.api import proposals

@pytest.mark.asyncio
async def test_regenerate_section(authenticated_client, mocker):
    client = authenticated_client

    # We patch the `regenerate_section_logic` function directly to isolate the test
    mocker.patch(
        'backend.api.proposals.regenerate_section_logic',
        return_value="Regenerated Content"
    )

    # Mock Redis `setex` as a new session is created
    mocker.patch('backend.api.proposals.redis_client.setex')

    # Mock the repository method
    mocker.patch.object(proposals.proposal_repository, 'get_proposal_is_accepted', return_value=False)
    mocker.patch.object(proposals.proposal_repository, 'get_proposal_template_name', return_value="proposal_template_unhcr.json")

    # Prepare payload
    proposal_id = str(uuid.uuid4())
    regenerate_payload = {
        "section": "Introduction",
        "concise_input": "Make it better.",
        "form_data": {"Project title": "Child Protection"},
        "project_description": "A project for regenerate section test."
    }

    # Make the API call using the proposal_id in the URL
    response = client.post(f"/api/regenerate_section/{proposal_id}", json=regenerate_payload)

    # Assert the response
    assert response.status_code == 200
    assert response.json()["message"] == "Content regenerated for Introduction"
    assert response.json()["generated_text"] == "Regenerated Content"
