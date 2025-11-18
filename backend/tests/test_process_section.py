import uuid
from unittest.mock import MagicMock
import pytest
from backend.api import proposals
from backend.repository.proposal_repository import ProposalRepository

def test_process_section(authenticated_client, mocker):
    client = authenticated_client

    # Mock the crew kickoff method
    mock_result = MagicMock()
    mock_result.raw = '{"generated_content": "Test content", "evaluation_status": "Approved"}'
    mocker.patch("backend.api.proposals.ProposalCrew.generate_proposal_crew", return_value=MagicMock(kickoff=MagicMock(return_value=mock_result)))

    # Mock database and redis calls within the endpoint
    mocker.patch('backend.api.proposals.redis_client.get', return_value='{"proposal_template": {"sections": [{"section_name": "Summary"}]}}')
    mocker.patch('backend.api.proposals.redis_client.setex')

    # Mock the repository methods
    mocker.patch.object(proposals.proposal_repository, 'get_proposal_is_accepted', return_value=False)
    mocker.patch.object(proposals.proposal_repository, 'get_proposal_generated_sections', return_value={})
    mocker.patch.object(proposals.proposal_repository, 'update_proposal_section')

    # Prepare payload
    session_id = str(uuid.uuid4())
    proposal_id = str(uuid.uuid4())
    section_payload = {
        "section": "Summary",
        "proposal_id": proposal_id,
        "form_data": {"Project title": "Education Access"},
        "project_description": "A test for process section endpoint."
    }

    # Make the call
    response = client.post(f"/api/process_section/{session_id}", json=section_payload)
    response_data = response.json()

    # Assertions
    assert response.status_code == 200
    assert response_data["message"] == "Content generated for Summary"
    assert response_data["generated_text"] == "Test content"
