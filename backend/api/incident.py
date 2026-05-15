# backend/api/incident.py
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

from backend.core.db import get_engine
from backend.core.security import get_current_user
from backend.core.authorization import (
    check_proposal_access,
    check_knowledge_card_access,
    check_template_access,
    get_user_id,
    is_admin,
)

try:
    from backend.core.redis import DictStorage
except ImportError:
    # This will fail when redis is connected, but that's fine.
    # DictStorage is already imported from backend.core.redis
    pass


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
                # Fetch the proposal ID from the review
                proposal_id = connection.execute(
                    text("SELECT proposal_id FROM proposal_peer_reviews WHERE id = :review_id"),
                    {"review_id": source_review_id},
                ).scalar()

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
                # Fetch the knowledge card ID from the review
                card_id = connection.execute(
                    text("SELECT knowledge_card_id FROM knowledge_card_reviews WHERE id = :review_id"),
                    {"review_id": source_review_id},
                ).scalar()

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
                # For templates, we need to check the template comment
                # The source_review_id might be a comment ID in donor_template_comments
                template_id = connection.execute(
                    text("SELECT template_request_id FROM donor_template_comments WHERE id = :comment_id"),
                    {"comment_id": source_review_id},
                ).scalar()

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
            return service.analyze_incident(payload)
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
            return service.analyze_incident(payload)
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
            return service.analyze_incident(payload)
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
            return service.analyze_incident(payload)
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
                    proposal_id = connection.execute(
                        text("SELECT proposal_id FROM proposal_peer_reviews WHERE id = :review_id"),
                        {"review_id": source_review_id},
                    ).scalar()
                    if proposal_id:
                        await check_proposal_access(int(proposal_id), current_user)
                    else:
                        raise HTTPException(status_code=404, detail="Proposal review not found")

                elif artifact_type == "knowledge_card":
                    card_id = connection.execute(
                        text("SELECT knowledge_card_id FROM knowledge_card_reviews WHERE id = :review_id"),
                        {"review_id": source_review_id},
                    ).scalar()
                    if card_id:
                        await check_knowledge_card_access(int(card_id), current_user)
                    else:
                        raise HTTPException(status_code=404, detail="Knowledge card review not found")

                elif artifact_type == "template":
                    template_id = connection.execute(
                        text("SELECT template_request_id FROM donor_template_comments WHERE id = :comment_id"),
                        {"comment_id": source_review_id},
                    ).scalar()
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
