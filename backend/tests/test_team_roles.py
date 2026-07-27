# Standard Library
import uuid
from sqlalchemy import text
from sqlalchemy.orm import Session

# Internal Modules
from backend.models.user import User


def test_team_role_creation_and_assignment(test_engine):
    """Test creating team roles and assigning them to teams."""
    with test_engine.connect() as connection:
        # Create a test role

        connection.execute(
            text("INSERT INTO roles (id, name, role_key, component) VALUES (:id, :name, :name, 'TestComponent')"),
            {"id": 1, "name": "test_role"},
        )

        # Create a test team
        team_id = str(uuid.uuid4())
        connection.execute(
            text("INSERT INTO teams (id, name) VALUES (:id, :name)"),
            {"id": team_id, "name": "Test Team"},
        )

        # Assign role to team
        connection.execute(
            text("INSERT INTO team_roles (team_id, role_id, role_key) " "VALUES (:team_id, :role_id, :role_key)"),
            {"team_id": team_id, "role_id": 1, "role_key": "test_role"},
        )

        # Verify the assignment
        result = connection.execute(
            text("SELECT * FROM team_roles WHERE team_id = :team_id AND role_id = :role_id"),
            {"team_id": team_id, "role_id": 1},
        )
        team_role = result.fetchone()
        assert team_role is not None
        assert team_role[0] == team_id
        assert team_role[1] == 1


def test_role_inheritance_for_team_members(test_engine):
    """Test that team members inherit roles from their teams."""
    with test_engine.connect() as connection:
        # Create roles
        connection.execute(
            text(
                "INSERT INTO roles (id, name, role_key, component) VALUES "
                "(1, 'direct_role', 'direct_role', 'DirectComponent'), "
                "(2, 'team_role', 'team_role', 'TeamComponent')"
            )
        )

        # Create team
        team_id = str(uuid.uuid4())
        connection.execute(
            text("INSERT INTO teams (id, name) VALUES (:id, :name)"),
            {"id": team_id, "name": "Test Team"},
        )

        # Create user
        user_id = str(uuid.uuid4())
        connection.execute(
            text("INSERT INTO users (id, email, password, name) VALUES (:id, :email, :password, :name)"),
            {
                "id": user_id,
                "email": "test@example.com",
                "password": "password",
                "name": "Test User",
            },
        )

        # Add user to team
        connection.execute(
            text("INSERT INTO team_members (team_id, user_id) VALUES (:team_id, :user_id)"),
            {"team_id": team_id, "user_id": user_id},
        )

        # Assign role to team
        connection.execute(
            text("INSERT INTO team_roles (team_id, role_id, role_key) " "VALUES (:team_id, :role_id, 'team_role')"),
            {"team_id": team_id, "role_id": 2},
        )

        # Assign direct role to user
        connection.execute(
            text("INSERT INTO user_roles (user_id, role_id) VALUES (:user_id, :role_id)"),
            {"user_id": user_id, "role_id": 1},
        )

        session = Session(bind=connection)
        user = session.get(User, user_id)
        assert user is not None
        user.team_id = team_id
        role_names = user.get_all_roles_with_inheritance(session)
        assert "direct_role" in role_names
        assert "team_role" in role_names
        assert len(role_names) == 2


def test_user_model_role_inheritance(test_engine):
    """Test the User model's role inheritance functionality."""
    with test_engine.connect() as connection:
        # Create roles
        connection.execute(
            text(
                "INSERT INTO roles (id, name, role_key, component) VALUES "
                "(1, 'direct_role', 'direct_role', 'DirectComponent'), "
                "(2, 'team_role', 'team_role', 'TeamComponent')"
            )
        )

        # Create team
        team_id = str(uuid.uuid4())
        connection.execute(
            text("INSERT INTO teams (id, name) VALUES (:id, :name)"),
            {"id": team_id, "name": "Test Team"},
        )

        # Create user with team
        user_id = str(uuid.uuid4())
        connection.execute(
            text(
                (
                    "INSERT INTO users (id, email, password, name, team_id) "
                    "VALUES (:id, :email, :password, :name, :team_id)"
                )
            ),
            {
                "id": user_id,
                "email": "test@example.com",
                "password": "password",
                "name": "Test User",
                "team_id": team_id,
            },
        )

        # Add user to team
        connection.execute(
            text("INSERT INTO team_members (team_id, user_id) VALUES (:team_id, :user_id)"),
            {"team_id": team_id, "user_id": user_id},
        )

        # Assign role to team
        connection.execute(
            text("INSERT INTO team_roles (team_id, role_id, role_key) " "VALUES (:team_id, :role_id, 'team_role')"),
            {"team_id": team_id, "role_id": 2},
        )

        # Assign direct role to user
        connection.execute(
            text("INSERT INTO user_roles (user_id, role_id) VALUES (:user_id, :role_id)"),
            {"user_id": user_id, "role_id": 1},
        )

        session = Session(bind=connection)
        user = session.get(User, user_id)
        assert user is not None
        all_roles = user.get_all_roles_with_inheritance(session)
        assert "direct_role" in all_roles
        assert "team_role" in all_roles
        assert len(all_roles) == 2


