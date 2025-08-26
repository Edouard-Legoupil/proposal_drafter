import pytest
from httpx import AsyncClient
from backend.main import app
from backend.core.config import load_proposal_template
from backend.core.db import get_engine
from sqlalchemy import text
import uuid
import json

# Load sections from a default template for test setup
try:
    DEFAULT_TEMPLATE = load_proposal_template("unhcr_proposal_template.json")
    SECTIONS = [section.get("section_name") for section in DEFAULT_TEMPLATE.get("sections", [])]
except Exception as e:
    # If template loading fails, set to a fallback list to avoid crashing tests.
    SECTIONS = ["Summary", "Background", "Objectives"]
    print(f"Warning: Could not load default template for tests. Using fallback sections. Error: {e}")


@pytest.mark.asyncio
async def test_generate_document():
    # This test requires a valid user session. For simplicity in this test,
    # we will bypass authentication and assume a user context.
    # In a real-world scenario, you would mock the get_current_user dependency.
    user_id = "test_user_id"
    proposal_id = str(uuid.uuid4())

    # Step 1: Manually insert a mock proposal into the database
    # This is necessary because the endpoint now reads directly from the database.
    mock_proposal = {
        "id": proposal_id,
        "user_id": user_id,
        "form_data": json.dumps({"Project title": "Disaster Relief"}),
        "project_description": "Testing document generation.",
        "generated_sections": json.dumps({section: f"Sample content for {section}" for section in SECTIONS}),
        "template_name": "unhcr_proposal_template.json"
    }

    engine = get_engine()
    with engine.begin() as connection:
        # Clean up any previous test runs
        connection.execute(text("DELETE FROM proposals WHERE id = :id"), {"id": proposal_id})
        # Insert the new mock proposal
        connection.execute(
            text("""
                INSERT INTO proposals (id, user_id, form_data, project_description, generated_sections, template_name)
                VALUES (:id, :user_id, :form_data, :project_description, :generated_sections, :template_name)
            """),
            mock_proposal
        )

    # Step 2: Call the generate-document endpoint
    # We need to provide a mock for get_current_user to avoid auth errors.
    # For this test, we'll assume the endpoint is accessible. A more robust test would use dependency overrides.

    # To test the endpoint directly, we need to simulate a logged-in user.
    # A simple way is to create a dummy token or override the dependency.
    # Given the constraints, we'll assume the happy path where user is authenticated.
    # Note: This is a simplification. Real tests should handle auth properly.

    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Mocking get_current_user to return a dummy user
        app.dependency_overrides[app.url_path_for("generate_and_download_document").__self__.get_current_user] = lambda: {"user_id": user_id}

        response = await ac.get(f"/generate-document/{proposal_id}?format=docx")

    # Step 3: Assertions
    assert response.status_code == 200
    assert response.headers['content-type'] == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    assert "attachment; filename=" in response.headers['content-disposition']
    assert len(response.content) > 0

    # Clean up the database
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM proposals WHERE id = :id"), {"id": proposal_id})

    # Restore original dependency
    app.dependency_overrides = {}
