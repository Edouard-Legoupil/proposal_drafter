import pytest
from httpx import AsyncClient
from backend.main import app
from unittest.mock import patch, MagicMock
from httpx import AsyncClient
from httpx import ASGITransport

@pytest.mark.asyncio
async def test_process_section(mocker):
    # Step 1: Store base data to get a session ID
    # transport = ASGITransport(app=app)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "form_data": {"Project title": "Education Access"},
            "project_description": "A test for process section endpoint."
        }
        post_response = await ac.post("/api/store_base_data", json=payload)
        session_id = post_response.json()["session_id"]

    # Step 2: Mock the database query to return a non-finalized proposal
    mock_connection = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar.return_value = False  # Not finalized
    mock_connection.execute.return_value = mock_result
    mocker.patch("backend.api.proposals.engine.connect").return_value.__enter__.return_value = mock_connection

    # Step 2: Mock the proposal_data
    mocker.patch("backend.api.proposals.proposal_data", {"sections": [{"section_name": "Summary"}]})

    # Step 3: Mock Crew kickoff method
    mock_crew_result = MagicMock()
    mock_crew_result.raw = '{"generated_content": "Test content", "evaluation_status": "Approved", "feedback": ""}'
    mocker.patch("backend.utils.crew.ProposalCrew.generate_proposal_crew", return_value=MagicMock(kickoff=MagicMock(return_value=mock_crew_result)))

    # Step 3: Call process_section
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        section_payload = {"section": "Summary", "proposal_id": "test-proposal-id"}
        response = await ac.post(f"/api/process_section/{session_id}", json=section_payload)
        response_data = response.json()
        print(response_data)

    # Step 4: Assertions
    assert response.status_code == 200
    assert "generated_text" in response_data
    assert response_data["generated_text"] == "Test content"