def test_user_model_does_not_inherit_roles_from_pending_membership(test_engine):
    with test_engine.connect() as connection:
        connection.execute(
            text(
                "INSERT INTO roles (id, name, role_key, component) "
                "VALUES (1, 'team_role', 'team_role', 'TeamComponent')"
            )
        )
        connection.execute(text("INSERT INTO teams (id, name) VALUES ('team-1', 'Test Team')"))
        connection.execute(
            text(
                "INSERT INTO users (id, email, password, team_id) "
                "VALUES ('user-1', 'test@example.org', 'secret', 'team-1')"
            )
        )
        connection.execute(
            text("INSERT INTO team_members (team_id, user_id, status) " "VALUES ('team-1', 'user-1', 'PENDING')")
        )
        connection.execute(
            text("INSERT INTO team_roles (team_id, role_id, role_key) " "VALUES ('team-1', 1, 'team_role')")
        )

        user = Session(bind=connection).get(User, "user-1")

        assert user is not None
        assert "team_role" not in user.get_all_roles_with_inheritance(Session(bind=connection))


def test_new_access_roles(test_engine):
    """Test the new access control roles."""
    with test_engine.connect() as connection:
        # Create the new roles
        access_roles = [
            (1, "access_metrics"),
            (2, "access_template"),
            (3, "access_incident"),
            (4, "access_quality_gate"),
        ]

        for role_id, role_name in access_roles:
            connection.execute(
                text("INSERT INTO roles (id, name) VALUES (:id, :name)"),
                {"id": role_id, "name": role_name},
            )

        # Verify roles were created
        result = connection.execute(text("SELECT name FROM roles WHERE name LIKE 'access_%'"))
        roles = result.fetchall()

        role_names = [role[0] for role in roles]
        assert "access_metrics" in role_names
        assert "access_template" in role_names
        assert "access_incident" in role_names
        assert "access_quality_gate" in role_names
        assert len(roles) == 4


def test_permission_checking_with_inherited_roles(test_engine):
    """Test permission checking with inherited roles."""
    with test_engine.connect() as connection:
        # Create roles
        connection.execute(
            text(
                "INSERT INTO roles (id, name, role_key, component) VALUES "
                "(1, 'access_metrics', 'access_metrics', 'MetricsDashboard'), "
                "(2, 'access_template', 'access_template', 'TemplateLibrary')"
            )
        )

        # Create team
        team_id = str(uuid.uuid4())
        connection.execute(
            text("INSERT INTO teams (id, name) VALUES (:id, :name)"),
            {"id": team_id, "name": "Metrics Team"},
        )

        # Create user
        user_id = str(uuid.uuid4())
        connection.execute(
            text(
                (
                    "INSERT INTO users (id, email, password, name, team_id) "
                    "VALUES (:id, :email, :password, :name, :team_id)"
                )
            ),
            {
                "id": user_id,
                "email": "test@example.com",
                "password": "password",
                "name": "Test User",
                "team_id": team_id,
            },
        )

        # Add user to team
        connection.execute(
            text("INSERT INTO team_members (team_id, user_id) VALUES (:team_id, :user_id)"),
            {"team_id": team_id, "user_id": user_id},
        )

        # Assign role to team
        connection.execute(
            text(
                "INSERT INTO team_roles (team_id, role_id, role_key) " "VALUES (:team_id, :role_id, 'access_metrics')"
            ),
            {"team_id": team_id, "role_id": 1},  # access_metrics
        )

        session = Session(bind=connection)
        user = session.get(User, user_id)
        assert user is not None
        assert user.has_permission("access_metrics", session)
        assert not user.has_permission("access_template", session)
        assert not user.has_permission("access_incident", session)


def test_admin_bypass(test_engine):
    """Test that admin users bypass all permission checks."""
    with test_engine.connect() as connection:
        # Create admin role
        connection.execute(text("INSERT INTO roles (id, name) VALUES (1, 'system admin')"))

        # Create user with admin role
        user_id = str(uuid.uuid4())
        connection.execute(
            text("INSERT INTO users (id, email, password, name) VALUES (:id, :email, :password, :name)"),
            {
                "id": user_id,
                "email": "admin@example.com",
                "password": "password",
                "name": "Admin User",
            },
        )
        connection.execute(
            text("INSERT INTO user_roles (user_id, role_id) VALUES (:user_id, :role_id)"),
            {"user_id": user_id, "role_id": 1},
        )

        session = Session(bind=connection)
        user = session.get(User, user_id)
        assert user is not None

        # Test that admin has all permissions
        assert user.is_admin
        assert user.has_permission("access_metrics")
        assert user.has_permission("access_template")
        assert user.has_permission("nonexistent_permission")
