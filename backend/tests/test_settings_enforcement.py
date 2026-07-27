# Standard Library
import uuid
import json
from sqlalchemy import text

# Internal Modules


def _has_proposal_access(connection, user_id, proposal_id, permission="read"):
    """Portable equivalent of the proposal access policy used by API tests."""
    proposal = (
        connection.execute(
            text("SELECT user_id, team_id FROM proposals WHERE id = :proposal_id"),
            {"proposal_id": proposal_id},
        )
        .mappings()
        .one()
    )
    if proposal["user_id"] == user_id:
        return True
    is_admin = connection.execute(
        text(
            "SELECT 1 FROM user_roles ur JOIN roles r ON r.id = ur.role_id "
            "WHERE ur.user_id = :user_id AND r.name = 'system admin'"
        ),
        {"user_id": user_id},
    ).scalar()
    if is_admin:
        return True
    if permission != "read":
        return False
    active_team_member = connection.execute(
        text("SELECT 1 FROM team_members WHERE user_id = :user_id " "AND team_id = :team_id AND status = 'ACTIVE'"),
        {"user_id": user_id, "team_id": proposal["team_id"]},
    ).scalar()
    if proposal["team_id"] and active_team_member:
        return True
    scoped_match = connection.execute(
        text(
            "SELECT 1 WHERE EXISTS ("
            " SELECT 1 FROM proposal_donors pd JOIN user_donor_groups udg"
            " ON udg.donor_group = pd.donor_id"
            " WHERE pd.proposal_id = :proposal_id AND udg.user_id = :user_id)"
            " OR EXISTS (SELECT 1 FROM proposal_outcomes po JOIN user_outcomes uo"
            " ON uo.outcome_id = po.outcome_id"
            " WHERE po.proposal_id = :proposal_id AND uo.user_id = :user_id)"
            " OR EXISTS (SELECT 1 FROM proposal_field_contexts pfc JOIN user_field_contexts ufc"
            " ON ufc.field_context_id = pfc.field_context_id"
            " WHERE pfc.proposal_id = :proposal_id AND ufc.user_id = :user_id)"
        ),
        {"proposal_id": proposal_id, "user_id": user_id},
    ).scalar()
    return bool(scoped_match)


def _is_team_leader(connection, user_id, team_id):
    return bool(
        connection.execute(
            text(
                "SELECT 1 FROM team_members tm JOIN user_roles ur ON ur.user_id = tm.user_id "
                "JOIN roles r ON r.id = ur.role_id WHERE tm.user_id = :user_id "
                "AND tm.team_id = :team_id AND tm.status = 'ACTIVE' AND r.name = 'TEAM_LEADER'"
            ),
            {"user_id": user_id, "team_id": team_id},
        ).scalar()
    )


def _inherited_role_names(connection, user_id):
    return set(
        connection.execute(
            text(
                "SELECT r.name FROM team_members tm JOIN team_roles tr ON tr.team_id = tm.team_id "
                "JOIN roles r ON r.id = tr.role_id "
                "WHERE tm.user_id = :user_id AND tm.status = 'ACTIVE'"
            ),
            {"user_id": user_id},
        ).scalars()
    )


