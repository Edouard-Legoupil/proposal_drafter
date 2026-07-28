"""Administrative object-level access management endpoints."""

import json
import logging
import uuid
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import JSON, bindparam, text

from backend.core.db import get_engine
from backend.core.security import is_system_admin

router = APIRouter(prefix="/admin", tags=["Admin Resource Access"])
logger = logging.getLogger(__name__)

RESOURCE_CONFIG = {
    "proposals": {"table": "proposals", "owner": "user_id", "label": "proposal"},
    "knowledge-cards": {"table": "knowledge_cards", "owner": "created_by", "label": "knowledge_card"},
    "templates": {"table": "templates", "owner": "created_by", "label": "template"},
}
PERMISSIONS = {
    "proposals": {"read", "edit", "delete"},
    "knowledge-cards": {"read", "edit", "delete"},
    "templates": {"read", "edit", "delete"},
}
OPERATIONS = {
    "proposals": {"GET": "read", "PUT": "edit", "PATCH": "edit", "DELETE": "delete"},
    "knowledge-cards": {"GET": "read", "PUT": "edit", "PATCH": "edit", "DELETE": "delete"},
    "templates": {"view": "read", "edit": "edit", "delete": "delete"},
}
RESOURCE_ROLES = {
    "proposals": {"proposal writer", "project reviewer"},
    "knowledge-cards": {
        "knowledge manager donors",
        "knowledge manager outcome",
        "knowledge manager field context",
    },
    "templates": {"access_template"},
}


class GrantRequest(BaseModel):
    subject_type: Literal["team"] = "team"
    subject_id: uuid.UUID
    permissions: list[str] = Field(min_length=1)
    data_scope: Literal["team"] = "team"

    @model_validator(mode="before")
    @classmethod
    def accept_frontend_casing(cls, values: Any):
        if isinstance(values, dict):
            values = dict(values)
            values.setdefault("subject_type", values.get("subjectType", "team"))
            values.setdefault("subject_id", values.get("subjectId"))
            values["data_scope"] = "team"
        return values


class RevokeRequest(BaseModel):
    grant_id: uuid.UUID


class AccessTestRequest(BaseModel):
    subject_type: Literal["team"] = "team"
    subject_id: uuid.UUID
    operation: str = Field(min_length=1)

    @model_validator(mode="before")
    @classmethod
    def accept_frontend_casing(cls, values: Any):
        if isinstance(values, dict):
            values = dict(values)
            values.setdefault("subject_type", values.get("subjectType", "team"))
            values.setdefault("subject_id", values.get("subjectId"))
        return values


class OwnerRequest(BaseModel):
    owner_id: uuid.UUID


class VisibilityRequest(BaseModel):
    visibility: Literal["private", "organization", "restricted"]


def _config(resource: str) -> dict[str, str]:
    config = RESOURCE_CONFIG.get(resource)
    if config is None:
        raise HTTPException(status_code=404, detail="Unsupported resource type")
    return config


def _decode_json(value: Any, default: Any):
    if value is None:
        return default
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return default
    return value


def _resource(connection, resource: str, resource_id: str):
    config = _config(resource)
    row = (
        connection.execute(
            text(
                f"SELECT r.*, u.id AS owner_id, u.name AS owner_name, u.email AS owner_email "
                f"FROM {config['table']} r LEFT JOIN users u ON r.{config['owner']} = u.id WHERE r.id = :id"
            ),
            {"id": resource_id},
        )
        .mappings()
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail=f"{config['label'].replace('_', ' ').title()} not found")
    return row


def _serialize_resource(resource: str, row) -> dict[str, Any]:
    data = {
        "id": str(row["id"]),
        "status": row.get("status"),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
        "owner": {
            "id": str(row["owner_id"]) if row.get("owner_id") else None,
            "name": row.get("owner_name"),
            "email": row.get("owner_email"),
        },
    }
    if resource == "proposals":
        form_data = _decode_json(row.get("form_data"), {})
        data["title"] = form_data.get("projectTitle") or form_data.get("title") or str(row["id"])
    elif resource == "knowledge-cards":
        data["title"] = row.get("summary") or str(row["id"])
    else:
        data["title"] = row.get("name") or str(row["id"])
    return data


