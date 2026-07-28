import os
import pytest
import uuid
import jwt
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool
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
os.environ.setdefault("AUDIT_LOG_FILE", "/tmp/proposal-drafter-test-audit.log")

# --- Application and Dependency Imports ---
from backend.main import app  # noqa: E402
from backend.core import db as db_module  # noqa: E402
from backend.core.db import get_engine  # noqa: E402
from backend.core.security import get_current_user  # noqa: E402


def _create_test_engine():
    """Build an isolated SQLite database with the API's supported test schema."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.connect() as connection:
        connection.execute(text("PRAGMA foreign_keys=ON"))
        connection.commit()
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
                CREATE TABLE IF NOT EXISTS roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    role_key TEXT UNIQUE,
                    component TEXT,
                    UNIQUE (id, role_key)
                )
            """
                )
            )
            connection.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS teams (
                    id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    created_by TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
                )
            )
            connection.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS team_members (
                    team_id TEXT, user_id TEXT,
                    status TEXT NOT NULL DEFAULT 'ACTIVE',
                    joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (team_id, user_id),
                    CHECK (status IN ('PENDING', 'ACTIVE', 'REJECTED')),
                    FOREIGN KEY (team_id) REFERENCES teams(id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """
                )
            )
            connection.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS team_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    team_id TEXT NOT NULL,
                    setting_type TEXT NOT NULL,
                    setting_value TEXT NOT NULL,
                    UNIQUE (team_id, setting_type, setting_value),
                    FOREIGN KEY (team_id) REFERENCES teams(id)
                )
            """
                )
            )
            connection.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS team_roles (
                    team_id TEXT NOT NULL,
                    role_id INTEGER NOT NULL,
                    role_key TEXT NOT NULL,
                    PRIMARY KEY (team_id, role_id),
                    UNIQUE (team_id, role_key),
                    CHECK (role_key NOT IN ('system admin', 'TEAM_LEADER')),
                    FOREIGN KEY (team_id) REFERENCES teams(id),
                    FOREIGN KEY (role_id, role_key) REFERENCES roles(id, role_key)
                )
            """
                )
            )
            connection.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS team_member_roles (
                    team_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    role_key TEXT NOT NULL CHECK (role_key = 'TEAM_LEADER'),
                    assigned_by TEXT NOT NULL,
                    assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (team_id, user_id, role_key),
                    FOREIGN KEY (team_id, user_id) REFERENCES team_members(team_id, user_id) ON DELETE CASCADE,
                    FOREIGN KEY (role_key) REFERENCES roles(role_key),
                    FOREIGN KEY (assigned_by) REFERENCES users(id)
                )
            """
                )
            )
            connection.execute(
                text(
                    """
                CREATE TRIGGER IF NOT EXISTS enforce_active_team_leader_membership_insert
                BEFORE INSERT ON team_member_roles
                WHEN NOT EXISTS (
                    SELECT 1 FROM team_members tm
                    WHERE tm.team_id = NEW.team_id
                      AND tm.user_id = NEW.user_id
                      AND tm.status = 'ACTIVE'
                )
                BEGIN
                    SELECT RAISE(ABORT, 'TEAM_LEADER requires an active membership');
                END
            """
                )
            )
            connection.execute(
                text(
                    """
                CREATE TRIGGER IF NOT EXISTS enforce_active_team_leader_membership_update
                BEFORE UPDATE ON team_member_roles
                WHEN NOT EXISTS (
                    SELECT 1 FROM team_members tm
                    WHERE tm.team_id = NEW.team_id
                      AND tm.user_id = NEW.user_id
                      AND tm.status = 'ACTIVE'
                )
                BEGIN
                    SELECT RAISE(ABORT, 'TEAM_LEADER requires an active membership');
                END
            """
                )
            )
            connection.execute(
                text(
                    """
                CREATE TRIGGER IF NOT EXISTS remove_inactive_team_leader_assignment
                AFTER UPDATE OF status ON team_members
                WHEN NEW.status <> 'ACTIVE'
                BEGIN
                    DELETE FROM team_member_roles
                    WHERE team_id = NEW.team_id AND user_id = NEW.user_id;
                END
            """
                )
            )
            connection.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS access_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    team_id TEXT NOT NULL,
                    role_key TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL CHECK (json_valid(value)),
                    created_by TEXT NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (user_id, team_id, role_key, key),
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (team_id) REFERENCES teams(id),
                    FOREIGN KEY (role_key) REFERENCES roles(role_key),
                    FOREIGN KEY (created_by) REFERENCES users(id)
                )
            """
                )
            )
            connection.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS user_settings_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    setting_type TEXT NOT NULL,
                    setting_value TEXT NOT NULL,
                    requested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    approved_by TEXT,
                    approved_at DATETIME,
                    rejection_reason TEXT,
                    UNIQUE (user_id, setting_type, setting_value),
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (approved_by) REFERENCES users(id)
                )
            """
                )
            )
            connection.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS user_donors (
                    user_id TEXT NOT NULL,
                    donor_id TEXT NOT NULL,
                    PRIMARY KEY (user_id, donor_id),
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (donor_id) REFERENCES donors(id)
                )
            """
                )
            )
            connection.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS user_outcomes (
                    user_id TEXT NOT NULL,
                    outcome_id TEXT NOT NULL,
                    PRIMARY KEY (user_id, outcome_id),
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (outcome_id) REFERENCES outcomes(id)
                )
            """
                )
            )
            connection.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS user_field_contexts (
                    user_id TEXT NOT NULL,
                    field_context_id TEXT NOT NULL,
                    PRIMARY KEY (user_id, field_context_id),
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (field_context_id) REFERENCES field_contexts(id)
                )
            """
                )
            )
            connection.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS user_donor_groups (
                    user_id TEXT NOT NULL,
                    donor_group TEXT NOT NULL,
                    PRIMARY KEY (user_id, donor_group),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """
                )
            )
            connection.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS user_roles (
                    user_id TEXT, role_id INTEGER,
                    PRIMARY KEY (user_id, role_id),
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (role_id) REFERENCES roles(id)
                )
            """
                )
            )
            connection.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS user_role_requests (
                    user_id TEXT NOT NULL,
                    role_id INTEGER NOT NULL,
                    PRIMARY KEY (user_id, role_id),
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (role_id) REFERENCES roles(id)
                )
            """
                )
            )
            connection.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL,
                    name TEXT, team_id TEXT, security_questions TEXT, session_active BOOLEAN,
                    is_admin BOOLEAN DEFAULT FALSE,
                    geographic_coverage_type TEXT,
                    geographic_coverage_region TEXT,
                    geographic_coverage_country TEXT,
                    requested_role_id INTEGER,
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
                    status TEXT, contribution_id TEXT, team_id TEXT, access_rules TEXT,
                    reviews TEXT, created_by TEXT, updated_by TEXT,
                    template_registry_id TEXT, template_version_id TEXT,
                    created_at DATETIME, updated_at DATETIME,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """
                )
            )
            connection.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS resource_access_grants (
                    id TEXT PRIMARY KEY,
                    resource_type TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    subject_type TEXT NOT NULL,
                    subject_id TEXT NOT NULL,
                    permissions TEXT NOT NULL,
                    data_scope TEXT NOT NULL DEFAULT 'self',
                    created_by TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (resource_type, resource_id, subject_type, subject_id)
                )
            """
                )
            )
            connection.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS resource_access_settings (
                    resource_type TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    visibility TEXT NOT NULL DEFAULT 'private',
                    updated_by TEXT NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (resource_type, resource_id)
                )
            """
                )
            )
            connection.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS resource_access_audit (
                    id TEXT PRIMARY KEY,
                    resource_type TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    actor_id TEXT NOT NULL,
                    details TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
                )
            )
            connection.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS artifact_runs (
                    id TEXT PRIMARY KEY,
                    artifact_type TEXT NOT NULL,
                    artifact_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    run_status TEXT NOT NULL DEFAULT 'drafting',
                    start_time DATETIME,
                    end_time DATETIME,
                    agents_executed TEXT DEFAULT '[]',
                    model_deployment TEXT,
                    tokens_input INTEGER DEFAULT 0,
                    tokens_output INTEGER DEFAULT 0,
                    estimated_cost REAL DEFAULT 0,
                    step_count INTEGER DEFAULT 0,
                    retry_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    total_latency_ms INTEGER,
                    stage_latencies TEXT DEFAULT '{}',
                    sections_generated INTEGER DEFAULT 0,
                    pages_generated INTEGER DEFAULT 0,
                    words_generated INTEGER DEFAULT 0,
                    export_events TEXT DEFAULT '[]',
                    template_name TEXT,
                    template_version TEXT,
                    metadata TEXT DEFAULT '{}',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
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
            for join_table, value_column in (
                ("proposal_donors", "donor_id"),
                ("proposal_outcomes", "outcome_id"),
                ("proposal_field_contexts", "field_context_id"),
            ):
                connection.execute(
                    text(
                        f"CREATE TABLE IF NOT EXISTS {join_table} ("
                        f"proposal_id TEXT NOT NULL, {value_column} TEXT NOT NULL, "
                        f"PRIMARY KEY (proposal_id, {value_column}))"
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
                    team_id TEXT,
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
                CREATE TABLE IF NOT EXISTS templates (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    filename TEXT NOT NULL UNIQUE,
                    template_type TEXT NOT NULL,
                    description TEXT,
                    status TEXT DEFAULT 'draft',
                    is_default BOOLEAN DEFAULT FALSE,
                    team_id TEXT,
                    created_by TEXT,
                    updated_by TEXT,
                    created_at DATETIME,
                    updated_at DATETIME
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
                    knowledge_card_id TEXT,
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
                    donor_ids TEXT,
                    template_type TEXT DEFAULT 'proposal',
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


@pytest.fixture
def test_engine_factory():
    """Return a factory so isolation itself can be regression tested."""
    return _create_test_engine


@pytest.fixture(scope="function")
def test_engine(test_engine_factory):
    """Create and dispose an isolated SQLite engine for each test."""
    engine = test_engine_factory()
    yield engine
    engine.dispose()


@pytest.fixture(scope="function", autouse=True)
def override_get_engine(test_engine):
    """Fixture to override the get_engine dependency for all tests."""
    previous_engine = db_module.engine
    db_module.engine = test_engine
    app.dependency_overrides[get_engine] = lambda: test_engine
    yield
    app.dependency_overrides.pop(get_engine, None)
    db_module.engine = previous_engine


@pytest.fixture(scope="function")
def db_session(test_engine):
    """Provides a transactional scope for each test function."""
    connection = test_engine.connect()
    transaction = connection.begin()
    yield connection
    if transaction.is_active:
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
                "access_template",
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
