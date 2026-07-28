import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import JSON, bindparam, inspect, text
from sqlalchemy.exc import IntegrityError

from backend.core.db import get_engine
from backend.core.access_roles import ROLE_REGISTRY
from backend.core.security import get_current_user
from backend.models.access_management import AccessSettingUpsert, TeamCreate, TeamRoleAssignment, TeamUpdate


router = APIRouter()


def _require_admin(current_user: dict[str, Any]) -> None:
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="System administrator access required.")


def _require_team_manager(current_user: dict[str, Any], team_id: str) -> None:
    if current_user.get("is_admin"):
        return
    active_team = current_user.get("active_team") or {}
    if current_user.get("team_leadership") and str(active_team.get("id")) == str(team_id):
        return
    raise HTTPException(status_code=403, detail="Team leader access is required for this team.")


def _audit(connection, actor_id: str, action: str, resource_type: str, resource_id: str, details=None) -> None:
    connection.execute(
        text(
            """
            INSERT INTO resource_access_audit
                (id, resource_type, resource_id, action, actor_id, details)
            VALUES
                (:id, :resource_type, :resource_id, :action, :actor_id, :details)
            """
        ),
        {
            "id": str(uuid.uuid4()),
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action": action,
            "actor_id": actor_id,
            "details": json.dumps(details or {}),
        },
    )


def _setting_payload(row) -> dict[str, Any]:
    value = row[5]
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            pass
    return {
        "id": row[0],
        "user_id": str(row[1]),
        "team_id": str(row[2]),
        "role_key": row[3],
        "key": row[4],
        "value": value,
    }


def create_team_record(request: TeamCreate, current_user: dict[str, Any]) -> dict[str, Any]:
    _require_admin(current_user)
    actor_id = str(current_user["user_id"])
    team_id = str(uuid.uuid4())
    with get_engine().begin() as connection:
        existing = connection.execute(
            text("SELECT 1 FROM teams WHERE lower(name) = lower(:name)"),
            {"name": request.name},
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="A team with this name already exists.")
        connection.execute(
            text(
                "INSERT INTO teams (id, name, description, created_by) "
                "VALUES (:id, :name, :description, :created_by)"
            ),
            {
                "id": team_id,
                "name": request.name,
                "description": request.description,
                "created_by": actor_id,
            },
        )
        _audit(connection, actor_id, "team.created", "team", team_id, {"name": request.name})
    return {"id": team_id, "name": request.name, "description": request.description}


@router.post("/teams", status_code=status.HTTP_201_CREATED)
async def create_team(request: TeamCreate, current_user: dict = Depends(get_current_user)):
    return create_team_record(request, current_user)


@router.get("/teams")
async def list_teams(current_user: dict = Depends(get_current_user)):
    with get_engine().connect() as connection:
        rows = connection.execute(text("SELECT id, name, description FROM teams ORDER BY name")).fetchall()
    return {"teams": [{"id": str(row[0]), "name": row[1], "description": row[2]} for row in rows]}


@router.patch("/teams/{team_id}")
async def update_team(team_id: str, request: TeamUpdate, current_user: dict = Depends(get_current_user)):
    _require_admin(current_user)
    actor_id = str(current_user["user_id"])
    changes = request.model_dump(exclude_unset=True)
    with get_engine().begin() as connection:
        row = connection.execute(
            text("SELECT id, name, description FROM teams WHERE id = :team_id"),
            {"team_id": team_id},
        ).first()
        if not row:
            raise HTTPException(status_code=404, detail="Team not found.")
        name = changes.get("name", row[1])
        description = changes.get("description", row[2])
        duplicate = connection.execute(
            text("SELECT 1 FROM teams WHERE lower(name) = lower(:name) AND id <> :team_id"),
            {"name": name, "team_id": team_id},
        ).first()
        if duplicate:
            raise HTTPException(status_code=409, detail="A team with this name already exists.")
        connection.execute(
            text(
                "UPDATE teams SET name = :name, description = :description, updated_at = CURRENT_TIMESTAMP "
                "WHERE id = :team_id"
            ),
            {"name": name, "description": description, "team_id": team_id},
        )
        _audit(connection, actor_id, "team.updated", "team", team_id, changes)
    return {"id": team_id, "name": name, "description": description}


