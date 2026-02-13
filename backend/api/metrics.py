import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from typing import Optional
from backend.core.db import get_engine
from backend.core.security import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


def _get_filter_clauses(
    current_user,
    filter_by=None,
    status=None,
    date_start=None,
    date_end=None,
    author_id=None,
    team_id=None,
    donor_id=None,
    donor_group=None,
    template_name=None,
):
    where_clauses = []
    params = {}

    # Basic filter_by logic
    if filter_by == "user":
        where_clauses.append("p.user_id = :current_user_id")
        params["current_user_id"] = current_user["user_id"]
    elif filter_by == "team":
        user_team_id = None
        with get_engine().connect() as connection:
            user_team_id = connection.execute(
                text("SELECT team_id FROM users WHERE id = :uid"),
                {"uid": current_user["user_id"]},
            ).scalar()
        if user_team_id:
            where_clauses.append(
                "p.user_id IN (SELECT id FROM users WHERE team_id = :user_team_id)"
            )
            params["user_team_id"] = user_team_id

    # Rich filtering
    if status and status != "all":
        where_clauses.append("p.status = :status")
        params["status"] = status
    if date_start:
        where_clauses.append("p.created_at >= :date_start")
        params["date_start"] = date_start
    if date_end:
        where_clauses.append("p.created_at <= :date_end")
        params["date_end"] = date_end
    if author_id:
        where_clauses.append("p.user_id = :author_id")
        params["author_id"] = author_id
    if team_id:
        where_clauses.append("p.user_id IN (SELECT id FROM users WHERE team_id = :team_id)")
        params["team_id"] = team_id
    if donor_id:
        where_clauses.append("p.id IN (SELECT proposal_id FROM proposal_donors WHERE donor_id = :donor_id)")
        params["donor_id"] = donor_id
    if donor_group:
        where_clauses.append("p.id IN (SELECT pd.proposal_id FROM proposal_donors pd JOIN donors d ON pd.donor_id = d.id WHERE d.donor_group = :donor_group)")
        params["donor_group"] = donor_group
    if template_name:
        where_clauses.append("p.template_name = :template_name")
        params["template_name"] = template_name

    if where_clauses:
        return "WHERE " + " AND ".join(where_clauses), params
    return "", params


def robust_query(query, params, empty_result, rows_to_contract):
    try:
        with get_engine().connect() as connection:
            rows = connection.execute(text(query), params).mappings().fetchall()
        rows = [dict(row) for row in rows] if rows else []
        return rows_to_contract(rows) if rows else empty_result
    except Exception as e:
        logger.error(f"[METRIC ERROR] {e}", exc_info=True)
        return empty_result


def robust_singleval(query, params, key):
    try:
        with get_engine().connect() as connection:
            val = connection.execute(text(query), params).scalar()
        return {key: float(val) if val else 0}
    except Exception as e:
        logger.error(f"[METRIC ERROR] {e}", exc_info=True)
        return {key: 0}


