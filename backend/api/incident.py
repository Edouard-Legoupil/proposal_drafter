# backend/api/knowledge.py
import json
import os
import uuid
import logging
import asyncio
import concurrent.futures

from fastapi import APIRouter, Depends, HTTPException

from backend.core.db import get_engine
from backend.core.redis import redis_client
from backend.core.security import get_current_user, check_user_group_access
try:
    from backend.core.redis import DictStorage
except ImportError:
    # This will fail when redis is connected, but that's fine.
    class DictStorage:
        pass

from backend.utils.incident_service import IncidentService
from backend.utils.incident_repository import IncidentRepository

from backend.models.schemas import ArtifactType, Severity
from backend.models.schemas import IncidentAnalyzeRequest, IncidentAnalysisResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/incidents", tags=["Incidents"])


@router.post("/analyze", response_model=IncidentAnalysisResponse)
async def analyze_incident(
    payload: IncidentAnalyzeRequest,
):
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
):
    try:
        with get_engine().begin() as connection:
            repo = IncidentRepository(connection)
            review = repo.fetch_proposal_review(review_id)
            if not review:
                raise HTTPException(status_code=404, detail="Proposal review not found.")

            payload = IncidentAnalyzeRequest(
                artifact_type=ArtifactType.proposal,
                severity=Severity(review["severity"]),
                incident_type=review["type_of_comment"],
                source_review_id=review_id,
            )
            service = IncidentService(connection)
            return service.analyze_incident(payload)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Incident analysis failed: {e}")


@router.post("/analyze/knowledge-card-review/{review_id}", response_model=IncidentAnalysisResponse)
async def analyze_knowledge_card_review(
    review_id: str,
):
    try:
        with get_engine().begin() as connection:
            repo = IncidentRepository(connection)
            review = repo.fetch_knowledge_card_review(review_id)
            if not review:
                raise HTTPException(status_code=404, detail="Knowledge card review not found.")

            payload = IncidentAnalyzeRequest(
                artifact_type=ArtifactType.knowledge_card,
                severity=Severity(review["severity"]),
                incident_type=review["type_of_comment"],
                source_review_id=review_id,
            )
            service = IncidentService(connection)
            return service.analyze_incident(payload)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Incident analysis failed: {e}")


@router.post("/analyze/template-review/{review_id}", response_model=IncidentAnalysisResponse)
async def analyze_template_review(
    review_id: str,
):
    try:
        with get_engine().begin() as connection:
            repo = IncidentRepository(connection)
            review = repo.fetch_template_comment(review_id)
            if not review:
                raise HTTPException(status_code=404, detail="Template review not found.")

            payload = IncidentAnalyzeRequest(
                artifact_type=ArtifactType.template,
                severity=Severity(review["severity"]),
                incident_type=review["type_of_comment"],
                source_review_id=review_id,
            )
            service = IncidentService(connection)
            return service.analyze_incident(payload)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Incident analysis failed: {e}")


@router.get("/result/{analysis_id}")
async def get_incident_result(
    analysis_id: str,
):
    try:
        with get_engine().begin() as connection:
            service = IncidentService(connection)
            result = service.get_persisted_result(analysis_id)
            if not result:
                raise HTTPException(status_code=404, detail="Analysis result not found.")
            return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve analysis result: {e}")