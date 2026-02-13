import pytest
import uuid
import json
from unittest.mock import MagicMock
from backend.main import app
from backend.api.proposals import FALLBACK_GENERATION_MESSAGE
from sqlalchemy import text

def test_process_section_fallback(authenticated_client, mocker, test_engine):
    client = authenticated_client

    # Prepare IDs
    proposal_id = str(uuid.uuid4())
    user_id = "test_user_id" # This should match whoever authenticated_client uses
    # Actually authenticated_client creates a user. Let's get it.
    
    with test_engine.connect() as conn:
        user = conn.execute(text("SELECT id FROM users LIMIT 1")).fetchone()
        user_id = user.id
        
        # Insert a proposal to test against
        conn.execute(
            text("INSERT INTO proposals (id, user_id, form_data, status, is_accepted) VALUES (:id, :uid, :form, 'draft', False)"),
            {"id": proposal_id, "uid": user_id, "form": json.dumps({})}
        )
        conn.commit()

    # Mock the crew kickoff method to return empty result
    mock_result = MagicMock()
    mock_result.raw = '{"generated_content": "", "evaluation_status": "Approved"}'
    mocker.patch("backend.api.proposals.ProposalCrew.generate_proposal_crew", return_value=MagicMock(kickoff=MagicMock(return_value=mock_result)))

    # Mock redis calls
    mocker.patch('backend.api.proposals.redis_client.get', return_value=json.dumps({
        "proposal_id": proposal_id,
        "proposal_template": {"sections": [{"section_name": "Summary"}]},
        "form_data": {},
        "project_description": "Test"
    }))
    mocker.patch('backend.api.proposals.redis_client.setex')

    # Prepare payload
    session_id = "test_session_id"
    section_payload = {
        "section": "Summary",
        "proposal_id": proposal_id,
        "form_data": {},
        "project_description": "A test for fallback mechanism."
    }

    # Make the call
    # We need to make sure the authenticated_client uses the user_id we just used
    # The authenticated_client fixture overrides get_current_user
    
    response = client.post(f"/api/process_section/{session_id}", json=section_payload)
    
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["generated_text"] == FALLBACK_GENERATION_MESSAGE

    # Verify DB content
    with test_engine.connect() as conn:
        result = conn.execute(text("SELECT generated_sections FROM proposals WHERE id = :id"), {"id": proposal_id}).fetchone()
        sections = json.loads(result.generated_sections)
        assert sections["Summary"] == FALLBACK_GENERATION_MESSAGE