def _protected_team_resources(connection, team_id: str) -> list[str]:
    protected = []
    if inspect(connection).has_table("proposals"):
        count = connection.execute(
            text("SELECT COUNT(*) FROM proposals WHERE team_id = :team_id"),
            {"team_id": team_id},
        ).scalar()
        if count:
            protected.append("proposals")
    if inspect(connection).has_table("knowledge_cards"):
        count = connection.execute(
            text("SELECT COUNT(*) FROM knowledge_cards WHERE team_id = :team_id"),
            {"team_id": team_id},
        ).scalar()
        if count:
            protected.append("knowledge cards")
    if inspect(connection).has_table("template_registry"):
        count = connection.execute(
            text("SELECT COUNT(*) FROM template_registry WHERE owning_team_id = :team_id"),
            {"team_id": team_id},
        ).scalar()
        if count:
            protected.append("templates")
    return protected


@router.delete("/teams/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(team_id: str, current_user: dict = Depends(get_current_user)):
    _require_admin(current_user)
    actor_id = str(current_user["user_id"])
    with get_engine().begin() as connection:
        exists = connection.execute(text("SELECT 1 FROM teams WHERE id = :team_id"), {"team_id": team_id}).first()
        if not exists:
            raise HTTPException(status_code=404, detail="Team not found.")
        protected = _protected_team_resources(connection, team_id)
        if protected:
            raise HTTPException(
                status_code=409,
                detail={"message": "Team owns protected resources.", "resources": protected},
            )
        _audit(connection, actor_id, "team.deleted", "team", team_id)
        try:
            connection.execute(text("DELETE FROM teams WHERE id = :team_id"), {"team_id": team_id})
        except IntegrityError as exc:
            raise HTTPException(status_code=409, detail="Team still has dependent resources.") from exc
    return None


@router.get("/teams/{team_id}/members")
async def list_members(team_id: str, current_user: dict = Depends(get_current_user)):
    _require_team_manager(current_user, team_id)
    with get_engine().connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT tm.user_id, u.name, u.email, tm.status,
                       EXISTS (
                           SELECT 1 FROM team_member_roles tmr
                           WHERE tmr.team_id = tm.team_id
                             AND tmr.user_id = tm.user_id
                             AND tmr.role_key = 'TEAM_LEADER'
                       ) AS is_leader
                FROM team_members tm
                JOIN users u ON u.id = tm.user_id
                WHERE tm.team_id = :team_id AND tm.status = 'ACTIVE'
                ORDER BY u.name, u.email
                """
            ),
            {"team_id": team_id},
        ).fetchall()
    return {
        "team_id": team_id,
        "members": [
            {
                "user_id": str(row[0]),
                "name": row[1],
                "email": row[2],
                "status": row[3],
                "is_leader": bool(row[4]),
            }
            for row in rows
        ],
    }


@router.post("/teams/{team_id}/members/{user_id}", status_code=status.HTTP_201_CREATED)
async def add_member(team_id: str, user_id: str, current_user: dict = Depends(get_current_user)):
    _require_admin(current_user)
    actor_id = str(current_user["user_id"])
    with get_engine().begin() as connection:
        if not connection.execute(text("SELECT 1 FROM teams WHERE id = :id"), {"id": team_id}).first():
            raise HTTPException(status_code=404, detail="Team not found.")
        if not connection.execute(text("SELECT 1 FROM users WHERE id = :id"), {"id": user_id}).first():
            raise HTTPException(status_code=404, detail="User not found.")
        existing = connection.execute(
            text("SELECT status FROM team_members WHERE team_id = :team_id AND user_id = :user_id"),
            {"team_id": team_id, "user_id": user_id},
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail=f"Membership is already {existing[0]}.")
        connection.execute(
            text("INSERT INTO team_members (team_id, user_id, status) " "VALUES (:team_id, :user_id, 'ACTIVE')"),
            {"team_id": team_id, "user_id": user_id},
        )
        _audit(
            connection,
            actor_id,
            "team_member.added",
            "team_member",
            f"{team_id}:{user_id}",
            {"team_id": team_id, "user_id": user_id},
        )
    return {"team_id": team_id, "user_id": user_id, "status": "ACTIVE"}


@router.delete("/teams/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(team_id: str, user_id: str, current_user: dict = Depends(get_current_user)):
    _require_admin(current_user)
    actor_id = str(current_user["user_id"])
    with get_engine().begin() as connection:
        existing = connection.execute(
            text("SELECT status FROM team_members WHERE team_id = :team_id AND user_id = :user_id"),
            {"team_id": team_id, "user_id": user_id},
        ).first()
        if not existing:
            raise HTTPException(status_code=404, detail="Membership not found.")
        connection.execute(
            text("DELETE FROM team_members WHERE team_id = :team_id AND user_id = :user_id"),
            {"team_id": team_id, "user_id": user_id},
        )
        _audit(
            connection,
            actor_id,
            "team_member.removed",
            "team_member",
            f"{team_id}:{user_id}",
            {"previous_status": existing[0]},
        )
    return None


@router.post("/teams/{team_id}/join")
async def join_team(team_id: str, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["user_id"])
    with get_engine().begin() as connection:
        if not connection.execute(text("SELECT 1 FROM teams WHERE id = :id"), {"id": team_id}).first():
            raise HTTPException(status_code=404, detail="Team not found.")
        existing = connection.execute(
            text("SELECT status FROM team_members WHERE team_id = :team_id AND user_id = :user_id"),
            {"team_id": team_id, "user_id": user_id},
        ).first()
        if existing and existing[0] in {"PENDING", "ACTIVE"}:
            raise HTTPException(status_code=409, detail=f"Membership is already {existing[0]}.")
        if existing:
            connection.execute(
                text("UPDATE team_members SET status = 'PENDING' " "WHERE team_id = :team_id AND user_id = :user_id"),
                {"team_id": team_id, "user_id": user_id},
            )
        else:
            connection.execute(
                text("INSERT INTO team_members (team_id, user_id, status) " "VALUES (:team_id, :user_id, 'PENDING')"),
                {"team_id": team_id, "user_id": user_id},
            )
        _audit(
            connection,
            user_id,
            "team_membership.requested",
            "team_member",
            f"{team_id}:{user_id}",
        )
    return {"team_id": team_id, "user_id": user_id, "status": "PENDING"}


@router.get("/teams/{team_id}/requests")
async def list_requests(team_id: str, current_user: dict = Depends(get_current_user)):
    _require_team_manager(current_user, team_id)
    with get_engine().connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT tm.user_id, u.name, u.email, tm.status
                FROM team_members tm
                JOIN users u ON u.id = tm.user_id
                WHERE tm.team_id = :team_id AND tm.status = 'PENDING'
                ORDER BY u.name, u.email
                """
            ),
            {"team_id": team_id},
        ).fetchall()
    return {
        "team_id": team_id,
        "pending_requests": [
            {
                "user_id": str(row[0]),
                "user_name": row[1],
                "user_email": row[2],
                "status": row[3],
            }
            for row in rows
        ],
    }


