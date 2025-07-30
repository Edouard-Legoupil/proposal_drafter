import pytest
from unittest.mock import MagicMock

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
