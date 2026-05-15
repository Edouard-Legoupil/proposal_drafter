import os
import pytest
import uuid
import jwt
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from fastapi.testclient import TestClient

# --- Environment Variable Setup ---
# Set TESTING flag BEFORE any imports to prevent production DB connections
os.environ["TESTING"] = "true"

os.environ["DB_USERNAME"] = "testuser"
os.environ["DB_PASSWORD"] = "testpass"
os.environ["DB_HOST"] = "localhost"
os.environ["DB_NAME"] = "testdb"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["AZURE_OPENAI_ENDPOINT"] = "https://test.openai.azure.com/"
os.environ["AZURE_OPENAI_API_KEY"] = "test-key"
os.environ["OPENAI_API_VERSION"] = "2023-07-01-preview"
os.environ["AZURE_OPENAI_DEPLOYMENT"] = "test-deployment"
os.environ["AZURE_DEPLOYMENT_NAME"] = "test-deployment"
os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"] = "test-embedding-deployment"
os.environ["SERPER_API_KEY"] = "test_serper_key"

# --- Application and Dependency Imports ---
from backend.main import app
from backend.core.db import get_engine
from backend.core.security import get_current_user


@pytest.fixture(scope="function")
def test_engine():
    """Creates a fresh, in-memory SQLite engine for each test function."""
    engine = create_engine(
        "sqlite:///file::memory:?cache=shared",
        connect_args={"check_same_thread": False},
    )
    with engine.connect() as connection:
        # Use transaction to ensure DDL is committed
        with connection.begin():
            connection.execute(text("DROP TABLE IF EXISTS knowledge_card_reviews"))
            connection.execute(text("DROP TABLE IF EXISTS users"))
            connection.execute(text("DROP TABLE IF EXISTS teams"))
            connection.execute(text("DROP TABLE IF EXISTS proposal_peer_reviews"))
            connection.execute(text("DROP TABLE IF EXISTS proposal_status_history"))
            connection.execute(text("DROP TABLE IF EXISTS proposals"))
            connection.execute(text("DROP TABLE IF EXISTS donor_template_comments"))
            connection.execute(text("DROP TABLE IF EXISTS donor_template_requests"))
            connection.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS teams (
                    id TEXT PRIMARY KEY, name TEXT UNIQUE NOT NULL
                )
            """
                )
            )
            connection.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL,
                    name TEXT, security_questions TEXT, session_active BOOLEAN,
                    created_at DATETIME, updated_at DATETIME
                )
            """
                )
            )
            connection.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS proposals (
                    id TEXT PRIMARY KEY, user_id TEXT, form_data TEXT, project_description TEXT,
                    generated_sections TEXT, is_accepted BOOLEAN, template_name TEXT,
                    status TEXT, contribution_id TEXT,
                    created_at DATETIME, updated_at DATETIME,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """
                )
            )
            connection.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS proposal_status_history (
                    id TEXT PRIMARY KEY, proposal_id TEXT, status TEXT,
                    generated_sections_snapshot TEXT, created_at DATETIME,
                    FOREIGN KEY (proposal_id) REFERENCES proposals(id)
                )
            """
                )
            )
            connection.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS proposal_peer_reviews (
                    id TEXT PRIMARY KEY, proposal_id TEXT, reviewer_id TEXT,
                    proposal_status_history_id TEXT, section_name TEXT,
                    rating TEXT, status TEXT, deadline DATETIME,
                    review_text TEXT, author_response TEXT,
                    author_response_by TEXT,
                    type_of_comment TEXT, severity TEXT,
                    created_at DATETIME, updated_at DATETIME,
                    FOREIGN KEY (proposal_id) REFERENCES proposals(id),
                    FOREIGN KEY (reviewer_id) REFERENCES users(id)
                )
            """
                )
            )
            connection.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS knowledge_card_reviews (
                    id TEXT PRIMARY KEY, knowledge_card_id TEXT, reviewer_id TEXT,
                    section_name TEXT, rating TEXT, review_text TEXT,
                    type_of_comment TEXT, severity TEXT,
                    author_response TEXT, status TEXT,
                    author_response_by TEXT,
                    created_at DATETIME, updated_at DATETIME,
                    FOREIGN KEY (knowledge_card_id) REFERENCES knowledge_cards(id),
                    FOREIGN KEY (reviewer_id) REFERENCES users(id)
                )
            """
                )
            )
            connection.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS knowledge_cards (
                    id TEXT PRIMARY KEY,
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
            """
                )
            )
            connection.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS knowledge_card_history (
                    id TEXT PRIMARY KEY,
                    knowledge_card_id TEXT NOT NULL,
                    generated_sections_snapshot TEXT,
                    created_by TEXT,
                    created_at DATETIME,
                    FOREIGN KEY (knowledge_card_id) REFERENCES knowledge_cards(id)
                )
            """
                )
            )
            connection.execute(
                text(
                    """
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
            """
                )
            )
            connection.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS knowledge_card_reference_vectors (
                    id TEXT PRIMARY KEY,
                    reference_id TEXT NOT NULL,
                    text_chunk TEXT,
                    embedding TEXT,
                    FOREIGN KEY (reference_id) REFERENCES knowledge_card_references(id)
                )
            """
                )
            )
            connection.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS knowledge_card_to_references (
                    knowledge_card_id TEXT NOT NULL REFERENCES knowledge_cards(id),
                    reference_id TEXT NOT NULL REFERENCES knowledge_card_references(id),
                    PRIMARY KEY (knowledge_card_id, reference_id)
                )
            """
                )
            )
            connection.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS donors (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_by TEXT
                )
            """
                )
            )
            connection.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS outcomes (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_by TEXT
                )
            """
                )
            )
            connection.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS field_contexts (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    title TEXT,
                    category TEXT,
                    geographic_coverage TEXT,
                    created_by TEXT
                )
            """
                )
            )
            connection.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS donor_template_requests (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    donor_id TEXT,
                    configuration TEXT,
                    initial_file_content TEXT,
                    status TEXT DEFAULT 'pending',
                    created_by TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
                )
            )
            connection.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS donor_template_comments (
                    id TEXT PRIMARY KEY,
                    template_request_id TEXT NOT NULL,
                    template_name TEXT,
                    user_id TEXT NOT NULL,
                    comment_text TEXT NOT NULL,
                    section_name TEXT,
                    rating TEXT,
                    severity TEXT,
                    type_of_comment TEXT,
                    author_response TEXT,
                    author_response_by TEXT,
                    status TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
                )
            )
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
        {
            "id": user_id,
            "email": user_email,
            "name": "Test User",
            "password": "password",
        },
    )

    def get_current_user_override():
        return {
            "user_id": user_id,
            "email": user_email,
            "name": "Test User",
            "roles": [
                "knowledge manager donors",
                "knowledge manager outcome",
                "knowledge manager field context",
                "proposal writer",
                "project reviewer",
            ],
        }

    app.dependency_overrides[get_current_user] = get_current_user_override

    token_data = {"email": user_email, "exp": datetime.utcnow() + timedelta(minutes=30)}
    token = jwt.encode(token_data, os.environ["SECRET_KEY"], algorithm="HS256")
    client.cookies["auth_token"] = token

    yield client

    app.dependency_overrides.pop(get_current_user, None)


# =============================================================================
# Authorization Test Fixtures (T004 - for Object-Level Authorization)
# =============================================================================


@pytest.fixture
def user_a(db_session):
    """
    Test fixture: User A - a regular user with resources.
    Used for authorization tests to verify ownership checks.
    """
    user_id = str(uuid.uuid4())
    user_email = "user_a@example.com"

    # Clear existing user
    db_session.execute(text("DELETE FROM users WHERE email = :email"), {"email": user_email})

    # Insert User A
    db_session.execute(
        text(
            "INSERT INTO users (id, email, name, password, is_admin) "
            "VALUES (:id, :email, :name, :password, :is_admin)"
        ),
        {
            "id": user_id,
            "email": user_email,
            "name": "User A",
            "password": "password123",
            "is_admin": False,
        },
    )
    db_session.commit()

    # Create a mock User object with the necessary attributes
    class MockUser:
        id = user_id
        email = user_email
        name = "User A"
        is_admin = False

        @classmethod
        async def has_permission(cls, permission):
            """Mock has_permission for User A (regular user)."""
            return permission in ["read", "write"]  # Regular user permissions

        @classmethod
        async def is_team_member(cls, team_id):
            """Mock is_team_member for User A."""
            return team_id == 1  # User A is in team 1

        @classmethod
        async def is_donor_group_member(cls, donor_group_id):
            """Mock is_donor_group_member for User A."""
            return donor_group_id == 1  # User A is in donor group 1

    return MockUser


@pytest.fixture
def user_b(db_session):
    """
    Test fixture: User B - another regular user without access to User A's resources.
    Used for authorization tests to verify access denial.
    """
    user_id = str(uuid.uuid4())
    user_email = "user_b@example.com"

    # Clear existing user
    db_session.execute(text("DELETE FROM users WHERE email = :email"), {"email": user_email})

    # Insert User B
    db_session.execute(
        text(
            "INSERT INTO users (id, email, name, password, is_admin) "
            "VALUES (:id, :email, :name, :password, :is_admin)"
        ),
        {
            "id": user_id,
            "email": user_email,
            "name": "User B",
            "password": "password456",
            "is_admin": False,
        },
    )
    db_session.commit()

    # Create a mock User object with the necessary attributes
    class MockUser:
        id = user_id
        email = user_email
        name = "User B"
        is_admin = False

        @classmethod
        async def has_permission(cls, permission):
            """Mock has_permission for User B (regular user)."""
            return permission in ["read", "write"]

        @classmethod
        async def is_team_member(cls, team_id):
            """Mock is_team_member for User B."""
            return team_id == 2  # User B is in team 2 (not team 1)

        @classmethod
        async def is_donor_group_member(cls, donor_group_id):
            """Mock is_donor_group_member for User B."""
            return donor_group_id == 2  # User B is in donor group 2 (not group 1)

    return MockUser


@pytest.fixture
def admin_user(db_session):
    """
    Test fixture: Admin user with full access to all resources.
    Used for authorization tests to verify admin bypass.
    """
    user_id = str(uuid.uuid4())
    user_email = "admin@example.com"

    # Clear existing user
    db_session.execute(text("DELETE FROM users WHERE email = :email"), {"email": user_email})

    # Insert Admin user
    db_session.execute(
        text(
            "INSERT INTO users (id, email, name, password, is_admin) "
            "VALUES (:id, :email, :name, :password, :is_admin)"
        ),
        {
            "id": user_id,
            "email": user_email,
            "name": "Admin User",
            "password": "admin123",
            "is_admin": True,
        },
    )
    db_session.commit()

    # Create a mock Admin User object
    class MockAdminUser:
        id = user_id
        email = user_email
        name = "Admin User"
        is_admin = True

        @classmethod
        async def has_permission(cls, permission):
            """Admin has all permissions."""
            return True

        @classmethod
        async def is_team_member(cls, team_id):
            """Admin is member of all teams."""
            return True

        @classmethod
        async def is_donor_group_member(cls, donor_group_id):
            """Admin is member of all donor groups."""
            return True

    return MockAdminUser


# =============================================================================
# Mock Resource Models for Authorization Tests
# =============================================================================


@pytest.fixture
def mock_proposal_owned_by_user_a():
    """Mock proposal object owned by User A."""

    class MockProposal:
        id = 1
        title = "User A's Proposal"
        owner_id = "user_a_id"  # Will be set to user_a's ID
        team_id = 1
        donor_group_id = 1
        status = "draft"
        content = {}
        created_at = datetime.utcnow()
        updated_at = datetime.utcnow()

    return MockProposal


@pytest.fixture
def mock_proposal_owned_by_user_b():
    """Mock proposal object owned by User B."""

    class MockProposal:
        id = 2
        title = "User B's Proposal"
        owner_id = "user_b_id"  # Will be set to user_b's ID
        team_id = 2
        donor_group_id = 2
        status = "draft"
        content = {}
        created_at = datetime.utcnow()
        updated_at = datetime.utcnow()

    return MockProposal


@pytest.fixture
def mock_knowledge_card_owned_by_user_a():
    """Mock knowledge card object owned by User A."""

    class MockKnowledgeCard:
        id = 1
        title = "User A's Knowledge Card"
        owner_id = "user_a_id"
        shared_with = []
        classification = "public"
        status = "approved"
        content = {}
        created_at = datetime.utcnow()
        updated_at = datetime.utcnow()

    return MockKnowledgeCard


@pytest.fixture
def mock_template_owned_by_user_a():
    """Mock template object owned by User A."""

    class MockTemplate:
        id = 1
        name = "User A's Template"
        owner_id = "user_a_id"
        organization_id = 1
        is_public = False
        status = "active"
        content = {}
        created_at = datetime.utcnow()
        updated_at = datetime.utcnow()

    return MockTemplate


@pytest.fixture
def mock_public_template():
    """Mock public template accessible to organization members."""

    class MockTemplate:
        id = 2
        name = "Public Template"
        owner_id = "admin_id"
        organization_id = 1
        is_public = True
        status = "active"
        content = {}
        created_at = datetime.utcnow()
        updated_at = datetime.utcnow()

    return MockTemplate


# =============================================================================
# JWT Token Creation for Authorization Tests
# =============================================================================


@pytest.fixture
def token_for_user(user_data, db_session):
    """
    Create a JWT token for a test user.

    Args:
        user_data: Dict containing user_id, email, etc.

    Returns:
        JWT token string
    """
    token_data = {
        "sub": str(user_data.get("user_id", user_data.get("id"))),
        "email": user_data.get("email"),
        "exp": datetime.utcnow() + timedelta(hours=1),
    }
    token = jwt.encode(token_data, os.environ["SECRET_KEY"], algorithm="HS256")
    return token


@pytest.fixture
def create_test_token():
    """
    Factory fixture to create JWT tokens for any user.

    Usage:
        token = create_test_token({"user_id": "123", "email": "test@example.com"})
    """

    def _create_token(user_data: dict, expires_delta: timedelta = timedelta(hours=1)) -> str:
        token_data = {
            "sub": str(user_data.get("user_id", user_data.get("id"))),
            "email": user_data.get("email"),
            "exp": datetime.utcnow() + expires_delta,
        }
        return jwt.encode(token_data, os.environ["SECRET_KEY"], algorithm="HS256")

    return _create_token


# =============================================================================
# Client Fixtures with Different Users
# =============================================================================


@pytest.fixture
def client_user_a(client, user_a, create_test_token):
    """
    TestClient authenticated as User A.

    Usage:
        def test_something(client_user_a):
            response = client_user_a.get("/api/proposals/1")
            assert response.status_code == 200
    """
    # Create token for User A
    token = create_test_token(
        {
            "user_id": user_a.id,
            "email": user_a.email,
        }
    )

    # Set up dependency override
    def get_current_user_override():
        return user_a

    app.dependency_overrides[get_current_user] = get_current_user_override
    client.headers["Authorization"] = f"Bearer {token}"

    yield client

    app.dependency_overrides.pop(get_current_user, None)
    if "Authorization" in client.headers:
        del client.headers["Authorization"]


@pytest.fixture
def client_user_b(client, user_b, create_test_token):
    """
    TestClient authenticated as User B.

    Usage:
        def test_something(client_user_b):
            response = client_user_b.get("/api/proposals/1")
            assert response.status_code == 403  # Should be forbidden
    """
    # Create token for User B
    token = create_test_token(
        {
            "user_id": user_b.id,
            "email": user_b.email,
        }
    )

    # Set up dependency override
    def get_current_user_override():
        return user_b

    app.dependency_overrides[get_current_user] = get_current_user_override
    client.headers["Authorization"] = f"Bearer {token}"

    yield client

    app.dependency_overrides.pop(get_current_user, None)
    if "Authorization" in client.headers:
        del client.headers["Authorization"]


@pytest.fixture
def client_admin(client, admin_user, create_test_token):
    """
    TestClient authenticated as Admin user.

    Usage:
        def test_something(client_admin):
            response = client_admin.get("/api/proposals/1")
            assert response.status_code == 200  # Admin can access anything
    """
    # Create token for Admin
    token = create_test_token(
        {
            "user_id": admin_user.id,
            "email": admin_user.email,
        }
    )

    # Set up dependency override
    def get_current_user_override():
        return admin_user

    app.dependency_overrides[get_current_user] = get_current_user_override
    client.headers["Authorization"] = f"Bearer {token}"

    yield client

    app.dependency_overrides.pop(get_current_user, None)
    if "Authorization" in client.headers:
        del client.headers["Authorization"]


@pytest.fixture
def unauthenticated_client(client):
    """
    TestClient without authentication (clears any existing auth headers).

    Usage:
        def test_something(unauthenticated_client):
            response = unauthenticated_client.get("/api/proposals/1")
            assert response.status_code == 401  # Should be unauthorized
    """
    # Clear any existing auth headers
    if "Authorization" in client.headers:
        del client.headers["Authorization"]

    # Clear cookie-based auth if present
    client.cookies.clear()

    yield client