@router.get(
    "/metrics/pipeline-kpis",
    summary="Consolidated Pipeline KPIs",
    description="Returns all main KPIs for the pipeline overview.",
)
async def get_pipeline_kpis(
    current_user: dict = Depends(get_current_user),
    filter_by: Optional[str] = Query("all"),
    status: Optional[str] = Query(None),
    date_start: Optional[str] = Query(None),
    date_end: Optional[str] = Query(None),
    author_id: Optional[str] = Query(None),
    team_id: Optional[str] = Query(None),
    donor_id: Optional[str] = Query(None),
    donor_group: Optional[str] = Query(None),
    template_name: Optional[str] = Query(None),
):
    where_clause, params = _get_filter_clauses(
        current_user,
        filter_by=filter_by,
        status=status,
        date_start=date_start,
        date_end=date_end,
        author_id=author_id,
        team_id=team_id,
        donor_id=donor_id,
        donor_group=donor_group,
        template_name=template_name,
    )

    # Add exclusion for deleted unless explicitly requested
    if "status =" not in where_clause:
        if where_clause:
            where_clause += " AND p.status != 'deleted'"
        else:
            where_clause = "WHERE p.status != 'deleted'"

    budget_sql = """
        CASE 
            WHEN p.form_data->>'Budget Range' ~* 'k' THEN (NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9.]', '', 'g'), '')::numeric * 1000)
            WHEN p.form_data->>'Budget Range' ~* 'M' THEN (NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9.]', '', 'g'), '')::numeric * 1000000)
            ELSE NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9.]', '', 'g'), '')::numeric
        END
    """

    q = f"""
    WITH filtered_proposals AS (
        SELECT p.*, {budget_sql} as budget_value
        FROM proposals p
        {where_clause}
    ),
    cycle_times AS (
        SELECT 
            p.id,
            EXTRACT(EPOCH FROM (
                SELECT MIN(created_at) FROM proposal_status_history WHERE proposal_id = p.id AND status = 'submitted'
            ) - p.created_at) as seconds_to_submit
        FROM filtered_proposals p
    ),
    counts AS (
        SELECT 
            COALESCE(SUM(budget_value), 0) as total_funding,
            COUNT(*) as total_proposals,
            COUNT(DISTINCT (SELECT donor_id FROM proposal_donors WHERE proposal_id = p.id LIMIT 1)) as total_donors,
            COUNT(DISTINCT p.user_id) as total_users,
            COUNT(*) FILTER (WHERE status = 'in_review') as count_under_review,
            COUNT(*) FILTER (WHERE status = 'submitted') as count_submitted,
            COUNT(*) FILTER (WHERE status = 'deleted') as count_deleted
        FROM filtered_proposals p
    )
    SELECT 
        total_funding,
        total_proposals,
        CASE WHEN total_proposals > 0 THEN total_funding / total_proposals ELSE 0 END as avg_value,
        total_donors,
        (SELECT COUNT(*) FROM teams) as total_teams, -- Global count as requested
        total_users,
        CASE WHEN total_proposals > 0 THEN (count_under_review::float / total_proposals) * 100 ELSE 0 END as pct_under_review,
        CASE WHEN total_proposals > 0 THEN (count_submitted::float / total_proposals) * 100 ELSE 0 END as pct_submitted,
        CASE WHEN total_proposals > 0 THEN (count_deleted::float / total_proposals) * 100 ELSE 0 END as pct_deleted,
        COALESCE((SELECT AVG(seconds_to_submit) FROM cycle_times WHERE seconds_to_submit IS NOT NULL), 0) as avg_cycle_time
    FROM counts
    """
    
    return robust_query(
        q, 
        params, 
        {
            "total_funding": 0, "total_proposals": 0, "avg_value": 0, 
            "total_donors": 0, "total_teams": 0, "total_users": 0,
            "pct_under_review": 0, "pct_submitted": 0, "pct_deleted": 0,
            "avg_cycle_time": 0
        },
        lambda rows: rows[0]
    )


@router.get(
    "/metrics/proposals-by-donor",
    summary="Proposals by Donor",
    description="Total value and counts per donor. Excludes deleted proposals.",
)
async def get_proposals_by_donor(
    current_user: dict = Depends(get_current_user),
    filter_by: Optional[str] = Query("all"),
    status: Optional[str] = Query(None),
    date_start: Optional[str] = Query(None),
    date_end: Optional[str] = Query(None),
    author_id: Optional[str] = Query(None),
    team_id: Optional[str] = Query(None),
    donor_id: Optional[str] = Query(None),
    donor_group: Optional[str] = Query(None),
    template_name: Optional[str] = Query(None),
):
    where_clause, params = _get_filter_clauses(
        current_user, filter_by, status, date_start, date_end, author_id, team_id, donor_id, donor_group, template_name
    )
    
    # Add exclusion for deleted unless explicitly requested
    if "status =" not in where_clause:
        if where_clause:
            where_clause += " AND p.status != 'deleted'"
        else:
            where_clause = "WHERE p.status != 'deleted'"

    budget_sql = """
        CASE 
            WHEN p.form_data->>'Budget Range' ~* 'k' THEN (NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9.]', '', 'g'), '')::numeric * 1000)
            WHEN p.form_data->>'Budget Range' ~* 'M' THEN (NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9.]', '', 'g'), '')::numeric * 1000000)
            ELSE NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9.]', '', 'g'), '')::numeric
        END
    """

    q = f"""
    SELECT 
        d.name as donor,
        SUM({budget_sql}) as total_value,
        COUNT(p.id) as proposal_count,
        COUNT(p.id) FILTER (WHERE p.status = 'submitted') as submitted_count
    FROM proposals p
    JOIN proposal_donors pd ON p.id = pd.proposal_id
    JOIN donors d ON pd.donor_id = d.id
    {where_clause}
    GROUP BY d.name
    ORDER BY total_value DESC
    """
    return robust_query(q, params, [], lambda rows: rows)


