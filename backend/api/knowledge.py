# backend/api/knowledge.py
import json
import os
import uuid
import logging
import asyncio
import concurrent.futures
from fastapi import APIRouter, Depends, HTTPException, Body, UploadFile, File, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.engine import Engine
import litellm
from slugify import slugify
from PyPDF2 import PdfReader
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime, timedelta

from backend.core.db import get_engine
from backend.core.redis import redis_client
from backend.core.security import get_current_user
try:
    from backend.core.redis import DictStorage
except ImportError:
    # This will fail when redis is connected, but that's fine.
    class DictStorage:
        pass
from backend.core.config import load_proposal_template
from backend.core.llm import get_embedder_config
from backend.utils.crew_reference import ReferenceIdentificationCrew
from backend.utils.crew_knowledge import ContentGenerationCrew
from backend.utils.scraper import scrape_url
from backend.utils.embedding_utils import process_and_store_text
from langchain.text_splitter import RecursiveCharacterTextSplitter
import litellm
import numpy as np

router = APIRouter()
logger = logging.getLogger(__name__)

# Pydantic Models for request bodies
class KnowledgeCardReferenceIn(BaseModel):
    url: str
    reference_type: str
    summary: Optional[str] = None

class IdentifyReferencesIn(BaseModel):
    title: Optional[str] = None  # Made optional as it's built from linked elements
    linked_element: str  # This is now required
    summary: Optional[str] = None  # Keep optional but won't be used from frontend

class UpdateSectionIn(BaseModel):
    content: str

class KnowledgeCardIn(BaseModel):
    summary: str
    template_name: Optional[str] = None
    donor_id: Optional[uuid.UUID] = None
    outcome_id: Optional[uuid.UUID] = None
    field_context_id: Optional[uuid.UUID] = None
    references: Optional[List[KnowledgeCardReferenceIn]] = []

    @field_validator('donor_id', 'outcome_id', 'field_context_id')
    def check_one_link_only(cls, v, values):
        if v is not None:
            if sum(1 for field in ['donor_id', 'outcome_id', 'field_context_id'] if values.data.get(field) is not None) > 1:
                raise ValueError('Only one of donor_id, outcome_id, or field_context_id can be set.')
        return v

def _save_knowledge_card_content_to_file(connection, card_id: uuid.UUID, generated_sections: dict):
    """
    Saves the generated content of a knowledge card to a file in the 'backend/knowledge' directory.
    The filename is a concatenation of the link type, a human-readable link label, and a slugified summary.
    """
    try:
        # Fetch the knowledge card's details and the name of the linked entity
        card_details = connection.execute(
            text("""
                SELECT
                    kc.summary,
                    kc.donor_id,
                    kc.outcome_id,
                    kc.field_context_id,
                    d.name as donor_name,
                    o.name as outcome_name,
                    fc.name as field_context_name
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
            """),
            {"card_id": str(card_id)}
        ).fetchone()

        if not card_details:
            logger.error(f"Cannot save content to file: Knowledge card with id {card_id} not found.")
            return

        card_summary = card_details.summary
        link_type = None
        link_label = None

        if card_details.donor_id:
            link_type = "donor"
            link_label = card_details.donor_name
        elif card_details.outcome_id:
            link_type = "outcome"
            link_label = card_details.outcome_name
        elif card_details.field_context_id:
            link_type = "field_context"
            link_label = card_details.field_context_name

        # Create a clean, URL-safe filename using the human-readable label
        if link_type and link_label:
            filename = f"{link_type}-{slugify(link_label)}-{slugify(card_summary)}.json"
        else:
            # Fallback for cards without a direct link
            filename = f"{slugify(card_summary)}.json"

        # Construct a robust path to the 'backend/knowledge' directory.
        # This is relative to this file's location to avoid CWD issues.
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # from backend/api/ go to backend/ and then knowledge/
        knowledge_dir = os.path.join(current_dir, "..", "knowledge")
        filepath = os.path.join(knowledge_dir, filename)

        # Ensure the knowledge directory exists
        os.makedirs(knowledge_dir, exist_ok=True)

        # Write the generated sections to the JSON file
        with open(filepath, 'w') as f:
            json.dump(generated_sections, f, indent=4)

        logger.info(f"Knowledge card content saved to {filepath}")

    except Exception as e:
        logger.error(f"Failed to save knowledge card content to file for card {card_id}: {e}", exc_info=True)


def create_knowledge_card_history_entry(connection, card_id: uuid.UUID, generated_sections: dict, user_id: uuid.UUID):
    """
    Creates a history entry for a knowledge card.
    """
    history_id = uuid.uuid4()
    connection.execute(
        text("""
            INSERT INTO knowledge_card_history (id, knowledge_card_id, generated_sections_snapshot, created_by, created_at)
            VALUES (:id, :knowledge_card_id, :generated_sections_snapshot, :created_by, CURRENT_TIMESTAMP)
        """),
        {
            "id": str(history_id),
            "knowledge_card_id": str(card_id),
            "generated_sections_snapshot": json.dumps(generated_sections),
            "created_by": str(user_id)
        }
    )

