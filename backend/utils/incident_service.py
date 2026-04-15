from __future__ import annotations

import logging
import json
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
    ArtifactType,
    Severity,
)
from backend.utils.evidence_builder import EvidenceBuilder
from backend.utils.validators import validate_taxonomy, mandatory_human_review
from backend.core.config import settings

logger = logging.getLogger(__name__)


class IncidentService:
    def __init__(self, connection):
        self.connection = connection
        self.repo = IncidentRepository(connection)
        self.evidence_builder = EvidenceBuilder(self.repo)
        self.persistence = PersistenceRepository(connection)
        self.crew = IncidentAnalysisCrew()

    def analyze_incident(
        self, request: IncidentAnalyzeRequest
    ) -> IncidentAnalysisResponse:
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
        # Ensure consistency issues and flags are strings to satisfy Pydantic
        consistency_output["issues"] = [
            issue if isinstance(issue, str) else json.dumps(issue)
            for issue in consistency_output.get("issues", [])
        ]
        consistency_output["policy_flags"] = [
            flag if isinstance(flag, str) else json.dumps(flag)
            for flag in consistency_output.get("policy_flags", [])
        ]

        # Coerce any string entries in evidence_refs into minimal dicts for Pydantic
        refs = correction_output.get("evidence_refs", [])
        normalized_refs = []
        for ref in refs:
            if isinstance(ref, dict):
                normalized_refs.append(ref)
            else:
                normalized_refs.append({"id": str(ref)})
        correction_output["evidence_refs"] = normalized_refs
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
            knowledge_card_id=evidence_pack.get("incident", {}).get(
                "knowledge_card_id"
            ),
            template_request_id=evidence_pack.get("incident", {}).get(
                "template_request_id"
            ),
            section_name=evidence_pack.get("incident", {}).get("section_name"),
            user_comment=evidence_pack.get("incident", {}).get("user_comment"),
            normalized_summary=triage_output.get("normalized_summary"),
            evidence=evidence_pack.get("evidence", {}),
            user_suggestion=user_suggestion,
            root_cause_analysis=root_cause_analysis,
            suggested_system_fix=suggested_system_fix,
            consistency_check=consistency_check,
            needs_human_review=needs_review
            or triage_output.get("requires_human_review", False),
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

    def _needs_additional_info(self, analysis: IncidentAnalysisResponse) -> bool:
        confidence = getattr(analysis.user_suggestion, "confidence", 0.0) or 0.0
        human_reason = (analysis.human_review_reason or "").lower()
        keywords = ["missing", "context", "detail", "information", "clarity"]
        reason_triggers = any(keyword in human_reason for keyword in keywords)
        return analysis.needs_human_review and (confidence < 0.65 or reason_triggers)

    def _build_system_reply(
        self, analysis: IncidentAnalysisResponse
    ) -> tuple[str, str]:
        summary = (analysis.user_suggestion.summary or "").strip()
        action = (analysis.user_suggestion.proposed_action or "").strip()
        parts = []
        if summary:
            parts.append(summary)
        if action and action not in summary:
            parts.append(action)
        base_message = (
            "\n\n".join(parts)
            if parts
            else "The automated analysis generated a response."
        )

        if self._needs_additional_info(analysis):
            reason = (
                analysis.human_review_reason
                or "Additional context is required to proceed."
            )
            follow_up = (
                "The automated analysis requires more information before providing a confident recommendation. "
                f"{reason.strip()} Please reply with any relevant documents or clarifications you can share."
            )
            return f"{base_message}\n\n{follow_up}".strip(), "needs-more-info"

        return base_message.strip(), "pending"

    def auto_analyze_review(self, artifact_type: ArtifactType, review_id: str):
        """
        Background task to run analysis crew and update review status/response.
        """
        # 1. Fetch review data
        review = None
        if artifact_type == ArtifactType.proposal:
            review = self.repo.fetch_proposal_review(review_id)
        elif artifact_type == ArtifactType.knowledge_card:
            review = self.repo.fetch_knowledge_card_review(review_id)
        elif artifact_type == ArtifactType.template:
            review = self.repo.fetch_template_comment(review_id)

        if not review:
            logger.warning(f"Could not find review {review_id} for {artifact_type}")
            return

        # 2. Run analysis
        try:
            request = IncidentAnalyzeRequest(
                artifact_type=artifact_type,
                severity=Severity(review["severity"]),
                incident_type=review["type_of_comment"],
                source_review_id=review_id,
            )
            analysis = self.analyze_incident(request)
            auto_reply, reply_status = self._build_system_reply(analysis)

            if artifact_type == ArtifactType.proposal:
                self.repo.update_proposal_review(
                    review_id, auto_reply, reply_status, response_author="system"
                )
            elif artifact_type == ArtifactType.knowledge_card:
                self.repo.update_knowledge_card_review(
                    review_id, auto_reply, reply_status, response_author="system"
                )
            elif artifact_type == ArtifactType.template:
                self.repo.update_template_comment(
                    review_id, auto_reply, reply_status, response_author="system"
                )

            logger.info(
                f"Auto-analysis completed for {artifact_type} review {review_id}"
            )

        except Exception as e:
            logger.error(
                f"Auto-analysis failed for {artifact_type} review {review_id}: {e}",
                exc_info=True,
            )