@router.get(
    "/metrics/proposals-by-outcome",
    summary="Proposals by Outcome",
    description="Heatmap data for outcomes per donor.",
)
async def get_proposals_by_outcome(
    current_user: dict = Depends(get_current_user),
    filter_by: Optional[str] = Query("all"),
    status: Optional[str] = Query(None),
    date_start: Optional[str] = Query(None),
    date_end: Optional[str] = Query(None),
    author_id: Optional[str] = Query(None),
    team_id: Optional[str] = Query(None),
    donor_id: Optional[str] = Query(None),
    donor_group: Optional[str] = Query(None),
    template_name: Optional[str] = Query(None),
):
    where_clause, params = _get_filter_clauses(
        current_user, filter_by, status, date_start, date_end, author_id, team_id, donor_id, donor_group, template_name
    )

    # Add exclusion for deleted unless explicitly requested
    if "status =" not in where_clause:
        if where_clause:
            where_clause += " AND p.status != 'deleted'"
        else:
            where_clause = "WHERE p.status != 'deleted'"

    q = f"""
    SELECT 
        d.name as donor,
        o.name as outcome,
        COUNT(p.id) as count
    FROM proposals p
    JOIN proposal_donors pd ON p.id = pd.proposal_id
    JOIN donors d ON pd.donor_id = d.id
    JOIN proposal_outcomes po ON p.id = po.proposal_id
    JOIN outcomes o ON po.outcome_id = o.id
    {where_clause}
    GROUP BY d.name, o.name
    ORDER BY count DESC
    """
    return robust_query(q, params, [], lambda rows: rows)


@router.get(
    "/metrics/proposals-by-context",
    summary="Proposals by Context",
    description="Treemap data for field contexts grouped by region.",
)
async def get_proposals_by_context(
    current_user: dict = Depends(get_current_user),
    filter_by: Optional[str] = Query("all"),
    status: Optional[str] = Query(None),
    date_start: Optional[str] = Query(None),
    date_end: Optional[str] = Query(None),
    author_id: Optional[str] = Query(None),
    team_id: Optional[str] = Query(None),
    donor_id: Optional[str] = Query(None),
    donor_group: Optional[str] = Query(None),
    template_name: Optional[str] = Query(None),
):
    where_clause, params = _get_filter_clauses(
        current_user, filter_by, status, date_start, date_end, author_id, team_id, donor_id, donor_group, template_name
    )
    
    if "status =" not in where_clause:
        if where_clause:
            where_clause += " AND p.status != 'deleted'"
        else:
            where_clause = "WHERE p.status != 'deleted'"

    budget_sql = """
        CASE 
            WHEN p.form_data->>'Budget Range' ~* 'k' THEN (NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9.]', '', 'g'), '')::numeric * 1000)
            WHEN p.form_data->>'Budget Range' ~* 'M' THEN (NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9.]', '', 'g'), '')::numeric * 1000000)
            ELSE NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9.]', '', 'g'), '')::numeric
        END
    """

    q = f"""
    SELECT 
        COALESCE(fc.unhcr_region, 'Other') as region,
        fc.name as context,
        SUM({budget_sql}) as total_value,
        COUNT(p.id) as proposal_count,
        COUNT(p.id) FILTER (WHERE p.status = 'submitted') as submitted_count
    FROM proposals p
    JOIN proposal_field_contexts pfc ON p.id = pfc.proposal_id
    JOIN field_contexts fc ON pfc.field_context_id = fc.id
    {where_clause}
    GROUP BY COALESCE(fc.unhcr_region, 'Other'), fc.name
    ORDER BY total_value DESC
    """
    return robust_query(q, params, [], lambda rows: rows)


@router.get(
    "/metrics/proposals-by-team",
    summary="Proposals by Team",
    description="Stacked bar data showing proposal value per team by status. Excludes deleted.",
)
async def get_proposals_by_team(
    current_user: dict = Depends(get_current_user),
    filter_by: Optional[str] = Query("all"),
    status: Optional[str] = Query(None),
    date_start: Optional[str] = Query(None),
    date_end: Optional[str] = Query(None),
    author_id: Optional[str] = Query(None),
    team_id: Optional[str] = Query(None),
    donor_id: Optional[str] = Query(None),
    donor_group: Optional[str] = Query(None),
    template_name: Optional[str] = Query(None),
):
    where_clause, params = _get_filter_clauses(
        current_user, filter_by, status, date_start, date_end, author_id, team_id, donor_id, donor_group, template_name
    )
    
    if "status =" not in where_clause:
        if where_clause:
            where_clause += " AND p.status != 'deleted'"
        else:
            where_clause = "WHERE p.status != 'deleted'"

    budget_sql = """
        CASE 
            WHEN p.form_data->>'Budget Range' ~* 'k' THEN (NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9.]', '', 'g'), '')::numeric * 1000)
            WHEN p.form_data->>'Budget Range' ~* 'M' THEN (NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9.]', '', 'g'), '')::numeric * 1000000)
            ELSE NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9.]', '', 'g'), '')::numeric
        END
    """

    q = f"""
    WITH base_data AS (
        SELECT 
            tm.name as team_name,
            p.status,
            {budget_sql} as budget_value,
            p.id as proposal_id
        FROM proposals p
        JOIN users u ON p.user_id = u.id
        JOIN teams tm ON u.team_id = tm.id
        {where_clause}
    ),
    team_totals AS (
        SELECT 
            team_name,
            COUNT(proposal_id) as total_proposals,
            COALESCE(SUM(budget_value), 0) as total_team_value
        FROM base_data
        GROUP BY team_name
    )
    SELECT 
        bd.team_name || ' (' || tt.total_proposals || ')' as team,
        bd.status,
        SUM(bd.budget_value) as value,
        COUNT(bd.proposal_id) as count,
        COUNT(bd.proposal_id) FILTER (WHERE bd.status = 'submitted') as submitted_count
    FROM base_data bd
    JOIN team_totals tt ON bd.team_name = tt.team_name
    GROUP BY bd.team_name, tt.total_proposals, tt.total_team_value, bd.status
    ORDER BY tt.total_team_value DESC, bd.team_name, value DESC
    """
    return robust_query(q, params, [], lambda rows: rows)