def _decide_request(team_id: str, user_id: str, decision: str, current_user: dict[str, Any]):
    _require_team_manager(current_user, team_id)
    actor_id = str(current_user["user_id"])
    with get_engine().begin() as connection:
        current = connection.execute(
            text("SELECT status FROM team_members WHERE team_id = :team_id AND user_id = :user_id"),
            {"team_id": team_id, "user_id": user_id},
        ).first()
        if not current or current[0] != "PENDING":
            raise HTTPException(status_code=409, detail="Membership request is not pending.")
        connection.execute(
            text("UPDATE team_members SET status = :decision " "WHERE team_id = :team_id AND user_id = :user_id"),
            {"decision": decision, "team_id": team_id, "user_id": user_id},
        )
        _audit(
            connection,
            actor_id,
            f"team_membership.{decision.lower()}",
            "team_member",
            f"{team_id}:{user_id}",
        )
    return {"team_id": team_id, "user_id": user_id, "status": decision}


@router.post("/teams/{team_id}/approve/{user_id}")
async def approve_request(team_id: str, user_id: str, current_user: dict = Depends(get_current_user)):
    return _decide_request(team_id, user_id, "ACTIVE", current_user)


@router.post("/teams/{team_id}/reject/{user_id}")
async def reject_request(team_id: str, user_id: str, current_user: dict = Depends(get_current_user)):
    return _decide_request(team_id, user_id, "REJECTED", current_user)


