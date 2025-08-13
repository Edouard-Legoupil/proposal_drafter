import pytest
from fastapi.testclient import TestClient
from backend.main import app
from unittest.mock import MagicMock

def test_process_section(authenticated_client, mocker):
    client = authenticated_client

    # Mock the crew kickoff method
    mock_result = MagicMock()
    mock_result.raw = '{"generated_content": "Test content", "evaluation_status": "Approved", "feedback": ""}'
    mocker.patch("backend.utils.crew.ProposalCrew.generate_proposal_crew", return_value=MagicMock(kickoff=MagicMock(return_value=mock_result)))

    # Store base data to get a session ID
    payload = {
        "form_data": {"Project title": "Education Access"},
        "project_description": "A test for process section endpoint."
    }
    post_response = client.post("/api/store_base_data", json=payload)
    session_id = post_response.json()["session_id"]

    # Save a draft to get a proposal_id
    draft_payload = {
        "form_data": {"Project title": "Education Access"},
        "project_description": "A test for process section endpoint.",
        "generated_sections": {}
    }
    draft_response = client.post("/api/save-draft", json=draft_payload)
    proposal_id = draft_response.json()["proposal_id"]

    # Call process_section
    section_payload = {"section": "Summary", "proposal_id": proposal_id}
    response = client.post(f"/api/process_section/{session_id}", json=section_payload)
    response_data = response.json()

    # Assertions
    assert response.status_code == 200
    assert "generated_text" in response_data
    assert response_data["generated_text"] == "Test content"