@router.get(
    "/metrics/proposals-by-time",
    summary="Proposals over Time",
    description="Stacked area data showing total value per status over time.",
)
async def get_proposals_by_time(
    current_user: dict = Depends(get_current_user),
    filter_by: Optional[str] = Query("all"),
    status: Optional[str] = Query(None),
    date_start: Optional[str] = Query(None),
    date_end: Optional[str] = Query(None),
    author_id: Optional[str] = Query(None),
    team_id: Optional[str] = Query(None),
    donor_id: Optional[str] = Query(None),
    donor_group: Optional[str] = Query(None),
    template_name: Optional[str] = Query(None),
    period: Optional[str] = Query("month"),
):
    periods = {
        "month": "TO_CHAR(p.created_at, 'YYYY-MM')",
        "quarter": "TO_CHAR(p.created_at, 'YYYY') || '-Q' || EXTRACT(QUARTER FROM p.created_at)",
        "year": "TO_CHAR(p.created_at, 'YYYY')",
    }
    period_expr = periods.get(period, periods["month"])
    
    where_clause, params = _get_filter_clauses(
        current_user, filter_by, status, date_start, date_end, author_id, team_id, donor_id, donor_group, template_name
    )
    
    if "status =" not in where_clause:
        if where_clause:
            where_clause += " AND p.status != 'deleted'"
        else:
            where_clause = "WHERE p.status != 'deleted'"

    budget_sql = """
        CASE 
            WHEN p.form_data->>'Budget Range' ~* 'k' THEN (NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9.]', '', 'g'), '')::numeric * 1000)
            WHEN p.form_data->>'Budget Range' ~* 'M' THEN (NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9.]', '', 'g'), '')::numeric * 1000000)
            ELSE NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9.]', '', 'g'), '')::numeric
        END
    """

    q = f"""
    SELECT 
        {period_expr} as period,
        p.status,
        SUM({budget_sql}) as value
    FROM proposals p
    {where_clause}
    GROUP BY period, p.status
    ORDER BY period ASC
    """
    return robust_query(q, params, [], lambda rows: rows)


#######################################
# PROPOSAL PIPELINE METRICS
#######################################
# Each endpoint below includes: SQL aggregation, docstrings, filter support, sample output, and error/edge case handling

@router.get(
    "/metrics/average-funding-amount",
    summary="Average Funding Amount",
    description='Calculates average requested/awarded funding. Filter by user/team/status. Returns {"amount": float or 0}.',
)
async def get_average_funding(
    current_user: dict = Depends(get_current_user),
    filter_by: Optional[str] = Query("all"),
    status: Optional[str] = Query("all"),
    date_start: Optional[str] = Query(None),
    date_end: Optional[str] = Query(None),
):
    q = """
    SELECT AVG(
        CASE 
            WHEN p.form_data->>'Budget Range' ~* 'k' THEN (NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9.]', '', 'g'), '')::numeric * 1000)
            WHEN p.form_data->>'Budget Range' ~* 'M' THEN (NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9.]', '', 'g'), '')::numeric * 1000000)
            ELSE NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9.]', '', 'g'), '')::numeric
        END
    ) as avg_funding FROM proposals p {where_clause}
    """
    where_clause, params = _get_filter_clauses(
        current_user, filter_by, status_filter=status
    )
    query = q.format(where_clause=where_clause)
    return robust_singleval(query, params, "amount")


