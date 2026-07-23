# Standard Library
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
import json
import logging

# Internal Modules
from backend.core.db import get_engine
from backend.core.security import get_current_user
from backend.core.authorization import check_proposal_access

router = APIRouter()


@router.get("/proposals/with-settings")
async def list_proposals_with_settings(current_user: dict = Depends(get_current_user)):
    """
    Lists all proposals accessible to the current user, filtered by their settings.

    This endpoint implements settings-based filtering as specified in the access management spec.
    It considers:
    - User's team memberships
    - User's donor group associations
    - User's outcome focal areas
    - User's field context focal areas
    - Object-level access rules
    """
    user_id = current_user["user_id"]
    proposal_list = []

    try:
        engine = get_engine()
        with engine.connect() as connection:
            # Get user's settings and associations
            user_settings = {}

            # Get user's teams
            teams_result = connection.execute(
                text(
                    """
                SELECT team_id FROM team_members
                WHERE user_id = :user_id AND status = 'ACTIVE'
                """
                ),
                {"user_id": user_id},
            )
            user_teams = [row[0] for row in teams_result.fetchall()]
            user_settings["teams"] = user_teams

            # Get user's donor groups
            donors_result = connection.execute(
                text(
                    """
                SELECT donor_group FROM user_donor_groups
                WHERE user_id = :user_id
                """
                ),
                {"user_id": user_id},
            )
            user_donors = [row[0] for row in donors_result.fetchall()]
            user_settings["donors"] = user_donors

            # Get user's outcomes
            outcomes_result = connection.execute(
                text(
                    """
                SELECT outcome_id FROM user_outcomes
                WHERE user_id = :user_id
                """
                ),
                {"user_id": user_id},
            )
            user_outcomes = [row[0] for row in outcomes_result.fetchall()]
            user_settings["outcomes"] = user_outcomes

            # Get user's field contexts
            field_contexts_result = connection.execute(
                text(
                    """
                SELECT field_context_id FROM user_field_contexts
                WHERE user_id = :user_id
                """
                ),
                {"user_id": user_id},
            )
            user_field_contexts = [row[0] for row in field_contexts_result.fetchall()]
            user_settings["field_contexts"] = user_field_contexts

            # Build the main query with settings filters
            query = text(
                """
                SELECT DISTINCT
                    p.id,
                    p.form_data,
                    p.project_description,
                    p.status,
                    p.created_at,
                    p.updated_at,
                    p.is_accepted,
                    p.user_id as owner_id,
                    p.team_id,
                    string_agg(DISTINCT d.name, ', ') AS donor_name,
                    string_agg(DISTINCT fc.name, ', ') AS country_name,
                    string_agg(DISTINCT o.name, ', ') AS outcome_names,
                    t.name AS team_name,
                    u.name AS author_name
                FROM
                    proposals p
                JOIN
                    users u ON p.user_id = u.id
                LEFT JOIN
                    teams t ON p.team_id = t.id
                LEFT JOIN
                    proposal_donors pd ON p.id = pd.proposal_id
                LEFT JOIN
                    donors d ON pd.donor_id = d.id
                LEFT JOIN
                    proposal_field_contexts pfc ON p.id = pfc.proposal_id
                LEFT JOIN
                    field_contexts fc ON pfc.field_context_id = fc.id
                LEFT JOIN
                    proposal_outcomes po ON p.id = po.outcome_id
                LEFT JOIN
                    outcomes o ON po.outcome_id = o.id
                WHERE
                    p.status != 'deleted'
                    AND (
                        -- User is owner
                        p.user_id = :user_id
                        OR
                        -- User is in the same team as the proposal
                        p.team_id IN (SELECT team_id FROM team_members WHERE user_id = :user_id AND status = 'ACTIVE')
                        OR
                        -- User has access via donor groups
                        EXISTS (
                            SELECT 1 FROM proposal_donors pd2
                            JOIN user_donor_groups udg ON pd2.donor_id = udg.donor_group
                            WHERE pd2.proposal_id = p.id AND udg.user_id = :user_id
                        )
                        OR
                        -- User has access via outcomes
                        EXISTS (
                            SELECT 1 FROM proposal_outcomes po2
                            JOIN user_outcomes uo ON po2.outcome_id = uo.outcome_id
                            WHERE po2.proposal_id = p.id AND uo.user_id = :user_id
                        )
                        OR
                        -- User has access via field contexts
                        EXISTS (
                            SELECT 1 FROM proposal_field_contexts pfc2
                            JOIN user_field_contexts ufc ON pfc2.field_context_id = ufc.field_context_id
                            WHERE pfc2.proposal_id = p.id AND ufc.user_id = :user_id
                        )
                        OR
                        -- Admin users can see everything
                        :is_admin = TRUE
                    )
                GROUP BY
                    p.id, t.name, u.name
                ORDER BY
                    p.updated_at DESC
            """
            )

            result = connection.execute(
                query,
                {"user_id": user_id, "is_admin": current_user.get("is_admin", False)},
            )
            rows = result.mappings().fetchall()

            for row in rows:
                try:
                    form_data = json.loads(row["form_data"]) if isinstance(row["form_data"], str) else row["form_data"]

                    # Apply object-level access control
                    try:
                        await check_proposal_access(str(row["id"]), current_user, "read")
                        access_granted = True
                    except HTTPException:
                        access_granted = False

                    if access_granted:
                        proposal_list.append(
                            {
                                "proposal_id": str(row["id"]),
                                "project_title": form_data.get("Project Draft Short name")
                                or form_data.get("Project title", "Untitled Proposal"),
                                "summary": row["project_description"] or "",
                                "created_at": (row["created_at"].isoformat() if row["created_at"] else None),
                                "updated_at": (row["updated_at"].isoformat() if row["updated_at"] else None),
                                "is_accepted": row["is_accepted"],
                                "status": row["status"],
                                "donor": row["donor_name"],
                                "country": row["country_name"],
                                "outcomes": (row["outcome_names"].split(", ") if row["outcome_names"] else []),
                                "budget": form_data.get("Budget Range", "N/A"),
                                "team_name": row["team_name"],
                                "team_id": (str(row["team_id"]) if row["team_id"] else None),
                                "author_name": row["author_name"],
                                "owner_id": str(row["owner_id"]),
                                "access_info": {
                                    "can_edit": (
                                        str(row["owner_id"]) == user_id or current_user.get("is_admin", False)
                                    ),
                                    "can_delete": (
                                        str(row["owner_id"]) == user_id or current_user.get("is_admin", False)
                                    ),
                                    "access_via": ("owner" if str(row["owner_id"]) == user_id else "team"),
                                },
                            }
                        )
                except Exception as e:
                    logger.error(f"Error processing proposal {row['id']}: {e}")
                    continue

        return {
            "message": "Proposals fetched successfully with settings filtering.",
            "proposals": proposal_list,
            "user_settings": user_settings,
            "access_info": {
                "user_id": user_id,
                "is_admin": current_user.get("is_admin", False),
                "teams": user_teams,
                "donors": user_donors,
                "outcomes": user_outcomes,
                "field_contexts": user_field_contexts,
            },
        }

    except Exception as e:
        logger.error(f"[LIST PROPOSALS WITH SETTINGS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch proposals with settings")


