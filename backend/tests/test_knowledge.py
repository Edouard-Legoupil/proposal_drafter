import os
import json
import uuid
import io
from unittest.mock import patch, MagicMock, AsyncMock
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

    # The test client runs in a separate thread and doesn't share the transaction.
    # We need to commit the changes to the database so that the API endpoint can see them.
    db_session.commit()

    response = authenticated_client.put(
        f"/api/knowledge-cards/{card_id}/sections/section_1",
        json={"content": updated_content}
    )
    assert response.status_code == 200, f"Expected status 200, got {response.status_code}. Response: {response.text}"

    # 6. Verify that the file was updated
    with open(filepath, 'r') as f:
        saved_content = json.load(f)
        assert saved_content == generated_sections

    # 7. Clean up the created file
    os.remove(filepath)


@patch('backend.api.knowledge.process_and_store_text', new_callable=AsyncMock)
@patch('backend.api.knowledge.PdfReader')
def test_upload_pdf_reference_success(mock_pdf_reader, mock_process_and_store, authenticated_client: TestClient, db_session):
    """
    Tests the successful upload of a PDF for a reference, mocking the processing part.
    """
    # 1. Setup mock for PdfReader to avoid actual PDF parsing
    mock_page = MagicMock()
    extracted_text = "This is test text from the mocked PDF."
    mock_page.extract_text.return_value = extracted_text
    mock_pdf_reader.return_value.pages = [mock_page]

    # 2. Setup database entries: a knowledge card and a reference
    user_id = authenticated_client.app.dependency_overrides[get_current_user]().get("user_id")
    card_id = str(uuid.uuid4())
    reference_id = str(uuid.uuid4())

    db_session.execute(
        text("INSERT INTO knowledge_cards (id, summary, created_by, updated_by) VALUES (:id, 'Test Card for PDF Upload', :user_id, :user_id)"),
        {"id": card_id, "user_id": user_id}
    )
    db_session.execute(
        text("""
            INSERT INTO knowledge_card_references (id, knowledge_card_id, url, reference_type, created_by, updated_by)
            VALUES (:id, :card_id, 'http://example.com/pdf', 'PDF Test', :user_id, :user_id)
        """),
        {"id": reference_id, "card_id": card_id, "user_id": user_id}
    )
    db_session.commit()

    # 3. Create a dummy in-memory file to upload
    dummy_file_content = io.BytesIO(b"This is a dummy pdf.")

    # 4. Make the POST request to the upload endpoint
    response = authenticated_client.post(
        f"/api/knowledge-cards/references/{reference_id}/upload",
        files={"file": ("test.pdf", dummy_file_content, "application/pdf")}
    )

    # 5. Assert the response is successful
    assert response.status_code == 200, f"Expected status 200, got {response.status_code}. Response: {response.text}"
    assert response.json()["message"] == "PDF content ingested successfully."

    # 6. Verify that the mocked functions were called as expected
    mock_pdf_reader.assert_called_once()
    mock_process_and_store.assert_awaited_once()

    # 7. Check the arguments passed to the text processing function
    args, _ = mock_process_and_store.call_args
    assert args[0] == uuid.UUID(reference_id)  # Check reference_id
    assert args[1] == extracted_text           # Check extracted text
    # args[2] is the connection object, which is harder to assert on directly, but we know it was passed
    assert args[2] is not None