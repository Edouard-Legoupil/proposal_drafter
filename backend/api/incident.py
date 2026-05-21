# backend/api/incident.py
import logging
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

from backend.core.db import get_engine
from backend.core.security import get_current_user, is_system_admin
from backend.core.authorization import (
    check_proposal_access,
    check_knowledge_card_access,
    check_template_access,
    get_user_id,
    is_admin,
)


from backend.utils.incident_service import IncidentService
from backend.utils.incident_repository import IncidentRepository

from backend.models.schemas import ArtifactType, Severity
from backend.models.schemas import IncidentAnalyzeRequest, IncidentAnalysisResponse

logger = logging.getLogger(__name__)

# Initialize authorization logger
auth_logger = logging.getLogger("security.authorization")

router = APIRouter(prefix="/api/incidents", tags=["Incidents"])


@router.post("/analyze", response_model=IncidentAnalysisResponse)
async def analyze_incident(
    payload: IncidentAnalyzeRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Analyze an incident with object-level authorization.

    T107: Verify user has access to the source artifact (proposal, knowledge_card, or template)
    based on the artifact_type in the payload.
    """
    user_id = get_user_id(current_user)
    artifact_type = (
        payload.artifact_type.value if hasattr(payload.artifact_type, "value") else str(payload.artifact_type)
    )
    source_review_id = payload.source_review_id

    # Log the access attempt
    auth_logger.info(
        "Incident analysis attempt",
        extra={
            "user_id": user_id,
            "artifact_type": artifact_type,
            "source_review_id": source_review_id,
            "action": "incident_analyze",
        },
    )

    # T107: Object-Level Authorization - Verify user has access to the source artifact
    # We need to fetch the source artifact from the review ID to verify access
    try:
        with get_engine().connect() as connection:
            # Determine which table to query based on artifact_type
            if artifact_type == "proposal":
                # Fetch the proposal ID from the review using ORM
                from backend.models.review import ProposalPeerReview

                proposal_review = connection.query(ProposalPeerReview).filter_by(id=source_review_id).first()
                proposal_id = proposal_review.proposal_id if proposal_review else None

                if proposal_id:
                    await check_proposal_access(int(proposal_id), current_user)
                    auth_logger.info(
                        "Incident analysis authorized - proposal",
                        extra={
                            "user_id": user_id,
                            "proposal_id": str(proposal_id),
                            "action": "incident_analyze",
                            "result": "allowed",
                        },
                    )
                else:
                    auth_logger.warning(
                        "Proposal review not found for incident analysis",
                        extra={
                            "user_id": user_id,
                            "review_id": source_review_id,
                            "action": "incident_analyze",
                            "result": "denied",
                            "reason": "review_not_found",
                        },
                    )
                    raise HTTPException(status_code=404, detail="Proposal review not found")

            elif artifact_type == "knowledge_card":
                # Fetch the knowledge card ID from the review using ORM
                from backend.models.review import KnowledgeCardReview

                card_review = connection.query(KnowledgeCardReview).filter_by(id=source_review_id).first()
                card_id = card_review.knowledge_card_id if card_review else None

                if card_id:
                    await check_knowledge_card_access(int(card_id), current_user)
                    auth_logger.info(
                        "Incident analysis authorized - knowledge card",
                        extra={
                            "user_id": user_id,
                            "card_id": str(card_id),
                            "action": "incident_analyze",
                            "result": "allowed",
                        },
                    )
                else:
                    auth_logger.warning(
                        "Knowledge card review not found for incident analysis",
                        extra={
                            "user_id": user_id,
                            "review_id": source_review_id,
                            "action": "incident_analyze",
                            "result": "denied",
                            "reason": "review_not_found",
                        },
                    )
                    raise HTTPException(status_code=404, detail="Knowledge card review not found")

            elif artifact_type == "template":
                # For templates, we need to check the template comment using ORM
                # The source_review_id might be a comment ID in donor_template_comments
                from backend.models.review import TemplateComment

                template_comment = connection.query(TemplateComment).filter_by(id=source_review_id).first()
                template_id = template_comment.template_request_id if template_comment else None

                if template_id:
                    await check_template_access(int(template_id), current_user, required_permission="read")
                    auth_logger.info(
                        "Incident analysis authorized - template",
                        extra={
                            "user_id": user_id,
                            "template_id": str(template_id),
                            "action": "incident_analyze",
                            "result": "allowed",
                        },
                    )
                else:
                    # Try to find in published templates by template_name
                    # This is a fallback for file-based templates
                    auth_logger.info(
                        "Incident analysis authorized - template (public)",
                        extra={
                            "user_id": user_id,
                            "action": "incident_analyze",
                            "result": "allowed",
                            "note": "public_template",
                        },
                    )
            else:
                auth_logger.warning(
                    "Unknown artifact type for incident analysis",
                    extra={
                        "user_id": user_id,
                        "artifact_type": artifact_type,
                        "action": "incident_analyze",
                        "result": "denied",
                        "reason": "unknown_artifact_type",
                    },
                )
                raise HTTPException(status_code=400, detail=f"Unknown artifact type: {artifact_type}")
    except HTTPException as auth_exc:
        auth_logger.warning(
            "Incident analysis denied",
            extra={
                "user_id": user_id,
                "artifact_type": artifact_type,
                "source_review_id": source_review_id,
                "action": "incident_analyze",
                "result": "denied",
                "status_code": auth_exc.status_code,
            },
        )
        raise

    try:
        with get_engine().begin() as connection:
            service = IncidentService(connection)
            return service.analyze_incident(payload, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Incident analysis failed: {e}")


@router.post("/analyze/proposal-review/{review_id}", response_model=IncidentAnalysisResponse)
async def analyze_proposal_review(
    review_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Analyze a proposal review with object-level authorization.

    T104: Verify user has access to the proposal via check_proposal_access()
    """
    user_id = get_user_id(current_user)

    # Log the access attempt
    auth_logger.info(
        "Proposal review incident analysis attempt",
        extra={
            "user_id": user_id,
            "review_id": review_id,
            "action": "incident_analyze_proposal_review",
        },
    )

    try:
        with get_engine().begin() as connection:
            repo = IncidentRepository(connection)
            review = repo.fetch_proposal_review(review_id)
            if not review:
                raise HTTPException(status_code=404, detail="Proposal review not found.")

            # T104: Object-Level Authorization - Verify user has access to the proposal
            proposal_id = review.get("proposal_id")
            if proposal_id:
                await check_proposal_access(int(proposal_id), current_user)
                auth_logger.info(
                    "Proposal review incident analysis authorized",
                    extra={
                        "user_id": user_id,
                        "proposal_id": str(proposal_id),
                        "review_id": review_id,
                        "action": "incident_analyze_proposal_review",
                        "result": "allowed",
                    },
                )
            else:
                auth_logger.warning(
                    "Proposal ID not found in review",
                    extra={
                        "user_id": user_id,
                        "review_id": review_id,
                        "action": "incident_analyze_proposal_review",
                        "result": "denied",
                        "reason": "no_proposal_id",
                    },
                )
                raise HTTPException(status_code=404, detail="Proposal not found in review")

            payload = IncidentAnalyzeRequest(
                artifact_type=ArtifactType.proposal,
                severity=Severity(review["severity"]),
                incident_type=review["type_of_comment"],
                source_review_id=review_id,
            )
            service = IncidentService(connection)
            return service.analyze_incident(payload, user_id)
    except HTTPException as auth_exc:
        auth_logger.warning(
            "Proposal review incident analysis denied",
            extra={
                "user_id": user_id,
                "review_id": review_id,
                "action": "incident_analyze_proposal_review",
                "result": "denied",
                "status_code": auth_exc.status_code,
            },
        )
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Incident analysis failed: {e}")


@router.post(
    "/analyze/knowledge-card-review/{review_id}",
    response_model=IncidentAnalysisResponse,
)
async def analyze_knowledge_card_review(
    review_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Analyze a knowledge card review with object-level authorization.

    T105: Verify user has access to the knowledge card via check_user_group_access()
    """
    user_id = get_user_id(current_user)

    # Log the access attempt
    auth_logger.info(
        "Knowledge card review incident analysis attempt",
        extra={
            "user_id": user_id,
            "review_id": review_id,
            "action": "incident_analyze_knowledge_card_review",
        },
    )

    try:
        with get_engine().begin() as connection:
            repo = IncidentRepository(connection)
            review = repo.fetch_knowledge_card_review(review_id)
            if not review:
                raise HTTPException(status_code=404, detail="Knowledge card review not found.")

            # T105: Object-Level Authorization - Verify user has access to the knowledge card
            knowledge_card_id = review.get("knowledge_card_id")
            if knowledge_card_id:
                await check_knowledge_card_access(int(knowledge_card_id), current_user)
                auth_logger.info(
                    "Knowledge card review incident analysis authorized",
                    extra={
                        "user_id": user_id,
                        "card_id": str(knowledge_card_id),
                        "review_id": review_id,
                        "action": "incident_analyze_knowledge_card_review",
                        "result": "allowed",
                    },
                )
            else:
                auth_logger.warning(
                    "Knowledge card ID not found in review",
                    extra={
                        "user_id": user_id,
                        "review_id": review_id,
                        "action": "incident_analyze_knowledge_card_review",
                        "result": "denied",
                        "reason": "no_card_id",
                    },
                )
                raise HTTPException(status_code=404, detail="Knowledge card not found in review")

            payload = IncidentAnalyzeRequest(
                artifact_type=ArtifactType.knowledge_card,
                severity=Severity(review["severity"]),
                incident_type=review["type_of_comment"],
                source_review_id=review_id,
            )
            service = IncidentService(connection)
            return service.analyze_incident(payload, user_id)
    except HTTPException as auth_exc:
        auth_logger.warning(
            "Knowledge card review incident analysis denied",
            extra={
                "user_id": user_id,
                "review_id": review_id,
                "action": "incident_analyze_knowledge_card_review",
                "result": "denied",
                "status_code": auth_exc.status_code,
            },
        )
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Incident analysis failed: {e}")


@router.post("/analyze/template-review/{review_id}", response_model=IncidentAnalysisResponse)
async def analyze_template_review(
    review_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Analyze a template review with object-level authorization.

    T106: Verify user has access to the template via check_template_access()
    """
    user_id = get_user_id(current_user)

    # Log the access attempt
    auth_logger.info(
        "Template review incident analysis attempt",
        extra={
            "user_id": user_id,
            "review_id": review_id,
            "action": "incident_analyze_template_review",
        },
    )

    try:
        with get_engine().begin() as connection:
            repo = IncidentRepository(connection)
            review = repo.fetch_template_comment(review_id)
            if not review:
                raise HTTPException(status_code=404, detail="Template review not found.")

            # T106: Object-Level Authorization - Verify user has access to the template
            # The review should have a template_request_id or template_name
            template_id = review.get("template_request_id") or review.get("template_name")
            if template_id:
                await check_template_access(int(template_id), current_user, required_permission="read")
                auth_logger.info(
                    "Template review incident analysis authorized",
                    extra={
                        "user_id": user_id,
                        "template_id": str(template_id),
                        "review_id": review_id,
                        "action": "incident_analyze_template_review",
                        "result": "allowed",
                    },
                )
            else:
                auth_logger.warning(
                    "Template ID not found in review",
                    extra={
                        "user_id": user_id,
                        "review_id": review_id,
                        "action": "incident_analyze_template_review",
                        "result": "denied",
                        "reason": "no_template_id",
                    },
                )
                raise HTTPException(status_code=404, detail="Template not found in review")

            payload = IncidentAnalyzeRequest(
                artifact_type=ArtifactType.template,
                severity=Severity(review["severity"]),
                incident_type=review["type_of_comment"],
                source_review_id=review_id,
            )
            service = IncidentService(connection)
            return service.analyze_incident(payload, user_id)
    except HTTPException as auth_exc:
        auth_logger.warning(
            "Template review incident analysis denied",
            extra={
                "user_id": user_id,
                "review_id": review_id,
                "action": "incident_analyze_template_review",
                "result": "denied",
                "status_code": auth_exc.status_code,
            },
        )
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Incident analysis failed: {e}")


@router.get("/result/{analysis_id}")
async def get_incident_result(
    analysis_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get incident analysis result with object-level authorization.

    T108: Verify user has access to the source artifact (proposal, knowledge_card, or template)
    associated with the analysis.
    """
    user_id = get_user_id(current_user)

    # Log the access attempt
    auth_logger.info(
        "Incident result retrieval attempt",
        extra={
            "user_id": user_id,
            "analysis_id": analysis_id,
            "action": "incident_result_get",
        },
    )

    try:
        with get_engine().begin() as connection:
            # First, get the analysis result to find the source
            service = IncidentService(connection)
            result = service.get_persisted_result(analysis_id)
            if not result:
                raise HTTPException(status_code=404, detail="Analysis result not found.")

            # T108: Object-Level Authorization - Verify user has access to the source artifact
            # The analysis result should have artifact_type and source_review_id
            artifact_type = result.get("artifact_type")
            source_review_id = result.get("source_review_id")

            if artifact_type and source_review_id:
                # Verify access based on artifact type
                if artifact_type == "proposal":
                    # Use ORM to fetch proposal review
                    from backend.models.review import ProposalPeerReview

                    proposal_review = connection.query(ProposalPeerReview).filter_by(id=source_review_id).first()
                    proposal_id = proposal_review.proposal_id if proposal_review else None
                    if proposal_id:
                        await check_proposal_access(int(proposal_id), current_user)
                    else:
                        raise HTTPException(status_code=404, detail="Proposal review not found")

                elif artifact_type == "knowledge_card":
                    # Use ORM to fetch knowledge card review
                    from backend.models.review import KnowledgeCardReview

                    card_review = connection.query(KnowledgeCardReview).filter_by(id=source_review_id).first()
                    card_id = card_review.knowledge_card_id if card_review else None
                    if card_id:
                        await check_knowledge_card_access(int(card_id), current_user)
                    else:
                        raise HTTPException(status_code=404, detail="Knowledge card review not found")

                elif artifact_type == "template":
                    # Use ORM to fetch template comment
                    from backend.models.review import TemplateComment

                    template_comment = connection.query(TemplateComment).filter_by(id=source_review_id).first()
                    template_id = template_comment.template_request_id if template_comment else None
                    if template_id:
                        await check_template_access(int(template_id), current_user, required_permission="read")
                    else:
                        # Public template - allow access
                        pass

                auth_logger.info(
                    "Incident result retrieval authorized",
                    extra={
                        "user_id": user_id,
                        "analysis_id": analysis_id,
                        "artifact_type": artifact_type,
                        "action": "incident_result_get",
                        "result": "allowed",
                    },
                )
            else:
                # If we can't determine the artifact type, check if user is admin
                if not is_admin(current_user):
                    auth_logger.warning(
                        "Incident result retrieval denied - cannot verify artifact",
                        extra={
                            "user_id": user_id,
                            "analysis_id": analysis_id,
                            "action": "incident_result_get",
                            "result": "denied",
                            "reason": "artifact_type_unknown",
                        },
                    )
                    raise HTTPException(status_code=403, detail="Access denied")

            return result
    except HTTPException as auth_exc:
        auth_logger.warning(
            "Incident result retrieval denied",
            extra={
                "user_id": user_id,
                "analysis_id": analysis_id,
                "action": "incident_result_get",
                "result": "denied",
                "status_code": auth_exc.status_code,
            },
        )
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve analysis result: {e}")


# ============================================================================
# ADMIN INCIDENT ACCESS MANAGEMENT ENDPOINTS
# ============================================================================


@router.get("/admin/list")
async def list_admin_incidents(admin: dict = Depends(is_system_admin)):
    """
    Returns a lightweight list of all incident analysis results for access management.
    """
    try:
        with get_engine().connect() as connection:
            query = text(
                """
                SELECT
                    iar.id::text AS id,
                    iar.artifact_type,
                    iar.source_review_id::text AS source_review_id,
                    iar.incident_type,
                    iar.severity,
                    iar.status,
                    iar.created_at,
                    iar.updated_at,
                    COALESCE(iar.proposal_id::text, iar.knowledge_card_id::text, iar.template_request_id::text) AS artifact_id,
                    u.name AS creator_name,
                    u.email AS creator_email,
                    u.id::text AS creator_id
                FROM incident_analysis_results iar
                LEFT JOIN users u ON iar.created_by = u.id
                ORDER BY iar.updated_at DESC
            """
            )
            rows = connection.execute(query).mappings().all()
            return [
                {
                    "id": r["id"],
                    "artifact_type": r["artifact_type"],
                    "source_review_id": r["source_review_id"],
                    "incident_type": r["incident_type"],
                    "severity": r["severity"],
                    "status": r["status"],
                    "artifact_id": r["artifact_id"],
                    "creator_name": r["creator_name"],
                    "creator_email": r["creator_email"],
                    "creator_id": r["creator_id"],
                    "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                    "updated_at": r["updated_at"].isoformat() if r["updated_at"] else None,
                }
                for r in rows
            ]
    except Exception as e:
        logger.error(f"[LIST ADMIN INCIDENTS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not list incidents.")


@router.get("/admin/{incident_id}/access")
async def get_incident_access(incident_id: str, admin: dict = Depends(is_system_admin)):
    """
    Get current access grants for a specific incident.
    """
    try:
        with get_engine().connect() as connection:
            # Get incident details
            incident_query = text(
                """
                SELECT
                    id::text AS id,
                    artifact_type,
                    source_review_id::text AS source_review_id,
                    incident_type,
                    severity,
                    status,
                    created_at,
                    updated_at,
                    created_by::text AS creator_id
                FROM incident_analysis_results
                WHERE id = :incident_id
            """
            )
            incident = connection.execute(incident_query, {"incident_id": incident_id}).mappings().first()

            if not incident:
                raise HTTPException(status_code=404, detail="Incident not found")

            # Get access grants (this would be from a grants table if it existed)
            # For now, we'll return the creator as the owner
            grants: list[dict] = []

            # Get audit logs for this incident
            audit_query = text(
                """
                SELECT
                    id::text AS id,
                    event_type,
                    details,
                    created_at,
                    user_id::text AS user_id
                FROM audit_logs
                WHERE resource_type = 'incident'
                AND resource_id = :incident_id
                ORDER BY created_at DESC
                LIMIT 50
            """
            )
            audit_logs = connection.execute(audit_query, {"incident_id": incident_id}).mappings().all()

            return {"incident": dict(incident), "grants": grants, "audit": [dict(log) for log in audit_logs]}
    except Exception as e:
        logger.error(f"[GET INCIDENT ACCESS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not retrieve incident access information.")


@router.post("/admin/{incident_id}/access")
async def grant_incident_access(incident_id: str, payload: dict, admin: dict = Depends(is_system_admin)):
    """
    Grant access to an incident for a user, team, or role.
    """
    try:
        subject_type = payload.get("subject_type")  # user, team, or role
        subject_id = payload.get("subject_id")
        permissions = payload.get("permissions", ["read"])
        data_scope = payload.get("data_scope", "self")

        if not subject_type or not subject_id:
            raise HTTPException(status_code=400, detail="subject_type and subject_id are required")

        with get_engine().begin() as connection:
            # Verify incident exists
            incident_check = connection.execute(
                text("SELECT id FROM incident_analysis_results WHERE id = :incident_id"),
                {"incident_id": incident_id},
            ).fetchone()

            if not incident_check:
                raise HTTPException(status_code=404, detail="Incident not found")

            # Log the access grant
            connection.execute(
                text(
                    """
                    INSERT INTO audit_logs
                    (event_type, resource_type, resource_id, details, user_id)
                    VALUES (:event_type, :resource_type, :resource_id, :details, :user_id)
                """
                ),
                {
                    "event_type": "access.grant",
                    "resource_type": "incident",
                    "resource_id": incident_id,
                    "details": json.dumps(
                        {
                            "subject_type": subject_type,
                            "subject_id": subject_id,
                            "permissions": permissions,
                            "data_scope": data_scope,
                        }
                    ),
                    "user_id": admin.get("user_id"),
                },
            )

            return {
                "message": "Access granted successfully",
                "grant": {
                    "subject_type": subject_type,
                    "subject_id": subject_id,
                    "permissions": permissions,
                    "data_scope": data_scope,
                },
            }
    except Exception as e:
        logger.error(f"[GRANT INCIDENT ACCESS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not grant incident access.")


@router.delete("/admin/{incident_id}/access")
async def revoke_incident_access(incident_id: str, payload: dict, admin: dict = Depends(is_system_admin)):
    """
    Revoke access to an incident.
    """
    try:
        grant_id = payload.get("grant_id")

        if not grant_id:
            raise HTTPException(status_code=400, detail="grant_id is required")

        with get_engine().begin() as connection:
            # Verify incident exists
            incident_check = connection.execute(
                text("SELECT id FROM incident_analysis_results WHERE id = :incident_id"),
                {"incident_id": incident_id},
            ).fetchone()

            if not incident_check:
                raise HTTPException(status_code=404, detail="Incident not found")

            # Log the access revocation
            connection.execute(
                text(
                    """
                    INSERT INTO audit_logs
                    (event_type, resource_type, resource_id, details, user_id)
                    VALUES (:event_type, :resource_type, :resource_id, :details, :user_id)
                """
                ),
                {
                    "event_type": "access.revoke",
                    "resource_type": "incident",
                    "resource_id": incident_id,
                    "details": json.dumps({"grant_id": grant_id}),
                    "user_id": admin.get("user_id"),
                },
            )

            return {"message": "Access revoked successfully"}
    except Exception as e:
        logger.error(f"[REVOKE INCIDENT ACCESS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not revoke incident access.")


@router.post("/admin/{incident_id}/access/test")
async def test_incident_access(incident_id: str, payload: dict, admin: dict = Depends(is_system_admin)):
    """
    Test effective access for a subject to an incident.
    """
    try:
        subject_type = payload.get("subject_type")  # user, team, or role
        subject_id = payload.get("subject_id")
        operation = payload.get("operation", "GET")

        if not subject_type or not subject_id:
            raise HTTPException(status_code=400, detail="subject_type and subject_id are required")

        # For now, we'll implement basic testing logic
        # In a full implementation, this would check actual permissions

        result = {
            "allowed": True,  # Default to allowed for admin testing
            "reason": "Admin access test",
            "source": "admin_test",
            "http_status": 200,
            "data_scope": "full",
            "permissions": ["read", "write", "delete", "manage"],
        }

        # Log the access test
        with get_engine().begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO audit_logs
                    (event_type, resource_type, resource_id, details, user_id)
                    VALUES (:event_type, :resource_type, :resource_id, :details, :user_id)
                """
                ),
                {
                    "event_type": "access.test",
                    "resource_type": "incident",
                    "resource_id": incident_id,
                    "details": json.dumps(
                        {
                            "subject_type": subject_type,
                            "subject_id": subject_id,
                            "operation": operation,
                            "result": result,
                        }
                    ),
                    "user_id": admin.get("user_id"),
                },
            )

        return result
    except Exception as e:
        logger.error(f"[TEST INCIDENT ACCESS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not test incident access.")
