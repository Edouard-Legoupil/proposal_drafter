#  Standard Library
import logging
from typing import List

#  Third-Party Libraries
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

#  Internal Modules
from backend.core.db import get_engine
from backend.core.security import get_current_user
from backend.models.schemas import SelfServiceUserSettings, UserSettings, Role, User

# This router handles all endpoints related to users.
router = APIRouter()

# Configure logging
logger = logging.getLogger(__name__)


@router.get("/teams")
async def get_teams(current_user: dict = Depends(get_current_user)):
    """
    Returns a list of all teams in the system.
    """
    try:
        from sqlalchemy.orm import Session
        from backend.models.team import Team

        with get_engine().connect() as connection:
            # Create a session for ORM operations
            session = Session(connection)
            teams = session.query(Team).order_by(Team.name).all()
            teams_list = [{"id": str(team.id), "name": team.name} for team in teams]
            return {"teams": teams_list}
    except Exception as e:
        logger.error(f"[GET TEAMS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not retrieve teams.") from e


@router.get("/users", response_model=List[User])
async def get_users(role: str | None = None, current_user: dict = Depends(get_current_user)):
    """
    Returns a list of users in the system.
    If 'role' is provided, filters by that role.
    Otherwise, returns reviewers (for peer review selection).
    """
    try:
        with get_engine().connect() as connection:
            # We need to fetch donor_ids, outcomes, and field_contexts for preselection logic
            # Using subqueries or CTEs for aggregation
            base_query = """
                SELECT
                    u.id, u.name, u.email, t.name as team_name,
                    COALESCE(ARRAY_AGG(DISTINCT ud.donor_id)
                        FILTER (WHERE ud.donor_id IS NOT NULL), '{{}}') as donor_ids,
                    COALESCE(ARRAY_AGG(DISTINCT uo.outcome_id)
                        FILTER (WHERE uo.outcome_id IS NOT NULL), '{{}}') as outcomes,
                    COALESCE(ARRAY_AGG(DISTINCT uf.field_context_id)
                        FILTER (WHERE uf.field_context_id IS NOT NULL), '{{}}') as field_contexts
                FROM users u
                LEFT JOIN teams t ON u.team_id = t.id
                JOIN user_roles ur ON u.id = ur.user_id
                JOIN roles r ON ur.role_id = r.id
                LEFT JOIN user_donors ud ON u.id = ud.user_id
                LEFT JOIN user_outcomes uo ON u.id = uo.user_id
                LEFT JOIN user_field_contexts uf ON u.id = uf.user_id
                WHERE {where_clause}
                GROUP BY u.id, u.name, u.email, t.name
                ORDER BY t.name, u.name
            """

            if role:
                role_names = [role.lower()]
                if "drafter" in role.lower():
                    role_names.append(role.lower().replace("drafter", "writer"))
                elif "writer" in role.lower():
                    role_names.append(role.lower().replace("writer", "drafter"))

                logger.info(f"[GET USERS] Filtering by roles: {role_names}")
                query = text(base_query.format(where_clause="LOWER(r.name) IN :role_names"))
                result = connection.execute(query, {"role_names": tuple(role_names)})
            else:
                logger.info("[GET USERS] Fetching reviewers")
                query = text(
                    base_query.format(where_clause="LOWER(r.name) IN ('project reviewer', 'proposal reviewer')")
                )
                result = connection.execute(query)

            users = []
            for row in result.mappings():
                users.append(
                    User(
                        id=row["id"],
                        name=row["name"],
                        email=row["email"],
                        team_name=row["team_name"],
                        donor_ids=row["donor_ids"],
                        outcomes=row["outcomes"],
                        field_contexts=row["field_contexts"],
                    )
                )

            logger.info(f"[GET USERS] Found {len(users)} users total")

            # Exclude the current user from the list
            current_user_id = str(current_user["user_id"])
            users = [user for user in users if str(user.id) != current_user_id]
            logger.info(f"[GET USERS] Returning {len(users)} users after filtering current user")

            return users
    except Exception as e:
        logger.error(f"[GET USERS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not retrieve users.") from e


