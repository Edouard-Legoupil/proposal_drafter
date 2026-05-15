#  Standard Library
import logging
import uuid

#  Third-Party Libraries
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

#  Internal Modules
from backend.core.db import get_engine
from backend.core.security import is_system_admin
from backend.models.schemas import CreateTeamRequest, UpdateUserTeamRequest

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
            users_query = text(
                """
                SELECT u.id, u.name, u.email, t.name as team_name, u.requested_role_id, r.name as requested_role_name
                FROM users u
                LEFT JOIN teams t ON u.team_id = t.id
                LEFT JOIN roles r ON u.requested_role_id = r.id
                ORDER BY u.name
            """
            )
            users_result = connection.execute(users_query).mappings().all()

            users_list = []
            for user in users_result:
                user_id = str(user["id"])
                # Fetch roles
                roles_query = text(
                    """
                    SELECT r.id, r.name
                    FROM roles r
                    JOIN user_roles ur ON r.id = ur.role_id
                    WHERE ur.user_id = :user_id
                """
                )
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
                user_check = connection.execute(
                    text("SELECT id FROM users WHERE id = :user_id"),
                    {"user_id": user_id},
                ).fetchone()
                if not user_check:
                    raise HTTPException(status_code=404, detail="User not found.")

                # Clear all existing associations
                connection.execute(
                    text("DELETE FROM user_roles WHERE user_id = :user_id"),
                    {"user_id": user_id},
                )
                connection.execute(
                    text("DELETE FROM user_donor_groups WHERE user_id = :user_id"),
                    {"user_id": user_id},
                )
                connection.execute(
                    text("DELETE FROM user_outcomes WHERE user_id = :user_id"),
                    {"user_id": user_id},
                )
                connection.execute(
                    text("DELETE FROM user_field_contexts WHERE user_id = :user_id"),
                    {"user_id": user_id},
                )

                # Clear pending role request
                connection.execute(
                    text("UPDATE users SET requested_role_id = NULL WHERE id = :user_id"),
                    {"user_id": user_id},
                )

                # Insert new roles
                if role_ids:
                    connection.execute(
                        text("INSERT INTO user_roles (user_id, role_id) VALUES (:user_id, :role_id)"),
                        [{"user_id": user_id, "role_id": rid} for rid in role_ids],
                    )

                # Insert new donor groups
                if donor_groups:
                    connection.execute(
                        text("INSERT INTO user_donor_groups (user_id, donor_group) VALUES (:user_id, :donor_group)"),
                        [{"user_id": user_id, "donor_group": dg} for dg in donor_groups],
                    )

                # Insert new outcomes
                if outcomes:
                    connection.execute(
                        text("INSERT INTO user_outcomes (user_id, outcome_id) VALUES (:user_id, :outcome_id)"),
                        [{"user_id": user_id, "outcome_id": oid} for oid in outcomes],
                    )

                # Insert new field contexts
                if field_contexts:
                    connection.execute(
                        text("INSERT INTO user_field_contexts (user_id, field_context_id) VALUES (:user_id, :fc_id)"),
                        [{"user_id": user_id, "fc_id": fcid} for fcid in field_contexts],
                    )

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
            field_contexts = (
                connection.execute(text("SELECT id, name FROM field_contexts ORDER BY name")).mappings().all()
            )

            # Teams
            teams = connection.execute(text("SELECT id, name FROM teams ORDER BY name")).mappings().all()

            # Pending template requests count
            pending_templates_count = connection.execute(
                text("SELECT COUNT(*) FROM donor_template_requests WHERE status = 'pending'")
            ).scalar()

            return {
                "roles": [dict(r) for r in roles],
                "donor_groups": [row[0] for row in donors],
                "outcomes": [dict(o) for o in outcomes],
                "field_contexts": [dict(fc) for fc in field_contexts],
                "teams": [dict(t) for t in teams],
                "pending_template_requests": pending_templates_count,
            }
    except Exception as e:
        logger.error(f"[GET ADMIN OPTIONS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not retrieve admin options.")