@router.get("/proposals/{proposal_id}/access-info")
async def get_proposal_access_info(proposal_id: str, current_user: dict = Depends(get_current_user)):
    """
    Get detailed access information for a specific proposal.

    Returns information about why the user can/cannot access the proposal.
    """
    try:
        # Check if user has access
        try:
            await check_proposal_access(proposal_id, current_user, "read")
            can_access = True
        except HTTPException:
            can_access = False

        # Get proposal details for context
        engine = get_engine()
        with engine.connect() as connection:
            proposal_data = connection.execute(
                text(
                    """
                SELECT
                    p.id,
                    p.user_id as owner_id,
                    p.team_id,
                    p.status,
                    u.name as owner_name,
                    t.name as team_name
                FROM proposals p
                JOIN users u ON p.user_id = u.id
                LEFT JOIN teams t ON p.team_id = t.id
                WHERE p.id = :proposal_id
                """
                ),
                {"proposal_id": proposal_id},
            ).fetchone()

        if not proposal_data:
            raise HTTPException(status_code=404, detail="Proposal not found")

        # Determine access reasons
        access_reasons = []
        user_id = current_user["user_id"]

        if current_user.get("is_admin", False):
            access_reasons.append("admin")

        if str(proposal_data["owner_id"]) == user_id:
            access_reasons.append("owner")

        if proposal_data["team_id"]:
            team_access = connection.execute(
                text(
                    """
                SELECT 1 FROM team_members
                WHERE team_id = :team_id AND user_id = :user_id AND status = 'ACTIVE'
                """
                ),
                {"team_id": str(proposal_data["team_id"]), "user_id": user_id},
            ).fetchone()

            if team_access:
                access_reasons.append("team_member")

        # Check donor group access
        donor_access = connection.execute(
            text(
                """
            SELECT 1 FROM proposal_donors pd
            JOIN user_donor_groups udg ON pd.donor_id = udg.donor_group
            WHERE pd.proposal_id = :proposal_id AND udg.user_id = :user_id
            """
            ),
            {"proposal_id": proposal_id, "user_id": user_id},
        ).fetchone()

        if donor_access:
            access_reasons.append("donor_group")

        # Check outcome access
        outcome_access = connection.execute(
            text(
                """
            SELECT 1 FROM proposal_outcomes po
            JOIN user_outcomes uo ON po.outcome_id = uo.outcome_id
            WHERE po.proposal_id = :proposal_id AND uo.user_id = :user_id
            """
            ),
            {"proposal_id": proposal_id, "user_id": user_id},
        ).fetchone()

        if outcome_access:
            access_reasons.append("outcome")

        # Check field context access
        field_context_access = connection.execute(
            text(
                """
            SELECT 1 FROM proposal_field_contexts pfc
            JOIN user_field_contexts ufc ON pfc.field_context_id = ufc.field_context_id
            WHERE pfc.proposal_id = :proposal_id AND ufc.user_id = :user_id
            """
            ),
            {"proposal_id": proposal_id, "user_id": user_id},
        ).fetchone()

        if field_context_access:
            access_reasons.append("field_context")

        return {
            "proposal_id": proposal_id,
            "can_access": can_access,
            "access_reasons": access_reasons,
            "owner_id": str(proposal_data["owner_id"]),
            "owner_name": proposal_data["owner_name"],
            "team_id": (str(proposal_data["team_id"]) if proposal_data["team_id"] else None),
            "team_name": proposal_data["team_name"],
            "status": proposal_data["status"],
            "user_access_via": access_reasons[0] if access_reasons else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[GET PROPOSAL ACCESS INFO ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get proposal access info")


# Import logger

logger = logging.getLogger(__name__)
