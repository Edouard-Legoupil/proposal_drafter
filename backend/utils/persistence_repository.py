from __future__ import annotations

from typing import Any
from sqlalchemy import text
import json
import logging

logger = logging.getLogger(__name__)


class PersistenceRepository:
    def __init__(self, connection):
        self.connection = connection

    def save_incident_analysis(
        self,
        *,
        artifact_type: str,
        source_review_id: str,
        proposal_id: str | None,
        knowledge_card_id: str | None,
        template_request_id: str | None,
        incident_type: str,
        severity: str,
        analysis_payload: dict[str, Any],
    ) -> str:
        try:
            query = text("""
                INSERT INTO incident_analysis_results (
                    artifact_type,
                    source_review_id,
                    proposal_id,
                    knowledge_card_id,
                    template_request_id,
                    incident_type,
                    severity,
                    status,
                    analysis_payload
                )
                VALUES (
                    :artifact_type,
                    :source_review_id,
                    :proposal_id,
                    :knowledge_card_id,
                    :template_request_id,
                    :incident_type,
                    :severity,
                    'analyzed',
                    CAST(:analysis_payload AS JSONB)
                )
                ON CONFLICT (artifact_type, source_review_id)
                DO UPDATE SET
                    incident_type = EXCLUDED.incident_type,
                    severity = EXCLUDED.severity,
                    status = 'analyzed',
                    analysis_payload = EXCLUDED.analysis_payload,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id::text
            """)
            result = self.connection.execute(
                query,
                {
                    "artifact_type": artifact_type,
                    "source_review_id": source_review_id,
                    "proposal_id": proposal_id,
                    "knowledge_card_id": knowledge_card_id,
                    "template_request_id": template_request_id,
                    "incident_type": incident_type,
                    "severity": severity,
                    "analysis_payload": json.dumps(analysis_payload),
                },
            )
            row = result.first()
            logger.info(
                f"Saved incident analysis for {artifact_type}/{source_review_id}"
            )
            return row[0]
        except Exception as e:
            logger.error(
                f"Error saving incident analysis for {artifact_type}/{source_review_id}: {e}"
            )
            raise

    def get_analysis_result(self, analysis_id: str) -> dict[str, Any] | None:
        query = text("""
            SELECT
                id::text AS id,
                artifact_type,
                source_review_id::text AS source_review_id,
                proposal_id::text AS proposal_id,
                knowledge_card_id::text AS knowledge_card_id,
                template_request_id::text AS template_request_id,
                incident_type,
                severity,
                status,
                analysis_payload,
                created_at,
                updated_at
            FROM incident_analysis_results
            WHERE id = :analysis_id
            LIMIT 1
        """)
        result = self.connection.execute(query, {"analysis_id": analysis_id})
        row = result.mappings().first()
        return dict(row) if row else None
