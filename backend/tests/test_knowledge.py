import os
import json
import uuid
from slugify import slugify
from fastapi.testclient import TestClient
from sqlalchemy import text
from backend.core.security import get_current_user

def test_create_and_update_knowledge_card_saves_content_to_file(authenticated_client: TestClient, db_session):
    """
    Tests that creating and updating a knowledge card saves the generated content to a file.
    """
    # 1. Create a knowledge card
    card_summary = "Test Knowledge Card for File Saving"
    card_id = str(uuid.uuid4())
    user_id = authenticated_client.app.dependency_overrides[get_current_user]().get("user_id")

    db_session.execute(
        text("""
            INSERT INTO knowledge_cards (id, summary, created_by, updated_by, status)
            VALUES (:id, :summary, :user_id, :user_id, 'draft')
        """),
        {"id": card_id, "summary": card_summary, "user_id": user_id}
    )

    # 2. Generate content for the card
    generated_sections = {
        "section_1": "This is the first section.",
        "section_2": "This is the second section."
    }

    # Simulate the background generation process
    db_session.execute(
        text("UPDATE knowledge_cards SET generated_sections = :sections WHERE id = :id"),
        {"sections": json.dumps(generated_sections), "id": card_id}
    )

    # Manually call the file saving function to test its logic
    from backend.api.knowledge import _save_knowledge_card_content_to_file
    _save_knowledge_card_content_to_file(db_session, card_id, generated_sections)

    # 3. Verify that the file was created
    filename = f"{slugify(card_summary)}.json"
    filepath = os.path.join("backend", "knowledge", filename)
    assert os.path.exists(filepath)

    # 4. Read the file and verify its content
    with open(filepath, 'r') as f:
        saved_content = json.load(f)
        assert saved_content == generated_sections

    # 5. Update a section of the card
    updated_content = "This is the updated first section."
    generated_sections["section_1"] = updated_content

    response = authenticated_client.put(
        f"/api/knowledge-cards/{card_id}/sections/section_1",
        json={"content": updated_content}
    )
    assert response.status_code == 200

    # 6. Verify that the file was updated
    with open(filepath, 'r') as f:
        saved_content = json.load(f)
        assert saved_content == generated_sections

    # 7. Clean up the created file
    os.remove(filepath)