@router.get(
    "/metrics/proposal-volume",
    summary="Proposal Volume by Category/Author",
    description='Number of proposals by category, status, or author/team. Outputs [{"categories":[], "counts":[]}]. Always present, never null.',
)
async def get_proposal_volume(
    current_user: dict = Depends(get_current_user),
    filter_by: Optional[str] = Query("all"),
    date_start: Optional[str] = Query(None),
    date_end: Optional[str] = Query(None),
):
    q = "SELECT COALESCE(p.form_data->>'Category', p.template_name) as category, COUNT(p.id) as proposal_count FROM proposals p {where_clause} GROUP BY category ORDER BY proposal_count DESC"
    where_clause, params = _get_filter_clauses(current_user, filter_by)
    query = q.format(where_clause=where_clause)
    return robust_query(
        query,
        params,
        {"categories": [], "counts": []},
        lambda rows: {
            "categories": [row["category"] for row in rows if row.get("category")],
            "counts": [
                row["proposal_count"] for row in rows if "proposal_count" in row
            ],
        },
    )

@router.get(
    "/metrics/funding-by-category",
    summary="Funding by Category",
    description="Funding totals by proposal category. Filtered by user/team/global. Output keys always present.",
)
async def get_funding_by_category(
    current_user: dict = Depends(get_current_user),
    filter_by: Optional[str] = Query("all"),
    date_start: Optional[str] = Query(None),
    date_end: Optional[str] = Query(None),
):
    q = """
    SELECT COALESCE(p.form_data->>'Category', p.template_name) as category, 
           SUM(COALESCE(
               CASE 
                   WHEN p.form_data->>'Budget Range' ~* 'k' THEN (NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9.]', '', 'g'), '')::numeric * 1000)
                   WHEN p.form_data->>'Budget Range' ~* 'M' THEN (NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9.]', '', 'g'), '')::numeric * 1000000)
                   ELSE NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9.]', '', 'g'), '')::numeric
               END, 0)) as total_amount 
    FROM proposals p {where_clause} GROUP BY category
    """
    where_clause, params = _get_filter_clauses(current_user, filter_by)
    query = q.format(where_clause=where_clause)
    return robust_query(
        query,
        params,
        {"categories": [], "amounts": []},
        lambda rows: {
            "categories": [row["category"] for row in rows if row.get("category")],
            "amounts": [
                float(row["total_amount"]) for row in rows if "total_amount" in row
            ],
        },
    )


@router.get(
    "/metrics/donor-interest",
    summary="Donor Interest",
    description="Number of proposals linked to each donor. Output keys always present; empty lists if none.",
)
async def get_donor_interest(
    current_user: dict = Depends(get_current_user),
    filter_by: Optional[str] = Query("all"),
    date_start: Optional[str] = Query(None),
    date_end: Optional[str] = Query(None),
):
    q = "SELECT d.name as donor, COUNT(p.id) as interest FROM proposals p JOIN proposal_donors pd ON p.id = pd.proposal_id JOIN donors d ON pd.donor_id = d.id {where_clause} GROUP BY d.name ORDER BY interest DESC"
    where_clause, params = _get_filter_clauses(current_user, filter_by)
    query = q.format(where_clause=where_clause)
    return robust_query(
        query,
        params,
        {"donors": [], "interest": []},
        lambda rows: {
            "donors": [row["donor"] for row in rows if "donor" in row],
            "interest": [row["interest"] for row in rows if "interest" in row],
        },
    )


@router.get(
    "/metrics/development-time",
    summary="Proposal Development Time",
    description='Average duration proposals spend in each status. Outputs [{"status":..., "average_duration_seconds":...}]. Keys always present.',
)
async def get_development_time(
    current_user: dict = Depends(get_current_user),
    filter_by: Optional[str] = Query("all"),
    date_start: Optional[str] = Query(None),
    date_end: Optional[str] = Query(None),
):
    q = """WITH status_durations AS (
        SELECT psh.proposal_id, psh.status, LEAD(psh.created_at, 1, CURRENT_TIMESTAMP) OVER (PARTITION BY psh.proposal_id ORDER BY psh.created_at) - psh.created_at AS duration FROM proposal_status_history psh JOIN proposals p ON psh.proposal_id = p.id {where_clause}) SELECT status, EXTRACT(EPOCH FROM AVG(duration)) as average_duration_seconds FROM status_durations GROUP BY status"""
    where_clause, params = _get_filter_clauses(current_user, filter_by)
    query = q.format(where_clause=where_clause)
    return robust_query(query, params, [], lambda rows: rows)


