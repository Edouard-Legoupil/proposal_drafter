# Standard Library
import uuid
import json
from sqlalchemy import text
from sqlalchemy.orm import Session

# Internal Modules
from backend.models.user import User


def test_team_membership_workflow(test_engine):
    """Test the complete team membership workflow (PENDING -> APPROVE -> REJECT)"""
    with test_engine.connect() as connection:
        # Setup: Create team and users
        team_id = str(uuid.uuid4())
        connection.execute(
            text("INSERT INTO teams (id, name) VALUES (:id, :name)"),
            {"id": team_id, "name": "Test Team"},
        )

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

        team_leader_id = str(uuid.uuid4())
        connection.execute(
            text("INSERT INTO users (id, email, password, name) VALUES (:id, :email, :password, :name)"),
            {
                "id": team_leader_id,
                "email": "leader@example.com",
                "password": "password",
                "name": "Team Leader",
            },
        )

        # Make user a team leader
        connection.execute(
            text("INSERT INTO team_members (team_id, user_id, status) VALUES (:team_id, :user_id, 'ACTIVE')"),
            {"team_id": team_id, "user_id": team_leader_id},
        )

        # Assign TEAM_LEADER directly to the active leader.
        connection.execute(text("INSERT INTO roles (id, name, role_key) VALUES (998, 'TEAM_LEADER', 'TEAM_LEADER')"))
        connection.execute(
            text("INSERT INTO user_roles (user_id, role_id) VALUES (:user_id, 998)"),
            {"user_id": team_leader_id},
        )

        # Test 1: User requests to join team (creates PENDING membership)
        connection.execute(
            text("INSERT INTO team_members (team_id, user_id, status) VALUES (:team_id, :user_id, 'PENDING')"),
            {"team_id": team_id, "user_id": user_id},
        )

        # Verify PENDING status
        membership = connection.execute(
            text("SELECT status FROM team_members WHERE team_id = :team_id AND user_id = :user_id"),
            {"team_id": team_id, "user_id": user_id},
        ).fetchone()

        assert membership is not None
        assert membership[0] == "PENDING"

        # Test 2: Team leader can see pending requests
        requests = connection.execute(
            text(
                """
            SELECT user_id FROM team_members
            WHERE team_id = :team_id AND status = 'PENDING'
            """
            ),
            {"team_id": team_id},
        ).fetchall()

        assert len(requests) == 1
        assert requests[0][0] == user_id

        # Test 3: Team leader approves request
        connection.execute(
            text("UPDATE team_members SET status = 'ACTIVE' WHERE team_id = :team_id AND user_id = :user_id"),
            {"team_id": team_id, "user_id": user_id},
        )

        # Verify ACTIVE status
        membership = connection.execute(
            text("SELECT status FROM team_members WHERE team_id = :team_id AND user_id = :user_id"),
            {"team_id": team_id, "user_id": user_id},
        ).fetchone()

        assert membership[0] == "ACTIVE"

        # Test 4: User can now be rejected (changes to REJECTED)
        connection.execute(
            text("UPDATE team_members SET status = 'REJECTED' WHERE team_id = :team_id AND user_id = :user_id"),
            {"team_id": team_id, "user_id": user_id},
        )

        # Verify REJECTED status
        membership = connection.execute(
            text("SELECT status FROM team_members WHERE team_id = :team_id AND user_id = :user_id"),
            {"team_id": team_id, "user_id": user_id},
        ).fetchone()

        assert membership[0] == "REJECTED"


