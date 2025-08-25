import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine, text
from fastapi.testclient import TestClient
from backend.main import app
from backend.core.db import get_engine as main_engine
from backend.core.security import get_current_user
import jwt
from datetime import datetime, timedelta
from backend.core.config import SECRET_KEY
import uuid

@pytest.fixture(scope="function")
def test_db():
    # Use an in-memory SQLite database for testing
    engine = create_engine("sqlite:///:memory:")
    with get_engine().connect() as connection:
        # Create tables
        connection.execute(text("""
            CREATE TABLE users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                name TEXT,
                security_questions TEXT,
                session_active BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        connection.execute(text("""
            CREATE TABLE proposals (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                form_data TEXT NOT NULL,
                project_description TEXT NOT NULL,
                generated_sections TEXT,
                is_accepted BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        connection.commit()
        yield connection

@pytest.fixture(scope="function")
def authenticated_client(test_db):
    user_id = str(uuid.uuid4())
    user_email = "test@example.com"

    # Create a test user
    test_db.execute(text("INSERT INTO users (id, email, name, password) VALUES (:id, :email, :name, :password)"),
                    {"id": user_id, "email": user_email, "name": "Test User", "password": "password"})
    test_db.commit()

    # Generate a token
    token_data = {"email": user_email, "exp": datetime.utcnow() + timedelta(minutes=30)}
    token = jwt.encode(token_data, SECRET_KEY, algorithm="HS256")

    # Override the get_current_user dependency
    def get_current_user_override():
        return {"user_id": user_id, "email": user_email, "name": "Test User"}

    app.dependency_overrides[get_current_user] = get_current_user_override

    with patch('backend.core.db.engine', test_db.engine):
         with TestClient(app) as c:
            c.cookies["auth_token"] = token
            yield c

    app.dependency_overrides = {}
