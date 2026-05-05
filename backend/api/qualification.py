from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import logging

from backend.core.db import get_engine
from backend.core.security import get_current_user
from backend.utils.qualification_service import QualificationService

router = APIRouter()


@router.post("/qualification/run", status_code=202)
async def run_qualification(
    artifact_type: str,
    artifact_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """
    Schedule qualification rule evaluation for a given artifact.
    """
    background_tasks.add_task(_run_qualification_task, artifact_type, artifact_id)
    return {"message": "Qualification scheduled"}


@router.get("/qualification/status")
async def get_qualification_status(
    template_type: str = "proposal",
    current_user: dict = Depends(get_current_user),
):
    """
    Retrieve qualification summary for active templates and rules.
    Returns rule metadata and pass/fail for each template.
    """
    query_rules = text("""
        SELECT qr.rule_code, qr.rule_name, qr.description
        FROM qualification_rules qr
        JOIN qualification_rule_sets qs ON qr.rule_set_id = qs.id
        WHERE qs.template_type = :tpl AND qr.is_active
        ORDER BY qr.rule_code
    """)
    query_data = text("""
        SELECT
            tr.id::text as artifact_id,
            qr.rule_code,
            qre.result = 'pass' as passed
        FROM template_registry tr
        JOIN template_versions tv ON tv.template_registry_id = tr.id
        JOIN template_qualification_runs tqr ON tqr.template_version_id = tv.id
        JOIN qualification_rule_evaluations qre ON qre.qualification_run_id = tqr.id
        JOIN qualification_rules qr ON qre.rule_id = qr.id
        WHERE tr.template_type = :tpl
        ORDER BY tr.id, qr.rule_code, tqr.created_at DESC
    """)
    query_templates = text("""
        SELECT id::text as id, template_name
        FROM template_registry
        WHERE template_type = :tpl
    """)

    with get_engine().connect() as conn:
        rules = [
            dict(row)
            for row in conn.execute(query_rules, {"tpl": template_type}).mappings()
        ]
        templates = [
            dict(row)
            for row in conn.execute(query_templates, {"tpl": template_type}).mappings()
        ]
        rows = conn.execute(query_data, {"tpl": template_type}).mappings().all()

    # Build map of artifact_id -> result per rule_code (latest pass/fail)
    summaries = {}
    for template in templates:
        summaries[template["id"]] = {
            "template_name": template["template_name"],
            "results": {}
        }
        
    for row in rows:
        art = row["artifact_id"]
        if art not in summaries:
            summaries[art] = {
                "template_name": art,
                "results": {}
            }
        
        if row["rule_code"] not in summaries[art]["results"]:
            summaries[art]["results"][row["rule_code"]] = row["passed"]

    # Compose data array
    data = []
    for art_id, info in summaries.items():
        results = info["results"]
        overall = False
        if rules:
            overall = all(results.get(r["rule_code"], False) for r in rules)
            
        data.append(
            {
                "artifact_id": art_id,
                "template_name": info["template_name"],
                "overall": overall,
                "results": results,
            }
        )

    return {"rules": rules, "data": data}


def _run_qualification_task(artifact_type: str, artifact_id: str) -> None:
    try:
        with get_engine().begin() as connection:
            QualificationService(connection).run_for_artifact(
                artifact_type, artifact_id
            )
    except SQLAlchemyError as e:
        # Log and swallow to avoid background crash
        logger = logging.getLogger(__name__)
        logger.error(
            f"Background qualification failed for {artifact_type}/{artifact_id}: {e}",
            exc_info=True,
        )