@router.put("/teams/{team_id}/leaders/{user_id}")
async def assign_leader(team_id: str, user_id: str, current_user: dict = Depends(get_current_user)):
    _require_admin(current_user)
    actor_id = str(current_user["user_id"])
    with get_engine().begin() as connection:
        membership = connection.execute(
            text("SELECT status FROM team_members WHERE team_id = :team_id AND user_id = :user_id"),
            {"team_id": team_id, "user_id": user_id},
        ).first()
        if not membership or membership[0] != "ACTIVE":
            raise HTTPException(status_code=409, detail="Team leadership requires an active membership.")
        existing = connection.execute(
            text(
                "SELECT 1 FROM team_member_roles "
                "WHERE team_id = :team_id AND user_id = :user_id AND role_key = 'TEAM_LEADER'"
            ),
            {"team_id": team_id, "user_id": user_id},
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="User is already a team leader.")
        connection.execute(
            text(
                "INSERT INTO team_member_roles (team_id, user_id, role_key, assigned_by) "
                "VALUES (:team_id, :user_id, 'TEAM_LEADER', :assigned_by)"
            ),
            {"team_id": team_id, "user_id": user_id, "assigned_by": actor_id},
        )
        _audit(
            connection,
            actor_id,
            "team_leader.assigned",
            "team_member_role",
            f"{team_id}:{user_id}:TEAM_LEADER",
        )
    return {"team_id": team_id, "user_id": user_id, "role_key": "TEAM_LEADER"}


