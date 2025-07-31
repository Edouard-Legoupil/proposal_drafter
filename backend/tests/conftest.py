import pytest
from unittest.mock import MagicMock
from dotenv import load_dotenv
from backend.main import app
from backend.core.security import get_current_user

# Load environment variables from .env file before running tests
load_dotenv()

def mock_get_current_user():
    return {"user_id": "test-user-id", "name": "Test User", "email": "test@example.com"}

app.dependency_overrides[get_current_user] = mock_get_current_user

@pytest.fixture(autouse=True)
def mock_db_engine(monkeypatch):
    """
    This fixture automatically mocks the SQLAlchemy engine for all tests.
    It prevents tests from trying to connect to a real database by replacing
    the `engine` object in `backend.core.db` with a mock.
    """
    # Create a mock engine that can be used in place of the real one.
    mock_engine = MagicMock()

    # Use monkeypatch to replace the actual engine with our mock.
    # This change will be reverted automatically after each test.
    monkeypatch.setattr("backend.core.db.engine", mock_engine)

    # The mock is yielded so that it could be used in tests if needed,
    # though for this use case, its primary purpose is just to exist.
    yield mock_engine

@pytest.fixture(autouse=True)
def mock_json_knowledge_source(monkeypatch):
    """
    This fixture automatically mocks the JSONKnowledgeSource for all tests.
    It prevents tests from trying to load a real file by replacing
    the `JSONKnowledgeSource` object in `backend.utils.crew` with a mock.
    """
    # Create a mock JSONKnowledgeSource that can be used in place of the real one.
    mock_json_knowledge_source = MagicMock()

    # Use monkeypatch to replace the actual JSONKnowledgeSource with our mock.
    # This change will be reverted automatically after each test.
    monkeypatch.setattr("backend.utils.crew.JSONKnowledgeSource", mock_json_knowledge_source)

    # The mock is yielded so that it could be used in tests if needed,
    # though for this use case, its primary purpose is just to exist.
    yield mock_json_knowledge_source
