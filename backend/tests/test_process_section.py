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

    # Step 2: Mock Crew kickoff method
    mock_result = MagicMock()
    mock_result.raw = '{"generated_content": "Test content", "evaluation_status": "Approved", "feedback": ""}'
    mocker.patch("crew.ProposalCrew.generate_proposal_crew", return_value=MagicMock(kickoff=MagicMock(return_value=mock_result)))

    # Step 3: Call process_section
    async with AsyncClient(app=app, base_url="http://test") as ac:
        section_payload = {"section": "Summary"}
        response = await ac.post(f"/api/process_section/{session_id}", json=section_payload)
        response_data = response.json()

    # Step 4: Assertions
    assert response.status_code == 200
    assert "generated_text" in response_data
    assert response_data["generated_text"] == "Test content"
