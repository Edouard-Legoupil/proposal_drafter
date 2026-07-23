"""Supported interaction analytics API consumed by the metrics dashboard."""

from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends
from sqlalchemy import text

from backend.core.db import get_engine
from backend.core.security import require_any_role

router = APIRouter(prefix="/interactions", tags=["Interaction Analytics"])
analytics_access = require_any_role("ui_analysis", "system admin")


def _date_bounds(date_range: str) -> tuple[datetime, datetime]:
    end_date = datetime.now(timezone.utc)
    days = {"7d": 7, "30d": 30, "90d": 90, "all": 3650}[date_range]
    return end_date - timedelta(days=days), end_date


@router.get("/analytics/")
async def get_interaction_analytics(
    date_range: Literal["7d", "30d", "90d", "all"] = "30d",
    current_user: dict = Depends(analytics_access),  # noqa: B008
):
    """Return aggregate interaction data without exposing individual users."""
    del current_user
    start_date, end_date = _date_bounds(date_range)
    params = {"start_date": start_date, "end_date": end_date}

    with get_engine().connect() as connection:
        totals = (
            connection.execute(
                text(
                    """
                SELECT COUNT(*) AS total_interactions,
                       COUNT(DISTINCT session_id) AS total_sessions,
                       COUNT(DISTINCT user_id) AS total_users,
                       SUM(CASE WHEN was_successful = FALSE THEN 1 ELSE 0 END) AS errors
                FROM user_interactions
                WHERE interaction_timestamp BETWEEN :start_date AND :end_date
                """
                ),
                params,
            )
            .mappings()
            .one()
        )
        type_rows = connection.execute(
            text(
                """
                SELECT interaction_type, COUNT(*) AS count
                FROM user_interactions
                WHERE interaction_timestamp BETWEEN :start_date AND :end_date
                GROUP BY interaction_type
                ORDER BY count DESC
                """
            ),
            params,
        ).all()
        feature_rows = connection.execute(
            text(
                """
                SELECT component_name, COUNT(*) AS usage_count,
                       COUNT(DISTINCT user_id) AS user_count
                FROM user_interactions
                WHERE interaction_timestamp BETWEEN :start_date AND :end_date
                  AND component_name IS NOT NULL
                GROUP BY component_name
                ORDER BY usage_count DESC
                LIMIT 10
                """
            ),
            params,
        ).all()
        wizard = (
            connection.execute(
                text(
                    """
                SELECT COUNT(*) AS total_usage,
                       AVG(feedback_score) AS average_feedback_score,
                       AVG(CASE WHEN was_helpful = TRUE THEN 100.0 ELSE 0.0 END) AS helpful_percentage
                FROM wizard_interactions
                WHERE interaction_timestamp BETWEEN :start_date AND :end_date
                """
                ),
                params,
            )
            .mappings()
            .one()
        )
        question_rows = connection.execute(
            text(
                """
                SELECT search_query, feedback_score
                FROM wizard_interactions
                WHERE interaction_timestamp BETWEEN :start_date AND :end_date
                  AND search_query IS NOT NULL
                ORDER BY interaction_timestamp DESC
                LIMIT 20
                """
            ),
            params,
        ).all()

    total = int(totals["total_interactions"] or 0)
    sessions = int(totals["total_sessions"] or 0)
    interaction_types = [
        {
            "type": row[0],
            "count": row[1],
            "percentage": round((row[1] / total * 100) if total else 0, 2),
        }
        for row in type_rows
    ]
    return {
        "date_range": date_range,
        "start_date": start_date,
        "end_date": end_date,
        "total_interactions": total,
        "total_sessions": sessions,
        "total_users": int(totals["total_users"] or 0),
        "average_interactions_per_session": round(total / sessions, 2) if sessions else 0,
        "average_session_duration": None,
        "interaction_types": interaction_types,
        "most_used_features": [
            {
                "feature": row[0],
                "usage_count": row[1],
                "user_count": row[2],
                "popularity_score": round(row[1] / total * 100, 2) if total else 0,
            }
            for row in feature_rows
        ],
        "error_rate": round((int(totals["errors"] or 0) / total * 100) if total else 0, 2),
        "wizard_usage_stats": {
            "total_usage": int(wizard["total_usage"] or 0),
            "average_feedback_score": round(float(wizard["average_feedback_score"] or 0), 2),
            "helpful_percentage": round(float(wizard["helpful_percentage"] or 0), 2),
            "common_questions": [{"question": row[0], "feedback": row[1]} for row in question_rows],
        },
        "common_journey_patterns": [],
    }