@router.post("/knowledge-cards")
async def create_knowledge_card(card: KnowledgeCardIn, current_user: dict = Depends(get_current_user)):
    """
    Creates a new knowledge card.
    """
    card_id = uuid.uuid4()
    user_id = current_user['user_id']

    # Ensure that only one of the foreign keys is provided.
    foreign_keys = [card.donor_id, card.outcome_id, card.field_context_id]
    if sum(k is not None for k in foreign_keys) > 1:
        raise HTTPException(status_code=400, detail="A knowledge card can only be linked to one donor, outcome, or field context at a time.")

    # Determine the template name based on the linked entity if not provided
    template_name = card.template_name
    if not template_name:
        if card.donor_id:
            template_name = "knowledge_card_donor_template.json"
        elif card.outcome_id:
            template_name = "knowledge_card_outcome_template.json"
        elif card.field_context_id:
            template_name = "knowledge_card_field_context_template.json"

    try:
        with get_engine().begin() as connection:
            connection.execute(
                text("""
                    INSERT INTO knowledge_cards (id, title, summary, template_name, status, donor_id, outcome_id, field_context_id, created_by, updated_by, created_at, updated_at)
                    VALUES (:id, :summary, :summary, :template_name, 'draft', :donor_id, :outcome_id, :field_context_id, :user_id, :user_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """),
                {
                    "id": card_id,
                    "summary": card.summary,
                    "template_name": template_name,
                    "donor_id": card.donor_id,
                    "outcome_id": card.outcome_id,
                    "field_context_id": card.field_context_id,
                    "user_id": user_id
                }
            )
            if card.references:
                for ref in card.references:
                    # Check if reference already exists
                    existing_ref = connection.execute(
                        text("SELECT id FROM knowledge_card_references WHERE url = :url"),
                        {"url": ref.url}
                    ).fetchone()

                    if existing_ref:
                        reference_id = existing_ref.id
                    else:
                        # Insert new reference
                        new_ref_id = connection.execute(
                            text("""
                                INSERT INTO knowledge_card_references (url, reference_type, summary, created_by, updated_by, created_at, updated_at)
                                VALUES (:url, :reference_type, :summary, :user_id, :user_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                                RETURNING id
                            """),
                            {
                                "url": ref.url,
                                "reference_type": ref.reference_type,
                                "summary": ref.summary or "", # Ensure summary is not null
                                "user_id": user_id
                            }
                        ).scalar_one()
                        reference_id = new_ref_id

                    # Link reference to knowledge card
                    connection.execute(
                        text("""
                            INSERT INTO knowledge_card_to_references (knowledge_card_id, reference_id)
                            VALUES (:kcid, :ref_id)
                        """),
                        {"kcid": card_id, "ref_id": reference_id}
                    )
        return {"message": "Knowledge card created successfully.", "knowledge_card_id": card_id}
    except Exception as e:
        logger.error(f"[CREATE KNOWLEDGE CARD ERROR] {e}", exc_info=True)
        # Check for the specific constraint violation from the DB if possible
        if "violates not-null constraint" in str(e) or "violates foreign key constraint" in str(e):
             raise HTTPException(status_code=400, detail="Invalid data: Make sure all required fields are provided and valid.")
        if "one_link_only" in str(e):
            raise HTTPException(status_code=400, detail="A knowledge card can only be linked to one donor, outcome, or field context.")
        raise HTTPException(status_code=500, detail="Failed to create knowledge card.")