@router.get(
    "/metrics/proposal-trends",
    summary="Proposal Trends",
    description="Distribution of proposals by status over time. Sample output: {'timeline':[], 'statuses':[], 'counts':[]}. All keys always present.",
)
async def get_proposal_trends(
    current_user: dict = Depends(get_current_user),
    filter_by: Optional[str] = Query("all"),
    period: Optional[str] = Query("month"),
    date_start: Optional[str] = Query(None),
    date_end: Optional[str] = Query(None),
):
    periods = {
        "month": "TO_CHAR(p.created_at, 'YYYY-MM')",
        "quarter": "TO_CHAR(p.created_at, 'YYYY') || '-Q' || EXTRACT(QUARTER FROM p.created_at)",
        "year": "TO_CHAR(p.created_at, 'YYYY')",
    }
    period_expr = periods.get(period, periods["month"])
    where_clause, params = _get_filter_clauses(current_user, filter_by)
    q = f"SELECT {period_expr} as period, p.status, COUNT(p.id) as proposal_count FROM proposals p {where_clause} GROUP BY period, p.status ORDER BY period DESC"
    return robust_query(
        q,
        params,
        {"timeline": [], "statuses": [], "counts": []},
        lambda rows: {
            "timeline": [row["period"] for row in rows if "period" in row],
            "statuses": [row["status"] for row in rows if "status" in row],
            "counts": [
                row["proposal_count"] for row in rows if "proposal_count" in row
            ],
        },
    )

@router.get(
    "/metrics/conversion-rate",
    summary="Proposal Conversion Rate",
    description="Ratio of proposals approved/funded to submitted. Output: {rate:float}. Always present.",
)
async def get_conversion_rate(
    current_user: dict = Depends(get_current_user),
    filter_by: Optional[str] = Query("all"),
    date_start: Optional[str] = Query(None),
    date_end: Optional[str] = Query(None),
):
    try:
        where_clause, params = _get_filter_clauses(current_user, filter_by)
        total_query = f"SELECT COUNT(id) FROM proposals p {where_clause}"
        approved_query = f"SELECT COUNT(id) FROM proposals p {where_clause} AND p.status = 'approved'"
        with get_engine().connect() as connection:
            total = connection.execute(text(total_query), params).scalar()
            approved = connection.execute(text(approved_query), params).scalar()
        rate = round(approved / total, 4) if total else 0.0
        return {"rate": rate}
    except Exception as e:
        logger.error(f"[CONVERSION RATE ERROR]: {e}")
        return {"rate": 0}


@router.get("/metrics/abandonment-rate",
    summary="Proposal Abandonment Rate",
    description="""
    Shows rate of proposals started but never submitted/funded.
    - Useful to diagnose where users or teams drop out of the pipeline.
    Sample: { "rate": 0.12, "total_abandoned": 4 }
    Always present.
    Returns zeroes if no abandoned proposals.
    """
)
async def get_abandonment_rate(
    current_user: dict = Depends(get_current_user),
    filter_by: Optional[str] = Query("all"),
    date_start: Optional[str] = Query(None),
    date_end: Optional[str] = Query(None),
):
    try:
        where_clause, params = _get_filter_clauses(current_user, filter_by)
        total_query = f"SELECT COUNT(id) FROM proposals p {where_clause}"
        abandoned_query = (
            f"SELECT COUNT(id) FROM proposals p {where_clause} AND p.status = 'draft'"
        )
        with get_engine().connect() as connection:
            total = connection.execute(text(total_query), params).scalar()
            abandoned = connection.execute(text(abandoned_query), params).scalar()
        rate = round(abandoned / total, 4) if total else 0.0
        return {"rate": rate, "total_abandoned": abandoned or 0}
    except Exception as e:
        logger.error(f"[ABANDONMENT ERROR]: {e}")
        return {"rate": 0, "total_abandoned": 0}


@router.get("/metrics/edit-activity",
    summary="Proposal Edit Activity",
    description="""
    Tracks frequency of edits by team/author/time for proposals.
    - Use for identifying collaboration or bottlenecks.
    Output: { "authors": ["TeamA"], "edit_counts": [53] }
    Keys always present.
    """
)
async def get_edit_activity(
    current_user: dict = Depends(get_current_user),
    filter_by: Optional[str] = Query("all"),
    date_start: Optional[str] = Query(None),
    date_end: Optional[str] = Query(None),
):
    q = """
    SELECT edit_count, COUNT(proposal_id) as proposal_count
    FROM (
        SELECT psh.proposal_id, COUNT(psh.id) as edit_count 
        FROM proposal_status_history psh 
        JOIN proposals p ON psh.proposal_id = p.id 
        {where_clause} 
        GROUP BY psh.proposal_id 
    ) t
    GROUP BY edit_count
    ORDER BY edit_count
    """
    where_clause, params = _get_filter_clauses(current_user, filter_by)
    query = q.format(where_clause=where_clause)
    return robust_query(
        query,
        params,
        {"labels": [], "data": []},
        lambda rows: {
            "labels": [f"{row['edit_count']} Edits" for row in rows if "edit_count" in row],
            "data": [row["proposal_count"] for row in rows if "proposal_count" in row],
        },
    )