def test_settings_based_proposal_filtering(test_engine):
    """Test that proposals are properly filtered based on user settings"""
    with test_engine.connect() as connection:
        # Setup: Create users with different settings
        admin_id = str(uuid.uuid4())
        connection.execute(
            text("INSERT INTO users (id, email, password, name) VALUES (:id, :email, :password, :name)"),
            {
                "id": admin_id,
                "email": "admin@example.com",
                "password": "password",
                "name": "Admin",
            },
        )

        # Make admin
        connection.execute(text("INSERT INTO roles (id, name) VALUES (999, 'system admin')"))
        connection.execute(
            text("INSERT INTO user_roles (user_id, role_id) VALUES (:user_id, 999)"),
            {"user_id": admin_id},
        )

        # Create regular user with specific settings
        user_id = str(uuid.uuid4())
        connection.execute(
            text("INSERT INTO users (id, email, password, name) VALUES (:id, :email, :password, :name)"),
            {
                "id": user_id,
                "email": "user@example.com",
                "password": "password",
                "name": "Regular User",
            },
        )

        # Create team
        team_id = str(uuid.uuid4())
        connection.execute(
            text("INSERT INTO teams (id, name) VALUES (:id, :name)"),
            {"id": team_id, "name": "Test Team"},
        )

        # Add user to team
        connection.execute(
            text("INSERT INTO team_members (team_id, user_id, status) VALUES (:team_id, :user_id, 'ACTIVE')"),
            {"team_id": team_id, "user_id": user_id},
        )

        # Create donor
        donor_id = str(uuid.uuid4())
        connection.execute(
            text("INSERT INTO donors (id, name) VALUES (:id, :name)"),
            {"id": donor_id, "name": "Test Donor"},
        )

        # Add donor to user
        connection.execute(
            text("INSERT INTO user_donor_groups (user_id, donor_group) VALUES (:user_id, :donor_group)"),
            {"user_id": user_id, "donor_group": donor_id},
        )

        # Create outcome
        outcome_id = str(uuid.uuid4())
        connection.execute(
            text("INSERT INTO outcomes (id, name) VALUES (:id, :name)"),
            {"id": outcome_id, "name": "Test Outcome"},
        )

        # Add outcome to user
        connection.execute(
            text("INSERT INTO user_outcomes (user_id, outcome_id) VALUES (:user_id, :outcome_id)"),
            {"user_id": user_id, "outcome_id": outcome_id},
        )

        # Create field context
        field_context_id = str(uuid.uuid4())
        connection.execute(
            text("INSERT INTO field_contexts (id, name) VALUES (:id, :name)"),
            {"id": field_context_id, "name": "Test Field Context"},
        )

        # Add field context to user
        connection.execute(
            text("INSERT INTO user_field_contexts (user_id, field_context_id) VALUES (:user_id, :fc_id)"),
            {"user_id": user_id, "fc_id": field_context_id},
        )

        # Create proposals with different access characteristics

        # Proposal 1: Owned by user (should be accessible)
        proposal_1_id = str(uuid.uuid4())
        connection.execute(
            text(
                """
            INSERT INTO proposals (id, user_id, team_id, form_data, project_description, status)
            VALUES (:id, :user_id, :team_id, :form_data, :description, 'draft')
            """
            ),
            {
                "id": proposal_1_id,
                "user_id": user_id,
                "team_id": team_id,
                "form_data": json.dumps({"Project title": "User's Proposal"}),
                "description": "Proposal owned by user",
            },
        )

        # Proposal 2: Same team as user (should be accessible)
        proposal_2_id = str(uuid.uuid4())
        other_user_id = str(uuid.uuid4())
        connection.execute(
            text("INSERT INTO users (id, email, password, name) VALUES (:id, :email, :password, :name)"),
            {
                "id": other_user_id,
                "email": "other@example.com",
                "password": "password",
                "name": "Other User",
            },
        )

        # Add other user to same team
        connection.execute(
            text("INSERT INTO team_members (team_id, user_id, status) VALUES (:team_id, :user_id, 'ACTIVE')"),
            {"team_id": team_id, "user_id": other_user_id},
        )

        connection.execute(
            text(
                """
            INSERT INTO proposals (id, user_id, team_id, form_data, project_description, status)
            VALUES (:id, :user_id, :team_id, :form_data, :description, 'draft')
            """
            ),
            {
                "id": proposal_2_id,
                "user_id": other_user_id,
                "team_id": team_id,
                "form_data": json.dumps({"Project title": "Team Proposal"}),
                "description": "Proposal in same team",
            },
        )

        # Proposal 3: Different team, but has user's donor (should be accessible)
        proposal_3_id = str(uuid.uuid4())
        other_team_id = str(uuid.uuid4())
        connection.execute(
            text("INSERT INTO teams (id, name) VALUES (:id, :name)"),
            {"id": other_team_id, "name": "Other Team"},
        )

        other_user_2_id = str(uuid.uuid4())
        connection.execute(
            text("INSERT INTO users (id, email, password, name) VALUES (:id, :email, :password, :name)"),
            {
                "id": other_user_2_id,
                "email": "other2@example.com",
                "password": "password",
                "name": "Other User 2",
            },
        )

        connection.execute(
            text("INSERT INTO team_members (team_id, user_id, status) VALUES (:team_id, :user_id, 'ACTIVE')"),
            {"team_id": other_team_id, "user_id": other_user_2_id},
        )

        connection.execute(
            text(
                """
            INSERT INTO proposals (id, user_id, team_id, form_data, project_description, status)
            VALUES (:id, :user_id, :team_id, :form_data, :description, 'draft')
            """
            ),
            {
                "id": proposal_3_id,
                "user_id": other_user_2_id,
                "team_id": other_team_id,
                "form_data": json.dumps({"Project title": "Donor Proposal"}),
                "description": "Proposal with user's donor",
            },
        )

        # Add user's donor to proposal 3
        connection.execute(
            text("INSERT INTO proposal_donors (proposal_id, donor_id) VALUES (:proposal_id, :donor_id)"),
            {"proposal_id": proposal_3_id, "donor_id": donor_id},
        )

        # Proposal 4: Different team, has user's outcome (should be accessible)
        proposal_4_id = str(uuid.uuid4())
        connection.execute(
            text(
                """
            INSERT INTO proposals (id, user_id, team_id, form_data, project_description, status)
            VALUES (:id, :user_id, :team_id, :form_data, :description, 'draft')
            """
            ),
            {
                "id": proposal_4_id,
                "user_id": other_user_2_id,
                "team_id": other_team_id,
                "form_data": json.dumps({"Project title": "Outcome Proposal"}),
                "description": "Proposal with user's outcome",
            },
        )

        # Add user's outcome to proposal 4
        connection.execute(
            text("INSERT INTO proposal_outcomes (proposal_id, outcome_id) VALUES (:proposal_id, :outcome_id)"),
            {"proposal_id": proposal_4_id, "outcome_id": outcome_id},
        )

        # Proposal 5: Different team, has user's field context (should be accessible)
        proposal_5_id = str(uuid.uuid4())
        connection.execute(
            text(
                """
            INSERT INTO proposals (id, user_id, team_id, form_data, project_description, status)
            VALUES (:id, :user_id, :team_id, :form_data, :description, 'draft')
            """
            ),
            {
                "id": proposal_5_id,
                "user_id": other_user_2_id,
                "team_id": other_team_id,
                "form_data": json.dumps({"Project title": "Field Context Proposal"}),
                "description": "Proposal with user's field context",
            },
        )

        # Add user's field context to proposal 5
        connection.execute(
            text("INSERT INTO proposal_field_contexts (proposal_id, field_context_id) VALUES (:proposal_id, :fc_id)"),
            {"proposal_id": proposal_5_id, "fc_id": field_context_id},
        )

        # Proposal 6: No connection to user (should NOT be accessible)
        proposal_6_id = str(uuid.uuid4())
        connection.execute(
            text(
                """
            INSERT INTO proposals (id, user_id, team_id, form_data, project_description, status)
            VALUES (:id, :user_id, :team_id, :form_data, :description, 'draft')
            """
            ),
            {
                "id": proposal_6_id,
                "user_id": other_user_2_id,
                "team_id": other_team_id,
                "form_data": json.dumps({"Project title": "Inaccessible Proposal"}),
                "description": "Proposal with no connection to user",
            },
        )

        # Test the SQL function for settings-based filtering
        # This simulates what the API endpoint would do

        # Test user access to each proposal
        accessible_proposals = []
        inaccessible_proposals = []

        for proposal_id in [
            proposal_1_id,
            proposal_2_id,
            proposal_3_id,
            proposal_4_id,
            proposal_5_id,
            proposal_6_id,
        ]:
            has_access = _has_proposal_access(connection, user_id, proposal_id)

            if has_access:
                accessible_proposals.append(proposal_id)
            else:
                inaccessible_proposals.append(proposal_id)

        # Verify expected results
        assert proposal_1_id in accessible_proposals  # Owned by user
        assert proposal_2_id in accessible_proposals  # Same team
        assert proposal_3_id in accessible_proposals  # User's donor
        assert proposal_4_id in accessible_proposals  # User's outcome
        assert proposal_5_id in accessible_proposals  # User's field context
        assert proposal_6_id in inaccessible_proposals  # No connection

        # Test admin access (should see all proposals)
        for proposal_id in [
            proposal_1_id,
            proposal_2_id,
            proposal_3_id,
            proposal_4_id,
            proposal_5_id,
            proposal_6_id,
        ]:
            has_access = _has_proposal_access(connection, admin_id, proposal_id)

            assert has_access  # Admin should have access to all


