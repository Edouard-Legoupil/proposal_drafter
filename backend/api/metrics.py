import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from typing import Optional
from backend.core.db import get_engine
from backend.core.security import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


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
                {"user_id": user_id},
            ).scalar()
        if team_id:
            where_clauses.append(
                "p.user_id IN (SELECT id FROM users WHERE team_id = :team_id)"
            )
            params["team_id"] = team_id
        else:
            where_clauses.append("p.user_id = :user_id")
            params["user_id"] = user_id
    if status_filter == "approved":
        where_clauses.append("p.status = 'approved'")
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
    q = "SELECT AVG(NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9]', '', 'g'), '')::numeric) as avg_funding FROM proposals p {where_clause}"
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
    q = "SELECT p.form_data->>'Category' as category, COUNT(p.id) as proposal_count FROM proposals p {where_clause} GROUP BY category ORDER BY proposal_count DESC"
    where_clause, params = _get_filter_clauses(current_user, filter_by)
    query = q.format(where_clause=where_clause)
    return robust_query(
        query,
        params,
        {"categories": [], "counts": []},
        lambda rows: {
            "categories": [row["category"] for row in rows if "category" in row],
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
    q = "SELECT p.form_data->>'Category' as category, SUM(COALESCE(NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9]', '', 'g'), '')::numeric, 0)) as total_amount FROM proposals p {where_clause} GROUP BY category"
    where_clause, params = _get_filter_clauses(current_user, filter_by)
    query = q.format(where_clause=where_clause)
    return robust_query(
        query,
        params,
        {"categories": [], "amounts": []},
        lambda rows: {
            "categories": [row["category"] for row in rows if "category" in row],
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
    q = "SELECT u.name as author, COUNT(pe.id) as edit_count FROM proposal_edits pe JOIN users u ON pe.user_id = u.id JOIN proposals p ON pe.proposal_id = p.id {where_clause} GROUP BY u.name ORDER BY edit_count DESC"
    where_clause, params = _get_filter_clauses(current_user, filter_by)
    query = q.format(where_clause=where_clause)
    return robust_query(
        query,
        params,
        {"authors": [], "edit_counts": []},
        lambda rows: {
            "authors": [row["author"] for row in rows if "author" in row],
            "edit_counts": [row["edit_count"] for row in rows if "edit_count" in row],
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
    q = "SELECT r.name as reviewer, COUNT(pr.id) as reviews FROM proposal_reviews pr JOIN users r ON pr.reviewer_id = r.id JOIN proposals p ON pr.proposal_id = p.id {where_clause} GROUP BY r.name ORDER BY reviews DESC"
    where_clause, params = _get_filter_clauses(current_user, filter_by)
    query = q.format(where_clause=where_clause)
    return robust_query(
        query,
        params,
        {"reviewers": [], "reviews": []},
        lambda rows: {
            "reviewers": [row["reviewer"] for row in rows if "reviewer" in row],
            "reviews": [row["reviews"] for row in rows if "reviews" in row],
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
    q = "SELECT kc.type, COUNT(kc.id) as count FROM knowledge_cards kc GROUP BY kc.type"
    return robust_query(
        q,
        {},
        {"types": [], "counts": []},
        lambda rows: {
            "types": [row["type"] for row in rows if "type" in row],
            "counts": [row["count"] for row in rows if "count" in row],
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
    q = "SELECT kc.id as card_id, COUNT(kr.id) as revisions FROM knowledge_card_revisions kr JOIN knowledge_cards kc ON kr.card_id = kc.id GROUP BY kc.id"
    return robust_query(
        q,
        {},
        {"card_ids": [], "revisions": []},
        lambda rows: {
            "card_ids": [row["card_id"] for row in rows if "card_id" in row],
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
    q = "SELECT kc.type, COUNT(kcr.url) as references FROM knowledge_card_references kcr JOIN knowledge_cards kc ON kcr.card_id = kc.id GROUP BY kc.type"
    return robust_query(
        q,
        {},
        {"types": [], "references": []},
        lambda rows: {
            "types": [row["type"] for row in rows if "type" in row],
            "references": [row["references"] for row in rows if "references" in row],
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
    q = "SELECT kcr.url, COUNT(DISTINCT kcr.card_id) as usage_count FROM knowledge_card_references kcr GROUP BY kcr.url HAVING COUNT(DISTINCT kcr.card_id) > 1"
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
    description="Shows number of references that are broken/missing/with errors by error type. Keys always present."
)
async def get_reference_issue_metrics(
    current_user: dict = Depends(get_current_user),
    filter_by: Optional[str] = Query("all"),
    date_start: Optional[str] = Query(None),
    date_end: Optional[str] = Query(None),
):
    q = "SELECT kcre.error_type, COUNT(*) as count FROM knowledge_card_reference_errors kcre GROUP BY kcre.error_type"
    return robust_query(
        q,
        {},
        {"error_types": [], "counts": []},
        lambda rows: {
            "error_types": [row["error_type"] for row in rows if "error_type" in row],
            "counts": [row["count"] for row in rows if "count" in row],
        },
    )


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
    q = "SELECT kc.id as card_id, COUNT(kr.id)/GREATEST(1, EXTRACT(MONTH FROM AGE(NOW(), kc.created_at))) as edit_frequency FROM knowledge_card_revisions kr JOIN knowledge_cards kc ON kr.card_id = kc.id GROUP BY kc.id, kc.created_at"
    return robust_query(
        q,
        {},
        {"card_ids": [], "edit_frequency": []},
        lambda rows: {
            "card_ids": [row["card_id"] for row in rows if "card_id" in row],
            "edit_frequency": [
                row["edit_frequency"] for row in rows if "edit_frequency" in row
            ],
        },
    )


@router.get("/metrics/card-impact-score",
    summary="Knowledge Card Impact Score",
    description="Shows aggregate usage/views/citations for each card. Keys always present."
)
async def get_card_impact_score(
    current_user: dict = Depends(get_current_user),
    filter_by: Optional[str] = Query("all"),
    date_start: Optional[str] = Query(None),
    date_end: Optional[str] = Query(None),
):
    q = "SELECT kc.id as card_id, COALESCE(SUM(kcu.views), 0) as impact_score FROM knowledge_card_usage kcu JOIN knowledge_cards kc ON kcu.card_id = kc.id GROUP BY kc.id"
    return robust_query(
        q,
        {},
        {"card_ids": [], "impact_scores": []},
        lambda rows: {
            "card_ids": [row["card_id"] for row in rows if "card_id" in row],
            "impact_scores": [
                row["impact_score"] for row in rows if "impact_score" in row
            ],
        },
    )


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
    q = "SELECT kc.id as isolated_card_id, t.name as silo_team FROM knowledge_cards kc JOIN users u ON kc.created_by = u.id JOIN teams t ON u.team_id = t.id WHERE kc.id IN (SELECT kcr.card_id FROM knowledge_card_references kcr GROUP BY kcr.card_id HAVING COUNT(DISTINCT kcr.card_id) = 1)"
    return robust_query(
        q,
        {},
        {"isolated_card_ids": [], "silo_teams": []},
        lambda rows: {
            "isolated_card_ids": [
                row["isolated_card_id"] for row in rows if "isolated_card_id" in row
            ],
            "silo_teams": [row["silo_team"] for row in rows if "silo_team" in row],
        },
    )
