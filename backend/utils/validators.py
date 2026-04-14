from __future__ import annotations

from typing import Any
from backend.models.schemas import TYPE_OF_COMMENT_OPTIONS


def validate_taxonomy(artifact_type: str, severity: str, incident_type: str) -> None:
    """Validate that incident_type is allowed for the given artifact_type and severity.
    
    Args:
        artifact_type: Type of artifact (proposal, knowledge_card, template)
        severity: Severity level (P0, P1, P2, P3)
        incident_type: Specific type of incident
        
    Raises:
        ValueError: If the incident_type is not valid for the given artifact_type and severity
    """
    allowed = TYPE_OF_COMMENT_OPTIONS[artifact_type][severity]
    if incident_type not in allowed:
        raise ValueError(
            f"incident_type '{incident_type}' is not valid for "
            f"{artifact_type}/{severity}. "
            f"Allowed: {allowed}"
        )


def mandatory_human_review(severity: str, confidence_values: list[float]) -> tuple[bool, str]:
    """Determine if human review is required based on severity and confidence scores.
    
    Args:
        severity: Severity level (P0, P1, P2, P3)
        confidence_values: List of confidence scores from different agents
        
    Returns:
        tuple: (requires_review: bool, reason: str)
    """
    # High severity incidents always require human review
    if severity in ["P0", "P1"]:
        return True, "High severity incident requires human review"
    
    # Calculate average confidence if values are provided
    avg_confidence = sum(confidence_values) / len(confidence_values) if confidence_values else 0
    
    # Low confidence requires human review
    if avg_confidence < 0.7:
        return True, "Low confidence requires human review"
        
    return False, ""

    async def fetch_knowledge_card_review(self, review_id: str) -> dict[str, Any] | None:
        query = text("""
            SELECT
                kcr.id::text AS review_id,
                kcr.knowledge_card_id::text AS knowledge_card_id,
                kcr.reviewer_id::text AS reviewer_id,
                kcr.section_name,
                kcr.rating,
                kcr.review_text,
                kcr.author_response,
                kcr.type_of_comment,
                kcr.severity,
                kcr.status AS review_status,
                kcr.created_at AS review_created_at,
                kcr.updated_at AS review_updated_at,
                kc.id::text AS kc_pk,
                kc.template_name,
                kc.type AS knowledge_card_type,
                kc.summary,
                kc.generated_sections,
                kc.is_accepted,
                kc.status AS knowledge_card_status,
                kc.donor_id::text AS donor_id,
                kc.outcome_id::text AS outcome_id,
                kc.field_context_id::text AS field_context_id,
                kc.created_at AS kc_created_at,
                kc.updated_at AS kc_updated_at
            FROM knowledge_card_reviews kcr
            JOIN knowledge_cards kc ON kc.id = kcr.knowledge_card_id
            WHERE kcr.id = :review_id
            LIMIT 1
        """)
        result = await self.db.execute(query, {"review_id": review_id})
        row = result.mappings().first()
        return dict(row) if row else None

    async def fetch_template_comment(self, review_id: str) -> dict[str, Any] | None:
        query = text("""
            SELECT
                dtc.id::text AS review_id,
                dtc.template_request_id::text AS template_request_id,
                dtc.template_name,
                dtc.user_id::text AS reviewer_id,
                dtc.comment_text AS review_text,
                dtc.section_name,
                dtc.rating,
                dtc.severity,
                dtc.type_of_comment,
                dtc.created_at AS review_created_at,
                dtr.name AS request_name,
                dtr.template_type,
                dtr.configuration,
                dtr.initial_file_content,
                dtr.status AS template_request_status,
                dtr.donor_id::text AS donor_id,
                dtr.donor_ids
            FROM donor_template_comments dtc
            LEFT JOIN donor_template_requests dtr
                ON dtr.id = dtc.template_request_id
            WHERE dtc.id = :review_id
            LIMIT 1
        """)
        result = await self.db.execute(query, {"review_id": review_id})
        row = result.mappings().first()
        return dict(row) if row else None

    async def fetch_latest_proposal_history(self, proposal_id: str) -> dict[str, Any] | None:
        query = text("""
            SELECT
                id::text AS history_id,
                proposal_id::text AS proposal_id,
                status::text AS status,
                generated_sections_snapshot,
                created_at
            FROM proposal_status_history
            WHERE proposal_id = :proposal_id
            ORDER BY created_at DESC
            LIMIT 1
        """)
        result = await self.db.execute(query, {"proposal_id": proposal_id})
        row = result.mappings().first()
        return dict(row) if row else None

    async def fetch_proposal_dimensions(self, proposal_id: str) -> dict[str, Any]:
        donors_q = text("""
            SELECT d.id::text AS id, d.name
            FROM proposal_donors pd
            JOIN donors d ON d.id = pd.donor_id
            WHERE pd.proposal_id = :proposal_id
        """)
        outcomes_q = text("""
            SELECT o.id::text AS id, o.name
            FROM proposal_outcomes po
            JOIN outcomes o ON o.id = po.outcome_id
            WHERE po.proposal_id = :proposal_id
        """)
        fields_q = text("""
            SELECT fc.id::text AS id, fc.name, fc.category, fc.geographic_coverage, fc.unhcr_region
            FROM proposal_field_contexts pfc
            JOIN field_contexts fc ON fc.id = pfc.field_context_id
            WHERE pfc.proposal_id = :proposal_id
        """)

        donors = (await self.db.execute(donors_q, {"proposal_id": proposal_id})).mappings().all()
        outcomes = (await self.db.execute(outcomes_q, {"proposal_id": proposal_id})).mappings().all()
        fields = (await self.db.execute(fields_q, {"proposal_id": proposal_id})).mappings().all()

        return {
            "donors": [dict(x) for x in donors],
            "outcomes": [dict(x) for x in outcomes],
            "field_contexts": [dict(x) for x in fields],
        }

    async def fetch_knowledge_card_history(self, knowledge_card_id: str) -> list[dict[str, Any]]:
        query = text("""
            SELECT
                id::text AS history_id,
                knowledge_card_id::text AS knowledge_card_id,
                generated_sections_snapshot,
                created_by::text AS created_by,
                created_at
            FROM knowledge_card_history
            WHERE knowledge_card_id = :knowledge_card_id
            ORDER BY created_at DESC
            LIMIT 5
        """)
        result = await self.db.execute(query, {"knowledge_card_id": knowledge_card_id})
        return [dict(r) for r in result.mappings().all()]

    async def fetch_knowledge_card_references(self, knowledge_card_id: str) -> list[dict[str, Any]]:
        query = text("""
            SELECT
                r.id::text AS reference_id,
                r.url,
                r.reference_type,
                r.summary,
                r.scraped_at,
                r.scraping_error
            FROM knowledge_card_to_references kctr
            JOIN knowledge_card_references r ON r.id = kctr.reference_id
            WHERE kctr.knowledge_card_id = :knowledge_card_id
        """)
        result = await self.db.execute(query, {"knowledge_card_id": knowledge_card_id})
        return [dict(r) for r in result.mappings().all()]

    async def fetch_reference_chunks(self, knowledge_card_id: str, limit: int = 10) -> list[dict[str, Any]]:
        query = text("""
            SELECT
                r.id::text AS reference_id,
                rv.id::text AS vector_id,
                rv.text_chunk
            FROM knowledge_card_to_references kctr
            JOIN knowledge_card_references r ON r.id = kctr.reference_id
            JOIN knowledge_card_reference_vectors rv ON rv.reference_id = r.id
            WHERE kctr.knowledge_card_id = :knowledge_card_id
            LIMIT :limit
        """)
        result = await self.db.execute(query, {"knowledge_card_id": knowledge_card_id, "limit": limit})
        return [dict(r) for r in result.mappings().all()]

    async def fetch_rag_logs(self, knowledge_card_id: str, limit: int = 10) -> list[dict[str, Any]]:
        query = text("""
            SELECT
                id::text AS log_id,
                knowledge_card_id::text AS knowledge_card_id,
                query,
                retrieved_context,
                generated_answer,
                created_at
            FROM rag_evaluation_logs
            WHERE knowledge_card_id = :knowledge_card_id
            ORDER BY created_at DESC
            LIMIT :limit
        """)
        result = await self.db.execute(query, {"knowledge_card_id": knowledge_card_id, "limit": limit})
        return [dict(r) for r in result.mappings().all()]