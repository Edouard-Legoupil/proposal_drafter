# backend/api/knowledge.py
import json
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy import text
from pydantic import BaseModel, Field, validator
from typing import List, Optional

from backend.core.db import get_engine
from backend.core.security import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

# Pydantic Models for request bodies
class KnowledgeCardReferenceIn(BaseModel):
    url: str
    reference_type: str

class KnowledgeCardIn(BaseModel):
    title: str
    summary: Optional[str] = None
    template_name: Optional[str] = "knowledge_card_template.json"
    donor_id: Optional[uuid.UUID] = None
    outcome_id: Optional[uuid.UUID] = None
    field_context_id: Optional[uuid.UUID] = None
    references: Optional[List[KnowledgeCardReferenceIn]] = []

    @validator('donor_id', 'outcome_id', 'field_context_id', pre=True, always=True)
    def check_one_link_only(cls, v, values):
        if v is not None:
            if sum(1 for field in ['donor_id', 'outcome_id', 'field_context_id'] if values.get(field) is not None) > 0:
                raise ValueError('Only one of donor_id, outcome_id, or field_context_id can be set.')
        return v

@router.post("/knowledge-cards")
async def create_knowledge_card(card: KnowledgeCardIn, current_user: dict = Depends(get_current_user)):
    """
    Creates a new knowledge card.
    """
    card_id = uuid.uuid4()
    # Check that only one of the foreign keys is provided.
    if sum(1 for v in [card.donor_id, card.outcome_id, card.field_context_id] if v is not None) > 1:
        raise HTTPException(status_code=400, detail="A knowledge card can only be linked to one donor, outcome, or field context at a time.")

    try:
        with get_engine().begin() as connection:
            connection.execute(
                text("""
                    INSERT INTO knowledge_cards (id, title, summary, template_name, status, donor_id, outcome_id, field_context_id)
                    VALUES (:id, :title, :summary, :template_name, 'draft', :donor_id, :outcome_id, :field_context_id)
                """),
                {
                    "id": card_id,
                    "title": card.title,
                    "summary": card.summary,
                    "template_name": card.template_name,
                    "donor_id": card.donor_id,
                    "outcome_id": card.outcome_id,
                    "field_context_id": card.field_context_id
                }
            )
            if card.references:
                for ref in card.references:
                    connection.execute(
                        text("""
                            INSERT INTO knowledge_card_references (knowledge_card_id, url, reference_type)
                            VALUES (:kcid, :url, :type)
                        """),
                        {"kcid": card_id, "url": ref.url, "reference_type": ref.reference_type}
                    )
        return {"message": "Knowledge card created successfully.", "knowledge_card_id": card_id}
    except Exception as e:
        logger.error(f"[CREATE KNOWLEDGE CARD ERROR] {e}", exc_info=True)
        if "one_link_only" in str(e):
            raise HTTPException(status_code=400, detail="A knowledge card can only be linked to one donor, outcome, or field context.")
        raise HTTPException(status_code=500, detail="Failed to create knowledge card.")


@router.get("/knowledge-cards")
async def get_knowledge_cards(current_user: dict = Depends(get_current_user)):
    """
    Fetches all knowledge cards from the database.
    """
    try:
        with get_engine().connect() as connection:
            query = text("""
                SELECT
                    kc.id,
                    kc.title,
                    kc.summary,
                    kc.template_name,
                    kc.status,
                    kc.created_at,
                    kc.updated_at,
                    d.name as donor_name,
                    o.name as outcome_name,
                    fc.name as field_context_name,
                    (SELECT json_agg(json_build_object('url', kcr.url, 'reference_type', kcr.reference_type))
                     FROM knowledge_card_references kcr
                     WHERE kcr.knowledge_card_id = kc.id) as "references"
                FROM
                    knowledge_cards kc
                LEFT JOIN
                    donors d ON kc.donor_id = d.id
                LEFT JOIN
                    outcomes o ON kc.outcome_id = o.id
                LEFT JOIN
                    field_contexts fc ON kc.field_context_id = fc.id
                ORDER BY
                    kc.updated_at DESC
            """)
            result = connection.execute(query)
            cards = [dict(row) for row in result.mappings().fetchall()]
            for card in cards:
                if card.get('references') is None:
                    card['references'] = []
            return {"knowledge_cards": cards}
    except Exception as e:
        logger.error(f"[GET KNOWLEDGE CARDS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch knowledge cards.")
