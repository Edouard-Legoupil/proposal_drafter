import uuid
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from backend.core.security import get_current_user
from unittest.mock import MagicMock, patch

@pytest.fixture(autouse=True)
def mock_get_engine(test_engine):
    import backend.core.db
    old_engine = backend.core.db.engine
    backend.core.db.engine = test_engine
    yield
    backend.core.db.engine = old_engine

def test_proposal_review_with_rating(authenticated_client: TestClient, db_session):
    user_id = authenticated_client.app.dependency_overrides[get_current_user]().get("user_id")
    proposal_id = str(uuid.uuid4())

    # Setup proposal
    db_session.execute(
        text("INSERT INTO proposals (id, user_id, form_data, project_description, status) VALUES (:id, :uid, '{}', 'desc', 'in_review')"),
        {"id": proposal_id, "uid": user_id}
    )
    db_session.execute(
        text("INSERT INTO proposal_status_history (proposal_id, status) VALUES (:pid, 'in_review')"),
        {"pid": proposal_id}
    )
    # Assign reviewer
    db_session.execute(
        text("INSERT INTO proposal_peer_reviews (proposal_id, reviewer_id, status) VALUES (:pid, :rid, 'pending')"),
        {"pid": proposal_id, "rid": user_id}
    )
    db_session.commit()

    # Submit review with rating
    review_payload = {
        "comments": [
            {
                "section_name": "Summary",
                "review_text": "Good",
                "type_of_comment": "General",
                "severity": "Low",
                "rating": "up"
            }
        ]
    }
    response = authenticated_client.post(f"/api/proposals/{proposal_id}/review", json=review_payload)
    assert response.status_code == 200

    # Verify in DB
    result = db_session.execute(
        text("SELECT rating, review_text FROM proposal_peer_reviews WHERE proposal_id = :pid"),
        {"pid": proposal_id}
    ).fetchone()
    assert result[0] == "up"
    assert result[1] == "Good"

def test_knowledge_card_review(authenticated_client: TestClient, db_session):
    user_id = authenticated_client.app.dependency_overrides[get_current_user]().get("user_id")
    card_id = str(uuid.uuid4())
    other_user_id = str(uuid.uuid4())

    # Create another user as owner
    db_session.execute(
        text("INSERT INTO users (id, email, password, name) VALUES (:id, :email, 'pass', 'Other')"),
        {"id": other_user_id, "email": f"other_{uuid.uuid4()}@example.com"}
    )

    # Setup knowledge card
    db_session.execute(
        text("INSERT INTO knowledge_cards (id, summary, created_by, status) VALUES (:id, 'summary', :uid, 'draft')"),
        {"id": card_id, "uid": other_user_id}
    )
    db_session.commit()

    # Submit review
    review_payload = {
        "comments": [
            {
                "section_name": "Main Section",
                "review_text": "Needs work",
                "type_of_comment": "Clarity",
                "severity": "Medium",
                "rating": "down"
            }
        ]
    }
    response = authenticated_client.post(f"/api/knowledge-cards/{card_id}/review", json=review_payload)
    assert response.status_code == 200

    # Get card for review
    response = authenticated_client.get(f"/api/review-knowledge-card/{card_id}")
    assert response.status_code == 200
    data = response.json()
    assert data['draft_comments']['Main Section']['rating'] == "down"
