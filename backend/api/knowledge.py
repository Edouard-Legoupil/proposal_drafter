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
from backend.core.config import load_proposal_template

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
                            VALUES (:kcid, :url, :reference_type)
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


@router.get("/knowledge-cards/{card_id}")
async def get_knowledge_card(card_id: uuid.UUID, current_user: dict = Depends(get_current_user)):
    """
    Fetches a single knowledge card by its ID.
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
                    kc.donor_id,
                    kc.outcome_id,
                    kc.field_context_id,
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
                WHERE
                    kc.id = :card_id
            """)
            result = connection.execute(query, {"card_id": card_id})
            card = result.mappings().fetchone()
            if not card:
                raise HTTPException(status_code=404, detail="Knowledge card not found.")

            card_dict = dict(card)
            if card_dict.get('references') is None:
                card_dict['references'] = []

            return {"knowledge_card": card_dict}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"[GET KNOWLEDGE CARD ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch knowledge card.")


@router.put("/knowledge-cards/{card_id}")
async def update_knowledge_card(card_id: uuid.UUID, card: KnowledgeCardIn, current_user: dict = Depends(get_current_user)):
    """
    Updates an existing knowledge card.
    """
    # Check that only one of the foreign keys is provided.
    if sum(1 for v in [card.donor_id, card.outcome_id, card.field_context_id] if v is not None) > 1:
        raise HTTPException(status_code=400, detail="A knowledge card can only be linked to one donor, outcome, or field context at a time.")

    try:
        with get_engine().begin() as connection:
            # Check if card exists
            existing_card = connection.execute(text("SELECT id FROM knowledge_cards WHERE id = :id"), {"id": card_id}).fetchone()
            if not existing_card:
                raise HTTPException(status_code=404, detail="Knowledge card not found.")

            connection.execute(
                text("""
                    UPDATE knowledge_cards
                    SET title = :title, summary = :summary, template_name = :template_name,
                        donor_id = :donor_id, outcome_id = :outcome_id, field_context_id = :field_context_id,
                        updated_at = NOW()
                    WHERE id = :id
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
            # Delete existing references and add new ones
            connection.execute(text("DELETE FROM knowledge_card_references WHERE knowledge_card_id = :kcid"), {"kcid": card_id})
            if card.references:
                for ref in card.references:
                    connection.execute(
                        text("""
                            INSERT INTO knowledge_card_references (knowledge_card_id, url, reference_type)
                            VALUES (:kcid, :url, :reference_type)
                        """),
                        {"kcid": card_id, "url": ref.url, "reference_type": ref.reference_type}
                    )
        return {"message": "Knowledge card updated successfully.", "knowledge_card_id": card_id}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"[UPDATE KNOWLEDGE CARD ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update knowledge card.")


@router.post("/knowledge-cards/{card_id}/generate")
async def generate_knowledge_card_content(card_id: uuid.UUID, current_user: dict = Depends(get_current_user)):
    """
    Generates content for a knowledge card based on its linked entity.
    """
    try:
        with get_engine().begin() as connection:
            # Fetch the card to determine the link type
            card = connection.execute(
                text("SELECT donor_id, outcome_id, field_context_id FROM knowledge_cards WHERE id = :id"),
                {"id": card_id}
            ).fetchone()
            if not card:
                raise HTTPException(status_code=404, detail="Knowledge card not found.")

            # Determine which template to use
            if card.donor_id:
                template_name = "knowledge_card_donor_template.json"
            # TODO: Add logic for other link types
            # elif card.outcome_id:
            #     template_name = "knowledge_card_outcome_template.json"
            # elif card.field_context_id:
            #     template_name = "knowledge_card_field_context_template.json"
            else:
                raise HTTPException(status_code=400, detail="Knowledge card is not linked to any entity.")

            template = load_proposal_template(template_name)
            generated_sections = {}

            for section in template.get("sections", []):
                section_name = section.get("section_name")
                # Placeholder for actual content generation logic
                generated_sections[section_name] = f"This is placeholder content for the '{section_name}' section."

            # Save the generated sections to the database
            connection.execute(
                text("UPDATE knowledge_cards SET generated_sections = :sections, updated_at = NOW() WHERE id = :id"),
                {"sections": json.dumps(generated_sections), "id": card_id}
            )

        return {"message": "Knowledge card content generated successfully.", "generated_sections": generated_sections}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"[GENERATE KC CONTENT ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate knowledge card content.")