@router.post("/admin/teams")
async def create_team(request: CreateTeamRequest, admin: dict = Depends(is_system_admin)):
    """
    Creates a new team.
    """
    try:
        with get_engine().begin() as connection:
            # Check if team exists
            existing = connection.execute(
                text("SELECT id FROM teams WHERE lower(name) = :name"),
                {"name": request.name.lower()},
            ).fetchone()
            if existing:
                raise HTTPException(status_code=400, detail="Team with this name already exists.")

            team_id = str(uuid.uuid4())
            connection.execute(
                text("INSERT INTO teams (id, name) VALUES (:id, :name)"),
                {"id": team_id, "name": request.name},
            )
            return {
                "message": "Team created successfully.",
                "team": {"id": team_id, "name": request.name},
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CREATE TEAM ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create team.")


@router.put("/admin/users/{user_id}/team")
async def update_user_team(user_id: str, request: UpdateUserTeamRequest, admin: dict = Depends(is_system_admin)):
    """
    Updates a user's team.
    """
    try:
        with get_engine().begin() as connection:
            # Verify user exists
            user_check = connection.execute(
                text("SELECT id FROM users WHERE id = :user_id"), {"user_id": user_id}
            ).fetchone()
            if not user_check:
                raise HTTPException(status_code=404, detail="User not found.")

            # Verify team exists
            team_check = connection.execute(
                text("SELECT id FROM teams WHERE id = :team_id"),
                {"team_id": str(request.team_id)},
            ).fetchone()
            if not team_check:
                raise HTTPException(status_code=404, detail="Team not found.")

            connection.execute(
                text("UPDATE users SET team_id = :team_id WHERE id = :user_id"),
                {"team_id": str(request.team_id), "user_id": user_id},
            )
            return {"message": "User team updated successfully."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[UPDATE USER TEAM ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update user team.")


@router.delete("/admin/users/{user_id}")
async def delete_user(user_id: str, admin: dict = Depends(is_system_admin)):
    """
    Deletes a user and all their associations.
    """
    try:
        with get_engine().begin() as connection:
            # Verify user exists
            user_check = connection.execute(
                text("SELECT id FROM users WHERE id = :user_id"), {"user_id": user_id}
            ).fetchone()
            if not user_check:
                raise HTTPException(status_code=404, detail="User not found.")

            # Delete associations first (though ON DELETE CASCADE might handle this, explicit is safer if not configured)
            connection.execute(
                text("DELETE FROM user_roles WHERE user_id = :user_id"),
                {"user_id": user_id},
            )
            connection.execute(
                text("DELETE FROM user_donor_groups WHERE user_id = :user_id"),
                {"user_id": user_id},
            )
            connection.execute(
                text("DELETE FROM user_outcomes WHERE user_id = :user_id"),
                {"user_id": user_id},
            )
            connection.execute(
                text("DELETE FROM user_field_contexts WHERE user_id = :user_id"),
                {"user_id": user_id},
            )

            # Delete the user
            connection.execute(text("DELETE FROM users WHERE id = :user_id"), {"user_id": user_id})

            return {"message": "User deleted successfully."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DELETE USER ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete user.")


@router.get("/admin/template-requests")
async def get_admin_template_requests(admin: dict = Depends(is_system_admin)):
    """
    Returns a list of all template requests for admin download.
    """
    try:
        with get_engine().connect() as connection:
            query = text(
                """
                SELECT tr.*, u.name as creator_name, d.name as donor_name
                FROM donor_template_requests tr
                JOIN users u ON tr.created_by = u.id
                LEFT JOIN donors d ON tr.donor_id = d.id
                ORDER BY tr.created_at DESC
            """
            )
            result = connection.execute(query).mappings().all()

            requests = []
            for row in result:
                req = dict(row)
                req["id"] = str(row["id"])
                # Handle potential JSON strings or objects
                for field in ["configuration", "initial_file_content"]:
                    if isinstance(req[field], str):
                        try:
                            import json

                            req[field] = json.loads(req[field])
                        except Exception:
                            pass
                req["created_at"] = row["created_at"].isoformat() if row["created_at"] else None
                requests.append(req)

            return requests
    except Exception as e:
        logger.error(f"[GET ADMIN TEMPLATE REQUESTS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not retrieve template requests.")


@router.get("/admin/proposals/list")
async def list_admin_proposals(admin: dict = Depends(is_system_admin)):
    """
    Returns a lightweight list of all proposals with owner info for the access
    management resource picker.
    """
    try:
        with get_engine().connect() as connection:
            query = text(
                """
                SELECT
                    p.id,
                    COALESCE(p.form_data->>'projectTitle', p.form_data->>'title', p.id::text) AS title,
                    p.status::text AS status,
                    p.created_at,
                    p.updated_at,
                    u.name AS owner_name,
                    u.email AS owner_email,
                    u.id AS owner_id
                FROM proposals p
                JOIN users u ON p.user_id = u.id
                ORDER BY p.updated_at DESC
            """
            )
            rows = connection.execute(query).mappings().all()
            return [
                {
                    "id": str(r["id"]),
                    "title": r["title"],
                    "status": r["status"],
                    "owner_name": r["owner_name"],
                    "owner_email": r["owner_email"],
                    "owner_id": str(r["owner_id"]),
                    "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                    "updated_at": r["updated_at"].isoformat() if r["updated_at"] else None,
                }
                for r in rows
            ]
    except Exception as e:
        logger.error(f"[LIST ADMIN PROPOSALS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not list proposals.")


@router.get("/admin/knowledge-cards/list")
async def list_admin_knowledge_cards(admin: dict = Depends(is_system_admin)):
    """
    Returns a lightweight list of all knowledge cards with owner info for the
    access management resource picker.
    """
    try:
        with get_engine().connect() as connection:
            query = text(
                """
                SELECT
                    kc.id,
                    COALESCE(kc.summary, kc.id::text) AS title,
                    kc.type,
                    kc.status::text AS status,
                    kc.created_at,
                    kc.updated_at,
                    u.name AS owner_name,
                    u.email AS owner_email,
                    u.id AS owner_id,
                    d.name AS donor_name,
                    o.name AS outcome_name,
                    fc.name AS field_context_name
                FROM knowledge_cards kc
                JOIN users u ON kc.created_by = u.id
                LEFT JOIN donors d ON kc.donor_id = d.id
                LEFT JOIN outcomes o ON kc.outcome_id = o.id
                LEFT JOIN field_contexts fc ON kc.field_context_id = fc.id
                ORDER BY kc.updated_at DESC
            """
            )
            rows = connection.execute(query).mappings().all()
            return [
                {
                    "id": str(r["id"]),
                    "title": r["title"],
                    "type": r["type"],
                    "status": r["status"],
                    "owner_name": r["owner_name"],
                    "owner_email": r["owner_email"],
                    "owner_id": str(r["owner_id"]),
                    "donor_name": r["donor_name"],
                    "outcome_name": r["outcome_name"],
                    "field_context_name": r["field_context_name"],
                    "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                    "updated_at": r["updated_at"].isoformat() if r["updated_at"] else None,
                }
                for r in rows
            ]
    except Exception as e:
        logger.error(f"[LIST ADMIN KNOWLEDGE CARDS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not list knowledge cards.")


@router.get("/admin/templates/list")
async def list_admin_templates(admin: dict = Depends(is_system_admin)):
    """
    Returns a lightweight list of all templates with owner info for the access
    management resource picker.
    """
    try:
        with get_engine().connect() as connection:
            query = text(
                """
                SELECT
                    t.id,
                    t.name,
                    t.template_type::text AS template_type,
                    t.status::text AS status,
                    t.is_default,
                    t.created_at,
                    t.updated_at,
                    u.name AS owner_name,
                    u.email AS owner_email,
                    u.id AS owner_id
                FROM templates t
                LEFT JOIN users u ON t.created_by = u.id
                ORDER BY t.updated_at DESC
            """
            )
            rows = connection.execute(query).mappings().all()
            return [
                {
                    "id": str(r["id"]),
                    "name": r["name"],
                    "template_type": r["template_type"],
                    "status": r["status"],
                    "is_default": r["is_default"],
                    "owner_name": r["owner_name"],
                    "owner_email": r["owner_email"],
                    "owner_id": str(r["owner_id"]) if r["owner_id"] else None,
                    "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                    "updated_at": r["updated_at"].isoformat() if r["updated_at"] else None,
                }
                for r in rows
            ]
    except Exception as e:
        logger.error(f"[LIST ADMIN TEMPLATES ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not list templates.")
