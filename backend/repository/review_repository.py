#  Standard Library
import json
import uuid
from typing import List, Dict, Any

#  Third-Party Libraries
from sqlalchemy import text
from sqlalchemy.orm import Session

#  Internal Modules
from backend.core.db import get_engine

class ReviewRepository:
    def __init__(self):
        self.engine = get_engine()

    def get_review_assignment(self, proposal_id: uuid.UUID, user_id: uuid.UUID) -> Any:
        with self.engine.connect() as connection:
            result = connection.execute(
                text("SELECT status FROM proposal_peer_reviews WHERE proposal_id = :proposal_id AND reviewer_id = :user_id ORDER BY created_at DESC LIMIT 1"),
                {"proposal_id": proposal_id, "user_id": user_id}
            ).fetchone()
            return result

    def get_draft_comments(self, proposal_id: uuid.UUID, user_id: uuid.UUID) -> Dict[str, Any]:
        with self.engine.connect() as connection:
            comments_result = connection.execute(
                text("SELECT section_name, review_text, type_of_comment, severity FROM proposal_peer_reviews WHERE proposal_id = :proposal_id AND reviewer_id = :user_id AND status = 'draft'"),
                {"proposal_id": proposal_id, "user_id": user_id}
            ).mappings().fetchall()
            draft_comments = {}
            for comment in comments_result:
                draft_comments[comment['section_name']] = {
                    "review_text": comment['review_text'],
                    "type_of_comment": comment['type_of_comment'],
                    "severity": comment['severity']
                }
            return draft_comments

    def get_peer_reviews(self, proposal_id: uuid.UUID) -> List[Dict[str, Any]]:
        with self.engine.connect() as connection:
            query = text("""
                SELECT
                    pr.id,
                    pr.section_name,
                    pr.review_text,
                    pr.author_response,
                    u.name as reviewer_name
                FROM
                    proposal_peer_reviews pr
                JOIN
                    users u ON pr.reviewer_id = u.id
                WHERE
                    pr.proposal_id = :pid
            """)
            result = connection.execute(query, {"pid": proposal_id})
            return [dict(row) for row in result.mappings()]

    def get_reviewer_id(self, proposal_id: uuid.UUID, user_id: uuid.UUID) -> uuid.UUID:
        with self.engine.connect() as connection:
            result = connection.execute(
                text("SELECT reviewer_id FROM proposal_peer_reviews WHERE proposal_id = :proposal_id AND reviewer_id = :user_id AND (status = 'pending' OR status = 'draft')"),
                {"proposal_id": proposal_id, "user_id": user_id}
            ).scalar()
            return result

    def get_in_review_history_id(self, proposal_id: uuid.UUID) -> uuid.UUID:
        with self.engine.connect() as connection:
            result = connection.execute(
                text("SELECT id FROM proposal_status_history WHERE proposal_id = :pid AND status = 'in_review' ORDER BY created_at DESC LIMIT 1"),
                {"pid": proposal_id}
            ).scalar()
            return result

    def delete_pending_draft_comments(self, proposal_id: uuid.UUID, user_id: uuid.UUID) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text("DELETE FROM proposal_peer_reviews WHERE proposal_id = :proposal_id AND reviewer_id = :user_id AND (status = 'pending' OR status = 'draft')"),
                {"proposal_id": proposal_id, "user_id": user_id}
            )

    def create_review_comment(self, proposal_id: uuid.UUID, user_id: uuid.UUID, history_id: uuid.UUID, comment: Dict[str, Any]) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text("""
                    INSERT INTO proposal_peer_reviews (proposal_id, reviewer_id, proposal_status_history_id, section_name, review_text, type_of_comment, severity, status)
                    VALUES (:pid, :rid, :hid, :section, :text, :type, :severity, 'completed')
                """),
                {
                    "pid": proposal_id,
                    "rid": user_id,
                    "hid": history_id,
                    "section": comment.section_name,
                    "text": comment.review_text,
                    "type": comment.type_of_comment,
                    "severity": comment.severity
                }
            )

    def get_pending_reviews_count(self, proposal_id: uuid.UUID) -> int:
        with self.engine.connect() as connection:
            result = connection.execute(
                text("SELECT COUNT(*) FROM proposal_peer_reviews WHERE proposal_id = :proposal_id AND status = 'pending'"),
                {"proposal_id": proposal_id}
            ).scalar()
            return result

    def get_proposal_id_by_review_id(self, review_id: uuid.UUID) -> uuid.UUID:
        with self.engine.connect() as connection:
            result = connection.execute(
                text("SELECT proposal_id FROM proposal_peer_reviews WHERE id = :rid"),
                {"rid": review_id}
            ).scalar()
            return result

    def update_author_response(self, review_id: uuid.UUID, response: str) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text("UPDATE proposal_peer_reviews SET author_response = :response, updated_at = CURRENT_TIMESTAMP WHERE id = :rid"),
                {"response": response, "rid": review_id}
            )

    def create_draft_review_comment(self, proposal_id: uuid.UUID, user_id: uuid.UUID, history_id: uuid.UUID, comment: Dict[str, Any]) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text("""
                    INSERT INTO proposal_peer_reviews (proposal_id, reviewer_id, proposal_status_history_id, section_name, review_text, type_of_comment, severity, status)
                    VALUES (:pid, :rid, :hid, :section, :text, :type, :severity, 'draft')
                """),
                {
                    "pid": proposal_id,
                    "rid": user_id,
                    "hid": history_id,
                    "section": comment.section_name,
                    "text": comment.review_text,
                    "type": comment.type_of_comment,
                    "severity": comment.severity
                }
            )
    def get_proposals_for_review(self, user_id: uuid.UUID) -> List[Dict[str, Any]]:
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
                    string_agg(DISTINCT o.name, ', ') AS outcome_names,
                    u.name AS requester_name,
                    -- Determine the review status by checking for any 'completed' status for this reviewer and proposal
                    MAX(CASE WHEN pp.status = 'completed' THEN 1 ELSE 0 END) as is_completed,
                    -- Determine if there is a draft review
                    MAX(CASE WHEN pp.status = 'draft' THEN 1 ELSE 0 END) as is_draft,
                    -- Get the deadline from the 'pending' review row
                    MAX(CASE WHEN pp.status = 'pending' THEN pp.deadline ELSE NULL END) as deadline,
                    -- Get the completion date from the latest 'completed' review row
                    MAX(CASE WHEN pp.status = 'completed' THEN pp.updated_at ELSE NULL END) as review_completed_at
                FROM
                    proposals p
                JOIN
                    proposal_peer_reviews pp ON p.id = pp.proposal_id
                LEFT JOIN
                    users u ON p.user_id = u.id
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
                    pp.reviewer_id = :uid
                GROUP BY
                    p.id, d.name, fc.name, u.name
                ORDER BY
                    MAX(pp.updated_at) DESC
            """)
            result = connection.execute(query, {"uid": user_id})
            return [dict(row) for row in result.mappings().fetchall()]
