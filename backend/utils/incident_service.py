from __future__ import annotations

from datetime import datetime, timezone
import uuid

from backend.utils.crew_incident_analysis import IncidentAnalysisCrew
from backend.utils.incident_repository import IncidentRepository
from backend.utils.persistence_repository import PersistenceRepository
from backend.models.schemas import (
    IncidentAnalyzeRequest,
    IncidentAnalysisResponse,
    UserSuggestion,
    RootCauseAnalysis,
    SuggestedSystemFix,
    ConsistencyCheck,
)
from backend.utils.evidence_builder import EvidenceBuilder
from backend.utils.validators import validate_taxonomy, mandatory_human_review
from backend.core.config import settings


class IncidentService:
    def __init__(self, connection):
        self.connection = connection
        self.repo = IncidentRepository(connection)
        self.evidence_builder = EvidenceBuilder(self.repo)
        self.persistence = PersistenceRepository(connection)
        self.crew = IncidentAnalysisCrew()

    def analyze_incident(self, request: IncidentAnalyzeRequest) -> IncidentAnalysisResponse:
        validate_taxonomy(
            artifact_type=request.artifact_type.value,
            severity=request.severity.value,
            incident_type=request.incident_type,
        )

        evidence_pack = self.evidence_builder.build_from_request(request)
        incident = evidence_pack["incident"]

        crew_result = self.crew.analyze(incident=incident, evidence_pack=evidence_pack)

        triage_output = crew_result["triage_output"]
        correction_output = crew_result["correction_output"]
        rca_output = crew_result["rca_output"]
        remediation_output = crew_result["remediation_output"]
        consistency_output = crew_result["consistency_output"]

        user_suggestion = UserSuggestion.model_validate(correction_output)
        root_cause_analysis = RootCauseAnalysis.model_validate(rca_output)
        suggested_system_fix = SuggestedSystemFix.model_validate(remediation_output)
        consistency_check = ConsistencyCheck.model_validate(consistency_output)

        needs_review, review_reason = mandatory_human_review(
            severity=request.severity.value,
            confidence_values=[
                user_suggestion.confidence,
                root_cause_analysis.confidence,
                suggested_system_fix.confidence,
            ],
        )

        now = datetime.now(timezone.utc).isoformat()
        incident_id = str(uuid.uuid4())

        response = IncidentAnalysisResponse(
            incident_id=incident_id,
            artifact_type=request.artifact_type,
            severity=request.severity,
            incident_type=request.incident_type,
            status="analyzed",
            source_review_id=request.source_review_id,
            proposal_id=evidence_pack.get("incident", {}).get("proposal_id"),
            knowledge_card_id=evidence_pack.get("incident", {}).get("knowledge_card_id"),
            template_request_id=evidence_pack.get("incident", {}).get("template_request_id"),
            section_name=evidence_pack.get("incident", {}).get("section_name"),
            user_comment=evidence_pack.get("incident", {}).get("user_comment"),
            normalized_summary=triage_output.get("normalized_summary"),
            evidence=evidence_pack.get("evidence", {}),
            user_suggestion=user_suggestion,
            root_cause_analysis=root_cause_analysis,
            suggested_system_fix=suggested_system_fix,
            consistency_check=consistency_check,
            needs_human_review=needs_review or triage_output.get("requires_human_review", False),
            human_review_reason=review_reason,
            routing={
                "priority_score": triage_output.get("priority_score"),
                "routing_plan": triage_output.get("routing_plan", []),
            },
            agent_versions=crew_result["agent_versions"],
            created_at=now,
            updated_at=now,
        )

        if settings.persist_analysis_results and request.source_review_id:
            try:
                self.persistence.save_incident_analysis(
                    artifact_type=request.artifact_type.value,
                    source_review_id=request.source_review_id,
                    proposal_id=response.proposal_id,
                    knowledge_card_id=response.knowledge_card_id,
                    template_request_id=response.template_request_id,
                    incident_type=request.incident_type,
                    severity=request.severity.value,
                    analysis_payload=response.model_dump(mode="json"),
                )
            except Exception:
                # Don’t fail the API response if persistence is not set up yet
                pass

        return response

    def get_persisted_result(self, analysis_id: str):
        return self.persistence.get_analysis_result(analysis_id)