import pytest
from httpx import AsyncClient
from backend.main import app
from unittest.mock import patch, MagicMock
from httpx import AsyncClient
from httpx import ASGITransport

@pytest.mark.asyncio
async def test_regenerate_section(mocker):
    # Step 1: Store base data to get a session ID
    # transport = ASGITransport(app=app)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "form_data": {"Project title": "Child Protection"},
            "project_description": "A project for regenerate section test."
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
    mocker.patch("backend.utils.proposal_logic.proposal_data", {"sections": [{"section_name": "Summary"}]})

    # Step 3: Mock regenerate_proposal_crew kickoff
    mock_crew_result = MagicMock()
    mock_crew_result.raw = '{"generated_content": "Regenerated content", "evaluation_status": "Approved", "feedback": ""}'
    mocker.patch("backend.utils.crew.ProposalCrew.regenerate_proposal_crew", return_value=MagicMock(kickoff=MagicMock(return_value=mock_crew_result)))

    # Step 3: Call regenerate_section
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        section_payload = {
            "section": "Summary",
            "concise_input": "Simplify wording.",
            "proposal_id": "test-proposal-id"
        }
        response = await ac.post(f"/api/regenerate_section/{session_id}", json=section_payload)
        data = response.json()
        print(data)

    # Step 4: Assertions
    assert response.status_code == 200
    assert "generated_text" in data
    assert data["generated_text"] == "Regenerated content"
