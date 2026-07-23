# Standard Library
import uuid
import json
from sqlalchemy import text

# Internal Modules


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
            has_access = connection.execute(
                text(
                    """
                SELECT check_object_access(:user_id, 'proposal', :proposal_id, 'read')
                """
                ),
                {"user_id": user_id, "proposal_id": proposal_id},
            ).scalar()

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
            has_access = connection.execute(
                text(
                    """
                SELECT check_object_access(:user_id, 'proposal', :proposal_id, 'read')
                """
                ),
                {"user_id": admin_id, "proposal_id": proposal_id},
            ).scalar()

            assert has_access == True  # Admin should have access to all


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

        # Assign TEAM_LEADER role
        connection.execute(
            text("INSERT INTO team_roles (team_id, role_id) VALUES (:team_id, :role_id)"),
            {"team_id": team_id, "role_id": 998},
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
        leader_access = connection.execute(
            text(
                """
            SELECT is_team_leader(:user_id, :team_id)
            """
            ),
            {"user_id": leader_id, "team_id": team_id},
        ).scalar()

        assert leader_access == True

        # Test regular member is not leader
        member_leader_status = connection.execute(
            text(
                """
            SELECT is_team_leader(:user_id, :team_id)
            """
            ),
            {"user_id": member_id, "team_id": team_id},
        ).scalar()

        assert member_leader_status == False

        # Test that team leader can see team proposals
        leader_proposal_access = connection.execute(
            text(
                """
            SELECT check_object_access(:user_id, 'proposal', :proposal_id, 'read')
            """
            ),
            {"user_id": leader_id, "proposal_id": proposal_id},
        ).scalar()

        assert leader_proposal_access == True


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
        owner_access = connection.execute(
            text(
                """
            SELECT check_object_access(:user_id, 'proposal', :proposal_id, 'read')
            """
            ),
            {"user_id": owner_id, "proposal_id": legacy_proposal_id},
        ).scalar()

        assert owner_access == True

        # Non-owner should NOT have access (no team to fall back on)
        non_owner_access = connection.execute(
            text(
                """
            SELECT check_object_access(:user_id, 'proposal', :proposal_id, 'read')
            """
            ),
            {"user_id": team_member_id, "proposal_id": legacy_proposal_id},
        ).scalar()

        assert non_owner_access == False

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
        team_member_access = connection.execute(
            text(
                """
            SELECT check_object_access(:user_id, 'proposal', :proposal_id, 'read')
            """
            ),
            {"user_id": team_member_id, "proposal_id": team_proposal_id},
        ).scalar()

        assert team_member_access == True

        # But team members should NOT have write access by default
        team_member_write_access = connection.execute(
            text(
                """
            SELECT check_object_access(:user_id, 'proposal', :proposal_id, 'write')
            """
            ),
            {"user_id": team_member_id, "proposal_id": team_proposal_id},
        ).scalar()

        assert team_member_write_access == False

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
        restricted_read_access = connection.execute(
            text(
                """
            SELECT check_object_access(:user_id, 'proposal', :proposal_id, 'read')
            """
            ),
            {"user_id": team_member_id, "proposal_id": restricted_proposal_id},
        ).scalar()

        assert restricted_read_access == True

        # Team members should NOT have write access (explicitly denied)
        restricted_write_access = connection.execute(
            text(
                """
            SELECT check_object_access(:user_id, 'proposal', :proposal_id, 'write')
            """
            ),
            {"user_id": team_member_id, "proposal_id": restricted_proposal_id},
        ).scalar()

        assert restricted_write_access == False


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
        active_access = connection.execute(
            text(
                """
            SELECT check_object_access(:user_id, 'proposal', :proposal_id, 'read')
            """
            ),
            {"user_id": active_member_id, "proposal_id": proposal_id},
        ).scalar()

        assert active_access == True

        # Test pending member access (should NOT work - not active)
        pending_access = connection.execute(
            text(
                """
            SELECT check_object_access(:user_id, 'proposal', :proposal_id, 'read')
            """
            ),
            {"user_id": pending_member_id, "proposal_id": proposal_id},
        ).scalar()

        assert pending_access == False

        # Test rejected member access (should NOT work)
        rejected_access = connection.execute(
            text(
                """
            SELECT check_object_access(:user_id, 'proposal', :proposal_id, 'read')
            """
            ),
            {"user_id": rejected_member_id, "proposal_id": proposal_id},
        ).scalar()

        assert rejected_access == False

        # Test role inheritance with membership status
        # Add a role to the team
        connection.execute(text("INSERT INTO roles (id, name) VALUES (100, 'test_role')"))
        connection.execute(
            text("INSERT INTO team_roles (team_id, role_id) VALUES (:team_id, :role_id)"),
            {"team_id": team_id, "role_id": 100},
        )

        # Check role inheritance for active member (should work)
        active_roles = connection.execute(
            text("SELECT * FROM get_user_roles_with_inheritance(:user_id)"),
            {"user_id": active_member_id},
        ).fetchall()

        role_names = [role[1] for role in active_roles]
        assert "test_role" in role_names

        # Check role inheritance for pending member (should NOT work)
        pending_roles = connection.execute(
            text("SELECT * FROM get_user_roles_with_inheritance(:user_id)"),
            {"user_id": pending_member_id},
        ).fetchall()

        pending_role_names = [role[1] for role in pending_roles]
        assert "test_role" not in pending_role_names  # Pending members don't inherit roles
