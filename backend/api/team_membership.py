# Standard Library
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
import json

# Internal Modules
from backend.core.db import get_engine
from backend.core.security import get_current_user, is_system_admin

router = APIRouter()


@router.post("/teams/{team_id}/join")
async def request_team_membership(team_id: str, current_user: dict = Depends(get_current_user)):
    """
    Request to join a team. Creates a PENDING membership record.
    """
    try:
        user_id = current_user["user_id"]

        with get_engine().connect() as connection:
            # Check if team exists
            team_exists = connection.execute(
                text("SELECT 1 FROM teams WHERE id = :team_id"), {"team_id": team_id}
            ).fetchone()

            if not team_exists:
                raise HTTPException(status_code=404, detail="Team not found")

            # Check if user is already a member (any status)
            existing_membership = connection.execute(
                text("SELECT status FROM team_members WHERE team_id = :team_id AND user_id = :user_id"),
                {"team_id": team_id, "user_id": user_id},
            ).fetchone()

            if existing_membership:
                if existing_membership[0] == "PENDING":
                    raise HTTPException(
                        status_code=400,
                        detail="You already have a pending membership request for this team",
                    )
                elif existing_membership[0] == "ACTIVE":
                    raise HTTPException(status_code=400, detail="You are already a member of this team")
                elif existing_membership[0] == "REJECTED":
                    # Allow re-requesting if previously rejected
                    connection.execute(
                        text(
                            "UPDATE team_members SET status = 'PENDING' WHERE team_id = :team_id AND user_id = :user_id"
                        ),
                        {"team_id": team_id, "user_id": user_id},
                    )

                return {
                    "message": "Membership request updated successfully",
                    "status": "PENDING",
                }

            # Create new pending membership request
            connection.execute(
                text("INSERT INTO team_members (team_id, user_id, status) VALUES (:team_id, :user_id, 'PENDING')"),
                {"team_id": team_id, "user_id": user_id},
            )

        return {
            "message": "Membership request submitted successfully",
            "status": "PENDING",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit membership request: {str(e)}")


@router.get("/teams/{team_id}/requests")
async def get_team_membership_requests(team_id: str, current_user: dict = Depends(get_current_user)):
    """
    Get pending membership requests for a team.
    Only accessible to team leaders or system admins.
    """
    try:
        user_id = current_user["user_id"]

        with get_engine().connect() as connection:
            # Check if user is admin
            is_admin = connection.execute(
                text(
                    """
                SELECT EXISTS (
                    SELECT 1 FROM user_roles ur
                    JOIN roles r ON ur.role_id = r.id
                    WHERE ur.user_id = :user_id AND r.name = 'system admin'
                )
                """
                ),
                {"user_id": user_id},
            ).scalar()

            # Check if user is team leader
            is_team_leader = connection.execute(
                text(
                    """
                SELECT EXISTS (
                    SELECT 1 FROM team_members tm
                    JOIN team_roles tr ON tm.team_id = tr.team_id
                    WHERE tm.user_id = :user_id
                    AND tm.team_id = :team_id
                    AND tr.role_id = 998  -- TEAM_LEADER role
                    AND tm.status = 'ACTIVE'
                )
                """
                ),
                {"user_id": user_id, "team_id": team_id},
            ).scalar()

            if not is_admin and not is_team_leader:
                raise HTTPException(
                    status_code=403,
                    detail="Only team leaders and administrators can view membership requests",
                )

            # Get pending requests
            requests = connection.execute(
                text(
                    """
                SELECT
                    tm.user_id,
                    u.name as user_name,
                    u.email as user_email,
                    tm.status
                FROM team_members tm
                JOIN users u ON tm.user_id = u.id
                WHERE tm.team_id = :team_id
                AND tm.status = 'PENDING'
                ORDER BY u.name
                """
                ),
                {"team_id": team_id},
            ).fetchall()

        return {
            "team_id": team_id,
            "pending_requests": [
                {
                    "user_id": row[0],
                    "user_name": row[1],
                    "user_email": row[2],
                    "status": row[3],
                }
                for row in requests
            ],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch membership requests: {str(e)}")


@router.post("/teams/{team_id}/approve/{user_id}")
async def approve_team_membership(team_id: str, user_id: str, current_user: dict = Depends(get_current_user)):
    """
    Approve a pending team membership request.
    Only accessible to team leaders or system admins.
    """
    try:
        admin_user_id = current_user["user_id"]

        with get_engine().connect() as connection:
            # Check if user is admin
            is_admin = connection.execute(
                text(
                    """
                SELECT EXISTS (
                    SELECT 1 FROM user_roles ur
                    JOIN roles r ON ur.role_id = r.id
                    WHERE ur.user_id = :user_id AND r.name = 'system admin'
                )
                """
                ),
                {"user_id": admin_user_id},
            ).scalar()

            # Check if user is team leader
            is_team_leader = connection.execute(
                text(
                    """
                SELECT EXISTS (
                    SELECT 1 FROM team_members tm
                    JOIN team_roles tr ON tm.team_id = tr.team_id
                    WHERE tm.user_id = :user_id
                    AND tm.team_id = :team_id
                    AND tr.role_id = 998  -- TEAM_LEADER role
                    AND tm.status = 'ACTIVE'
                )
                """
                ),
                {"user_id": admin_user_id, "team_id": team_id},
            ).scalar()

            if not is_admin and not is_team_leader:
                raise HTTPException(
                    status_code=403,
                    detail="Only team leaders and administrators can approve membership requests",
                )

            # Check if the membership request exists and is pending
            request_exists = connection.execute(
                text(
                    """
                SELECT 1 FROM team_members
                WHERE team_id = :team_id
                AND user_id = :user_id
                AND status = 'PENDING'
                """
                ),
                {"team_id": team_id, "user_id": user_id},
            ).fetchone()

            if not request_exists:
                raise HTTPException(status_code=404, detail="Pending membership request not found")

            # Approve the request
            connection.execute(
                text(
                    """
                UPDATE team_members
                SET status = 'ACTIVE'
                WHERE team_id = :team_id
                AND user_id = :user_id
                """
                ),
                {"team_id": team_id, "user_id": user_id},
            )

            # Log the approval in audit logs
            connection.execute(
                text(
                    """
                INSERT INTO audit_logs
                (event_type, resource_type, resource_id, details, user_id)
                VALUES (:event_type, :resource_type, :resource_id, :details, :user_id)
                """
                ),
                {
                    "event_type": "team_membership.approved",
                    "resource_type": "team_member",
                    "resource_id": f"{team_id}-{user_id}",
                    "details": json.dumps(
                        {
                            "team_id": team_id,
                            "user_id": user_id,
                            "approved_by": admin_user_id,
                        }
                    ),
                    "user_id": admin_user_id,
                },
            )

        return {
            "message": "Team membership approved successfully",
            "team_id": team_id,
            "user_id": user_id,
            "status": "ACTIVE",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to approve team membership: {str(e)}")


@router.post("/teams/{team_id}/reject/{user_id}")
async def reject_team_membership(team_id: str, user_id: str, current_user: dict = Depends(get_current_user)):
    """
    Reject a pending team membership request.
    Only accessible to team leaders or system admins.
    """
    try:
        admin_user_id = current_user["user_id"]

        with get_engine().connect() as connection:
            # Check if user is admin
            is_admin = connection.execute(
                text(
                    """
                SELECT EXISTS (
                    SELECT 1 FROM user_roles ur
                    JOIN roles r ON ur.role_id = r.id
                    WHERE ur.user_id = :user_id AND r.name = 'system admin'
                )
                """
                ),
                {"user_id": admin_user_id},
            ).scalar()

            # Check if user is team leader
            is_team_leader = connection.execute(
                text(
                    """
                SELECT EXISTS (
                    SELECT 1 FROM team_members tm
                    JOIN team_roles tr ON tm.team_id = tr.team_id
                    WHERE tm.user_id = :user_id
                    AND tm.team_id = :team_id
                    AND tr.role_id = 998  -- TEAM_LEADER role
                    AND tm.status = 'ACTIVE'
                )
                """
                ),
                {"user_id": admin_user_id, "team_id": team_id},
            ).scalar()

            if not is_admin and not is_team_leader:
                raise HTTPException(
                    status_code=403,
                    detail="Only team leaders and administrators can reject membership requests",
                )

            # Check if the membership request exists and is pending
            request_exists = connection.execute(
                text(
                    """
                SELECT 1 FROM team_members
                WHERE team_id = :team_id
                AND user_id = :user_id
                AND status = 'PENDING'
                """
                ),
                {"team_id": team_id, "user_id": user_id},
            ).fetchone()

            if not request_exists:
                raise HTTPException(status_code=404, detail="Pending membership request not found")

            # Reject the request
            connection.execute(
                text(
                    """
                UPDATE team_members
                SET status = 'REJECTED'
                WHERE team_id = :team_id
                AND user_id = :user_id
                """
                ),
                {"team_id": team_id, "user_id": user_id},
            )

            # Log the rejection in audit logs
            connection.execute(
                text(
                    """
                INSERT INTO audit_logs
                (event_type, resource_type, resource_id, details, user_id)
                VALUES (:event_type, :resource_type, :resource_id, :details, :user_id)
                """
                ),
                {
                    "event_type": "team_membership.rejected",
                    "resource_type": "team_member",
                    "resource_id": f"{team_id}-{user_id}",
                    "details": json.dumps(
                        {
                            "team_id": team_id,
                            "user_id": user_id,
                            "rejected_by": admin_user_id,
                        }
                    ),
                    "user_id": admin_user_id,
                },
            )

        return {
            "message": "Team membership request rejected successfully",
            "team_id": team_id,
            "user_id": user_id,
            "status": "REJECTED",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reject team membership: {str(e)}")


@router.get("/teams/{team_id}/roles")
async def get_team_roles(team_id: str, current_user: dict = Depends(get_current_user)):
    """
    Get all roles assigned to a team.
    Only accessible to team leaders or system admins.
    """
    try:
        user_id = current_user["user_id"]

        with get_engine().connect() as connection:
            # Check if user is admin
            is_admin = connection.execute(
                text(
                    """
                SELECT EXISTS (
                    SELECT 1 FROM user_roles ur
                    JOIN roles r ON ur.role_id = r.id
                    WHERE ur.user_id = :user_id AND r.name = 'system admin'
                )
                """
                ),
                {"user_id": user_id},
            ).scalar()

            # Check if user is team leader
            is_team_leader = connection.execute(
                text(
                    """
                SELECT EXISTS (
                    SELECT 1 FROM team_members tm
                    JOIN team_roles tr ON tm.team_id = tr.team_id
                    WHERE tm.user_id = :user_id
                    AND tm.team_id = :team_id
                    AND tr.role_id = 998  -- TEAM_LEADER role
                    AND tm.status = 'ACTIVE'
                )
                """
                ),
                {"user_id": user_id, "team_id": team_id},
            ).scalar()

            if not is_admin and not is_team_leader:
                raise HTTPException(
                    status_code=403,
                    detail="Only team leaders and administrators can view team roles",
                )

            # Get team roles
            roles = connection.execute(
                text(
                    """
                SELECT r.id, r.name
                FROM team_roles tr
                JOIN roles r ON tr.role_id = r.id
                WHERE tr.team_id = :team_id
                ORDER BY r.name
                """
                ),
                {"team_id": team_id},
            ).fetchall()

        return {
            "team_id": team_id,
            "roles": [{"role_id": row[0], "role_name": row[1]} for row in roles],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch team roles: {str(e)}")


@router.post("/teams/{team_id}/roles")
async def assign_role_to_team(team_id: str, role_data: dict, admin: dict = Depends(is_system_admin)):
    """
    Assign a role to a team.
    Only accessible to system admins.
    """
    try:
        role_id = role_data.get("role_id")

        if not role_id:
            raise HTTPException(status_code=400, detail="role_id is required")

        with get_engine().connect() as connection:
            # Check if team exists
            team_exists = connection.execute(
                text("SELECT 1 FROM teams WHERE id = :team_id"), {"team_id": team_id}
            ).fetchone()

            if not team_exists:
                raise HTTPException(status_code=404, detail="Team not found")

            # Check if role exists
            role_exists = connection.execute(
                text("SELECT 1 FROM roles WHERE id = :role_id"), {"role_id": role_id}
            ).fetchone()

            if not role_exists:
                raise HTTPException(status_code=404, detail="Role not found")

            # Check if role is already assigned to team
            already_assigned = connection.execute(
                text("SELECT 1 FROM team_roles WHERE team_id = :team_id AND role_id = :role_id"),
                {"team_id": team_id, "role_id": role_id},
            ).fetchone()

            if already_assigned:
                raise HTTPException(status_code=400, detail="Role is already assigned to this team")

            # Assign role to team
            connection.execute(
                text("INSERT INTO team_roles (team_id, role_id) VALUES (:team_id, :role_id)"),
                {"team_id": team_id, "role_id": role_id},
            )

            # Log the assignment
            connection.execute(
                text(
                    """
                INSERT INTO audit_logs
                (event_type, resource_type, resource_id, details, user_id)
                VALUES (:event_type, :resource_type, :resource_id, :details, :user_id)
                """
                ),
                {
                    "event_type": "team_role.assigned",
                    "resource_type": "team_role",
                    "resource_id": f"{team_id}-{role_id}",
                    "details": json.dumps(
                        {
                            "team_id": team_id,
                            "role_id": role_id,
                            "assigned_by": admin["user_id"],
                        }
                    ),
                    "user_id": admin["user_id"],
                },
            )

        return {
            "message": "Role assigned to team successfully",
            "team_id": team_id,
            "role_id": role_id,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to assign role to team: {str(e)}")


@router.delete("/teams/{team_id}/roles/{role_id}")
async def remove_role_from_team(team_id: str, role_id: int, admin: dict = Depends(is_system_admin)):
    """
    Remove a role from a team.
    Only accessible to system admins.
    """
    try:
        with get_engine().connect() as connection:
            # Check if assignment exists
            assignment_exists = connection.execute(
                text("SELECT 1 FROM team_roles WHERE team_id = :team_id AND role_id = :role_id"),
                {"team_id": team_id, "role_id": role_id},
            ).fetchone()

            if not assignment_exists:
                raise HTTPException(status_code=404, detail="Role assignment not found")

            # Remove role from team
            connection.execute(
                text("DELETE FROM team_roles WHERE team_id = :team_id AND role_id = :role_id"),
                {"team_id": team_id, "role_id": role_id},
            )

            # Log the removal
            connection.execute(
                text(
                    """
                INSERT INTO audit_logs
                (event_type, resource_type, resource_id, details, user_id)
                VALUES (:event_type, :resource_type, :resource_id, :details, :user_id)
                """
                ),
                {
                    "event_type": "team_role.removed",
                    "resource_type": "team_role",
                    "resource_id": f"{team_id}-{role_id}",
                    "details": json.dumps(
                        {
                            "team_id": team_id,
                            "role_id": role_id,
                            "removed_by": admin["user_id"],
                        }
                    ),
                    "user_id": admin["user_id"],
                },
            )

        return {
            "message": "Role removed from team successfully",
            "team_id": team_id,
            "role_id": role_id,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove role from team: {str(e)}")
