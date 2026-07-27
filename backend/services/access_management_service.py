import json
from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException
from sqlalchemy import text


def _normalized_role(role: str) -> str:
    return role.lower().replace("_", " ").strip()


@dataclass
class AccessContext:
    user_id: str
    memberships: list[dict[str, str]]
    active_team: dict[str, str] | None
    roles: set[str]
    role_keys: set[str]
    team_leadership: bool
    settings: dict[str, dict[str, Any]]
    is_admin: bool


class AccessManagementService:
    """Resolve the least-privilege access context for one active team."""

    def __init__(self, bind):
        if hasattr(bind, "connect") and not hasattr(bind, "execute"):
            self.connection = bind.connect()
            self._owns_connection = True
        else:
            self.connection = bind
            self._owns_connection = False

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc_value, _traceback):
        if self._owns_connection:
            self.connection.close()

    def resolve_active_memberships(self, user_id: str) -> list[dict[str, str]]:
        rows = self.connection.execute(
            text(
                "SELECT t.id, t.name FROM team_members tm "
                "JOIN teams t ON t.id = tm.team_id "
                "WHERE tm.user_id = :user_id AND tm.status = 'ACTIVE' "
                "ORDER BY t.id"
            ),
            {"user_id": user_id},
        ).fetchall()
        return [{"id": str(row[0]), "name": row[1]} for row in rows]

    def select_active_team(
        self,
        memberships: list[dict[str, str]],
        requested_team_id: str | None,
        is_admin: bool = False,
    ) -> dict[str, str] | None:
        if requested_team_id is None:
            return memberships[0] if memberships else None

        selected = next(
            (membership for membership in memberships if membership["id"] == str(requested_team_id)),
            None,
        )
        if selected is None and is_admin:
            row = self.connection.execute(
                text("SELECT id, name FROM teams WHERE id = :team_id"),
                {"team_id": str(requested_team_id)},
            ).first()
            return {"id": str(row[0]), "name": row[1]} if row else None
        if selected is None:
            raise HTTPException(status_code=403, detail="Selected team is not an active membership.")
        return selected

    def get_team_roles(self, team_id: str | None) -> tuple[set[str], set[str]]:
        if team_id is None:
            return set(), set()

        rows = self.connection.execute(
            text(
                "SELECT DISTINCT r.name, r.role_key FROM team_roles tr "
                "JOIN roles r ON r.id = tr.role_id "
                "WHERE tr.team_id = :team_id AND r.component IS NOT NULL"
            ),
            {"team_id": team_id},
        ).fetchall()
        ordinary_rows = [
            row for row in rows if _normalized_role(str(row[1] or row[0])) not in {"system admin", "team leader"}
        ]
        return (
            {str(row[0]) for row in ordinary_rows},
            {str(row[1] or row[0]) for row in ordinary_rows},
        )

    def is_team_leader(self, user_id: str, team_id: str | None) -> bool:
        if team_id is None:
            return False
        return bool(
            self.connection.execute(
                text(
                    "SELECT 1 FROM team_member_roles tmr "
                    "JOIN team_members tm ON tm.team_id = tmr.team_id AND tm.user_id = tmr.user_id "
                    "WHERE tmr.user_id = :user_id AND tmr.team_id = :team_id "
                    "AND tmr.role_key = 'TEAM_LEADER' AND tm.status = 'ACTIVE'"
                ),
                {"user_id": user_id, "team_id": team_id},
            ).first()
        )

    def load_scoped_settings(
        self,
        user_id: str,
        team_id: str | None,
        role_keys: set[str],
    ) -> dict[str, dict[str, Any]]:
        if team_id is None or not role_keys:
            return {}

        authorized_roles = {_normalized_role(role_key) for role_key in role_keys}
        rows = self.connection.execute(
            text(
                "SELECT role_key, key, value FROM access_settings "
                "WHERE user_id = :user_id AND team_id = :team_id "
                "ORDER BY role_key, key"
            ),
            {"user_id": user_id, "team_id": team_id},
        ).fetchall()
        settings: dict[str, dict[str, Any]] = {}
        for role_key, key, value in rows:
            if _normalized_role(str(role_key)) not in authorized_roles:
                continue
            parsed_value = value
            if isinstance(value, str):
                try:
                    parsed_value = json.loads(value)
                except json.JSONDecodeError:
                    parsed_value = value
            settings.setdefault(str(role_key), {})[str(key)] = parsed_value
        return settings

    def is_system_admin(self, user_id: str) -> bool:
        direct_roles = self.connection.execute(
            text(
                "SELECT r.name, r.role_key FROM user_roles ur "
                "JOIN roles r ON r.id = ur.role_id WHERE ur.user_id = :user_id"
            ),
            {"user_id": user_id},
        ).fetchall()
        return any(_normalized_role(str(role_key or name)) == "system admin" for name, role_key in direct_roles)

    def resolve_context(self, user_id: str, requested_team_id: str | None = None) -> AccessContext:
        is_admin = self.is_system_admin(str(user_id))
        memberships = self.resolve_active_memberships(user_id)
        active_team = self.select_active_team(memberships, requested_team_id, is_admin)
        active_team_id = active_team["id"] if active_team else None
        active_membership_ids = {membership["id"] for membership in memberships}
        roles, role_keys = (
            self.get_team_roles(active_team_id) if active_team_id in active_membership_ids else (set(), set())
        )
        return AccessContext(
            user_id=str(user_id),
            memberships=memberships,
            active_team=active_team,
            roles=roles,
            role_keys=role_keys,
            team_leadership=self.is_team_leader(str(user_id), active_team_id),
            settings=self.load_scoped_settings(str(user_id), active_team_id, role_keys),
            is_admin=is_admin,
        )

    @staticmethod
    def require_component_access(context: AccessContext, *required_roles: str) -> None:
        if context.is_admin:
            return
        available = {_normalized_role(role) for role in context.roles}
        required = {_normalized_role(role) for role in required_roles}
        if available.isdisjoint(required):
            raise HTTPException(status_code=403, detail="Required role is not assigned in the active team.")