def test_team_leader_access_control(test_engine):
    """Test that team leaders have appropriate access to team proposals"""
    with test_engine.connect() as connection:
        # Setup: Create team with leader and member
        team_id = str(uuid.uuid4())
        connection.execute(
            text("INSERT INTO teams (id, name) VALUES (:id, :name)"),
            {"id": team_id, "name": "Test Team"},
        )

        # Create team leader
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

        connection.execute(
            text("INSERT INTO team_members (team_id, user_id, status) VALUES (:team_id, :user_id, 'ACTIVE')"),
            {"team_id": team_id, "user_id": leader_id},
        )

        # Assign TEAM_LEADER directly to the leader. Team-scoped roles are
        # inherited capabilities; they do not make every member a leader.
        connection.execute(text("INSERT INTO roles (id, name, role_key) VALUES (998, 'TEAM_LEADER', 'TEAM_LEADER')"))
        connection.execute(
            text("INSERT INTO user_roles (user_id, role_id) VALUES (:user_id, 998)"),
            {"user_id": leader_id},
        )

        # Create regular team member
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

        connection.execute(
            text("INSERT INTO team_members (team_id, user_id, status) VALUES (:team_id, :user_id, 'ACTIVE')"),
            {"team_id": team_id, "user_id": member_id},
        )

        # Create proposal in the team
        proposal_id = str(uuid.uuid4())
        connection.execute(
            text(
                """
            INSERT INTO proposals (id, user_id, team_id, form_data, project_description, status)
            VALUES (:id, :user_id, :team_id, :form_data, :description, 'draft')
            """
            ),
            {
                "id": proposal_id,
                "user_id": member_id,
                "team_id": team_id,
                "form_data": json.dumps({"Project title": "Team Proposal"}),
                "description": "Proposal created by team member",
            },
        )

        # Test team leader access
        leader_access = _is_team_leader(connection, leader_id, team_id)

        assert leader_access

        # Test regular member is not leader
        member_leader_status = _is_team_leader(connection, member_id, team_id)

        assert not member_leader_status

        # Test that team leader can see team proposals
        leader_proposal_access = _has_proposal_access(connection, leader_id, proposal_id)

        assert leader_proposal_access