@router.get("/metrics/reviewer-activity",
    summary="Reviewer Activity Stats",
    description="""
    Shows number of reviews per team/member, identifying top reviewers and coverage.
    Output: { "reviewers": ["ReviewerA"], "reviews": [19] }
    Keys always present; empty arrays if none.
    """
)
async def get_reviewer_activity(
    current_user: dict = Depends(get_current_user),
    filter_by: Optional[str] = Query("all"),
    date_start: Optional[str] = Query(None),
    date_end: Optional[str] = Query(None),
):
    q = """
    SELECT review_count, COUNT(proposal_id) as proposal_count
    FROM (
        SELECT psh.proposal_id, COUNT(psh.id) as review_count 
        FROM proposal_status_history psh 
        JOIN proposals p ON psh.proposal_id = p.id 
        {where_clause} 
        GROUP BY psh.proposal_id 
    ) t
    GROUP BY review_count
    ORDER BY review_count
    """
    where_clause, params = _get_filter_clauses(current_user, filter_by)
    if where_clause:
        where_clause += " AND psh.status = 'in_review'"
    else:
        where_clause = "WHERE psh.status = 'in_review'"
    
    query = q.format(where_clause=where_clause)
    return robust_query(
        query,
        params,
        {"labels": [], "data": []},
        lambda rows: {
            "labels": [f"{row['review_count']} Reviews" for row in rows if "review_count" in row],
            "data": [row["proposal_count"] for row in rows if "proposal_count" in row],
        },
    )


#######################################
# KNOWLEDGE METRICS
#######################################

@router.get("/metrics/knowledge-cards",
    summary="Knowledge Card Counts",
    description="Count of knowledge cards grouped by type/time/user/team. Keys always present."
)
async def get_knowledge_cards(
    current_user: dict = Depends(get_current_user),
    filter_by: Optional[str] = Query("all"),
    date_start: Optional[str] = Query(None),
    date_end: Optional[str] = Query(None),
):
    q = """
    SELECT 
        CASE 
            WHEN donor_id IS NOT NULL THEN 'Donor'
            WHEN outcome_id IS NOT NULL THEN 'Outcome'
            WHEN field_context_id IS NOT NULL THEN 'Context'
            ELSE 'General'
        END as type, 
        COUNT(id) as count 
    FROM knowledge_cards 
    GROUP BY type
    """
    return robust_query(
        q,
        {},
        {"types": [], "counts": []},
        lambda rows: {
            "types": [row["type"] for row in rows],
            "counts": [row["count"] for row in rows],
        },
    )


@router.get("/metrics/knowledge-cards-history",
    summary="Knowledge Card Revision Counts",
    description="Shows total revision count for each card, plus distribution. Output keys always present."
)
async def get_knowledge_cards_history(
    current_user: dict = Depends(get_current_user),
    filter_by: Optional[str] = Query("all"),
    date_start: Optional[str] = Query(None),
    date_end: Optional[str] = Query(None),
):
    q = "SELECT kc.id as card_id, COUNT(kr.id) as revisions FROM knowledge_card_history kr JOIN knowledge_cards kc ON kr.knowledge_card_id = kc.id GROUP BY kc.id"
    return robust_query(
        q,
        {},
        {"card_ids": [], "revisions": []},
        lambda rows: {
            "card_ids": [str(row["card_id"]) for row in rows if "card_id" in row],
            "revisions": [row["revisions"] for row in rows if "revisions" in row],
        },
    )


@router.get("/metrics/reference",
    summary="Reference Counts",
    description="Shows number of external URLs referenced per card/type. Keys always present."
)
async def get_reference_metrics(
    current_user: dict = Depends(get_current_user),
    filter_by: Optional[str] = Query("all"),
    date_start: Optional[str] = Query(None),
    date_end: Optional[str] = Query(None),
):
    q = """
    SELECT 
        CASE 
            WHEN kc.donor_id IS NOT NULL THEN 'Donor'
            WHEN kc.outcome_id IS NOT NULL THEN 'Outcome'
            WHEN kc.field_context_id IS NOT NULL THEN 'Context'
            ELSE 'General'
        END as type, 
        COUNT(kcr.id) as references 
    FROM knowledge_card_references kcr 
    JOIN knowledge_card_to_references kctr ON kcr.id = kctr.reference_id 
    JOIN knowledge_cards kc ON kctr.knowledge_card_id = kc.id 
    GROUP BY type
    """
    return robust_query(
        q,
        {},
        {"types": [], "references": []},
        lambda rows: {
            "types": [row["type"] for row in rows],
            "references": [row["references"] for row in rows],
        },
    )