def test_team_leader_role(test_engine):
    """Test TEAM_LEADER role functionality"""
    with test_engine.connect() as connection:
        # Setup: Create team and users
        team_id = str(uuid.uuid4())
        connection.execute(
            text("INSERT INTO teams (id, name) VALUES (:id, :name)"),
            {"id": team_id, "name": "Test Team"},
        )

        leader_id = str(uuid.uuid4())
        connection.execute(
            text("INSERT INTO users (id, email, password, name) VALUES (:id, :email, :password, :name)"),
            {
                "id": leader_id,
                "email": "leader@example.com",
                "password": "password",
                "name": "Team Leader",
            },
        )

        member_id = str(uuid.uuid4())
        connection.execute(
            text("INSERT INTO users (id, email, password, name) VALUES (:id, :email, :password, :name)"),
            {
                "id": member_id,
                "email": "member@example.com",
                "password": "password",
                "name": "Team Member",
            },
        )

        # Make leader a team leader
        connection.execute(
            text("INSERT INTO team_members (team_id, user_id, status) VALUES (:team_id, :user_id, 'ACTIVE')"),
            {"team_id": team_id, "user_id": leader_id},
        )

        connection.execute(text("INSERT INTO roles (id, name, role_key) VALUES (998, 'TEAM_LEADER', 'TEAM_LEADER')"))
        connection.execute(
            text("INSERT INTO user_roles (user_id, role_id) VALUES (:user_id, 998)"),
            {"user_id": leader_id},
        )

        # Make regular member
        connection.execute(
            text("INSERT INTO team_members (team_id, user_id, status) VALUES (:team_id, :user_id, 'ACTIVE')"),
            {"team_id": team_id, "user_id": member_id},
        )

        # Test is_team_leader function

        # Test with leader
        session = Session(bind=connection)
        leader = session.get(User, leader_id)
        assert leader is not None
        assert leader.is_team_leader(team_id, session) is True

        # Test with regular member
        member = session.get(User, member_id)
        assert member is not None
        assert member.is_team_leader(team_id, session) is False


def test_object_level_access_control(test_engine):
    """Test object-level access control for proposals"""
    with test_engine.connect() as connection:
        # Setup: Create team, users, and proposal
        team_id = str(uuid.uuid4())
        connection.execute(
            text("INSERT INTO teams (id, name) VALUES (:id, :name)"),
            {"id": team_id, "name": "Test Team"},
        )

        owner_id = str(uuid.uuid4())
        connection.execute(
            text("INSERT INTO users (id, email, password, name) VALUES (:id, :email, :password, :name)"),
            {
                "id": owner_id,
                "email": "owner@example.com",
                "password": "password",
                "name": "Owner",
            },
        )

        team_member_id = str(uuid.uuid4())
        connection.execute(
            text("INSERT INTO users (id, email, password, name) VALUES (:id, :email, :password, :name)"),
            {
                "id": team_member_id,
                "email": "member@example.com",
                "password": "password",
                "name": "Team Member",
            },
        )

        non_member_id = str(uuid.uuid4())
        connection.execute(
            text("INSERT INTO users (id, email, password, name) VALUES (:id, :email, :password, :name)"),
            {
                "id": non_member_id,
                "email": "nonmember@example.com",
                "password": "password",
                "name": "Non Member",
            },
        )

        # Make team member part of team
        connection.execute(
            text("INSERT INTO team_members (team_id, user_id, status) VALUES (:team_id, :user_id, 'ACTIVE')"),
            {"team_id": team_id, "user_id": team_member_id},
        )

        # Create proposal owned by owner and assigned to team
        proposal_id = str(uuid.uuid4())
        connection.execute(
            text(
                """
            INSERT INTO proposals (id, user_id, team_id, access_rules)
            VALUES (:id, :user_id, :team_id, :access_rules)
            """
            ),
            {
                "id": proposal_id,
                "user_id": owner_id,
                "team_id": team_id,
                "access_rules": json.dumps([{"team_id": team_id, "permissions": ["read", "write"]}]),
            },
        )

        def has_access(user_id, permission):
            proposal = connection.execute(
                text("SELECT user_id, team_id, access_rules FROM proposals WHERE id = :id"),
                {"id": proposal_id},
            ).one()
            if proposal.user_id == user_id:
                return True
            membership = connection.execute(
                text(
                    "SELECT 1 FROM team_members "
                    "WHERE team_id = :team_id AND user_id = :user_id AND status = 'ACTIVE'"
                ),
                {"team_id": proposal.team_id, "user_id": user_id},
            ).first()
            rules = json.loads(proposal.access_rules)
            return membership is not None and any(
                rule["team_id"] == proposal.team_id and permission in rule["permissions"] for rule in rules
            )

        assert has_access(owner_id, "read") is True
        assert has_access(team_member_id, "read") is True
        assert has_access(team_member_id, "write") is True
        assert has_access(non_member_id, "read") is False


