#  Standard Library
import json
import logging
import uuid

#  Third-Party Libraries
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

#  Internal Modules
from backend.core.db import get_engine
from backend.core.security import is_system_admin
from backend.models.schemas import CreateTeamRequest, UpdateUserTeamRequest
from backend.utils.notification_service import notification_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/admin/users")
async def get_admin_users(admin: dict = Depends(is_system_admin)):
    """
    Returns a list of all users with their roles for admin management.
    """
    try:
        from sqlalchemy.orm import Session

        with get_engine().connect() as connection:
            # Create a session for ORM operations
            session = Session(connection)

            # Fetch all users with all their data in a single optimized query
            users_query = text(
                """
                SELECT
                    u.id as user_id,
                    u.name as user_name,
                    u.email as user_email,
                    t.name as team_name,
                    u.requested_role_id,
                    r.name as requested_role_name,
                    -- Roles
                    array_agg(DISTINCT jsonb_build_object('id', ur.role_id, 'name', roles.name)) FILTER (WHERE ur.role_id IS NOT NULL) as roles,
                    -- Donor groups
                    array_agg(DISTINCT dg.donor_group) FILTER (WHERE dg.donor_group IS NOT NULL) as donor_groups,
                    -- Outcomes
                    array_agg(DISTINCT ou.outcome_id) FILTER (WHERE ou.outcome_id IS NOT NULL) as outcomes,
                    -- Field contexts
                    array_agg(DISTINCT fc.field_context_id) FILTER (WHERE fc.field_context_id IS NOT NULL) as field_contexts
                FROM users u
                LEFT JOIN teams t ON u.team_id = t.id
                LEFT JOIN roles r ON u.requested_role_id = r.id
                LEFT JOIN user_roles ur ON u.id = ur.user_id
                LEFT JOIN roles ON ur.role_id = roles.id
                LEFT JOIN user_donor_groups dg ON u.id = dg.user_id
                LEFT JOIN user_outcomes ou ON u.id = ou.user_id
                LEFT JOIN user_field_contexts fc ON u.id = fc.user_id
                GROUP BY u.id, u.name, u.email, t.name, u.requested_role_id, r.name
                ORDER BY u.name
            """
            )
            users_result = connection.execute(users_query).mappings().all()

            users_list = []
            for user in users_result:
                user_dict = {
                    "id": str(user["user_id"]),
                    "name": user["user_name"],
                    "email": user["user_email"],
                    "team_name": user["team_name"],
                    "requested_role_id": user["requested_role_id"],
                    "requested_role_name": user["requested_role_name"],
                    "roles": user["roles"] or [],
                    "donor_groups": user["donor_groups"] or [],
                    "outcomes": user["outcomes"] or [],
                    "field_contexts": user["field_contexts"] or [],
                }
                users_list.append(user_dict)

            # Debug: log the number of users returned
            logger.info(f"Admin users query returned {len(users_list)} users")
            return users_list
    except Exception as e:
        logger.error(f"[GET ADMIN USERS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Could not retrieve users for admin: {str(e)}")


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

        # Convert string IDs to integers for role_ids and validate
        role_ids = []
        for rid in settings.get("role_ids", []):
            if isinstance(rid, str) and rid.isdigit():
                role_ids.append(int(rid))
            elif isinstance(rid, int):
                role_ids.append(rid)
            else:
                logger.warning(f"Invalid role ID type: {type(rid)} - {rid}")

        with get_engine().begin() as connection:
            # Verify user exists
            user_check = connection.execute(
                text("SELECT id FROM users WHERE id = :user_id"),
                {"user_id": user_id},
            ).fetchone()
            if not user_check:
                raise HTTPException(status_code=404, detail=f"User {user_id} not found.")

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
                try:
                    connection.execute(
                        text("INSERT INTO user_roles (user_id, role_id) VALUES (:user_id, :role_id)"),
                        [{"user_id": user_id, "role_id": rid} for rid in role_ids],
                    )
                except Exception as e:
                    logger.error(f"Failed to insert roles: {e}")
                    raise HTTPException(status_code=400, detail=f"Failed to insert roles: {str(e)}")

            # Insert new donor groups
            if donor_groups:
                try:
                    connection.execute(
                        text("INSERT INTO user_donor_groups (user_id, donor_group) VALUES (:user_id, :donor_group)"),
                        [{"user_id": user_id, "donor_group": dg} for dg in donor_groups],
                    )
                except Exception as e:
                    logger.error(f"Failed to insert donor groups: {e}")
                    raise HTTPException(status_code=400, detail=f"Failed to insert donor groups: {str(e)}")

            # Insert new outcomes
            if outcomes:
                try:
                    connection.execute(
                        text("INSERT INTO user_outcomes (user_id, outcome_id) VALUES (:user_id, :outcome_id)"),
                        [{"user_id": user_id, "outcome_id": oid} for oid in outcomes],
                    )
                except Exception as e:
                    logger.error(f"Failed to insert outcomes: {e}")
                    raise HTTPException(status_code=400, detail=f"Failed to insert outcomes: {str(e)}")

            # Insert new field contexts
            if field_contexts:
                try:
                    connection.execute(
                        text("INSERT INTO user_field_contexts (user_id, field_context_id) VALUES (:user_id, :fc_id)"),
                        [{"user_id": user_id, "fc_id": fcid} for fcid in field_contexts],
                    )
                except Exception as e:
                    logger.error(f"Failed to insert field contexts: {e}")
                    raise HTTPException(status_code=400, detail=f"Failed to insert field contexts: {str(e)}")

        return {"message": "User settings updated successfully."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[UPDATE ADMIN USER SETTINGS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Could not update user settings: {str(e)}")


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


@router.post("/admin/roles")
async def create_role(request: CreateTeamRequest, admin: dict = Depends(is_system_admin)):
    """
    Creates a new role.
    """
    try:
        with get_engine().begin() as connection:
            # Check if role exists
            existing = connection.execute(
                text("SELECT id FROM roles WHERE lower(name) = :name"),
                {"name": request.name.lower()},
            ).fetchone()
            if existing:
                raise HTTPException(status_code=400, detail="Role with this name already exists.")

            role_id = str(uuid.uuid4())
            connection.execute(
                text("INSERT INTO roles (id, name) VALUES (:id, :name)"),
                {"id": role_id, "name": request.name},
            )
            return {
                "message": "Role created successfully.",
                "role": {"id": role_id, "name": request.name},
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CREATE ROLE ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create role.")


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


@router.get("/admin/role-requests")
async def get_admin_role_requests(admin: dict = Depends(is_system_admin)):
    """
    Returns a list of all pending role requests for approval.
    """
    try:
        with get_engine().connect() as connection:
            query = text(
                """
                SELECT
                    u.id::text as user_id,
                    u.name as user_name,
                    u.email as user_email,
                    u.requested_role_id::text as requested_role_id,
                    r.name as requested_role_name,
                    r.id::text as role_id,
                    u.created_at as requested_at,
                    u.updated_at as last_updated
                FROM users u
                JOIN roles r ON u.requested_role_id = r.id
                WHERE u.requested_role_id IS NOT NULL
                ORDER BY u.created_at DESC
            """
            )
            result = connection.execute(query).mappings().all()

            requests = []
            for row in result:
                req = dict(row)
                req["requested_at"] = row["requested_at"].isoformat() if row["requested_at"] else None
                req["last_updated"] = row["last_updated"].isoformat() if row["last_updated"] else None
                requests.append(req)

            return requests
    except Exception as e:
        logger.error(f"[GET ADMIN ROLE REQUESTS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not retrieve role requests.")


@router.post("/admin/role-requests/{user_id}/approve")
async def approve_role_request(user_id: str, admin_note: str | None = None, admin: dict = Depends(is_system_admin)):
    """
    Approve a role request and assign the requested role to the user.
    """
    try:
        with get_engine().begin() as connection:
            # Get the user's requested role
            user_query = text(
                """
                SELECT id, requested_role_id, name, email
                FROM users
                WHERE id = :user_id AND requested_role_id IS NOT NULL
            """
            )
            user = connection.execute(user_query, {"user_id": user_id}).fetchone()

            if not user:
                raise HTTPException(status_code=404, detail="User not found or no pending role request")

            requested_role_id = user[1]
            user_name = user[2]
            user_email = user[3]

            # Assign the requested role to the user
            connection.execute(
                text(
                    """
                    INSERT INTO user_roles (user_id, role_id)
                    VALUES (:user_id, :role_id)
                    ON CONFLICT (user_id, role_id) DO NOTHING
                """
                ),
                {"user_id": user_id, "role_id": requested_role_id},
            )

            # Clear the pending request
            connection.execute(
                text("UPDATE users SET requested_role_id = NULL WHERE id = :user_id"), {"user_id": user_id}
            )

            # Log the approval
            connection.execute(
                text(
                    """
                    INSERT INTO audit_logs
                    (event_type, resource_type, resource_id, details, user_id)
                    VALUES (:event_type, :resource_type, :resource_id, :details, :user_id)
                """
                ),
                {
                    "event_type": "role_request.approved",
                    "resource_type": "user",
                    "resource_id": user_id,
                    "details": json.dumps(
                        {
                            "requested_role_id": str(requested_role_id),
                            "admin_note": admin_note,
                            "approved_by": admin.get("user_id"),
                        }
                    ),
                    "user_id": admin.get("user_id"),
                },
            )

            # Get the role name for notification
            role_name_query = text("SELECT name FROM roles WHERE id = :role_id")
            role_result = connection.execute(role_name_query, {"role_id": requested_role_id}).fetchone()
            role_name = role_result[0] if role_result else "Unknown Role"

            # Send notification to user
            notification_service.send_role_request_approval_notification(
                user_id=user_id,
                user_name=user_name,
                user_email=user_email,
                role_name=role_name,
                admin_note=admin_note,
                approved_by=admin.get("user_id"),
            )

            return {
                "message": "Role request approved successfully",
                "user_id": user_id,
                "user_name": user_name,
                "user_email": user_email,
                "role_id": str(requested_role_id),
                "notification": "User notified of approval",
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[APPROVE ROLE REQUEST ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not approve role request.")


@router.post("/admin/role-requests/{user_id}/reject")
async def reject_role_request(user_id: str, admin_note: str | None = None, admin: dict = Depends(is_system_admin)):
    """
    Reject a role request.
    """
    try:
        with get_engine().begin() as connection:
            # Get the user's requested role for logging
            user_query = text(
                """
                SELECT id, requested_role_id, name, email, r.name as role_name
                FROM users u
                JOIN roles r ON u.requested_role_id = r.id
                WHERE u.id = :user_id AND u.requested_role_id IS NOT NULL
            """
            )
            user = connection.execute(user_query, {"user_id": user_id}).fetchone()

            if not user:
                raise HTTPException(status_code=404, detail="User not found or no pending role request")

            user_name = user[2]
            user_email = user[3]
            role_name = user[4]

            # Clear the pending request
            connection.execute(
                text("UPDATE users SET requested_role_id = NULL WHERE id = :user_id"), {"user_id": user_id}
            )

            # Log the rejection
            connection.execute(
                text(
                    """
                    INSERT INTO audit_logs
                    (event_type, resource_type, resource_id, details, user_id)
                    VALUES (:event_type, :resource_type, :resource_id, :details, :user_id)
                """
                ),
                {
                    "event_type": "role_request.rejected",
                    "resource_type": "user",
                    "resource_id": user_id,
                    "details": json.dumps(
                        {
                            "requested_role_name": role_name,
                            "admin_note": admin_note,
                            "rejected_by": admin.get("user_id"),
                        }
                    ),
                    "user_id": admin.get("user_id"),
                },
            )

            # Send notification to user
            notification_service.send_role_request_rejection_notification(
                user_id=user_id,
                user_name=user_name,
                user_email=user_email,
                role_name=role_name,
                admin_note=admin_note,
                rejected_by=admin.get("user_id"),
            )

            return {
                "message": "Role request rejected successfully",
                "user_id": user_id,
                "user_name": user_name,
                "user_email": user_email,
                "rejected_role": role_name,
                "notification": "User notified of rejection",
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[REJECT ROLE REQUEST ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not reject role request.")


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

            # Debug: log the number of rows returned
            logger.info(f"Knowledge cards query returned {len(rows)} rows")

            return [
                {
                    "id": str(r["id"]),
                    "title": r["title"],
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
        raise HTTPException(status_code=500, detail=f"Could not list knowledge cards: {str(e)}")


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