@router.delete("/teams/{team_id}/leaders/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_leader(team_id: str, user_id: str, current_user: dict = Depends(get_current_user)):
    _require_admin(current_user)
    actor_id = str(current_user["user_id"])
    with get_engine().begin() as connection:
        existing = connection.execute(
            text(
                "SELECT 1 FROM team_member_roles "
                "WHERE team_id = :team_id AND user_id = :user_id AND role_key = 'TEAM_LEADER'"
            ),
            {"team_id": team_id, "user_id": user_id},
        ).first()
        if not existing:
            raise HTTPException(status_code=404, detail="Team leader assignment not found.")
        connection.execute(
            text(
                "DELETE FROM team_member_roles "
                "WHERE team_id = :team_id AND user_id = :user_id AND role_key = 'TEAM_LEADER'"
            ),
            {"team_id": team_id, "user_id": user_id},
        )
        _audit(
            connection,
            actor_id,
            "team_leader.removed",
            "team_member_role",
            f"{team_id}:{user_id}:TEAM_LEADER",
        )
    return None


@router.get("/roles")
async def list_roles(current_user: dict = Depends(get_current_user)):
    with get_engine().connect() as connection:
        rows = connection.execute(
            text("SELECT id, name, role_key FROM roles WHERE role_key IS NOT NULL ORDER BY name")
        ).fetchall()
    return {
        "roles": [
            {
                "id": row[0],
                "name": row[1],
                "role_key": row[2],
                "component": ROLE_REGISTRY[row[2]].component,
            }
            for row in rows
            if row[2] in ROLE_REGISTRY
        ]
    }


@router.get("/teams/{team_id}/roles")
async def list_team_roles(team_id: str, current_user: dict = Depends(get_current_user)):
    _require_team_manager(current_user, team_id)
    with get_engine().connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT r.id, r.name, tr.role_key, r.component
                FROM team_roles tr
                JOIN roles r ON r.id = tr.role_id AND r.role_key = tr.role_key
                WHERE tr.team_id = :team_id
                ORDER BY r.name
                """
            ),
            {"team_id": team_id},
        ).fetchall()
    return {
        "team_id": team_id,
        "roles": [
            {
                "id": row[0],
                "name": row[1],
                "role_id": row[0],
                "role_name": row[1],
                "role_key": row[2],
                "component": row[3],
            }
            for row in rows
        ],
    }


@router.post("/teams/{team_id}/roles", status_code=status.HTTP_201_CREATED)
async def assign_team_role(
    team_id: str,
    request: TeamRoleAssignment,
    current_user: dict = Depends(get_current_user),
):
    _require_admin(current_user)
    actor_id = str(current_user["user_id"])
    with get_engine().begin() as connection:
        if not connection.execute(text("SELECT 1 FROM teams WHERE id = :id"), {"id": team_id}).first():
            raise HTTPException(status_code=404, detail="Team not found.")
        if request.role_key is not None:
            role_row = connection.execute(
                text("SELECT id, name, role_key, component FROM roles WHERE role_key = :role_key"),
                {"role_key": request.role_key},
            ).first()
        else:
            role_row = connection.execute(
                text("SELECT id, name, role_key, component FROM roles WHERE id = :role_id"),
                {"role_id": request.role_id},
            ).first()
        if not role_row:
            raise HTTPException(status_code=404, detail="Static role is not installed.")
        resolved_role_key = str(role_row[2])
        role = ROLE_REGISTRY.get(resolved_role_key)
        if role is None or role.component is None:
            raise HTTPException(status_code=422, detail="Only static component roles may be assigned to teams.")
        existing = connection.execute(
            text("SELECT 1 FROM team_roles WHERE team_id = :team_id AND role_key = :role_key"),
            {"team_id": team_id, "role_key": resolved_role_key},
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Role is already assigned to this team.")
        connection.execute(
            text("INSERT INTO team_roles (team_id, role_id, role_key) " "VALUES (:team_id, :role_id, :role_key)"),
            {"team_id": team_id, "role_id": role_row[0], "role_key": resolved_role_key},
        )
        _audit(
            connection,
            actor_id,
            "team_role.assigned",
            "team_role",
            f"{team_id}:{resolved_role_key}",
        )
    return {
        "team_id": team_id,
        "id": role_row[0],
        "name": role_row[1],
        "role_key": resolved_role_key,
        "component": role_row[3],
    }


@router.delete("/teams/{team_id}/roles/{role_key}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_team_role(team_id: str, role_key: str, current_user: dict = Depends(get_current_user)):
    _require_admin(current_user)
    actor_id = str(current_user["user_id"])
    with get_engine().begin() as connection:
        resolved_role_key = role_key
        if role_key.isdigit():
            legacy_role = connection.execute(
                text("SELECT role_key FROM roles WHERE id = :role_id"), {"role_id": int(role_key)}
            ).first()
            if not legacy_role:
                raise HTTPException(status_code=404, detail="Team role assignment not found.")
            resolved_role_key = str(legacy_role[0])
        existing = connection.execute(
            text("SELECT 1 FROM team_roles WHERE team_id = :team_id AND role_key = :role_key"),
            {"team_id": team_id, "role_key": resolved_role_key},
        ).first()
        if not existing:
            raise HTTPException(status_code=404, detail="Team role assignment not found.")
        connection.execute(
            text("DELETE FROM team_roles WHERE team_id = :team_id AND role_key = :role_key"),
            {"team_id": team_id, "role_key": resolved_role_key},
        )
        _audit(
            connection,
            actor_id,
            "team_role.removed",
            "team_role",
            f"{team_id}:{resolved_role_key}",
        )
    return None


@router.get("/settings")
async def list_access_settings(
    user_id: str | None = Query(default=None),
    team_id: str | None = Query(default=None),
    role_key: str | None = Query(default=None),
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("is_admin"):
        selected_user_id = user_id
        selected_team_id = team_id
        authorized_roles: set[str] | None = None
    else:
        if user_id is not None or team_id is not None or role_key is not None:
            raise HTTPException(status_code=403, detail="Only administrators may query another access scope.")
        active_team = current_user.get("active_team") or {}
        selected_user_id = str(current_user["user_id"])
        selected_team_id = active_team.get("id")
        if selected_team_id is None:
            return {"settings": []}
        authorized_roles = {str(value) for value in (current_user.get("role_keys") or current_user.get("roles") or [])}

    conditions = []
    parameters: dict[str, Any] = {}
    if selected_user_id is not None:
        conditions.append("user_id = :user_id")
        parameters["user_id"] = selected_user_id
    if selected_team_id is not None:
        conditions.append("team_id = :team_id")
        parameters["team_id"] = selected_team_id
    if role_key is not None:
        conditions.append("role_key = :role_key")
        parameters["role_key"] = role_key
    where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""

    with get_engine().connect() as connection:
        rows = connection.execute(
            text(
                "SELECT id, user_id, team_id, role_key, key, value FROM access_settings"
                f"{where_clause} ORDER BY role_key, key, id"
            ),
            parameters,
        ).fetchall()
    if authorized_roles is not None:
        rows = [row for row in rows if str(row[3]) in authorized_roles]
    return {"settings": [_setting_payload(row) for row in rows]}


@router.post("/settings", status_code=status.HTTP_201_CREATED)
async def upsert_access_setting(
    request: AccessSettingUpsert,
    response: Response,
    current_user: dict = Depends(get_current_user),
):
    _require_admin(current_user)
    actor_id = str(current_user["user_id"])
    with get_engine().begin() as connection:
        membership = connection.execute(
            text("SELECT 1 FROM team_members WHERE user_id = :user_id " "AND team_id = :team_id AND status = 'ACTIVE'"),
            {"user_id": request.user_id, "team_id": request.team_id},
        ).first()
        if not membership:
            raise HTTPException(status_code=422, detail="User must be an active member of the selected team.")

        assigned_role = connection.execute(
            text("SELECT 1 FROM team_roles WHERE team_id = :team_id AND role_key = :role_key"),
            {"team_id": request.team_id, "role_key": request.role_key},
        ).first()
        if not assigned_role:
            raise HTTPException(status_code=422, detail="Role must be assigned to the selected team.")

        existing_id = connection.execute(
            text(
                "SELECT id FROM access_settings WHERE user_id = :user_id AND team_id = :team_id "
                "AND role_key = :role_key AND key = :key"
            ),
            request.model_dump(exclude={"value"}),
        ).scalar()
        value_statement = bindparam("value", type_=JSON)
        parameters = request.model_dump()
        parameters["created_by"] = actor_id
        if existing_id is None:
            insert_statement = text(
                "INSERT INTO access_settings "
                "(user_id, team_id, role_key, key, value, created_by) "
                "VALUES (:user_id, :team_id, :role_key, :key, :value, :created_by) RETURNING id"
            ).bindparams(value_statement)
            setting_id = connection.execute(insert_statement, parameters).scalar_one()
            action = "access_setting.created"
        else:
            update_statement = text(
                "UPDATE access_settings SET value = :value, created_by = :created_by, "
                "updated_at = CURRENT_TIMESTAMP WHERE id = :id"
            ).bindparams(value_statement)
            connection.execute(
                update_statement,
                {"value": request.value, "created_by": actor_id, "id": existing_id},
            )
            setting_id = existing_id
            response.status_code = status.HTTP_200_OK
            action = "access_setting.updated"
        _audit(connection, actor_id, action, "access_setting", str(setting_id))

    return {"id": setting_id, **request.model_dump()}


@router.delete("/settings/{setting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_access_setting(setting_id: int, current_user: dict = Depends(get_current_user)):
    _require_admin(current_user)
    actor_id = str(current_user["user_id"])
    with get_engine().begin() as connection:
        existing = connection.execute(text("SELECT 1 FROM access_settings WHERE id = :id"), {"id": setting_id}).first()
        if not existing:
            raise HTTPException(status_code=404, detail="Access setting not found.")
        connection.execute(text("DELETE FROM access_settings WHERE id = :id"), {"id": setting_id})
        _audit(connection, actor_id, "access_setting.deleted", "access_setting", str(setting_id))
    return None