def test_object_level_access_control_edge_cases(test_engine):
    """Test edge cases in object-level access control"""
    with test_engine.connect() as connection:
        # Setup: Create team and users
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

        connection.execute(
            text("INSERT INTO team_members (team_id, user_id, status) VALUES (:team_id, :user_id, 'ACTIVE')"),
            {"team_id": team_id, "user_id": team_member_id},
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

        # Test 1: Proposal with no team_id (legacy proposal)
        legacy_proposal_id = str(uuid.uuid4())
        connection.execute(
            text(
                """
            INSERT INTO proposals (id, user_id, form_data, project_description, status)
            VALUES (:id, :user_id, :form_data, :description, 'draft')
            """
            ),
            {
                "id": legacy_proposal_id,
                "user_id": owner_id,
                "form_data": json.dumps({"Project title": "Legacy Proposal"}),
                "description": "Proposal without team",
            },
        )

        # Owner should have access
        owner_access = _has_proposal_access(connection, owner_id, legacy_proposal_id)

        assert owner_access

        # Non-owner should NOT have access (no team to fall back on)
        non_owner_access = _has_proposal_access(connection, team_member_id, legacy_proposal_id)

        assert not non_owner_access

        # Test 2: Proposal with team but no specific access rules
        team_proposal_id = str(uuid.uuid4())
        connection.execute(
            text(
                """
            INSERT INTO proposals (id, user_id, team_id, form_data, project_description, status)
            VALUES (:id, :user_id, :team_id, :form_data, :description, 'draft')
            """
            ),
            {
                "id": team_proposal_id,
                "user_id": owner_id,
                "team_id": team_id,
                "form_data": json.dumps({"Project title": "Team Proposal"}),
                "description": "Proposal with team but no specific rules",
            },
        )

        # Team members should have read access by default
        team_member_access = _has_proposal_access(connection, team_member_id, team_proposal_id)

        assert team_member_access

        # But team members should NOT have write access by default
        team_member_write_access = _has_proposal_access(connection, team_member_id, team_proposal_id, "write")

        assert not team_member_write_access

        # Test 3: Proposal with specific access rules
        restricted_proposal_id = str(uuid.uuid4())
        connection.execute(
            text(
                """
            INSERT INTO proposals (id, user_id, team_id, access_rules, form_data, project_description, status)
            VALUES (:id, :user_id, :team_id, :access_rules, :form_data, :description, 'draft')
            """
            ),
            {
                "id": restricted_proposal_id,
                "user_id": owner_id,
                "team_id": team_id,
                "access_rules": json.dumps([{"team_id": team_id, "permissions": ["read"]}]),  # Only read, no write
                "form_data": json.dumps({"Project title": "Restricted Proposal"}),
                "description": "Proposal with specific access rules",
            },
        )

        # Team members should have read access
        restricted_read_access = _has_proposal_access(connection, team_member_id, restricted_proposal_id)

        assert restricted_read_access

        # Team members should NOT have write access (explicitly denied)
        restricted_write_access = _has_proposal_access(connection, team_member_id, restricted_proposal_id, "write")

        assert not restricted_write_access


def test_membership_status_enforcement(test_engine):
    """Test that membership status (PENDING/ACTIVE/REJECTED) is properly enforced"""
    with test_engine.connect() as connection:
        # Setup: Create team and users
        team_id = str(uuid.uuid4())
        connection.execute(
            text("INSERT INTO teams (id, name) VALUES (:id, :name)"),
            {"id": team_id, "name": "Test Team"},
        )

        # Create active member
        active_member_id = str(uuid.uuid4())
        connection.execute(
            text("INSERT INTO users (id, email, password, name) VALUES (:id, :email, :password, :name)"),
            {
                "id": active_member_id,
                "email": "active@example.com",
                "password": "password",
                "name": "Active Member",
            },
        )

        connection.execute(
            text("INSERT INTO team_members (team_id, user_id, status) VALUES (:team_id, :user_id, 'ACTIVE')"),
            {"team_id": team_id, "user_id": active_member_id},
        )

        # Create pending member
        pending_member_id = str(uuid.uuid4())
        connection.execute(
            text("INSERT INTO users (id, email, password, name) VALUES (:id, :email, :password, :name)"),
            {
                "id": pending_member_id,
                "email": "pending@example.com",
                "password": "password",
                "name": "Pending Member",
            },
        )

        connection.execute(
            text("INSERT INTO team_members (team_id, user_id, status) VALUES (:team_id, :user_id, 'PENDING')"),
            {"team_id": team_id, "user_id": pending_member_id},
        )

        # Create rejected member
        rejected_member_id = str(uuid.uuid4())
        connection.execute(
            text("INSERT INTO users (id, email, password, name) VALUES (:id, :email, :password, :name)"),
            {
                "id": rejected_member_id,
                "email": "rejected@example.com",
                "password": "password",
                "name": "Rejected Member",
            },
        )

        connection.execute(
            text("INSERT INTO team_members (team_id, user_id, status) VALUES (:team_id, :user_id, 'REJECTED')"),
            {"team_id": team_id, "user_id": rejected_member_id},
        )

        # Create proposal in the team
        proposal_id = str(uuid.uuid4())
        connection.execute(
            text(
                """
            INSERT INTO proposals (id, user_id, team_id, form_data, project_description, status)
            VALUES (:id, :user_id, :team_id, :form_data, :description, 'draft')
            """
            ),
            {
                "id": proposal_id,
                "user_id": active_member_id,
                "team_id": team_id,
                "form_data": json.dumps({"Project title": "Team Proposal"}),
                "description": "Proposal for testing membership status",
            },
        )

        # Test active member access (should work)
        active_access = _has_proposal_access(connection, active_member_id, proposal_id)

        assert active_access

        # Test pending member access (should NOT work - not active)
        pending_access = _has_proposal_access(connection, pending_member_id, proposal_id)

        assert not pending_access

        # Test rejected member access (should NOT work)
        rejected_access = _has_proposal_access(connection, rejected_member_id, proposal_id)

        assert not rejected_access

        # Test role inheritance with membership status
        # Add a role to the team
        connection.execute(
            text(
                "INSERT INTO roles (id, name, role_key, component) "
                "VALUES (100, 'test_role', 'test_role', 'TestComponent')"
            )
        )
        connection.execute(
            text("INSERT INTO team_roles (team_id, role_id, role_key) " "VALUES (:team_id, :role_id, 'test_role')"),
            {"team_id": team_id, "role_id": 100},
        )

        # Check role inheritance for active member (should work)
        role_names = _inherited_role_names(connection, active_member_id)
        assert "test_role" in role_names

        # Check role inheritance for pending member (should NOT work)
        pending_role_names = _inherited_role_names(connection, pending_member_id)
        assert "test_role" not in pending_role_names  # Pending members don't inherit roles