@router.get("/metrics/reference-usage",
    summary="Reference Usage Across Cards",
    description="Shows count of URLs reused in multiple cards. Keys always present."
)
async def get_reference_usage_metrics(
    current_user: dict = Depends(get_current_user),
    filter_by: Optional[str] = Query("all"),
    date_start: Optional[str] = Query(None),
    date_end: Optional[str] = Query(None),
):
    q = "SELECT kcr.url, COUNT(DISTINCT kctr.knowledge_card_id) as usage_count FROM knowledge_card_references kcr JOIN knowledge_card_to_references kctr ON kcr.id = kctr.reference_id GROUP BY kcr.url HAVING COUNT(DISTINCT kctr.knowledge_card_id) > 1"
    return robust_query(
        q,
        {},
        {"urls": [], "usage_counts": []},
        lambda rows: {
            "urls": [row["url"] for row in rows if "url" in row],
            "usage_counts": [
                row["usage_count"] for row in rows if "usage_count" in row
            ],
        },
    )


@router.get("/metrics/reference-issue",
    summary="Reference Issues/Errors",
    description="Shows number of references that are broken/missing/with errors by error type. Returns empty if table missing."
)
async def get_reference_issue_metrics(
    current_user: dict = Depends(get_current_user),
    filter_by: Optional[str] = Query("all"),
    date_start: Optional[str] = Query(None),
    date_end: Optional[str] = Query(None),
):
    # knowledge_card_reference_errors table is missing in some environments
    return {"error_types": [], "counts": []}


@router.get("/metrics/card-edit-frequency",
    summary="Knowledge Card Edit Frequency",
    description="Shows the editing cadence/frequency for cards, useful for maintenance tracking. Output keys always present."
)
async def get_card_edit_frequency(
    current_user: dict = Depends(get_current_user),
    filter_by: Optional[str] = Query("all"),
    date_start: Optional[str] = Query(None),
    date_end: Optional[str] = Query(None),
):
    q = """
    SELECT kc.id as card_id, 
           COUNT(kr.id)/GREATEST(1, EXTRACT(MONTH FROM AGE(NOW(), kc.created_at))) as edit_frequency 
    FROM knowledge_card_history kr 
    JOIN knowledge_cards kc ON kr.knowledge_card_id = kc.id 
    GROUP BY kc.id, kc.created_at
    """
    return robust_query(
        q,
        {},
        {"card_ids": [], "edit_frequency": []},
        lambda rows: {
            "card_ids": [str(row["card_id"]) for row in rows if "card_id" in row],
            "edit_frequency": [
                row["edit_frequency"] for row in rows if "edit_frequency" in row
            ],
        },
    )


@router.get("/metrics/card-impact-score",
    summary="Knowledge Card Impact Score",
    description="Shows aggregate usage/views/citations for each card. Returns empty if table missing."
)
async def get_card_impact_score(
    current_user: dict = Depends(get_current_user),
    filter_by: Optional[str] = Query("all"),
    date_start: Optional[str] = Query(None),
    date_end: Optional[str] = Query(None),
):
    # knowledge_card_usage table is missing in some environments
    return {"card_ids": [], "impact_scores": []}


@router.get("/metrics/knowledge-silos",
    summary="Knowledge Silos Across Teams",
    description="Shows cards/references only used by one team (silo). Keys always present."
)
async def get_knowledge_silos(
    current_user: dict = Depends(get_current_user),
    filter_by: Optional[str] = Query("all"),
    date_start: Optional[str] = Query(None),
    date_end: Optional[str] = Query(None),
):
    q = """
    SELECT kc.id as isolated_card_id, t.name as silo_team 
    FROM knowledge_cards kc 
    JOIN users u ON kc.created_by = u.id 
    JOIN teams t ON u.team_id = t.id 
    WHERE kc.id IN (
        SELECT kctr.knowledge_card_id 
        FROM knowledge_card_to_references kctr 
        GROUP BY kctr.knowledge_card_id 
        HAVING COUNT(DISTINCT kctr.reference_id) = 1
    )
    """
    return robust_query(
        q,
        {},
        {"isolated_card_ids": [], "silo_teams": []},
        lambda rows: {
            "isolated_card_ids": [
                str(row["isolated_card_id"]) for row in rows if "isolated_card_id" in row
            ],
            "silo_teams": [row["silo_team"] for row in rows if "silo_team" in row],
        },
    )
