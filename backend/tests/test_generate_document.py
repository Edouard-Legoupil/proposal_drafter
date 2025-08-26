import pytest
import uuid
import json
from sqlalchemy import text
from backend.main import app
from backend.core.security import get_current_user

@pytest.mark.asyncio
async def test_generate_document(authenticated_client, db_session):
    client = authenticated_client
    user_id = app.dependency_overrides[get_current_user]()['user_id']
    proposal_id = str(uuid.uuid4())

    # Insert a mock proposal for the authenticated user
    db_session.execute(
        text("""
            INSERT INTO proposals (id, user_id, form_data, project_description, generated_sections, template_name, is_accepted)
            VALUES (:id, :user_id, :form_data, :project_description, :generated_sections, :template_name, :is_accepted)
        """),
        {
            "id": proposal_id, "user_id": user_id,
            "form_data": json.dumps({"Project Draft Short name": "Disaster Relief"}),
            "project_description": "Testing document generation.",
            "generated_sections": json.dumps({"Summary": "Content"}),
            "template_name": "unhcr_proposal_template.json", "is_accepted": False
        }
    )
    db_session.commit()

    # Call the endpoint
    response = client.get(f"/api/generate-document/{proposal_id}?format=docx")

    # Assertions
    assert response.status_code == 200
    assert 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in response.headers['content-type']