def _grant_dict(row) -> dict[str, Any]:
    return {
        "id": str(row["id"]),
        "subject_type": row["subject_type"],
        "subject_id": str(row["subject_id"]),
        "permissions": _decode_json(row["permissions"], []),
        "data_scope": row["data_scope"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _record_audit(connection, resource: str, resource_id: str, action: str, actor_id: str, details: dict):
    statement = text(
        "INSERT INTO resource_access_audit "
        "(id, resource_type, resource_id, action, actor_id, details, created_at) "
        "VALUES (:id, :resource_type, :resource_id, :action, :actor_id, :details, CURRENT_TIMESTAMP)"
    ).bindparams(bindparam("details", type_=JSON))
    connection.execute(
        statement,
        {
            "id": str(uuid.uuid4()),
            "resource_type": resource,
            "resource_id": resource_id,
            "action": action,
            "actor_id": actor_id,
            "details": details,
        },
    )


@router.get("/{resource}/{resource_id}/access")
def get_resource_access(resource: str, resource_id: str, admin: dict = Depends(is_system_admin)):
    config = _config(resource)
    with get_engine().connect() as connection:
        row = _resource(connection, resource, resource_id)
        grants = (
            connection.execute(
                text(
                    "SELECT * FROM resource_access_grants "
                    "WHERE resource_type = :resource_type AND resource_id = :resource_id ORDER BY created_at"
                ),
                {"resource_type": resource, "resource_id": resource_id},
            )
            .mappings()
            .all()
        )
        audit = (
            connection.execute(
                text(
                    "SELECT * FROM resource_access_audit "
                    "WHERE resource_type = :resource_type AND resource_id = :resource_id "
                    "ORDER BY created_at DESC LIMIT 50"
                ),
                {"resource_type": resource, "resource_id": resource_id},
            )
            .mappings()
            .all()
        )
        settings = (
            connection.execute(
                text(
                    "SELECT visibility FROM resource_access_settings "
                    "WHERE resource_type = :resource_type AND resource_id = :resource_id"
                ),
                {"resource_type": resource, "resource_id": resource_id},
            )
            .mappings()
            .first()
        )

    result: dict[str, Any] = {
        config["label"]: _serialize_resource(resource, row),
        "grants": [_grant_dict(grant) for grant in grants],
        "audit": [
            {
                "id": str(event["id"]),
                "action": event["action"],
                "actor_id": str(event["actor_id"]),
                "details": _decode_json(event["details"], {}),
                "created_at": event["created_at"],
            }
            for event in audit
        ],
    }
    if resource == "templates":
        result["template"]["visibility"] = settings["visibility"] if settings else "private"
    return result


@router.post("/{resource}/{resource_id}/access", status_code=status.HTTP_201_CREATED)
def grant_resource_access(
    resource: str,
    resource_id: str,
    request: GrantRequest,
    admin: dict = Depends(is_system_admin),
):
    allowed = PERMISSIONS.get(resource)
    if allowed is None:
        raise HTTPException(status_code=404, detail="Unsupported resource type")
    invalid = set(request.permissions) - allowed
    if invalid:
        raise HTTPException(status_code=422, detail=f"Unsupported permissions: {sorted(invalid)}")

    actor_id = str(admin["user_id"])
    grant_id = str(uuid.uuid4())
    with get_engine().begin() as connection:
        _resource(connection, resource, resource_id)
        if (
            connection.execute(text("SELECT id FROM teams WHERE id = :id"), {"id": str(request.subject_id)}).first()
            is None
        ):
            raise HTTPException(status_code=404, detail="Team not found")
        existing = connection.execute(
            text(
                "SELECT id FROM resource_access_grants WHERE resource_type = :resource_type "
                "AND resource_id = :resource_id AND subject_type = :subject_type AND subject_id = :subject_id"
            ),
            {
                "resource_type": resource,
                "resource_id": resource_id,
                "subject_type": request.subject_type,
                "subject_id": str(request.subject_id),
            },
        ).scalar()
        if existing:
            grant_id = str(existing)
            update_statement = text(
                "UPDATE resource_access_grants SET permissions = :permissions, data_scope = :data_scope, "
                "updated_at = CURRENT_TIMESTAMP WHERE id = :id"
            ).bindparams(bindparam("permissions", type_=JSON))
            connection.execute(
                update_statement,
                {"permissions": request.permissions, "data_scope": request.data_scope, "id": grant_id},
            )
        else:
            insert_statement = text(
                "INSERT INTO resource_access_grants "
                "(id, resource_type, resource_id, subject_type, subject_id, permissions, data_scope, "
                "created_by, created_at, updated_at) VALUES (:id, :resource_type, :resource_id, "
                ":subject_type, :subject_id, :permissions, :data_scope, :created_by, "
                "CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
            ).bindparams(bindparam("permissions", type_=JSON))
            connection.execute(
                insert_statement,
                {
                    "id": grant_id,
                    "resource_type": resource,
                    "resource_id": resource_id,
                    "subject_type": request.subject_type,
                    "subject_id": str(request.subject_id),
                    "permissions": request.permissions,
                    "data_scope": request.data_scope,
                    "created_by": actor_id,
                },
            )
        _record_audit(connection, resource, resource_id, "grant_updated", actor_id, request.model_dump(mode="json"))
        row = (
            connection.execute(text("SELECT * FROM resource_access_grants WHERE id = :id"), {"id": grant_id})
            .mappings()
            .one()
        )
    return {"grant": _grant_dict(row)}


@router.delete("/{resource}/{resource_id}/access")
def revoke_resource_access(
    resource: str,
    resource_id: str,
    request: RevokeRequest,
    admin: dict = Depends(is_system_admin),
):
    actor_id = str(admin["user_id"])
    with get_engine().begin() as connection:
        _resource(connection, resource, resource_id)
        deleted = connection.execute(
            text(
                "DELETE FROM resource_access_grants WHERE id = :id AND resource_type = :resource_type "
                "AND resource_id = :resource_id RETURNING id"
            ),
            {"id": str(request.grant_id), "resource_type": resource, "resource_id": resource_id},
        ).first()
        if deleted is None:
            raise HTTPException(status_code=404, detail="Grant not found")
        _record_audit(connection, resource, resource_id, "grant_revoked", actor_id, {"grant_id": str(request.grant_id)})
    return {"message": "Access grant revoked"}


def _effective_access(connection, resource: str, resource_id: str, request: AccessTestRequest):
    _resource(connection, resource, resource_id)
    permission = OPERATIONS.get(resource, {}).get(request.operation)
    if permission is None:
        raise HTTPException(status_code=422, detail="Unsupported operation")
    team_id = str(request.subject_id)
    team_roles = set(
        connection.execute(
            text("SELECT role_key FROM team_roles WHERE team_id = :team_id"), {"team_id": team_id}
        ).scalars()
    )
    if team_roles.isdisjoint(RESOURCE_ROLES[resource]):
        return False, permission, "missing_component_role"

    grants = connection.execute(
        text(
            "SELECT permissions FROM resource_access_grants WHERE resource_type = :resource_type "
            "AND resource_id = :resource_id AND subject_type = 'team' AND subject_id = :team_id"
        ),
        {"resource_type": resource, "resource_id": resource_id, "team_id": team_id},
    ).scalars()
    if any(permission in _decode_json(value, []) for value in grants):
        return True, permission, "team_grant"
    return False, permission, "no_matching_grant"


@router.post("/{resource}/{resource_id}/access/test")
def test_resource_access(
    resource: str,
    resource_id: str,
    request: AccessTestRequest,
    admin: dict = Depends(is_system_admin),
):
    with get_engine().connect() as connection:
        allowed, permission, reason = _effective_access(connection, resource, resource_id, request)
    return {"allowed": allowed, "permission": permission, "reason": reason}


@router.post("/{resource}/{resource_id}/owner")
def transfer_resource_owner(
    resource: str,
    resource_id: str,
    request: OwnerRequest,
    admin: dict = Depends(is_system_admin),
):
    if resource not in {"proposals", "knowledge-cards"}:
        raise HTTPException(status_code=404, detail="Ownership transfer is not supported for this resource")
    config = _config(resource)
    actor_id = str(admin["user_id"])
    with get_engine().begin() as connection:
        _resource(connection, resource, resource_id)
        new_owner = connection.execute(
            text("SELECT id FROM users WHERE id = :id"), {"id": str(request.owner_id)}
        ).first()
        if new_owner is None:
            raise HTTPException(status_code=404, detail="New owner not found")
        connection.execute(
            text(f"UPDATE {config['table']} SET {config['owner']} = :owner_id WHERE id = :resource_id"),
            {"owner_id": str(request.owner_id), "resource_id": resource_id},
        )
        _record_audit(
            connection, resource, resource_id, "owner_transferred", actor_id, {"owner_id": str(request.owner_id)}
        )
    return {"message": "Ownership transferred", "owner_id": str(request.owner_id)}


@router.post("/templates/{resource_id}/visibility")
def update_template_visibility(
    resource_id: str,
    request: VisibilityRequest,
    admin: dict = Depends(is_system_admin),
):
    actor_id = str(admin["user_id"])
    with get_engine().begin() as connection:
        _resource(connection, "templates", resource_id)
        existing = connection.execute(
            text(
                "SELECT resource_id FROM resource_access_settings "
                "WHERE resource_type = 'templates' AND resource_id = :resource_id"
            ),
            {"resource_id": resource_id},
        ).first()
        if existing:
            connection.execute(
                text(
                    "UPDATE resource_access_settings SET visibility = :visibility, updated_at = CURRENT_TIMESTAMP "
                    "WHERE resource_type = 'templates' AND resource_id = :resource_id"
                ),
                {"visibility": request.visibility, "resource_id": resource_id},
            )
        else:
            connection.execute(
                text(
                    "INSERT INTO resource_access_settings "
                    "(resource_type, resource_id, visibility, updated_by, updated_at) "
                    "VALUES ('templates', :resource_id, :visibility, :updated_by, CURRENT_TIMESTAMP)"
                ),
                {"resource_id": resource_id, "visibility": request.visibility, "updated_by": actor_id},
            )
        _record_audit(
            connection,
            "templates",
            resource_id,
            "visibility_updated",
            actor_id,
            {"visibility": request.visibility},
        )
    return {"message": "Visibility updated", "visibility": request.visibility}
