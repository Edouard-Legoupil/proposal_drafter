"""
Unit tests for Wizard API endpoints.

This module tests all wizard utility API endpoints including:
- Categories endpoint
- Q&A items endpoint
- Feedback submission
- Popular questions
- Search functionality
"""

from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from backend.main import app
from backend.core.dependencies import get_db_session

# Mock database session for testing
mock_db_session = MagicMock(spec=AsyncSession)


async def override_get_db_session():
    """Override the database session dependency with a mock for testing."""
    try:
        yield mock_db_session
    finally:
        pass


app.dependency_overrides[get_db_session] = override_get_db_session

client = TestClient(app)


@patch("backend.api.wizard.db.execute")
def test_create_category(mock_execute):
    """Test creating a new Q&A category."""
    # Mock the database response
    mock_result = MagicMock()
    mock_result.scalar.return_value = 1  # Mock the ID
    mock_execute.return_value = mock_result

    response = client.post("/api/wizard/categories", json={"name": "Test Category", "description": "Test Description"})
    print(f"Response status: {response.status_code}")
    print(f"Response content: {response.content}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Category"
    assert "id" in data
    assert "created_at" in data


def test_get_categories():
    """Test getting all Q&A categories."""
    response = client.get("/api/wizard/categories")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    # Should have at least the test category we created
    assert len(response.json()) >= 1


def test_create_qa_item():
    """Test creating a new Q&A item."""
    # First create a category
    category_response = client.post(
        "/api/wizard/categories", json={"name": "Test Category 2", "description": "Test Description 2"}
    )
    category_id = category_response.json()["id"]

    # Then create QA item
    response = client.post(
        "/api/wizard/qa", json={"question": "Test Question", "answer": "Test Answer", "category_id": category_id}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["question"] == "Test Question"
    assert data["category_id"] == category_id


def test_get_qa_items():
    """Test getting Q&A items with filtering."""
    response = client.get("/api/wizard/qa")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert "total" in data
    assert "limit" in data
    assert "offset" in data


def test_get_qa_items_with_category():
    """Test getting Q&A items filtered by category."""
    # Create a test category and item
    category_response = client.post(
        "/api/wizard/categories", json={"name": "Filter Test Category", "description": "Filter Test"}
    )
    category_id = category_response.json()["id"]

    client.post(
        "/api/wizard/qa",
        json={"question": "Filter Test Question", "answer": "Filter Test Answer", "category_id": category_id},
    )

    # Get items for this category
    response = client.get(f"/api/wizard/qa?category_id={category_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 1
    assert data["items"][0]["question"] == "Filter Test Question"


def test_get_qa_items_with_search():
    """Test getting Q&A items with search query."""
    # Create a test item with known content
    category_response = client.post(
        "/api/wizard/categories", json={"name": "Search Test Category", "description": "Search Test"}
    )
    category_id = category_response.json()["id"]

    client.post(
        "/api/wizard/qa",
        json={
            "question": "Searchable Test Question",
            "answer": "This answer contains searchable content",
            "category_id": category_id,
        },
    )

    # Search for it
    response = client.get("/api/wizard/qa?search=searchable")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 1
    assert "searchable" in data["items"][0]["question"].lower() or "searchable" in data["items"][0]["answer"].lower()


def test_search_qa():
    """Test the dedicated search endpoint."""
    response = client.post("/api/wizard/search", json={"query": "test"})
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert isinstance(data["results"], list)
    assert "total" in data


def test_get_popular_questions():
    """Test getting popular questions."""
    response = client.get("/api/wizard/popular")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_submit_feedback():
    """Test submitting feedback on a Q&A item."""
    # First create a QA item to provide feedback on
    category_response = client.post(
        "/api/wizard/categories", json={"name": "Feedback Test Category", "description": "Feedback Test"}
    )
    category_id = category_response.json()["id"]

    qa_response = client.post(
        "/api/wizard/qa",
        json={"question": "Feedback Test Question", "answer": "Feedback Test Answer", "category_id": category_id},
    )
    qa_item_id = qa_response.json()["id"]

    # Submit feedback
    feedback_response = client.post(
        "/api/wizard/feedback",
        json={"qa_item_id": qa_item_id, "feedback_score": 5, "feedback_comment": "Very helpful!"},
    )
    assert feedback_response.status_code == 200
    feedback_data = feedback_response.json()
    assert feedback_data["success"] == True
    assert "message" in feedback_data


def test_feedback_validation():
    """Test feedback score validation."""
    # Create a QA item
    category_response = client.post(
        "/api/wizard/categories", json={"name": "Validation Test Category", "description": "Validation Test"}
    )
    category_id = category_response.json()["id"]

    qa_response = client.post(
        "/api/wizard/qa",
        json={"question": "Validation Test Question", "answer": "Validation Test Answer", "category_id": category_id},
    )
    qa_item_id = qa_response.json()["id"]

    # Try invalid feedback score (0)
    response = client.post(
        "/api/wizard/feedback", json={"qa_item_id": qa_item_id, "feedback_score": 0, "feedback_comment": "Test"}
    )
    assert response.status_code == 400

    # Try invalid feedback score (6)
    response = client.post(
        "/api/wizard/feedback", json={"qa_item_id": qa_item_id, "feedback_score": 6, "feedback_comment": "Test"}
    )
    assert response.status_code == 400


def test_unique_constraints():
    """Test unique constraints on categories and questions."""
    # Try creating duplicate category
    client.post("/api/wizard/categories", json={"name": "Unique Test Category", "description": "First"})

    response = client.post("/api/wizard/categories", json={"name": "Unique Test Category", "description": "Duplicate"})
    assert response.status_code == 400

    # Try creating duplicate question
    category_response = client.post(
        "/api/wizard/categories", json={"name": "Unique Question Category", "description": "Unique Test"}
    )
    category_id = category_response.json()["id"]

    client.post(
        "/api/wizard/qa",
        json={"question": "Unique Test Question", "answer": "First answer", "category_id": category_id},
    )

    response = client.post(
        "/api/wizard/qa",
        json={"question": "Unique Test Question", "answer": "Duplicate answer", "category_id": category_id},
    )
    assert response.status_code == 400
