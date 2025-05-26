import pytest
from httpx import AsyncClient
from main import app
from unittest.mock import patch, MagicMock
from httpx import AsyncClient
from httpx import ASGITransport
from main import app

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

    # Step 2: Mock regenerate_proposal_crew kickoff
    mock_result = MagicMock()
    mock_result.raw = '{"generated_content": "Regenerated content", "evaluation_status": "Approved", "feedback": ""}'
    mocker.patch("crew.ProposalCrew.regenerate_proposal_crew", return_value=MagicMock(kickoff=MagicMock(return_value=mock_result)))

    # Step 3: Call regenerate_section
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        section_payload = {
            "section": "Summary",
            "concise_input": "Simplify wording."
        }
        response = await ac.post(f"/api/regenerate_section/{session_id}", json=section_payload)
        data = response.json()

    # Step 4: Assertions
    assert response.status_code == 200
    assert "generated_text" in data
    assert data["generated_text"] == "Regenerated content"
