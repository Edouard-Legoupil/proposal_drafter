import uuid
from unittest.mock import MagicMock


def test_process_section(authenticated_client, mocker):
    client = authenticated_client

    # Mock the crew kickoff method
    mock_result = MagicMock()
    mock_result.raw = '{"generated_content": "Test content", "evaluation_status": "Approved"}'
    proposal_crew = MagicMock()
    proposal_crew.generate_proposal_crew.return_value.kickoff.return_value = mock_result
    mocker.patch("backend.api.proposals.ProposalCrew", return_value=proposal_crew)

    # Mock database and redis calls within the endpoint
    mocker.patch(
        "backend.api.proposals.redis_client.get",
        return_value='{"proposal_template": {"sections": [{"section_name": "Summary"}]}}',
    )
    mocker.patch("backend.api.proposals.redis_client.setex")

    # Mock the database check for is_accepted
    mock_engine = MagicMock()
    mock_connection = MagicMock()
    mock_connection.execute.return_value.fetchone.return_value = (False,)
    mock_engine.connect.return_value.__enter__.return_value = mock_connection
    mocker.patch("backend.api.proposals.get_engine", return_value=mock_engine)

    # Prepare payload
    session_id = str(uuid.uuid4())
    proposal_id = str(uuid.uuid4())
    section_payload = {
        "section": "Summary",
        "proposal_id": proposal_id,
        "form_data": {"Project title": "Education Access"},
        "project_description": "A test for process section endpoint.",
    }

    # Make the call
    response = client.post(f"/api/process_section/{session_id}", json=section_payload)
    response_data = response.json()

    # Assertions
    assert response.status_code == 200
    assert "generated_text" in response_data
    assert response_data["generated_text"] == "Test content"


def test_process_section_rejects_finalized_proposal(authenticated_client, mocker):
    mocker.patch(
        "backend.api.proposals.redis_client.get",
        return_value='{"proposal_template": {"sections": [{"section_name": "Summary"}]}}',
    )
    mocker.patch("backend.api.proposals.redis_client.setex")
    mock_engine = MagicMock()
    mock_connection = MagicMock()
    mock_connection.execute.return_value.fetchone.return_value = (True,)
    mock_engine.connect.return_value.__enter__.return_value = mock_connection
    mocker.patch("backend.api.proposals.get_engine", return_value=mock_engine)

    response = authenticated_client.post(
        f"/api/process_section/{uuid.uuid4()}",
        json={
            "section": "Summary",
            "proposal_id": str(uuid.uuid4()),
            "form_data": {"Project title": "Locked"},
            "project_description": "A finalized proposal.",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "This proposal is finalized and cannot be modified."
