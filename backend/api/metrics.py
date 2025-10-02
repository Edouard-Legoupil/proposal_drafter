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
            team_id = connection.execute(
                text("SELECT team_id FROM users WHERE id = :user_id"),
                {"user_id": user_id}
            ).scalar()

        if team_id:
            where_clause = "WHERE p.user_id IN (SELECT id FROM users WHERE team_id = :team_id)"
            params["team_id"] = team_id
        else:
            # Fallback to user filter if the user is not in a team
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
    Calculates the number of proposals and total budget per status, donor, and outcome.
    """
    query_template = """
        SELECT
            p.status,
            d.name as donor_name,
            o.name as outcome_name,
            COUNT(p.id) as proposal_count,
            SUM(
                COALESCE(
                    NULLIF(
                        regexp_replace(
                            p.form_data->>'Budget Range',
                            '[^0-9]',
                            '',
                            'g'
                        ),
                        ''
                    )::numeric,
                    0
                )
            ) as total_budget
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
            # Convert rows to dictionaries, ensuring total_budget is a float
            data = [
                {**row, 'total_budget': float(row['total_budget'])}
                for row in result.mappings().fetchall()
            ]
        return {"filter": filter_by, "data": data}
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


def _get_filter_clauses(current_user, filter_by, status_filter=None):
    user_id = current_user["user_id"]
    where_clauses = []
    params = {}

    if filter_by == "user":
        where_clauses.append("p.user_id = :user_id")
        params["user_id"] = user_id
    elif filter_by == "team":
        with get_engine().connect() as connection:
            team_id = connection.execute(
                text("SELECT team_id FROM users WHERE id = :user_id"),
                {"user_id": user_id}
            ).scalar()

        if team_id:
            where_clauses.append("p.user_id IN (SELECT id FROM users WHERE team_id = :team_id)")
            params["team_id"] = team_id
        else:
            # Fallback to user filter if the user is not in a team
            where_clauses.append("p.user_id = :user_id")
            params["user_id"] = user_id

    if status_filter == "approved":
        where_clauses.append("p.status = 'approved'")

    if where_clauses:
        return "WHERE " + " AND ".join(where_clauses), params

    return "", params

@router.get("/metrics/average-funding-amount")
async def get_average_funding_amount_metrics(
    current_user: dict = Depends(get_current_user),
    filter_by: Optional[str] = Query("all", enum=["user", "team", "all"]),
    status: Optional[str] = Query("all", enum=["all", "approved"])
):
    """
    Calculates the average funding amount for proposals.
    Can be filtered by status ('all' or 'approved').
    """
    query_template = """
        SELECT
            AVG(
                NULLIF(
                    regexp_replace(
                        p.form_data->>'Budget Range',
                        '[^0-9]',
                        '',
                        'g'
                    ),
                    ''
                )::numeric
            ) as average_funding
        FROM
            proposals p
        {where_clause}
    """

    where_clause, params = _get_filter_clauses(current_user, filter_by, status_filter=status)
    final_query = query_template.format(where_clause=where_clause)

    try:
        with get_engine().connect() as connection:
            result = connection.execute(text(final_query), params).scalar()
        return {"filter": filter_by, "status": status, "average_funding": float(result) if result else 0}
    except Exception as e:
        logger.error(f"[GET AVG FUNDING METRICS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to calculate average funding amount.")


@router.get("/metrics/proposal-volume")
async def get_proposal_volume_metrics(
    current_user: dict = Depends(get_current_user)
):
    """
    Calculates the number of proposals created per user and per team.
    """
    user_volume_query = """
        SELECT
            u.name as user_name,
            COUNT(p.id) as proposal_count
        FROM
            proposals p
        JOIN
            users u ON p.user_id = u.id
        WHERE
            u.name IS NOT NULL
        GROUP BY
            u.name
        ORDER BY
            proposal_count DESC
    """

    team_volume_query = """
        SELECT
            t.name as team_name,
            COUNT(p.id) as proposal_count
        FROM
            proposals p
        JOIN
            users u ON p.user_id = u.id
        JOIN
            teams t ON u.team_id = t.id
        WHERE
            u.team_id IS NOT NULL
        GROUP BY
            t.name
        ORDER BY
            proposal_count DESC
    """

    try:
        with get_engine().connect() as connection:
            user_result = connection.execute(text(user_volume_query))
            user_data = [dict(row) for row in user_result.mappings().fetchall()]

            team_result = connection.execute(text(team_volume_query))
            team_data = [dict(row) for row in team_result.mappings().fetchall()]

        return {"by_user": user_data, "by_team": team_data}
    except Exception as e:
        logger.error(f"[GET PROPOSAL VOLUME METRICS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to calculate proposal volume metrics.")


# Future Metric Suggestions:
#
# 1.  **Average Funding Amount:**
#     - Calculate the average budget of all proposals, or approved proposals.
#     - This would require a query similar to get_funding_by_category_metrics,
#       but with an AVG aggregation on the parsed budget.
#
# 2.  **User/Team Proposal Volume:**
#     - Count the number of proposals created per user or team over a time period.
#     - This could be a simple COUNT grouped by user_id or team.