@router.get("/knowledge-cards")
async def get_knowledge_cards(
    donor_id: Optional[uuid.UUID] = None,
    outcome_id: Optional[uuid.UUID] = None,
    field_context_id: Optional[uuid.UUID] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Fetches knowledge cards from the database, with optional filtering.
    """
    try:
        with get_engine().connect() as connection:
            base_query = """
                SELECT
                    kc.id,
                    kc.summary,
                    kc.template_name,
                    kc.status,
                    kc.created_at,
                    kc.updated_at,
                    kc.generated_sections,
                    d.name as donor_name,
                    o.name as outcome_name,
                    fc.name as field_context_name,
                    (SELECT json_agg(json_build_object('id', kcr.id, 'url', kcr.url, 'reference_type', kcr.reference_type, 'summary', kcr.summary, 'scraped_at', kcr.scraped_at, 'scraping_error', kcr.scraping_error))
                     FROM knowledge_card_references kcr
                     JOIN knowledge_card_to_references kctr ON kcr.id = kctr.reference_id
                     WHERE kctr.knowledge_card_id = kc.id) as "references"
                FROM
                    knowledge_cards kc
                LEFT JOIN
                    donors d ON kc.donor_id = d.id
                LEFT JOIN
                    outcomes o ON kc.outcome_id = o.id
                LEFT JOIN
                    field_contexts fc ON kc.field_context_id = fc.id
            """

            filters = []
            params = {}
            if donor_id:
                filters.append("kc.donor_id = :donor_id")
                params["donor_id"] = donor_id
            if outcome_id:
                filters.append("kc.outcome_id = :outcome_id")
                params["outcome_id"] = outcome_id
            if field_context_id:
                filters.append("kc.field_context_id = :field_context_id")
                params["field_context_id"] = field_context_id

            if filters:
                base_query += " WHERE " + " OR ".join(filters)

            base_query += " ORDER BY kc.updated_at DESC"

            query = text(base_query)
            result = connection.execute(query, params)
            cards = [dict(row) for row in result.mappings().fetchall()]
            for card in cards:
                if card.get('references') is None:
                    card['references'] = []
                if card.get('generated_sections'):
                    # Handle both string and dict types
                    if isinstance(card['generated_sections'], str):
                        try:
                            card['generated_sections'] = json.loads(card['generated_sections'])
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse generated_sections for card {card['id']}")
                            card['generated_sections'] = {}
                    elif isinstance(card['generated_sections'], dict):
                        # Already a dict, no need to parse
                        pass
                    else:
                        card['generated_sections'] = {}
                else:
                    card['generated_sections'] = {}
            return {"knowledge_cards": cards}
    except Exception as e:
        logger.error(f"[GET KNOWLEDGE CARDS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch knowledge cards.")


@router.get("/knowledge-cards/{card_id}/history")
async def get_knowledge_card_history(card_id: uuid.UUID, current_user: dict = Depends(get_current_user)):
    """
    Fetches the history of a knowledge card.
    """
    try:
        with get_engine().connect() as connection:
            # Add user permission check ??
            # card_owner_check = connection.execute(
            #     text("SELECT created_by FROM knowledge_cards WHERE id = :card_id"),
            #     {"card_id": card_id}
            # ).fetchone()
            
            # if not card_owner_check:
            #     raise HTTPException(status_code=404, detail="Knowledge card not found.")
            
            query = text("""
                SELECT
                    kch.id,
                    kch.generated_sections_snapshot,
                    kch.created_at,
                    u.name as created_by_name
                FROM
                    knowledge_card_history kch
                JOIN
                    users u ON kch.created_by = u.id
                WHERE
                    kch.knowledge_card_id = :card_id
                ORDER BY
                    kch.created_at DESC
            """)
            result = connection.execute(query, {"card_id": card_id})
            history = [dict(row) for row in result.mappings().fetchall()]
            for entry in history:
                if entry.get('generated_sections_snapshot'):
                    # C Handle both string and dict types
                    if isinstance(entry['generated_sections_snapshot'], str):
                        try:
                            entry['generated_sections_snapshot'] = json.loads(entry['generated_sections_snapshot'])
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse history snapshot for card {card_id}")
                            entry['generated_sections_snapshot'] = {}
                    elif isinstance(entry['generated_sections_snapshot'], dict):
                        # Already a dict, no need to parse
                        pass
                    else:
                        entry['generated_sections_snapshot'] = {}
            return {"history": history}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[GET KC HISTORY ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch knowledge card history.")

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
                    kc.summary,
                    kc.template_name,
                    kc.status,
                    kc.created_at,
                    kc.updated_at,
                    kc.generated_sections,
                    kc.donor_id,
                    kc.outcome_id,
                    kc.field_context_id,
                    d.name as donor_name,
                    o.name as outcome_name,
                    fc.name as field_context_name,
                    (SELECT json_agg(json_build_object('id', kcr.id, 'url', kcr.url, 'reference_type', kcr.reference_type, 'summary', kcr.summary, 'scraped_at', kcr.scraped_at, 'scraping_error', kcr.scraping_error))
                     FROM knowledge_card_references kcr
                     JOIN knowledge_card_to_references kctr ON kcr.id = kctr.reference_id
                     WHERE kctr.knowledge_card_id = kc.id) as "references"
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
            if card_dict.get('generated_sections'):
                #  Handle both string and dict types
                if isinstance(card_dict['generated_sections'], str):
                    try:
                        card_dict['generated_sections'] = json.loads(card_dict['generated_sections'])
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse generated_sections for card {card_id}")
                        card_dict['generated_sections'] = {}
                elif isinstance(card_dict['generated_sections'], dict):
                    # Already a dict, no need to parse
                    pass
                else:
                    card_dict['generated_sections'] = {}
            else:
                card_dict['generated_sections'] = {}

            return {"knowledge_card": card_dict}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"[GET KNOWLEDGE CARD ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch knowledge card.")


@router.put("/knowledge-cards/{card_id}/sections/{section_name}")
async def update_knowledge_card_section(card_id: uuid.UUID, section_name: str, section: UpdateSectionIn, current_user: dict = Depends(get_current_user), engine: Engine = Depends(get_engine)):
    """
    Updates a specific section of a knowledge card.
    """
    try:
        with engine.begin() as connection:
            # Add user permission check
            # card_owner_check = connection.execute(
            #     text("SELECT created_by FROM knowledge_cards WHERE id = :id"),
            #     {"id": card_id}
            # ).fetchone()
            
            # if not card_owner_check:
            #     raise HTTPException(status_code=404, detail="Knowledge card not found.")

            # First, fetch the existing generated_sections
            result = connection.execute(
                text("SELECT generated_sections FROM knowledge_cards WHERE id = :id"),
                {"id": str(card_id)}
            ).fetchone()

            if not result or not result.generated_sections:
                raise HTTPException(status_code=404, detail="Knowledge card or sections not found.")

            generated_sections = result.generated_sections
            if isinstance(generated_sections, str):
                generated_sections = json.loads(generated_sections)

            if section_name not in generated_sections:
                raise HTTPException(status_code=404, detail=f"Section '{section_name}' not found.")

            # Update the specific section
            generated_sections[section_name] = section.content

            # Save the updated generated_sections back to the database
            connection.execute(
                text("UPDATE knowledge_cards SET generated_sections = :sections, updated_at = CURRENT_TIMESTAMP WHERE id = :id"),
                {"sections": json.dumps(generated_sections), "id": str(card_id)}
            )

            # Save content to file
            _save_knowledge_card_content_to_file(connection, card_id, generated_sections)

            # Create a history entry
            create_knowledge_card_history_entry(connection, card_id, generated_sections, current_user['user_id'])

        return {"message": f"Section '{section_name}' updated successfully."}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"[UPDATE KC SECTION ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update knowledge card section.")


@router.put("/knowledge-cards/{card_id}")
async def update_knowledge_card(card_id: uuid.UUID, card: KnowledgeCardIn, current_user: dict = Depends(get_current_user)):
    """
    Updates an existing knowledge card.
    """
    user_id = current_user['user_id']
    # Check that only one of the foreign keys is provided.
    if sum(1 for v in [card.donor_id, card.outcome_id, card.field_context_id] if v is not None) > 1:
        raise HTTPException(status_code=400, detail="A knowledge card can only be linked to one donor, outcome, or field context at a time.")

    try:
        with get_engine().begin() as connection:
            # CRITICAL FIX: Add user permission check
            existing_card = connection.execute(
                text("SELECT id, created_by FROM knowledge_cards WHERE id = :id"), 
                {"id": card_id}
            ).fetchone()
            
            if not existing_card:
                raise HTTPException(status_code=404, detail="Knowledge card not found.")

            # Update the main knowledge card fields
            connection.execute(
                text("""
                    UPDATE knowledge_cards
                    SET summary = :summary, donor_id = :donor_id, outcome_id = :outcome_id, field_context_id = :field_context_id, updated_by = :user_id, updated_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                """),
                {
                    "id": card_id,
                    "summary": card.summary,
                    "donor_id": card.donor_id,
                    "outcome_id": card.outcome_id,
                    "field_context_id": card.field_context_id,
                    "user_id": user_id
                }
            )

            # Update references: delete old associations and create new ones
            connection.execute(
                text("DELETE FROM knowledge_card_to_references WHERE knowledge_card_id = :kcid"),
                {"kcid": card_id}
            )
            if card.references:
                for ref in card.references:
                    # Check if reference already exists
                    existing_ref = connection.execute(
                        text("SELECT id FROM knowledge_card_references WHERE url = :url"),
                        {"url": ref.url}
                    ).fetchone()

                    if existing_ref:
                        reference_id = existing_ref.id
                    else:
                        # Insert new reference
                        new_ref_id = connection.execute(
                            text("""
                                INSERT INTO knowledge_card_references (url, reference_type, summary, created_by, updated_by, created_at, updated_at)
                                VALUES (:url, :reference_type, :summary, :user_id, :user_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                                RETURNING id
                            """),
                            {
                                "url": ref.url,
                                "reference_type": ref.reference_type,
                                "summary": ref.summary or "",
                                "user_id": user_id
                            }
                        ).scalar_one()
                        reference_id = new_ref_id

                    # Link reference to knowledge card
                    connection.execute(
                        text("""
                            INSERT INTO knowledge_card_to_references (knowledge_card_id, reference_id)
                            VALUES (:kcid, :ref_id)
                        """),
                        {"kcid": card_id, "ref_id": reference_id}
                    )

            # Fetch the generated_sections again to get the updated state
            updated_card = connection.execute(
                text("SELECT generated_sections FROM knowledge_cards WHERE id = :id"), 
                {"id": card_id}
            ).fetchone()
            
            # Handle both string and dict types
            generated_sections = {}
            if updated_card and updated_card.generated_sections:
                if isinstance(updated_card.generated_sections, dict):
                    generated_sections = updated_card.generated_sections
                elif isinstance(updated_card.generated_sections, str):
                    try:
                        generated_sections = json.loads(updated_card.generated_sections)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse generated_sections for card {card_id}")
                        generated_sections = {}
            
            # Save the updated knowledge card to a file to reflect changes
            _save_knowledge_card_content_to_file(connection, card_id, generated_sections)

            create_knowledge_card_history_entry(connection, card_id, generated_sections, user_id)
            
        return {"message": "Knowledge card updated successfully.", "knowledge_card_id": card_id}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"[UPDATE KNOWLEDGE CARD ERROR] {e}", exc_info=True)
        # More specific error messages
        if "violates foreign key constraint" in str(e):
            raise HTTPException(status_code=400, detail="Invalid reference: One or more linked entities do not exist.")
        raise HTTPException(status_code=500, detail="Failed to update knowledge card.")


@router.post("/knowledge-cards/{card_id}/references")
async def create_knowledge_card_reference(card_id: uuid.UUID, reference: KnowledgeCardReferenceIn, current_user: dict = Depends(get_current_user)):
    """
    Creates a new reference or links an existing one to a knowledge card.
    """
    user_id = current_user['user_id']
    try:
        with get_engine().begin() as connection:
            # Validate card exists
            card_check = connection.execute(
                text("SELECT id FROM knowledge_cards WHERE id = :id"),
                {"id": card_id}
            ).fetchone()
            if not card_check:
                raise HTTPException(status_code=404, detail="Knowledge card not found.")

            # Check if reference already exists
            existing_ref = connection.execute(
                text("SELECT id FROM knowledge_card_references WHERE url = :url"),
                {"url": reference.url}
            ).fetchone()

            if existing_ref:
                reference_id = existing_ref.id
            else:
                # Insert new reference
                new_ref_id = connection.execute(
                    text("""
                        INSERT INTO knowledge_card_references (url, reference_type, summary, created_by, updated_by, created_at, updated_at)
                        VALUES (:url, :reference_type, :summary, :user_id, :user_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        RETURNING id
                    """),
                    {
                        "url": reference.url,
                        "reference_type": reference.reference_type,
                        "summary": reference.summary or "",
                        "user_id": user_id
                    }
                ).scalar_one()
                reference_id = new_ref_id

            # Link reference to knowledge card
            connection.execute(
                text("""
                    INSERT INTO knowledge_card_to_references (knowledge_card_id, reference_id)
                    VALUES (:kcid, :ref_id)
                    ON CONFLICT (knowledge_card_id, reference_id) DO NOTHING
                """),
                {"kcid": card_id, "ref_id": reference_id}
            )

            # Return the created or found reference details
            new_reference_details = connection.execute(
                text("SELECT id, url, reference_type, summary FROM knowledge_card_references WHERE id = :id"),
                {"id": reference_id}
            ).fetchone()

        return {"reference": dict(new_reference_details._mapping)}
    except Exception as e:
        logger.error(f"[CREATE KC REFERENCE ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create or link reference.")


@router.put("/knowledge-cards/references/{reference_id}")
async def update_knowledge_card_reference(reference_id: uuid.UUID, reference: KnowledgeCardReferenceIn, current_user: dict = Depends(get_current_user)):
    """
    Updates an existing reference for a knowledge card.
    """
    user_id = current_user['user_id']
    try:
        with get_engine().begin() as connection:
            # Validate reference exists and user has permission
            # ref_check = connection.execute(
            #     text("SELECT id FROM knowledge_card_references WHERE id = :id"), 
            #     {"id": reference_id}
            # ).fetchone()
            
            # if not ref_check:
            #     raise HTTPException(status_code=404, detail="Reference not found.")
                
            connection.execute(
                text("""
                    UPDATE knowledge_card_references
                    SET url = :url, reference_type = :reference_type, summary = :summary, updated_by = :user_id, updated_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                """),
                {"id": reference_id, "url": reference.url, "reference_type": reference.reference_type, "summary": reference.summary, "user_id": user_id}
            )
        return {"message": "Reference updated successfully."}
    except Exception as e:
        logger.error(f"[UPDATE KC REFERENCE ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update reference.")


@router.delete("/knowledge-cards/{card_id}/references/{reference_id}")
async def delete_knowledge_card_reference(card_id: uuid.UUID, reference_id: uuid.UUID, current_user: dict = Depends(get_current_user)):
    """
    Deletes the association between a knowledge card and a reference.
    """
    try:
        with get_engine().begin() as connection:
            # Validate the association exists
            association_check = connection.execute(
                text("""
                    SELECT knowledge_card_id FROM knowledge_card_to_references
                    WHERE knowledge_card_id = :kcid AND reference_id = :ref_id
                """),
                {"kcid": card_id, "ref_id": reference_id}
            ).fetchone()
            
            if not association_check:
                raise HTTPException(status_code=404, detail="Reference association not found.")
                
            # Delete the association
            connection.execute(
                text("DELETE FROM knowledge_card_to_references WHERE knowledge_card_id = :kcid AND reference_id = :ref_id"),
                {"kcid": card_id, "ref_id": reference_id}
            )
        return {"message": "Reference unlinked successfully."}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"[DELETE KC REFERENCE LINK ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to unlink reference.")


async def ingest_reference_content(card_id: uuid.UUID, reference_id: uuid.UUID, force_scrape: bool = False, connection=None):
    """
    Ingests content from a reference URL, creates embeddings, and stores them.
    """
    # Better connection management without recursion
    should_close_connection = False
    if connection is None:
        connection = get_engine().begin()
        should_close_connection = True

    try:
        reference = connection.execute(
            text("SELECT id, url, scraped_at FROM knowledge_card_references WHERE id = :id"),
            {"id": reference_id}
        ).fetchone()

        if not reference:
            logger.error(f"Reference with id {reference_id} not found.")
            _update_ingest_progress(card_id, reference_id, "error", "Reference not found.")
            return

        _update_ingest_progress(card_id, reference_id, "processing", f"Attempting to ingest reference: {reference.url}")

        logger.info(f"Checking reference {reference.id}: scraped_at={reference.scraped_at}, force_scrape={force_scrape}")
        if reference.scraped_at and not force_scrape and (datetime.utcnow() - reference.scraped_at.replace(tzinfo=None)) < timedelta(days=7):
            _update_ingest_progress(card_id, reference_id, "skipped", "Scraped recently.")
            return

        content = scrape_url(reference.url)

        if not content:
            logger.warning(f"Failed to scrape content from {reference.url}")
            connection.execute(
                text("UPDATE knowledge_card_references SET scraping_error = TRUE, updated_at = CURRENT_TIMESTAMP WHERE id = :id"),
                {"id": reference.id}
            )
            _update_ingest_progress(card_id, reference_id, "error", "Failed to scrape content.")
            return

        _update_ingest_progress(card_id, reference_id, "processing", f"Successfully scraped content from {reference.url}")
        await process_and_store_text(reference.id, content, connection)
        _update_ingest_progress(card_id, reference_id, "ingested", "Content ingested successfully.")
        
    except Exception as e:
        logger.error(f"[INGEST REFERENCE CONTENT ERROR] {e}", exc_info=True)
        _update_ingest_progress(card_id, reference_id, "error", f"Processing error: {str(e)}")
    finally:
        if should_close_connection:
            connection.close()


@router.post("/knowledge-cards/references/{reference_id}/upload")
async def upload_pdf_reference(
    reference_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    engine: Engine = Depends(get_engine)
):
    """
    Uploads a PDF for a reference, extracts text, and stores embeddings.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF.")

    try:
        pdf_reader = PdfReader(file.file)
        text_content = ""
        for page in pdf_reader.pages:
            text_content += page.extract_text()

        if not text_content:
            raise HTTPException(status_code=400, detail="Could not extract text from PDF.")

        with engine.begin() as connection:
            await process_and_store_text(reference_id, text_content, connection)

        return {"status": "success", "message": "PDF content ingested successfully."}
    except Exception as e:
        logger.error(f"Error processing PDF for reference {reference_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process PDF file.")


def _update_progress(card_id: uuid.UUID, message: str, progress: int, section_name: str = None, section_content: str = None):
    """Update progress with error handling"""
    try:
        progress_data = {
            "message": message,
            "progress": progress
        }
        if section_name and section_content:
            progress_data["section_name"] = section_name
            progress_data["section_content"] = section_content

        redis_client.set(f"knowledge_card_generation:{card_id}", json.dumps(progress_data))
        if not isinstance(redis_client, DictStorage):
            redis_client.publish(f"knowledge_card_generation_channel:{card_id}", json.dumps(progress_data))
    except Exception as e:
        logger.error(f"[PROGRESS UPDATE ERROR] Failed to update progress: {e}")

def _update_ingest_progress(card_id: uuid.UUID, reference_id: uuid.UUID, status: str, message: str):
    """Update ingest progress with error handling"""
    try:
        progress_data = json.dumps({"reference_id": str(reference_id), "status": status, "message": message})
        redis_client.set(f"knowledge_card_ingest:{card_id}", progress_data)
        if not isinstance(redis_client, DictStorage):
            redis_client.publish(f"knowledge_card_ingest_channel:{card_id}", progress_data)
    except Exception as e:
        logger.error(f"[INGEST PROGRESS UPDATE ERROR] Failed to update ingest progress: {e}")


async def generate_content_background(card_id: uuid.UUID):
    """Background task for content generation with comprehensive error handling"""
    def progress_callback_for_reference_ingestion(message, progress):
        _update_progress(card_id, message, progress)

    try:
        progress_callback_for_reference_ingestion("Starting content generation...", 0)
        
        with get_engine().begin() as connection:
            connection.execute(
                text("UPDATE knowledge_cards SET status = 'generating_sections' WHERE id = :id"),
                {"id": card_id}
            )

        with get_engine().begin() as connection:
            card = connection.execute(
                text("""
                    SELECT 
                        kc.donor_id, 
                        kc.outcome_id, 
                        kc.field_context_id,
                        d.name as donor_name,
                        o.name as outcome_name,
                        fc.name as field_context_name
                    FROM knowledge_cards kc
                    LEFT JOIN donors d ON kc.donor_id = d.id
                    LEFT JOIN outcomes o ON kc.outcome_id = o.id
                    LEFT JOIN field_contexts fc ON kc.field_context_id = fc.id
                    WHERE kc.id = :id
                """),
                {"id": card_id}
            ).fetchone()

        if not card:
            raise Exception("Knowledge card not found")

        if card.donor_id:
            template_name = "knowledge_card_donor_template.json"
            name = card.donor_name
        elif card.outcome_id:
            template_name = "knowledge_card_outcome_template.json"
            name = card.outcome_name
        elif card.field_context_id:
            template_name = "knowledge_card_field_context_template.json"
            name = card.field_context_name
        else:
            raise Exception("Knowledge card is not linked to any entity.")

        template = load_proposal_template(template_name)
        pre_prompt = f"{template.get('description', '')} {name}."
        generated_sections = {}
        crew = ContentGenerationCrew(knowledge_card_id=str(card_id), pre_prompt=pre_prompt)

        num_sections = len(template.get("sections", []))
        for i, section in enumerate(template.get("sections", [])):
            progress = 50 + int(((i + 1) / num_sections) * 50)
            section_name = section.get("section_name")
            instructions = section.get("instructions")
            _update_progress(card_id, f"Generating section {i+1}/{num_sections}: {section_name}", progress)

            inputs = {
                "section_name": section_name,
                "instructions": instructions,
            }

            # Add timeout and error handling for each section
            try:
                result = crew.create_crew().kickoff(inputs=inputs)
                generated_sections[section_name] = str(result)
                _update_progress(card_id, f"Generated section {i+1}/{num_sections}: {section_name}", progress, section_name, str(result))
            except Exception as section_error:
                logger.error(f"[SECTION GENERATION ERROR] Failed to generate section {section_name}: {section_error}")
                generated_sections[section_name] = f"Error generating content: {str(section_error)}"
                _update_progress(card_id, f"Error generating section {section_name}", progress)

        with get_engine().begin() as connection:
            _update_progress(card_id, "Content generation complete.", 100)
            connection.execute(
                text("UPDATE knowledge_cards SET generated_sections = :sections, status = 'approved', updated_at = CURRENT_TIMESTAMP WHERE id = :id"),
                {"sections": json.dumps(generated_sections), "id": card_id}
            )
            
            # Save content to file
            _save_knowledge_card_content_to_file(connection, card_id, generated_sections)

            # Create a history entry
            result = connection.execute(
                text("SELECT created_by FROM knowledge_cards WHERE id = :id"),
                {"id": card_id}
            ).fetchone()
            if result:
                user_id = result[0]
                create_knowledge_card_history_entry(connection, card_id, generated_sections, user_id)

    except Exception as e:
        logger.error(f"[BACKGROUND KC GENERATION ERROR] {e}", exc_info=True)
        _update_progress(card_id, f"An unexpected error occurred: {e}", -1)
        with get_engine().begin() as connection:
            connection.execute(
                text("UPDATE knowledge_cards SET status = 'failed' WHERE id = :id"),
                {"id": card_id}
            )

@router.post("/knowledge-cards/{card_id}/ingest-references")
async def ingest_knowledge_card_references(card_id: uuid.UUID, background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    """
    Starts the ingestion of references for a knowledge card in the background.
    """
    #  Validate card exists and user has permission
    with get_engine().connect() as connection:
        card_check = connection.execute(
            text("SELECT id FROM knowledge_cards WHERE id = :card_id"), 
            {"card_id": card_id}
        ).fetchone()
        
        if not card_check:
            raise HTTPException(status_code=404, detail="Knowledge card not found.")

    async def ingest_references_background(card_id: uuid.UUID):
        with get_engine().begin() as connection:
            references = connection.execute(
                text("SELECT id FROM knowledge_card_references WHERE knowledge_card_id = :card_id"),
                {"card_id": card_id}
            ).fetchall()

            # Process references sequentially to avoid overload
            for ref in references:
                try:
                    await ingest_reference_content(card_id, ref.id, connection=connection)
                except Exception as e:
                    logger.error(f"[BACKGROUND INGEST ERROR] Failed to ingest reference {ref.id}: {e}")
                    continue  # Continue with next reference even if one fails

    background_tasks.add_task(ingest_references_background, card_id)
    return {"message": "Reference ingestion started in the background."}


@router.post("/knowledge-cards/{card_id}/references/{reference_id}/reingest")
async def reingest_knowledge_card_reference(card_id: uuid.UUID, reference_id: uuid.UUID, background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    """
    Starts the ingestion of a single reference for a knowledge card in the background.
    """
    #  Validate card and reference exist
    with get_engine().connect() as connection:
        ref_check = connection.execute(
            text("SELECT id FROM knowledge_card_references WHERE id = :ref_id AND knowledge_card_id = :card_id"),
            {"ref_id": reference_id, "card_id": card_id}
        ).fetchone()

        if not ref_check:
            raise HTTPException(status_code=404, detail="Reference not found for the given knowledge card.")

    async def ingest_single_reference_background(card_id: uuid.UUID, reference_id: uuid.UUID):
        with get_engine().begin() as connection:
            try:
                # Force scrape since we are manually re-ingesting
                await ingest_reference_content(card_id, reference_id, force_scrape=True, connection=connection)
            except Exception as e:
                logger.error(f"[BACKGROUND SINGLE INGEST ERROR] Failed to ingest reference {reference_id}: {e}")
                _update_ingest_progress(card_id, reference_id, "error", f"Processing error: {str(e)}")

    background_tasks.add_task(ingest_single_reference_background, card_id, reference_id)
    return {"message": "Single reference ingestion started in the background."}


@router.post("/knowledge-cards/{card_id}/generate")
async def generate_knowledge_card_content(card_id: uuid.UUID, background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    """
    Starts the generation of content for a knowledge card in the background.
    """
    #  Validate card exists and user has permission
    with get_engine().connect() as connection:
        card_check = connection.execute(
            text("SELECT id FROM knowledge_cards WHERE id = :card_id"), 
            {"card_id": card_id}
        ).fetchone()
        
        if not card_check:
            raise HTTPException(status_code=404, detail="Knowledge card not found.")
    
    background_tasks.add_task(generate_content_background, card_id)
    return {"message": "Knowledge card content generation started in the background."}

@router.get("/knowledge-cards/{card_id}/status")
async def get_knowledge_card_status(card_id: uuid.UUID, current_user: dict = Depends(get_current_user)):
    """
    Streams the status of a knowledge card generation task using SSE.
    """
    # Validate card exists and user has permission
    with get_engine().connect() as connection:
        card_check = connection.execute(
            text("SELECT id FROM knowledge_cards WHERE id = :card_id"), 
            {"card_id": card_id}
        ).fetchone()
        
        if not card_check:
            raise HTTPException(status_code=404, detail="Knowledge card not found.")

    async def event_generator():
        # Check if we are using the fallback in-memory storage or actual Redis
        if isinstance(redis_client, DictStorage):
            # Fallback for in-memory storage: polling
            logger.info(f"Using polling for knowledge card {card_id} status.")
            last_message = None
            try:
                while True:
                    # Add timeout to prevent infinite loops
                    progress_data = redis_client.get(f"knowledge_card_generation:{card_id}")
                    if progress_data and progress_data != last_message:
                        last_message = progress_data
                        yield f"data: {progress_data}\n\n"
                    
                    # Check if task is complete or failed
                    try:
                        progress_obj = json.loads(progress_data) if progress_data else {}
                        if progress_obj.get('progress', 0) >= 100 or progress_obj.get('progress', 0) == -1:
                            break
                    except:
                        pass
                        
                    await asyncio.sleep(1)  # Poll every second
            except asyncio.CancelledError:
                logger.info(f"Client disconnected from {card_id} status stream (polling).")
        else:
            # Original implementation for Redis
            logger.info(f"Using Redis Pub/Sub for knowledge card {card_id} status.")
            pubsub = redis_client.pubsub()
            channel = f"knowledge_card_generation_channel:{card_id}"
            await pubsub.subscribe(channel)
            try:
                while True:
                    message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=10)
                    if message:
                        yield f"data: {message['data']}\n\n"
                        
                        # Check if task is complete
                        try:
                            progress_obj = json.loads(message['data'])
                            if progress_obj.get('progress', 0) >= 100 or progress_obj.get('progress', 0) == -1:
                                break
                        except:
                            pass
                    
                    # Add small sleep to prevent busy waiting
                    await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                logger.info(f"Client disconnected from {card_id} status stream.")
            finally:
                #  Proper cleanup
                try:
                    await pubsub.unsubscribe(channel)
                    await pubsub.close()
                except:
                    pass

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/knowledge-cards/{card_id}/ingest-status")
async def get_knowledge_card_ingest_status(card_id: uuid.UUID, current_user: dict = Depends(get_current_user)):
    """
    Streams the status of a knowledge card reference ingestion task using SSE.
    """
    #  Validate card exists and user has permission
    with get_engine().connect() as connection:
        card_check = connection.execute(
            text("SELECT id FROM knowledge_cards WHERE id = :card_id"), 
            {"card_id": card_id}
        ).fetchone()
        
        if not card_check:
            raise HTTPException(status_code=404, detail="Knowledge card not found.")

    async def event_generator():
        if isinstance(redis_client, DictStorage):
            logger.info(f"Using polling for knowledge card {card_id} ingest status.")
            last_message = None
            try:
                while True:
                    progress_data = redis_client.get(f"knowledge_card_ingest:{card_id}")
                    if progress_data and progress_data != last_message:
                        last_message = progress_data
                        yield f"data: {progress_data}\n\n"
                    
                    # Add completion check
                    try:
                        progress_obj = json.loads(progress_data) if progress_data else {}
                        # Check if all references are processed (simplified check)
                        if progress_obj.get('status') in ['ingested', 'error', 'skipped']:
                            break
                    except:
                        pass
                        
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                logger.info(f"Client disconnected from {card_id} ingest status stream (polling).")
        else:
            logger.info(f"Using Redis Pub/Sub for knowledge card {card_id} ingest status.")
            pubsub = redis_client.pubsub()
            channel = f"knowledge_card_ingest_channel:{card_id}"
            await pubsub.subscribe(channel)
            try:
                while True:
                    message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=10)
                    if message:
                        yield f"data: {message['data']}\\n\\n"
                        
                        # Check for completion
                        try:
                            progress_obj = json.loads(message['data'])
                            if progress_obj.get('status') in ['ingested', 'error', 'skipped']:
                                break
                        except:
                            pass
                    
                    await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                logger.info(f"Client disconnected from {card_id} ingest status stream.")
            finally:
                #  Proper cleanup
                try:
                    await pubsub.unsubscribe(channel)
                    await pubsub.close()
                except:
                    pass

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/knowledge-cards/{card_id}/identify-references")
async def identify_references(card_id: uuid.UUID, data: IdentifyReferencesIn, current_user: dict = Depends(get_current_user)):
    """
    Identifies references for a knowledge card based on its title, summary, and linked element,
    and stores them in the database.
    """
    #  Validate card exists and user has permission
    with get_engine().connect() as connection:
        card_check = connection.execute(
            text("SELECT id, created_by FROM knowledge_cards WHERE id = :card_id"), 
            {"card_id": card_id}
        ).fetchone()
        
        if not card_check:
            raise HTTPException(status_code=404, detail="Knowledge card not found.")
        
        # Optional: Check user permission
        # if card_check.created_by != current_user['user_id']:
        #     raise HTTPException(status_code=403, detail="Access denied.")

    logger.info(f"Identifying references for query: {data.title}")

    try:
        crew = ReferenceIdentificationCrew()
        #  Use only the essential information
        topic = data.title or f"References for {data.linked_element}"
        
        result = crew.kickoff(link_type=data.linked_element, topic=topic)

        try:
            # Clean the raw output from the crew
            raw_output = result.raw.strip()
            if raw_output.startswith("```json"):
                raw_output = raw_output[7:]
            if raw_output.endswith("```"):
                raw_output = raw_output[:-3]
            raw_output = raw_output.strip()

            references = json.loads(raw_output)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON from crew output: {result.raw}")
            # If parsing fails, we can't proceed to store references.
            raise HTTPException(status_code=500, detail="Failed to parse references from crew output.")

        user_id = current_user['user_id']
        with get_engine().begin() as connection:
            # First, clear any existing associations for this card
            connection.execute(
                text("DELETE FROM knowledge_card_to_references WHERE knowledge_card_id = :kcid"),
                {"kcid": card_id}
            )
            # Then, process the new references
            for ref in references:
                if not ref.get("url") or not ref.get("reference_type"):
                    logger.warning(f"Skipping invalid reference: {ref}")
                    continue

                # Check if reference already exists
                existing_ref = connection.execute(
                    text("SELECT id FROM knowledge_card_references WHERE url = :url"),
                    {"url": ref.get("url")}
                ).fetchone()

                if existing_ref:
                    reference_id = existing_ref.id
                else:
                    # Insert new reference
                    new_ref_id = connection.execute(
                        text("""
                            INSERT INTO knowledge_card_references (url, reference_type, summary, created_by, updated_by, created_at, updated_at)
                            VALUES (:url, :reference_type, :summary, :user_id, :user_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                            RETURNING id
                        """),
                        {
                            "url": ref.get("url"),
                            "reference_type": ref.get("reference_type"),
                            "summary": ref.get("summary") or "",
                            "user_id": user_id
                        }
                    ).scalar_one()
                    reference_id = new_ref_id

                # Link reference to knowledge card
                connection.execute(
                    text("""
                        INSERT INTO knowledge_card_to_references (knowledge_card_id, reference_id)
                        VALUES (:kcid, :ref_id)
                        ON CONFLICT (knowledge_card_id, reference_id) DO NOTHING
                    """),
                    {"kcid": card_id, "ref_id": reference_id}
                )
            
            # Handle both string and dict types for generated_sections
            result = connection.execute(
                text("SELECT generated_sections FROM knowledge_cards WHERE id = :id"),
                {"id": card_id}
            ).fetchone()
            
            if result and result.generated_sections:
                # Check if generated_sections is already a dict or needs parsing
                if isinstance(result.generated_sections, dict):
                    generated_sections = result.generated_sections
                elif isinstance(result.generated_sections, str):
                    try:
                        generated_sections = json.loads(result.generated_sections)
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse generated_sections as JSON, using empty dict")
                        generated_sections = {}
                else:
                    generated_sections = {}
            else:
                generated_sections = {}
                
            create_knowledge_card_history_entry(connection, card_id, generated_sections, user_id)

        return {"references": references}
    except Exception as e:
        logger.error(f"[IDENTIFY REFERENCES ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to identify references.")