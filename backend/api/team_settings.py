# Standard Library
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

# Internal Modules
from backend.core.db import get_engine
from backend.core.security import is_system_admin

router = APIRouter()


@router.get("/admin/team-settings")
async def get_all_team_settings(admin: dict = Depends(is_system_admin)):
    """
    Get all team settings for admin management
    """
    try:
        with get_engine().connect() as connection:
            result = connection.execute(
                text(
                    """
                SELECT
                    ts.id,
                    ts.team_id,
                    t.name as team_name,
                    ts.setting_type,
                    ts.setting_value,
                    ts.created_at,
                    ts.updated_at
                FROM team_settings ts
                JOIN teams t ON ts.team_id = t.id
                ORDER BY t.name, ts.setting_type, ts.setting_value
                """
                )
            )

            team_settings = []
            for row in result.fetchall():
                team_settings.append(
                    {
                        "id": row[0],
                        "team_id": row[1],
                        "team_name": row[2],
                        "setting_type": row[3],
                        "setting_value": row[4],
                        "created_at": row[5].isoformat() if row[5] else None,
                        "updated_at": row[6].isoformat() if row[6] else None,
                    }
                )

            return {"team_settings": team_settings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch team settings: {str(e)}") from e


@router.post("/admin/team-settings")
async def add_team_setting(team_setting: dict, admin: dict = Depends(is_system_admin)):
    """
    Add a new team setting
    """
    try:
        required_fields = ["team_id", "setting_type", "setting_value"]
        for field in required_fields:
            if field not in team_setting:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

        # Validate setting type
        valid_types = ["donor_focal", "outcome_focal", "field_context_focal"]
        if team_setting["setting_type"] not in valid_types:
            raise HTTPException(
                status_code=400, detail=f"Invalid setting type. Must be one of: {', '.join(valid_types)}"
            )

        with get_engine().connect() as connection:
            # Check if team exists
            team_exists = connection.execute(
                text("SELECT 1 FROM teams WHERE id = :team_id"), {"team_id": team_setting["team_id"]}
            ).fetchone()

            if not team_exists:
                raise HTTPException(status_code=404, detail="Team not found")

            # Check if setting already exists
            exists = connection.execute(
                text(
                    """
                SELECT 1 FROM team_settings
                WHERE team_id = :team_id
                AND setting_type = :setting_type
                AND setting_value = :setting_value
                """
                ),
                {
                    "team_id": team_setting["team_id"],
                    "setting_type": team_setting["setting_type"],
                    "setting_value": team_setting["setting_value"],
                },
            ).fetchone()

            if exists:
                raise HTTPException(status_code=400, detail="This setting already exists for the team")

            # Insert the new setting
            connection.execute(
                text(
                    """
                INSERT INTO team_settings
                (team_id, setting_type, setting_value)
                VALUES (:team_id, :setting_type, :setting_value)
                """
                ),
                {
                    "team_id": team_setting["team_id"],
                    "setting_type": team_setting["setting_type"],
                    "setting_value": team_setting["setting_value"],
                },
            )

            # The trigger will automatically apply to team members

            return {
                "message": "Team setting added successfully",
                "team_id": team_setting["team_id"],
                "setting_type": team_setting["setting_type"],
                "setting_value": team_setting["setting_value"],
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add team setting: {str(e)}") from e


@router.delete("/admin/team-settings/{setting_id}")
async def remove_team_setting(setting_id: int, admin: dict = Depends(is_system_admin)):
    """
    Remove a team setting
    """
    try:
        with get_engine().begin() as connection:
            # Get the setting before deleting
            setting = connection.execute(
                text(
                    """
                SELECT team_id, setting_type, setting_value
                FROM team_settings
                WHERE id = :setting_id
                """
                ),
                {"setting_id": setting_id},
            ).fetchone()

            if not setting:
                raise HTTPException(status_code=404, detail="Team setting not found")

            # Delete the setting
            connection.execute(text("DELETE FROM team_settings WHERE id = :setting_id"), {"setting_id": setting_id})

            # Keep materialized inherited rows as audit history. Effective
            # access is dynamically gated by an active matching team grant.
            return {"message": "Team setting removed successfully", "setting_id": setting_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove team setting: {str(e)}") from e


@router.get("/admin/teams/{team_id}/effective-settings")
async def get_team_effective_settings(team_id: str, admin: dict = Depends(is_system_admin)):
    """
    Get all effective settings for a team (direct + inherited)
    """
    try:
        with get_engine().connect() as connection:
            # Get team settings
            team_settings = connection.execute(
                text(
                    """
                SELECT setting_type, setting_value
                FROM team_settings
                WHERE team_id = :team_id
                ORDER BY setting_type, setting_value
                """
                ),
                {"team_id": team_id},
            ).fetchall()

            # Get team members and their effective settings
            members = connection.execute(
                text(
                    """
                SELECT
                    u.id as user_id,
                    u.name as user_name,
                    COALESCE(ues.setting_type, 'none') as setting_type,
                    COALESCE(ues.setting_value, 'none') as setting_value,
                    COALESCE(ues.source, 'none') as source
                FROM users u
                JOIN team_members tm ON u.id = tm.user_id
                LEFT JOIN user_effective_settings ues ON u.id = ues.user_id
                WHERE tm.team_id = :team_id
                ORDER BY u.name, ues.setting_type, ues.setting_value
                """
                ),
                {"team_id": team_id},
            ).fetchall()

            team_settings_list = []
            for row in team_settings:
                team_settings_list.append({"setting_type": row[0], "setting_value": row[1]})

            members_list = []
            for row in members:
                members_list.append(
                    {
                        "user_id": row[0],
                        "user_name": row[1],
                        "setting_type": row[2],
                        "setting_value": row[3],
                        "source": row[4],
                    }
                )

            return {"team_id": team_id, "team_settings": team_settings_list, "team_members": members_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch team effective settings: {str(e)}") from e
