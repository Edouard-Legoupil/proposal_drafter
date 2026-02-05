#  Standard Library
import logging
import uuid
from typing import List

#  Third-Party Libraries
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

#  Internal Modules
from backend.core.db import get_engine
from backend.core.security import get_current_user
from backend.models.schemas import UserSettings, Role, User

# This router handles all endpoints related to users.
router = APIRouter()

# Configure logging
logger = logging.getLogger(__name__)


@router.get("/teams")
async def get_teams():
    """
    Returns a list of all teams in the system.
    """
    try:
        with get_engine().connect() as connection:
            result = connection.execute(text("SELECT id, name FROM teams ORDER BY name"))
            teams = [{"id": str(row[0]), "name": row[1]} for row in result]
            return {"teams": teams}
    except Exception as e:
        logger.error(f"[GET TEAMS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not retrieve teams.")


@router.get("/users", response_model=List[User])
async def get_users(current_user: dict = Depends(get_current_user)):
    """
    Returns a list of all users in the system.
    This is used to populate the peer review selection modal.
    """
    try:
        with get_engine().connect() as connection:
            query = text("""
                SELECT DISTINCT u.id, u.name, u.email, t.name as team_name
                FROM users u
                LEFT JOIN teams t ON u.team_id = t.id
                JOIN user_roles ur ON u.id = ur.user_id
                JOIN roles r ON ur.role_id = r.id
                WHERE LOWER(r.name) IN ('project reviewer', 'proposal reviewer')
                ORDER BY t.name, u.name
            """)
            result = connection.execute(query)
            users = [User(**row) for row in result.mappings()]
            # Exclude the current user from the list of potential reviewers
            users = [user for user in users if user.id != current_user["user_id"]]
            return users
    except Exception as e:
        logger.error(f"[GET USERS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not retrieve users.")

@router.get("/roles", response_model=List[Role])
async def get_roles():
    """
    Returns a list of all roles in the system.
    """
    try:
        with get_engine().connect() as connection:
            result = connection.execute(text("SELECT id, name FROM roles ORDER BY name"))
            roles = [Role(**row) for row in result.mappings()]
            return roles
    except Exception as e:
        logger.error(f"[GET ROLES ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not retrieve roles.")

@router.get("/donors/groups")
async def get_donor_groups():
    """
    Returns a list of all distinct donor groups.
    """
    try:
        with get_engine().connect() as connection:
            result = connection.execute(text("SELECT DISTINCT donor_group FROM donors ORDER BY donor_group"))
            donor_groups = [row[0] for row in result]
            return {"donor_groups": donor_groups}
    except Exception as e:
        logger.error(f"[GET DONOR GROUPS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not retrieve donor groups.")

@router.get("/outcomes")
async def get_outcomes():
    """
    Returns a list of all outcomes.
    """
    try:
        with get_engine().connect() as connection:
            result = connection.execute(text("SELECT id, name FROM outcomes ORDER BY name"))
            outcomes = [{"id": str(row[0]), "name": row[1]} for row in result]
            return {"outcomes": outcomes}
    except Exception as e:
        logger.error(f"[GET OUTCOMES ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not retrieve outcomes.")


@router.get("/users/me/settings", response_model=UserSettings)
async def get_user_settings(current_user: dict = Depends(get_current_user)):
    """
    Returns the current user's settings.
    """
    user_id = current_user["user_id"]
    try:
        with get_engine().connect() as connection:
            user_query = text("SELECT geographic_coverage_type, geographic_coverage_region, geographic_coverage_country FROM users WHERE id = :user_id")
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

            return UserSettings(
                geographic_coverage_type=user_result[0],
                geographic_coverage_region=user_result[1],
                geographic_coverage_country=user_result[2],
                roles=roles,
                donor_groups=donor_groups,
                outcomes=outcomes,
                field_contexts=field_contexts
            )
    except Exception as e:
        logger.error(f"[GET USER SETTINGS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not retrieve user settings.")

@router.put("/users/me/settings", status_code=204)
async def update_user_settings(settings: UserSettings, current_user: dict = Depends(get_current_user)):
    """
    Updates the current user's settings.
    """
    user_id = current_user["user_id"]
    try:
        with get_engine().connect() as connection:
            with connection.begin():
                # Update user's geographic coverage
                user_update_query = text("""
                    UPDATE users
                    SET geographic_coverage_type = :geographic_coverage_type,
                        geographic_coverage_region = :geographic_coverage_region,
                        geographic_coverage_country = :geographic_coverage_country
                    WHERE id = :user_id
                """)
                connection.execute(user_update_query, {
                    "geographic_coverage_type": settings.geographic_coverage_type,
                    "geographic_coverage_region": settings.geographic_coverage_region,
                    "geographic_coverage_country": settings.geographic_coverage_country,
                    "user_id": user_id
                })

                # Clear existing user roles, donor groups, outcomes, and field contexts
                connection.execute(text("DELETE FROM user_roles WHERE user_id = :user_id"), {"user_id": user_id})
                connection.execute(text("DELETE FROM user_donor_groups WHERE user_id = :user_id"), {"user_id": user_id})
                connection.execute(text("DELETE FROM user_outcomes WHERE user_id = :user_id"), {"user_id": user_id})
                connection.execute(text("DELETE FROM user_field_contexts WHERE user_id = :user_id"), {"user_id": user_id})

                # Insert new roles
                if settings.roles:
                    role_insert_query = text("INSERT INTO user_roles (user_id, role_id) VALUES (:user_id, :role_id)")
                    connection.execute(role_insert_query, [{"user_id": user_id, "role_id": role_id} for role_id in settings.roles])

                # Insert new donor groups
                if settings.donor_groups:
                    donor_group_insert_query = text("INSERT INTO user_donor_groups (user_id, donor_group) VALUES (:user_id, :donor_group)")
                    connection.execute(donor_group_insert_query, [{"user_id": user_id, "donor_group": dg} for dg in settings.donor_groups])

                # Insert new outcomes
                if settings.outcomes:
                    outcome_insert_query = text("INSERT INTO user_outcomes (user_id, outcome_id) VALUES (:user_id, :outcome_id)")
                    connection.execute(outcome_insert_query, [{"user_id": user_id, "outcome_id": outcome_id} for outcome_id in settings.outcomes])

                # Insert new field contexts
                if settings.field_contexts:
                    fc_insert_query = text("INSERT INTO user_field_contexts (user_id, field_context_id) VALUES (:user_id, :fc_id)")
                    connection.execute(fc_insert_query, [{"user_id": user_id, "fc_id": fc_id} for fc_id in settings.field_contexts])
    except Exception as e:
        logger.error(f"[UPDATE USER SETTINGS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not update user settings.")