@router.get("/roles", response_model=List[Role])
async def get_roles():
    """
    Returns a list of all roles in the system.
    """
    try:
        from sqlalchemy import text

        with get_engine().connect() as connection:
            # Use raw SQL instead of ORM to avoid circular import issues
            result = connection.execute(text("SELECT id, name FROM roles ORDER BY name"))
            roles = [{"id": row[0], "name": row[1]} for row in result]
            return roles
    except Exception as e:
        logger.error(f"[GET ROLES ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not retrieve roles.") from e


@router.get("/donors/groups")
async def get_donor_groups():
    """
    Returns a list of all distinct donor groups.
    """
    try:
        from backend.models.donor import Donor

        with get_engine().connect() as connection:
            donor_groups = Donor.get_distinct_groups(connection)
            return {"donor_groups": donor_groups}
    except Exception as e:
        logger.error(f"[GET DONOR GROUPS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not retrieve donor groups.") from e


@router.get("/outcomes")
async def get_outcomes():
    """
    Returns a list of all outcomes.
    """
    try:
        from backend.models.outcome import Outcome

        with get_engine().connect() as connection:
            outcomes = connection.query(Outcome).order_by(Outcome.name).all()
            return [{"id": str(outcome.id), "name": outcome.name} for outcome in outcomes]
    except Exception as e:
        logger.error(f"[GET OUTCOMES ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not retrieve outcomes.") from e


@router.get("/users/me/settings", response_model=UserSettings)
async def get_user_settings(current_user: dict = Depends(get_current_user)):
    """
    Returns the current user's settings.
    """
    user_id = current_user["user_id"]
    try:
        with get_engine().connect() as connection:
            user_query = text(
                """
                SELECT geographic_coverage_type, geographic_coverage_region,
                geographic_coverage_country FROM users WHERE id = :user_id
                """
            )
            user_result = connection.execute(user_query, {"user_id": user_id}).fetchone()
            if not user_result:
                raise HTTPException(status_code=404, detail="User not found.")

            roles_query = text("SELECT role_id FROM user_roles WHERE user_id = :user_id")
            roles_result = connection.execute(roles_query, {"user_id": user_id}).fetchall()
            roles = [row[0] for row in roles_result]

            donor_groups_query = text("SELECT donor_group FROM user_donor_groups WHERE user_id = :user_id")
            donor_groups_result = connection.execute(donor_groups_query, {"user_id": user_id}).fetchall()
            donor_groups = [row[0] for row in donor_groups_result]

            outcomes_query = text("SELECT outcome_id FROM user_outcomes WHERE user_id = :user_id")
            outcomes_result = connection.execute(outcomes_query, {"user_id": user_id}).fetchall()
            outcomes = [row[0] for row in outcomes_result]

            field_contexts_query = text("SELECT field_context_id FROM user_field_contexts WHERE user_id = :user_id")
            field_contexts_result = connection.execute(field_contexts_query, {"user_id": user_id}).fetchall()
            field_contexts = [row[0] for row in field_contexts_result]

            requested_roles_query = text("SELECT role_id FROM user_role_requests WHERE user_id = :user_id")
            requested_roles_result = connection.execute(requested_roles_query, {"user_id": user_id}).fetchall()
            requested_roles = [row[0] for row in requested_roles_result]

            donor_ids_query = text("SELECT donor_id FROM user_donors WHERE user_id = :user_id")
            donor_ids_result = connection.execute(donor_ids_query, {"user_id": user_id}).fetchall()
            donor_ids = [row[0] for row in donor_ids_result]

            # Get requested settings from user_settings_requests table
            requested_donor_ids_query = text(
                """
                SELECT setting_value FROM user_settings_requests
                WHERE user_id = :user_id AND setting_type = 'donor_focal' AND status = 'pending'
            """
            )
            requested_donor_ids_result = connection.execute(requested_donor_ids_query, {"user_id": user_id}).fetchall()
            requested_donor_ids = [row[0] for row in requested_donor_ids_result]

            requested_outcomes_query = text(
                """
                SELECT setting_value FROM user_settings_requests
                WHERE user_id = :user_id AND setting_type = 'outcome_focal' AND status = 'pending'
            """
            )
            requested_outcomes_result = connection.execute(requested_outcomes_query, {"user_id": user_id}).fetchall()
            requested_outcomes = [row[0] for row in requested_outcomes_result]

            requested_field_contexts_query = text(
                """
                SELECT setting_value FROM user_settings_requests
                WHERE user_id = :user_id AND setting_type = 'field_context_focal' AND status = 'pending'
            """
            )
            requested_field_contexts_result = connection.execute(
                requested_field_contexts_query, {"user_id": user_id}
            ).fetchall()
            requested_field_contexts = [row[0] for row in requested_field_contexts_result]

            requested_team_memberships_query = text(
                """
                SELECT setting_value FROM user_settings_requests
                WHERE user_id = :user_id AND setting_type = 'team_membership' AND status = 'pending'
            """
            )
            requested_team_memberships_result = connection.execute(
                requested_team_memberships_query, {"user_id": user_id}
            ).fetchall()
            requested_team_memberships = [row[0] for row in requested_team_memberships_result]

            # Get team memberships
            team_memberships_query = text("SELECT team_id FROM team_members WHERE user_id = :user_id")
            team_memberships_result = connection.execute(team_memberships_query, {"user_id": user_id}).fetchall()
            team_memberships = [row[0] for row in team_memberships_result]

            return UserSettings(
                geographic_coverage_type=user_result[0],
                geographic_coverage_region=user_result[1],
                geographic_coverage_country=user_result[2],
                roles=roles,
                requested_roles=requested_roles,
                donor_groups=donor_groups,
                donor_ids=donor_ids,
                requested_donor_ids=requested_donor_ids,
                outcomes=outcomes,
                requested_outcomes=requested_outcomes,
                field_contexts=field_contexts,
                requested_field_contexts=requested_field_contexts,
                team_memberships=team_memberships,
                requested_team_memberships=requested_team_memberships,
            )
    except Exception as e:
        logger.error(f"[GET USER SETTINGS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not retrieve user settings.") from e


