#  Standard Library
import logging
import uuid
from typing import List

#  Third-Party Libraries
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

#  Internal Modules
from backend.core.db import get_engine
from backend.core.security import is_system_admin
from backend.models.schemas import Role

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/admin/users")
async def get_admin_users(admin: dict = Depends(is_system_admin)):
    """
    Returns a list of all users with their roles for admin management.
    """
    try:
        with get_engine().connect() as connection:
            # Fetch all users
            users_query = text("""
                SELECT u.id, u.name, u.email, t.name as team_name, u.requested_role_id, r.name as requested_role_name
                FROM users u
                LEFT JOIN teams t ON u.team_id = t.id
                LEFT JOIN roles r ON u.requested_role_id = r.id
                ORDER BY u.name
            """)
            users_result = connection.execute(users_query).mappings().all()
            
            users_list = []
            for user in users_result:
                user_id = str(user["id"])
                # Fetch roles
                roles_query = text("""
                    SELECT r.id, r.name 
                    FROM roles r 
                    JOIN user_roles ur ON r.id = ur.role_id 
                    WHERE ur.user_id = :user_id
                """)
                roles_result = connection.execute(roles_query, {"user_id": user_id}).mappings().all()
                
                # Fetch donor groups
                dg_query = text("SELECT donor_group FROM user_donor_groups WHERE user_id = :user_id")
                dg_result = connection.execute(dg_query, {"user_id": user_id}).fetchall()
                
                # Fetch outcomes
                o_query = text("SELECT outcome_id FROM user_outcomes WHERE user_id = :user_id")
                o_result = connection.execute(o_query, {"user_id": user_id}).fetchall()
                
                # Fetch field contexts
                fc_query = text("SELECT field_context_id FROM user_field_contexts WHERE user_id = :user_id")
                fc_result = connection.execute(fc_query, {"user_id": user_id}).fetchall()
                
                user_dict = dict(user)
                user_dict["id"] = user_id
                user_dict["roles"] = [dict(role) for role in roles_result]
                user_dict["donor_groups"] = [row[0] for row in dg_result]
                user_dict["outcomes"] = [str(row[0]) for row in o_result]
                user_dict["field_contexts"] = [str(row[0]) for row in fc_result]
                users_list.append(user_dict)
                
            return users_list
    except Exception as e:
        logger.error(f"[GET ADMIN USERS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not retrieve users for admin.")

@router.put("/admin/users/{user_id}/settings")
async def update_admin_user_settings(user_id: str, settings: dict, admin: dict = Depends(is_system_admin)):
    """
    Updates all settings for a specific user.
    """
    try:
        role_ids = settings.get("role_ids", [])
        donor_groups = settings.get("donor_groups", [])
        outcomes = settings.get("outcomes", [])
        field_contexts = settings.get("field_contexts", [])

        with get_engine().connect() as connection:
            with connection.begin():
                # Verify user exists
                user_check = connection.execute(text("SELECT id FROM users WHERE id = :user_id"), {"user_id": user_id}).fetchone()
                if not user_check:
                    raise HTTPException(status_code=404, detail="User not found.")
                
                # Clear all existing associations
                connection.execute(text("DELETE FROM user_roles WHERE user_id = :user_id"), {"user_id": user_id})
                connection.execute(text("DELETE FROM user_donor_groups WHERE user_id = :user_id"), {"user_id": user_id})
                connection.execute(text("DELETE FROM user_outcomes WHERE user_id = :user_id"), {"user_id": user_id})
                connection.execute(text("DELETE FROM user_field_contexts WHERE user_id = :user_id"), {"user_id": user_id})
                
                # Clear pending role request
                connection.execute(text("UPDATE users SET requested_role_id = NULL WHERE id = :user_id"), {"user_id": user_id})
                
                # Insert new roles
                if role_ids:
                    connection.execute(text("INSERT INTO user_roles (user_id, role_id) VALUES (:user_id, :role_id)"), [{"user_id": user_id, "role_id": rid} for rid in role_ids])
                
                # Insert new donor groups
                if donor_groups:
                    connection.execute(text("INSERT INTO user_donor_groups (user_id, donor_group) VALUES (:user_id, :donor_group)"), [{"user_id": user_id, "donor_group": dg} for dg in donor_groups])
                
                # Insert new outcomes
                if outcomes:
                    connection.execute(text("INSERT INTO user_outcomes (user_id, outcome_id) VALUES (:user_id, :outcome_id)"), [{"user_id": user_id, "outcome_id": oid} for oid in outcomes])

                # Insert new field contexts
                if field_contexts:
                    connection.execute(text("INSERT INTO user_field_contexts (user_id, field_context_id) VALUES (:user_id, :fc_id)"), [{"user_id": user_id, "fc_id": fcid} for fcid in field_contexts])
                    
            return {"message": "User settings updated successfully."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[UPDATE ADMIN USER SETTINGS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not update user settings.")

@router.get("/admin/options")
async def get_admin_options(admin: dict = Depends(is_system_admin)):
    """
    Fetches all available options for roles, donor groups, outcomes, and field contexts.
    """
    try:
        with get_engine().connect() as connection:
            # Roles
            roles = connection.execute(text("SELECT id, name FROM roles ORDER BY name")).mappings().all()
            
            # Donor Groups (distinct donor names)
            donors = connection.execute(text("SELECT DISTINCT name FROM donors ORDER BY name")).fetchall()
            
            # Outcomes
            outcomes = connection.execute(text("SELECT id, name FROM outcomes ORDER BY name")).mappings().all()
            
            # Field Contexts
            field_contexts = connection.execute(text("SELECT id, name FROM field_contexts ORDER BY name")).mappings().all()
            
            return {
                "roles": [dict(r) for r in roles],
                "donor_groups": [row[0] for row in donors],
                "outcomes": [dict(o) for o in outcomes],
                "field_contexts": [dict(fc) for fc in field_contexts]
            }
    except Exception as e:
        logger.error(f"[GET ADMIN OPTIONS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not retrieve admin options.")
