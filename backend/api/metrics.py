import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from typing import Optional

from backend.core.db import get_engine
from backend.core.security import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/metrics/development-time")
async def get_development_time_metrics(
    current_user: dict = Depends(get_current_user),
    filter_by: Optional[str] = Query("all", enum=["user", "team", "all"])
):
    """
    Calculates the average time proposals spend in each status.
    Can be filtered by 'user', 'team', or 'all'.
    """
    user_id = current_user["user_id"]

    base_query = """
        WITH status_durations AS (
            SELECT
                psh.proposal_id,
                psh.status,
                LEAD(psh.created_at, 1, CURRENT_TIMESTAMP) OVER (PARTITION BY psh.proposal_id ORDER BY psh.created_at) - psh.created_at AS duration
            FROM
                proposal_status_history psh
            JOIN
                proposals p ON psh.proposal_id = p.id
            {where_clause}
        )
        SELECT
            status,
            EXTRACT(EPOCH FROM AVG(duration)) as average_duration_seconds
        FROM
            status_durations
        GROUP BY
            status
    """

    where_clause = ""
    params = {}

    if filter_by == "user":
        where_clause = "WHERE p.user_id = :user_id"
        params["user_id"] = user_id
    elif filter_by == "team":
        with get_engine().connect() as connection:
            team_result = connection.execute(
                text("SELECT team FROM users WHERE id = :user_id"),
                {"user_id": user_id}
            ).scalar()

        if team_result:
            where_clause = "WHERE p.user_id IN (SELECT id FROM users WHERE team = :team)"
            params["team"] = team_result
        else:
            where_clause = "WHERE p.user_id = :user_id"
            params["user_id"] = user_id

    final_query = base_query.format(where_clause=where_clause)

    try:
        with get_engine().connect() as connection:
            result = connection.execute(text(final_query), params)
            data = [dict(row) for row in result.mappings().fetchall()]
        return {"filter": filter_by, "data": data}
    except Exception as e:
        logger.error(f"[GET DEV TIME METRICS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to calculate development time metrics.")


@router.get("/metrics/funding-by-category")
async def get_funding_by_category_metrics(
    current_user: dict = Depends(get_current_user),
    filter_by: Optional[str] = Query("all", enum=["user", "team", "all"])
):
    """
    Calculates the number of proposals per status, donor, and outcome.
    Note: Does not aggregate budget due to string format; returns proposal count instead.
    """
    user_id = current_user["user_id"]

    query_template = """
        SELECT
            p.status,
            d.name as donor_name,
            o.name as outcome_name,
            COUNT(p.id) as proposal_count
        FROM
            proposals p
        LEFT JOIN proposal_donors pd ON p.id = pd.proposal_id
        LEFT JOIN donors d ON pd.donor_id = d.id
        LEFT JOIN proposal_outcomes po ON p.id = po.proposal_id
        LEFT JOIN outcomes o ON po.outcome_id = o.id
        {where_clause}
        GROUP BY p.status, d.name, o.name
        ORDER BY p.status, d.name, o.name
    """

    where_clause, params = _get_filter_clauses(current_user, filter_by)
    final_query = query_template.format(where_clause=where_clause)

    try:
        with get_engine().connect() as connection:
            result = connection.execute(text(final_query), params)
            data = [dict(row) for row in result.mappings().fetchall()]
        return {"filter": filter_by, "data": data, "note": "Budget is not aggregated; proposal_count is returned instead."}
    except Exception as e:
        logger.error(f"[GET FUNDING METRICS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to calculate funding metrics.")


@router.get("/metrics/donor-interest")
async def get_donor_interest_metrics(
    current_user: dict = Depends(get_current_user),
    filter_by: Optional[str] = Query("all", enum=["user", "team", "all"])
):
    """
    Calculates the number of projects per donor, outcome, and field context.
    """
    user_id = current_user["user_id"]

    query_template = """
        SELECT
            d.name as donor_name,
            o.name as outcome_name,
            fc.name as field_context_name,
            COUNT(p.id) as project_count
        FROM
            proposals p
        JOIN proposal_donors pd ON p.id = pd.proposal_id
        JOIN donors d ON pd.donor_id = d.id
        LEFT JOIN proposal_outcomes po ON p.id = po.proposal_id
        LEFT JOIN outcomes o ON po.outcome_id = o.id
        LEFT JOIN proposal_field_contexts pfc ON p.id = pfc.proposal_id
        LEFT JOIN field_contexts fc ON pfc.field_context_id = fc.id
        {where_clause}
        GROUP BY d.name, o.name, fc.name
        ORDER BY d.name, o.name, fc.name
    """

    where_clause, params = _get_filter_clauses(current_user, filter_by)
    final_query = query_template.format(where_clause=where_clause)

    try:
        with get_engine().connect() as connection:
            result = connection.execute(text(final_query), params)
            data = [dict(row) for row in result.mappings().fetchall()]
        return {"filter": filter_by, "data": data}
    except Exception as e:
        logger.error(f"[GET DONOR INTEREST METRICS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to calculate donor interest metrics.")

def _get_filter_clauses(current_user, filter_by):
    user_id = current_user["user_id"]
    where_clause = ""
    params = {}

    if filter_by == "user":
        where_clause = "WHERE p.user_id = :user_id"
        params["user_id"] = user_id
    elif filter_by == "team":
        with get_engine().connect() as connection:
            team_result = connection.execute(
                text("SELECT team FROM users WHERE id = :user_id"),
                {"user_id": user_id}
            ).scalar()

        if team_result:
            where_clause = "WHERE p.user_id IN (SELECT id FROM users WHERE team = :team)"
            params["team"] = team_result
        else:
            where_clause = "WHERE p.user_id = :user_id"
            params["user_id"] = user_id

    return where_clause, params