def test_role_inheritance_with_team_leader(test_engine):
    """Test role inheritance including TEAM_LEADER role"""
    with test_engine.connect() as connection:
        # Setup: Create roles
        connection.execute(
            text(
                "INSERT INTO roles (id, name, role_key, component) VALUES "
                "(1, 'access_metrics', 'access_metrics', 'MetricsDashboard'), "
                "(998, 'TEAM_LEADER', 'TEAM_LEADER', NULL)"
            )
        )

        # Create team
        team_id = str(uuid.uuid4())
        connection.execute(
            text("INSERT INTO teams (id, name) VALUES (:id, :name)"),
            {"id": team_id, "name": "Test Team"},
        )

        # Create users
        leader_id = str(uuid.uuid4())
        connection.execute(
            text(
                "INSERT INTO users (id, email, password, name, team_id) "
                "VALUES (:id, :email, :password, :name, :team_id)"
            ),
            {
                "id": leader_id,
                "email": "leader@example.com",
                "password": "password",
                "name": "Team Leader",
                "team_id": team_id,
            },
        )

        member_id = str(uuid.uuid4())
        connection.execute(
            text(
                "INSERT INTO users (id, email, password, name, team_id) "
                "VALUES (:id, :email, :password, :name, :team_id)"
            ),
            {
                "id": member_id,
                "email": "member@example.com",
                "password": "password",
                "name": "Team Member",
                "team_id": team_id,
            },
        )

        # Add users to team
        connection.execute(
            text("INSERT INTO team_members (team_id, user_id, status) VALUES (:team_id, :user_id, 'ACTIVE')"),
            {"team_id": team_id, "user_id": leader_id},
        )

        connection.execute(
            text("INSERT INTO team_members (team_id, user_id, status) VALUES (:team_id, :user_id, 'ACTIVE')"),
            {"team_id": team_id, "user_id": member_id},
        )

        # Assign access role to the team and leader role directly to one user.
        connection.execute(
            text(
                "INSERT INTO team_roles (team_id, role_id, role_key) " "VALUES (:team_id, :role_id, 'access_metrics')"
            ),
            {"team_id": team_id, "role_id": 1},  # access_metrics
        )

        connection.execute(
            text("INSERT INTO user_roles (user_id, role_id) VALUES (:user_id, :role_id)"),
            {"user_id": leader_id, "role_id": 998},
        )

        # Test role inheritance for leader
        session = Session(bind=connection)
        leader = session.get(User, leader_id)
        assert leader is not None
        role_names = leader.get_all_roles_with_inheritance(session)
        assert "access_metrics" in role_names  # Inherited from team
        assert "TEAM_LEADER" in role_names  # Team leader role

        # Test role inheritance for regular member
        member = session.get(User, member_id)
        assert member is not None
        role_names = member.get_all_roles_with_inheritance(session)
        assert "access_metrics" in role_names  # Inherited from team
        assert "TEAM_LEADER" not in role_names  # Not a team leader


def test_team_role_assignment(test_engine):
    """Test assigning roles to teams"""
    with test_engine.connect() as connection:
        # Setup: Create roles
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
            {"id": team_id, "name": "Test Team"},
        )

        # Assign roles to team
        connection.execute(
            text(
                "INSERT INTO team_roles (team_id, role_id, role_key) " "VALUES (:team_id, :role_id, 'access_metrics')"
            ),
            {"team_id": team_id, "role_id": 1},
        )

        connection.execute(
            text(
                "INSERT INTO team_roles (team_id, role_id, role_key) " "VALUES (:team_id, :role_id, 'access_template')"
            ),
            {"team_id": team_id, "role_id": 2},
        )

        # Verify roles are assigned
        roles = connection.execute(
            text("SELECT role_id FROM team_roles WHERE team_id = :team_id ORDER BY role_id"),
            {"team_id": team_id},
        ).fetchall()

        assert len(roles) == 2
        assert roles[0][0] == 1
        assert roles[1][0] == 2

        # Test removing a role
        connection.execute(
            text("DELETE FROM team_roles WHERE team_id = :team_id AND role_id = :role_id"),
            {"team_id": team_id, "role_id": 1},
        )

        # Verify role was removed
        roles = connection.execute(
            text("SELECT role_id FROM team_roles WHERE team_id = :team_id"),
            {"team_id": team_id},
        ).fetchall()

        assert len(roles) == 1
        assert roles[0][0] == 2
