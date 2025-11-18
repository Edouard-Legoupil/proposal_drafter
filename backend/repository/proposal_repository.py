#  Standard Library
import json
import uuid
from typing import List, Dict, Any

#  Third-Party Libraries
from sqlalchemy import text
from sqlalchemy.orm import Session

#  Internal Modules
from backend.core.db import get_engine

class ProposalRepository:
    def __init__(self):
        self.engine = get_engine()

    def get_proposal_by_id(self, proposal_id: uuid.UUID, user_id: uuid.UUID) -> Dict[str, Any]:
        with self.engine.connect() as connection:
            result = connection.execute(
                text("SELECT * FROM proposals WHERE id = :id AND user_id = :uid"),
                {"id": proposal_id, "uid": user_id}
            ).fetchone()
            return dict(result) if result else None

    def create_proposal(self, proposal_id: uuid.UUID, user_id: uuid.UUID, form_data: Dict[str, Any], project_description: str, template_name: str) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text("""
                    INSERT INTO proposals (id, user_id, created_by, updated_by, form_data, project_description, template_name, generated_sections)
                    VALUES (:id, :uid, :uid, :uid, :form, :desc, :template, '{}')
                """),
                {
                    "id": proposal_id,
                    "uid": user_id,
                    "form": json.dumps(form_data),
                    "desc": project_description,
                    "template": template_name,
                }
            )

    def create_proposal_status_history(self, proposal_id: uuid.UUID, status: str, snapshot: Dict[str, Any] = None) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text("INSERT INTO proposal_status_history (proposal_id, status, generated_sections_snapshot) VALUES (:pid, :status, :snapshot::jsonb)"),
                {"pid": proposal_id, "status": status, "snapshot": json.dumps(snapshot) if snapshot else "{}"}
            )

    def create_proposal_donor(self, proposal_id: uuid.UUID, donor_id: uuid.UUID) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text("INSERT INTO proposal_donors (proposal_id, donor_id) VALUES (:pid, :did)"),
                {"pid": proposal_id, "did": donor_id}
            )

    def create_proposal_outcome(self, proposal_id: uuid.UUID, outcome_id: uuid.UUID) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text("INSERT INTO proposal_outcomes (proposal_id, outcome_id) VALUES (:pid, :oid)"),
                {"pid": proposal_id, "oid": outcome_id}
            )

    def create_proposal_field_context(self, proposal_id: uuid.UUID, field_context_id: uuid.UUID) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text("INSERT INTO proposal_field_contexts (proposal_id, field_context_id) VALUES (:pid, :fid)"),
                {"pid": proposal_id, "fid": field_context_id}
            )

    def get_donor_name_by_id(self, donor_id: uuid.UUID) -> str:
        with self.engine.connect() as connection:
            result = connection.execute(
                text("SELECT name FROM donors WHERE id = :id"),
                {"id": donor_id}
            ).scalar()
            return result

    def update_proposal_status(self, proposal_id: uuid.UUID, status: str) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text("UPDATE proposals SET status = :status, updated_at = CURRENT_TIMESTAMP WHERE id = :id"),
                {"id": proposal_id, "status": status}
            )

    def update_proposal_sections(self, proposal_id: uuid.UUID, sections: Dict[str, Any]) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text("UPDATE proposals SET generated_sections = :sections, status = 'draft', updated_at = CURRENT_TIMESTAMP WHERE id = :id"),
                {"sections": json.dumps(sections), "id": proposal_id}
            )

    def get_proposal_is_accepted(self, proposal_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        with self.engine.connect() as connection:
            result = connection.execute(
                text("SELECT is_accepted FROM proposals WHERE id = :id AND user_id = :uid"),
                {"id": proposal_id, "uid": user_id}
            ).scalar()
            return result

    def get_proposal_generated_sections(self, proposal_id: uuid.UUID) -> Dict[str, Any]:
        with self.engine.connect() as connection:
            result = connection.execute(
                text("SELECT generated_sections FROM proposals WHERE id = :id"),
                {"id": proposal_id}
            ).scalar()
            return json.loads(result) if result else {}

    def update_proposal_section(self, proposal_id: uuid.UUID, section: str, content: str) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text("""
                    UPDATE proposals
                    SET generated_sections = jsonb_set(
                        generated_sections::jsonb,
                        ARRAY[:section],
                        to_jsonb(:content::text)
                    ),
                    updated_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                """),
                {
                    "section": section,
                    "content": content,
                    "id": proposal_id
                }
            )

    def get_proposal_template_name(self, proposal_id: str) -> str:
        with self.engine.connect() as connection:
            result = connection.execute(
                text("SELECT template_name FROM proposals WHERE id = :id"),
                {"id": proposal_id}
            ).scalar()
            return result or "proposal_template_unhcr.json"

    def list_proposals_for_user(self, user_id: uuid.UUID) -> List[Dict[str, Any]]:
        with self.engine.connect() as connection:
            query = text("""
                SELECT
                    p.id,
                    p.form_data,
                    p.project_description,
                    p.status,
                    p.created_at,
                    p.updated_at,
                    p.is_accepted,
                    d.name AS donor_name,
                    fc.name AS country_name,
                    string_agg(o.name, ', ') AS outcome_names
                FROM
                    proposals p
                LEFT JOIN
                    proposal_donors pd ON p.id = pd.proposal_id
                LEFT JOIN
                    donors d ON pd.donor_id = d.id
                LEFT JOIN
                    proposal_field_contexts pfc ON p.id = pfc.proposal_id
                LEFT JOIN
                    field_contexts fc ON pfc.field_context_id = fc.id
                LEFT JOIN
                    proposal_outcomes po ON p.id = po.proposal_id
                LEFT JOIN
                    outcomes o ON po.outcome_id = o.id
                WHERE
                    p.user_id = :uid AND p.status != 'deleted'
                GROUP BY
                    p.id, d.name, fc.name
                ORDER BY
                    p.updated_at DESC
            """)
            result = connection.execute(query, {"uid": user_id})
            return [dict(row) for row in result.mappings().fetchall()]

    def get_proposal_details_for_load(self, proposal_id: uuid.UUID, user_id: uuid.UUID) -> Dict[str, Any]:
        with self.engine.connect() as connection:
            draft = connection.execute(
                text("""
                    SELECT template_name, form_data, generated_sections, project_description,
                           is_accepted, created_at, updated_at, status, contribution_id
                    FROM proposals
                    WHERE id = :id AND user_id = :uid
                """),
                {"id": proposal_id, "uid": user_id}
            ).fetchone()
            return dict(draft) if draft else None

    def get_associated_knowledge_cards_for_proposal(self, proposal_id: uuid.UUID) -> List[Dict[str, Any]]:
        with self.engine.connect() as connection:
            associated_cards_result = connection.execute(
                text("""
                    SELECT DISTINCT
                        kc.id, kc.summary as title, kc.summary, kc.donor_id, kc.outcome_id, kc.field_context_id,
                        d.name as donor_name,
                        o.name as outcome_name,
                        fc.name as field_context_name
                    FROM knowledge_cards kc
                    LEFT JOIN donors d ON kc.donor_id = d.id
                    LEFT JOIN outcomes o ON kc.outcome_id = o.id
                    LEFT JOIN field_contexts fc ON kc.field_context_id = fc.id
                    WHERE
                        kc.donor_id IN (SELECT donor_id FROM proposal_donors WHERE proposal_id = :pid) OR
                        kc.outcome_id IN (SELECT outcome_id FROM proposal_outcomes WHERE proposal_id = :pid) OR
                        kc.field_context_id IN (SELECT field_context_id FROM proposal_field_contexts WHERE proposal_id = :pid)
                """),
                {"pid": proposal_id}
            ).mappings().fetchall()
            return [dict(card) for card in associated_cards_result]

    def get_proposal_status(self, proposal_id: uuid.UUID, user_id: uuid.UUID) -> str:
        with self.engine.connect() as connection:
            result = connection.execute(
                text("SELECT status FROM proposals WHERE id = :id AND user_id = :uid"),
                {"id": proposal_id, "uid": user_id}
            ).scalar()
            return result

    def update_proposal_contribution_id(self, proposal_id: uuid.UUID, contribution_id: str) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text("UPDATE proposals SET contribution_id = :contribution_id, updated_at = CURRENT_TIMESTAMP WHERE id = :id"),
                {"contribution_id": contribution_id, "id": proposal_id}
            )

    def get_proposal_owner(self, proposal_id: uuid.UUID) -> uuid.UUID:
        with self.engine.connect() as connection:
            result = connection.execute(
                text("SELECT user_id FROM proposals WHERE id = :id"),
                {"id": proposal_id}
            ).scalar()
            return result

    def update_proposal_sections_and_status(self, proposal_id: uuid.UUID, sections: Dict[str, Any], status: str) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text("""
                    UPDATE proposals
                    SET generated_sections = :sections, status = :status, updated_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                """),
                {"sections": json.dumps(sections), "id": proposal_id, "status": status}
            )

    def get_proposal_status_and_sections(self, proposal_id: uuid.UUID, user_id: uuid.UUID) -> Dict[str, Any]:
        with self.engine.connect() as connection:
            result = connection.execute(
                text("SELECT status, generated_sections FROM proposals WHERE id = :id AND user_id = :uid"),
                {"id": proposal_id, "uid": user_id}
            ).fetchone()
            return dict(result) if result else None

    def delete_draft(self, proposal_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        with self.engine.begin() as connection:
            result = connection.execute(
                text("DELETE FROM proposals WHERE id = :id AND user_id = :uid AND is_accepted = FALSE RETURNING id"),
                {"id": proposal_id, "uid": user_id}
            )
            return result.fetchone() is not None

    def transfer_proposal_ownership(self, proposal_id: uuid.UUID, new_owner_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        with self.engine.begin() as connection:
            result = connection.execute(
                text("UPDATE proposals SET user_id = :new_owner_id, updated_at = CURRENT_TIMESTAMP WHERE id = :id AND user_id = :uid RETURNING id"),
                {"new_owner_id": new_owner_id, "id": proposal_id, "uid": user_id}
            )
            return result.fetchone() is not None

    def get_proposal_status_history_snapshot(self, proposal_id: uuid.UUID, status: str) -> Dict[str, Any]:
        with self.engine.connect() as connection:
            result = connection.execute(
                text("""
                    SELECT generated_sections_snapshot
                    FROM proposal_status_history
                    WHERE proposal_id = :pid AND status = :status
                    ORDER BY created_at DESC
                    LIMIT 1
                """),
                {"pid": proposal_id, "status": status}
            ).fetchone()
            return json.loads(result[0]) if result else None

    def revert_proposal_to_status(self, proposal_id: uuid.UUID, status: str, snapshot: Dict[str, Any], user_id: uuid.UUID) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text("""
                    UPDATE proposals
                    SET status = :status, generated_sections = :snapshot, updated_at = CURRENT_TIMESTAMP
                    WHERE id = :id AND user_id = :uid
                """),
                {"status": status, "snapshot": json.dumps(snapshot), "id": proposal_id, "uid": user_id}
            )

    def get_proposal_status_history(self, proposal_id: uuid.UUID) -> List[str]:
        with self.engine.connect() as connection:
            result = connection.execute(
                text("""
                    SELECT DISTINCT status
                    FROM proposal_status_history
                    WHERE proposal_id = :pid
                """),
                {"pid": proposal_id}
            )
            return [row[0] for row in result.fetchall()]
