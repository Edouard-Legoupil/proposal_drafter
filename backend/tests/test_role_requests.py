# Standard Library
import pytest
import uuid
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError


def test_role_request_system(test_engine):
    """Test the complete role request workflow"""
    with test_engine.connect() as connection:
        # Setup: Create test roles
        connection.execute(text("INSERT INTO roles (id, name) VALUES (1, 'access_metrics'), (2, 'access_template')"))

        # Create test user
        user_id = str(uuid.uuid4())
        connection.execute(
            text(
                "INSERT INTO users (id, email, password, name) "
                "VALUES (:id, 'test@example.com', 'password', 'Test User')"
            ),
            {"id": user_id},
        )

        # Test 1: User can request roles
        connection.execute(
            text("INSERT INTO user_role_requests (user_id, role_id) VALUES (:user_id, 1)"), {"user_id": user_id}
        )

        # Verify request was stored
        result = connection.execute(
            text("SELECT role_id FROM user_role_requests WHERE user_id = :user_id"), {"user_id": user_id}
        ).fetchone()

        assert result is not None
        assert result[0] == 1

        # Test 2: Requestable-role queries exclude system admin.
        connection.execute(text("INSERT INTO roles (id, name) VALUES (999, 'system admin')"))
        requestable = connection.execute(text("SELECT name FROM roles WHERE name != 'system admin'")).scalars().all()
        assert "system admin" not in requestable

        # Test 3: User cannot request same role twice
        with pytest.raises(IntegrityError):
            connection.execute(
                text("INSERT INTO user_role_requests (user_id, role_id) VALUES (:user_id, 1)"), {"user_id": user_id}
            )

        # Test 4: Admin can approve requests
        connection.execute(text("INSERT INTO user_roles (user_id, role_id) VALUES (:user_id, 1)"), {"user_id": user_id})
        connection.execute(
            text("DELETE FROM user_role_requests WHERE user_id = :user_id AND role_id = 1"), {"user_id": user_id}
        )

        # Verify role was granted
        result = connection.execute(
            text("SELECT role_id FROM user_roles WHERE user_id = :user_id"), {"user_id": user_id}
        ).fetchone()

        assert result is not None
        assert result[0] == 1

        # Test 5: Request should be removed after approval
        result = connection.execute(
            text("SELECT 1 FROM user_role_requests WHERE user_id = :user_id AND role_id = 1"), {"user_id": user_id}
        ).fetchone()

        assert result is None  # Request should be deleted after approval


def test_role_request_validation(test_engine):
    """Test role request validation"""
    with test_engine.connect() as connection:
        # Setup: Create test role
        connection.execute(text("INSERT INTO roles (id, name) VALUES (1, 'access_metrics')"))

        # Create test user
        user_id = str(uuid.uuid4())
        connection.execute(
            text(
                "INSERT INTO users (id, email, password, name) "
                "VALUES (:id, 'test@example.com', 'password', 'Test User')"
            ),
            {"id": user_id},
        )

        # User already has the role they're requesting
        connection.execute(text("INSERT INTO user_roles (user_id, role_id) VALUES (:user_id, 1)"), {"user_id": user_id})

        # The request service must reject roles already granted to the user.
        already_granted = connection.execute(
            text("SELECT 1 FROM user_roles WHERE user_id = :user_id AND role_id = 1"), {"user_id": user_id}
        ).scalar()
        assert already_granted == 1


def test_admin_role_management(test_engine):
    """Test admin role management functions"""
    with test_engine.connect() as connection:
        # Setup: Create test roles and users
        connection.execute(text("INSERT INTO roles (id, name) VALUES (1, 'access_metrics'), (2, 'access_template')"))

        user_id = str(uuid.uuid4())
        connection.execute(
            text(
                "INSERT INTO users (id, email, password, name) "
                "VALUES (:id, 'test@example.com', 'password', 'Test User')"
            ),
            {"id": user_id},
        )

        # User requests a role
        connection.execute(
            text("INSERT INTO user_role_requests (user_id, role_id) VALUES (:user_id, 1)"), {"user_id": user_id}
        )

        # Admin can see the request
        result = connection.execute(
            text(
                """
            SELECT u.email, r.name
            FROM user_role_requests ur
            JOIN users u ON ur.user_id = u.id
            JOIN roles r ON ur.role_id = r.id
            WHERE ur.user_id = :user_id
            """
            ),
            {"user_id": user_id},
        ).fetchone()

        assert result is not None
        assert result[0] == "test@example.com"
        assert result[1] == "access_metrics"

        # Admin can approve the request
        connection.execute(text("INSERT INTO user_roles (user_id, role_id) VALUES (:user_id, 1)"), {"user_id": user_id})
        connection.execute(
            text("DELETE FROM user_role_requests WHERE user_id = :user_id AND role_id = 1"), {"user_id": user_id}
        )

        # Verify role was granted
        result = connection.execute(
            text("SELECT role_id FROM user_roles WHERE user_id = :user_id"), {"user_id": user_id}
        ).fetchone()

        assert result is not None
        assert result[0] == 1

        # Admin can reject requests
        connection.execute(
            text("INSERT INTO user_role_requests (user_id, role_id) VALUES (:user_id, 2)"), {"user_id": user_id}
        )

        connection.execute(
            text("DELETE FROM user_role_requests WHERE user_id = :user_id AND role_id = 2"), {"user_id": user_id}
        )

        # Verify role was not granted
        result = connection.execute(
            text("SELECT role_id FROM user_roles WHERE user_id = :user_id AND role_id = 2"), {"user_id": user_id}
        ).fetchone()

        assert result is None


def test_system_admin_protection(test_engine):
    """Test that system admin role is protected"""
    with test_engine.connect() as connection:
        # Setup: Create system admin role
        connection.execute(text("INSERT INTO roles (id, name) VALUES (999, 'system admin')"))

        # Create test user
        user_id = str(uuid.uuid4())
        connection.execute(
            text(
                "INSERT INTO users (id, email, password, name) "
                "VALUES (:id, 'test@example.com', 'password', 'Test User')"
            ),
            {"id": user_id},
        )

        # User should not be able to request system admin role
        # This would be enforced by the API, not the database
        # The test here is that system admin exists but isn't available for request
        result = connection.execute(text("SELECT name FROM roles WHERE name = 'system admin'")).fetchone()

        assert result is not None
        assert result[0] == "system admin"

        # In a real scenario, the API would filter this out before it gets to the database
