import os
import pytest
import uuid
import jwt
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from fastapi.testclient import TestClient

# --- Environment Variable Setup ---
os.environ['DB_USERNAME'] = 'testuser'
os.environ['DB_PASSWORD'] = 'testpass'
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_NAME'] = 'testdb'
os.environ['SECRET_KEY'] = 'test-secret-key'
os.environ['AZURE_OPENAI_ENDPOINT'] = 'https://test.openai.azure.com/'
os.environ['AZURE_OPENAI_API_KEY'] = 'test-key'
os.environ['OPENAI_API_VERSION'] = '2023-07-01-preview'
os.environ['AZURE_OPENAI_DEPLOYMENT'] = 'test-deployment'
os.environ['AZURE_DEPLOYMENT_NAME'] = 'test-deployment'
os.environ['AZURE_OPENAI_EMBEDDING_DEPLOYMENT'] = 'test-embedding-deployment'
os.environ['SERPER_API_KEY'] = 'test_serper_key'

# --- Application and Dependency Imports ---
from backend.main import app
from backend.core.db import get_engine
from backend.core.security import get_current_user

@pytest.fixture(scope="function")
def test_engine():
    """Creates a fresh, in-memory SQLite engine for each test function."""
    engine = create_engine("sqlite:///file::memory:?cache=shared", connect_args={"check_same_thread": False})
    with engine.connect() as connection:
        # Use transaction to ensure DDL is committed
        with connection.begin():
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL,
                    name TEXT, security_questions TEXT, session_active BOOLEAN,
                    created_at DATETIME, updated_at DATETIME
                )
            """))
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS proposals (
                    id TEXT PRIMARY KEY, user_id TEXT, form_data TEXT, project_description TEXT,
                    generated_sections TEXT, is_accepted BOOLEAN, template_name TEXT,
                    created_at DATETIME, updated_at DATETIME,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """))
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS knowledge_cards (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    summary TEXT,
                    template_name TEXT,
                    status TEXT,
                    donor_id TEXT,
                    outcome_id TEXT,
                    field_context_id TEXT,
                    created_by TEXT,
                    updated_by TEXT,
                    created_at DATETIME,
                    updated_at DATETIME,
                    generated_sections TEXT
                )
            """))
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS knowledge_card_history (
                    id TEXT PRIMARY KEY,
                    knowledge_card_id TEXT NOT NULL,
                    generated_sections_snapshot TEXT,
                    created_by TEXT,
                    created_at DATETIME,
                    FOREIGN KEY (knowledge_card_id) REFERENCES knowledge_cards(id)
                )
            """))
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS knowledge_card_references (
                    id TEXT PRIMARY KEY,
                    knowledge_card_id TEXT NOT NULL,
                    url TEXT,
                    reference_type TEXT,
                    summary TEXT,
                    created_by TEXT,
                    updated_by TEXT,
                    created_at DATETIME,
                    updated_at DATETIME,
                    scraped_at DATETIME,
                    scraping_error BOOLEAN,
                    FOREIGN KEY (knowledge_card_id) REFERENCES knowledge_cards(id)
                )
            """))
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS knowledge_card_reference_vectors (
                    id TEXT PRIMARY KEY,
                    reference_id TEXT NOT NULL,
                    text_chunk TEXT,
                    embedding TEXT,
                    FOREIGN KEY (reference_id) REFERENCES knowledge_card_references(id)
                )
            """))
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS donors (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_by TEXT
                )
            """))
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS outcomes (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_by TEXT
                )
            """))
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS field_contexts (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    title TEXT,
                    category TEXT,
                    geographic_coverage TEXT,
                    created_by TEXT
                )
            """))
    return engine

@pytest.fixture(scope="function", autouse=True)
def override_get_engine(test_engine):
    """Fixture to override the get_engine dependency for all tests."""
    app.dependency_overrides[get_engine] = lambda: test_engine
    yield
    app.dependency_overrides.pop(get_engine, None)

@pytest.fixture(scope="function")
def db_session(test_engine):
    """Provides a transactional scope for each test function."""
    connection = test_engine.connect()
    transaction = connection.begin()
    yield connection
    transaction.rollback()
    connection.close()

@pytest.fixture
def client():
    """A basic, unauthenticated TestClient."""
    return TestClient(app)

@pytest.fixture
def authenticated_client(client, db_session):
    """An authenticated TestClient."""
    user_id = str(uuid.uuid4())
    user_email = "test@example.com"

    # HACK: Clear the user if it exists to prevent IntegrityError in tests.
    # This is needed because some tests commit transactions, which can cause
    # data to leak between tests when using an in-memory SQLite DB.
    db_session.execute(text("DELETE FROM users WHERE email = :email"), {"email": user_email})

    db_session.execute(
        text("INSERT INTO users (id, email, name, password) VALUES (:id, :email, :name, :password)"),
        {"id": user_id, "email": user_email, "name": "Test User", "password": "password"}
    )

    def get_current_user_override():
        return {"user_id": user_id, "email": user_email, "name": "Test User"}

    app.dependency_overrides[get_current_user] = get_current_user_override

    token_data = {"email": user_email, "exp": datetime.utcnow() + timedelta(minutes=30)}
    token = jwt.encode(token_data, os.environ['SECRET_KEY'], algorithm="HS256")
    client.cookies["auth_token"] = token

    yield client

    app.dependency_overrides.pop(get_current_user, None)
