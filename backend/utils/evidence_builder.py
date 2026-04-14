from __future__ import annotations

from typing import Any
from backend.utils.incident_repository import IncidentRepository
from backend.models.schemas import ROOT_CAUSE_PRIORS


class EvidenceBuilder:
    def __init__(self, repo: IncidentRepository):
        self.repo = repo

    def build_from_request(self, request) -> dict[str, Any]:
        if request.source_review_id:
            if request.artifact_type.value == "proposal":
                return self._build_proposal_evidence(request.source_review_id)
            if request.artifact_type.value == "knowledge_card":
                return self._build_knowledge_card_evidence(request.source_review_id)
            if request.artifact_type.value == "template":
                return self._build_template_evidence(request.source_review_id)

        # manual fallback mode
        return {
            "incident": {
                "artifact_type": request.artifact_type.value,
                "severity": request.severity.value,
                "incident_type": request.incident_type,
                "source_review_id": request.source_review_id,
                "proposal_id": request.proposal_id,
                "knowledge_card_id": request.knowledge_card_id,
                "template_request_id": request.template_request_id,
                "section_name": request.section_name,
                "user_comment": request.user_comment,
            },
            "evidence": {
                "evidence_quality": "low",
                "note": "Evidence was supplied manually rather than loaded from review tables."
            },
            "priors": ROOT_CAUSE_PRIORS[request.artifact_type.value].get(request.incident_type, []),
        }

    def _build_proposal_evidence(self, review_id: str) -> dict[str, Any]:
        review = self.repo.fetch_proposal_review(review_id)
        if not review:
            raise ValueError(f"Proposal review '{review_id}' not found.")

        history = None
        if review.get("proposal_id"):
            history = self.repo.fetch_latest_proposal_history(review["proposal_id"])
            dimensions = self.repo.fetch_proposal_dimensions(review["proposal_id"])
        else:
            dimensions = {}

        return {
            "incident": {
                "artifact_type": "proposal",
                "severity": review["severity"],
                "incident_type": review["type_of_comment"],
                "source_review_id": review["review_id"],
                "proposal_id": review.get("proposal_id"),
                "section_name": review.get("section_name"),
                "user_comment": review.get("review_text"),
            },
            "proposal": {
                "proposal_id": review.get("proposal_id"),
                "template_name": review.get("template_name"),
                "form_data": review.get("form_data"),
                "project_description": review.get("project_description"),
                "generated_sections": review.get("generated_sections"),
                "reviews": review.get("reviews"),
                "proposal_status": review.get("proposal_status"),
                "contribution_id": review.get("contribution_id"),
            },
            "review": review,
            "history": history,
            "dimensions": dimensions,
            "evidence": {
                "proposal_excerpt": self._extract_section(review.get("generated_sections"), review.get("section_name")),
                "evidence_quality": "high" if review.get("generated_sections") else "medium",
            },
            "priors": ROOT_CAUSE_PRIORS["proposal"].get(review["type_of_comment"], []),
        }

    def _build_knowledge_card_evidence(self, review_id: str) -> dict[str, Any]:
        review = self.repo.fetch_knowledge_card_review(review_id)
        if not review:
            raise ValueError(f"Knowledge card review '{review_id}' not found.")

        history = self.repo.fetch_knowledge_card_history(review["knowledge_card_id"])
        refs = self.repo.fetch_knowledge_card_references(review["knowledge_card_id"])
        chunks = self.repo.fetch_reference_chunks(review["knowledge_card_id"])
        rag_logs = self.repo.fetch_rag_logs(review["knowledge_card_id"])

        return {
            "incident": {
                "artifact_type": "knowledge_card",
                "severity": review["severity"],
                "incident_type": review["type_of_comment"],
                "source_review_id": review["review_id"],
                "knowledge_card_id": review.get("knowledge_card_id"),
                "section_name": review.get("section_name"),
                "user_comment": review.get("review_text"),
            },
            "knowledge_card": {
                "knowledge_card_id": review.get("knowledge_card_id"),
                "template_name": review.get("template_name"),
                "type": review.get("knowledge_card_type"),
                "summary": review.get("summary"),
                "generated_sections": review.get("generated_sections"),
                "status": review.get("knowledge_card_status"),
                "donor_id": review.get("donor_id"),
                "outcome_id": review.get("outcome_id"),
                "field_context_id": review.get("field_context_id"),
            },
            "review": review,
            "history": history,
            "references": refs,
            "reference_chunks": chunks,
            "rag_logs": rag_logs,
            "evidence": {
                "proposal_excerpt": self._extract_section(review.get("generated_sections"), review.get("section_name")),
                "knowledge_card_refs": refs,
                "trace_refs": rag_logs,
                "evidence_quality": "high" if refs or rag_logs else "medium",
            },
            "priors": ROOT_CAUSE_PRIORS["knowledge_card"].get(review["type_of_comment"], []),
        }

    def _build_template_evidence(self, review_id: str) -> dict[str, Any]:
        review = self.repo.fetch_template_comment(review_id)
        if not review:
            raise ValueError(f"Template review '{review_id}' not found.")

        return {
            "incident": {
                "artifact_type": "template",
                "severity": review["severity"],
                "incident_type": review["type_of_comment"],
                "source_review_id": review["review_id"],
                "template_request_id": review.get("template_request_id"),
                "section_name": review.get("section_name"),
                "user_comment": review.get("review_text"),
            },
            "template": {
                "template_request_id": review.get("template_request_id"),
                "template_name": review.get("template_name"),
                "request_name": review.get("request_name"),
                "template_type": review.get("template_type"),
                "configuration": review.get("configuration"),
                "initial_file_content": review.get("initial_file_content"),
                "status": review.get("template_request_status"),
            },
            "review": review,
            "evidence": {
                "template_excerpt": self._extract_template_section(
                    review.get("initial_file_content"),
                    review.get("section_name"),
                ),
                "evidence_quality": "high" if review.get("initial_file_content") else "medium",
            },
            "priors": ROOT_CAUSE_PRIORS["template"].get(review["type_of_comment"], []),
        }

    def _extract_section(self, generated_sections, section_name: str | None) -> str | None:
        if not generated_sections or not section_name:
            return None

        if isinstance(generated_sections, dict):
            if section_name in generated_sections:
                section = generated_sections.get(section_name)
                return section if isinstance(section, str) else str(section)

            # loose match
            for k, v in generated_sections.items():
                if k.lower() == section_name.lower():
                    return v if isinstance(v, str) else str(v)

        return None

    def _extract_template_section(self, initial_file_content, section_name: str | None) -> str | None:
        if not initial_file_content or not section_name:
            return None

        if isinstance(initial_file_content, dict):
            if section_name in initial_file_content:
                sec = initial_file_content[section_name]
                return sec if isinstance(sec, str) else str(sec)

        return None