@router.put("/users/me/settings", status_code=204)
async def update_user_settings(settings: SelfServiceUserSettings, current_user: dict = Depends(get_current_user)):
    """
    Updates the current user's settings.
    """
    user_id = current_user["user_id"]
    try:
        with get_engine().connect() as connection:
            with connection.begin():
                # Update user's geographic coverage
                user_update_query = text(
                    """
                    UPDATE users
                    SET geographic_coverage_type = :geographic_coverage_type,
                        geographic_coverage_region = :geographic_coverage_region,
                        geographic_coverage_country = :geographic_coverage_country
                    WHERE id = :user_id
                """
                )
                connection.execute(
                    user_update_query,
                    {
                        "geographic_coverage_type": settings.geographic_coverage_type,
                        "geographic_coverage_region": settings.geographic_coverage_region,
                        "geographic_coverage_country": settings.geographic_coverage_country,
                        "user_id": user_id,
                    },
                )

                # Approved roles and access memberships are never modified by
                # this self-service endpoint. Only requests enter the approval
                # workflow.
                if settings.requested_roles:
                    for role_id in settings.requested_roles:
                        exists = connection.execute(
                            text("SELECT 1 FROM user_role_requests WHERE user_id = :user_id AND role_id = :role_id"),
                            {"user_id": user_id, "role_id": role_id},
                        ).fetchone()
                        if not exists:
                            connection.execute(
                                text("INSERT INTO user_role_requests (user_id, role_id) VALUES (:user_id, :role_id)"),
                                {"user_id": user_id, "role_id": role_id},
                            )

                # Insert requested settings into user_settings_requests table (like requested_roles)
                if settings.requested_donor_ids:
                    for donor_id in settings.requested_donor_ids:
                        # Check if this request already exists
                        existing_request = connection.execute(
                            text(
                                """
                                SELECT 1 FROM user_settings_requests
                                WHERE user_id = :user_id AND setting_type = 'donor_focal'
                                AND setting_value = :setting_value AND status = 'pending'
                            """
                            ),
                            {"user_id": user_id, "setting_value": str(donor_id)},
                        ).fetchone()

                        if not existing_request:
                            connection.execute(
                                text(
                                    """
                                    INSERT INTO user_settings_requests
                                    (user_id, setting_type, setting_value, status)
                                    VALUES (:user_id, 'donor_focal', :setting_value, 'pending')
                                """
                                ),
                                {"user_id": user_id, "setting_value": str(donor_id)},
                            )

                if settings.requested_outcomes:
                    for outcome_id in settings.requested_outcomes:
                        # Check if this request already exists
                        existing_request = connection.execute(
                            text(
                                """
                                SELECT 1 FROM user_settings_requests
                                WHERE user_id = :user_id AND setting_type = 'outcome_focal'
                                AND setting_value = :setting_value AND status = 'pending'
                            """
                            ),
                            {"user_id": user_id, "setting_value": str(outcome_id)},
                        ).fetchone()

                        if not existing_request:
                            connection.execute(
                                text(
                                    """
                                    INSERT INTO user_settings_requests
                                    (user_id, setting_type, setting_value, status)
                                    VALUES (:user_id, 'outcome_focal', :setting_value, 'pending')
                                """
                                ),
                                {"user_id": user_id, "setting_value": str(outcome_id)},
                            )

                if settings.requested_field_contexts:
                    for fc_id in settings.requested_field_contexts:
                        # Check if this request already exists
                        existing_request = connection.execute(
                            text(
                                """
                                SELECT 1 FROM user_settings_requests
                                WHERE user_id = :user_id AND setting_type = 'field_context_focal'
                                AND setting_value = :setting_value AND status = 'pending'
                            """
                            ),
                            {"user_id": user_id, "setting_value": str(fc_id)},
                        ).fetchone()

                        if not existing_request:
                            connection.execute(
                                text(
                                    """
                                    INSERT INTO user_settings_requests
                                    (user_id, setting_type, setting_value, status)
                                    VALUES (:user_id, 'field_context_focal', :setting_value, 'pending')
                                """
                                ),
                                {"user_id": user_id, "setting_value": str(fc_id)},
                            )

                if settings.requested_team_memberships:
                    for team_id in settings.requested_team_memberships:
                        # Check if this request already exists
                        existing_request = connection.execute(
                            text(
                                """
                                SELECT 1 FROM user_settings_requests
                                WHERE user_id = :user_id AND setting_type = 'team_membership'
                                AND setting_value = :setting_value AND status = 'pending'
                            """
                            ),
                            {"user_id": user_id, "setting_value": str(team_id)},
                        ).fetchone()

                        if not existing_request:
                            connection.execute(
                                text(
                                    """
                                    INSERT INTO user_settings_requests
                                    (user_id, setting_type, setting_value, status)
                                    VALUES (:user_id, 'team_membership', :setting_value, 'pending')
                                """
                                ),
                                {"user_id": user_id, "setting_value": str(team_id)},
                            )
    except Exception as e:
        logger.error(f"[UPDATE USER SETTINGS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not update user settings.") from e


@router.get("/users/me/approved-settings")
async def get_user_approved_settings(current_user: dict = Depends(get_current_user)):
    """
    Returns the current user's approved settings from the settings request system
    """
    user_id = current_user["user_id"]
    try:
        with get_engine().connect() as connection:
            # Get approved settings from user_settings_requests
            approved_settings = connection.execute(
                text(
                    """
                SELECT setting_type, setting_value, approved_at
                FROM user_settings_requests
                WHERE user_id = :user_id AND status = 'approved'
                ORDER BY approved_at DESC
                """
                ),
                {"user_id": user_id},
            ).fetchall()

            # Format the response
            settings_list = []
            for row in approved_settings:
                settings_list.append(
                    {
                        "setting_type": row[0],
                        "setting_value": row[1],
                        "approved_at": row[2].isoformat() if row[2] else None,
                    }
                )

            return {"approved_settings": settings_list}
    except Exception as e:
        logger.error(f"[GET APPROVED SETTINGS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch approved settings: {str(e)}") from e
