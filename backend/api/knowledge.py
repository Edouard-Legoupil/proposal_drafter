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
import litellm
from PyPDF2 import PdfReader
from pydantic import BaseModel, Field, validator
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
from backend.utils.reference_identification_crew import ReferenceIdentificationCrew
from backend.utils.content_generation_crew import ContentGenerationCrew
from backend.utils.scraper import scrape_url
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
    title: str
    summary: Optional[str] = None
    linked_element: Optional[str] = None

class UpdateSectionIn(BaseModel):
    content: str

class KnowledgeCardIn(BaseModel):
    summary: str
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

def create_knowledge_card_history_entry(connection, card_id: uuid.UUID, generated_sections: dict, user_id: uuid.UUID):
    """
    Creates a history entry for a knowledge card.
    """
    connection.execute(
        text("""
            INSERT INTO knowledge_card_history (knowledge_card_id, generated_sections_snapshot, created_by, created_at)
            VALUES (:knowledge_card_id, :generated_sections_snapshot, :created_by, NOW())
        """),
        {
            "knowledge_card_id": card_id,
            "generated_sections_snapshot": json.dumps(generated_sections),
            "created_by": user_id
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

    try:
        with get_engine().begin() as connection:
            connection.execute(
                text("""
                    INSERT INTO knowledge_cards (id, title, summary, template_name, status, donor_id, outcome_id, field_context_id, created_by, updated_by, created_at, updated_at)
                    VALUES (:id, :summary, :summary, :template_name, 'draft', :donor_id, :outcome_id, :field_context_id, :user_id, :user_id, NOW(), NOW())
                """),
                {
                    "id": card_id,
                    "summary": card.summary,
                    "template_name": card.template_name,
                    "donor_id": card.donor_id,
                    "outcome_id": card.outcome_id,
                    "field_context_id": card.field_context_id,
                    "user_id": user_id
                }
            )
            if card.references:
                for ref in card.references:
                    connection.execute(
                        text("""
                            INSERT INTO knowledge_card_references (knowledge_card_id, url, reference_type, summary, created_by, updated_by, created_at, updated_at)
                            VALUES (:kcid, :url, :reference_type, :summary, :user_id, :user_id, NOW(), NOW())
                        """),
                        {"kcid": card_id, "url": ref.url, "reference_type": ref.reference_type, "summary": ref.summary, "user_id": user_id}
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
                    (SELECT json_agg(json_build_object('url', kcr.url, 'reference_type', kcr.reference_type, 'summary', kcr.summary))
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
                    if isinstance(card['generated_sections'], str):
                        card['generated_sections'] = json.loads(card['generated_sections'])
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
                if isinstance(entry['generated_sections_snapshot'], str):
                    entry['generated_sections_snapshot'] = json.loads(entry['generated_sections_snapshot'])
            return {"history": history}
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
                    (SELECT json_agg(json_build_object('url', kcr.url, 'reference_type', kcr.reference_type, 'summary', kcr.summary))
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
            if card_dict.get('generated_sections'):
                if isinstance(card_dict['generated_sections'], str):
                    card_dict['generated_sections'] = json.loads(card_dict['generated_sections'])
            else:
                card_dict['generated_sections'] = {}

            return {"knowledge_card": card_dict}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"[GET KNOWLEDGE CARD ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch knowledge card.")


@router.put("/knowledge-cards/{card_id}/sections/{section_name}")
async def update_knowledge_card_section(card_id: uuid.UUID, section_name: str, section: UpdateSectionIn, current_user: dict = Depends(get_current_user)):
    """
    Updates a specific section of a knowledge card.
    """
    try:
        with get_engine().begin() as connection:
            # First, fetch the existing generated_sections
            result = connection.execute(
                text("SELECT generated_sections FROM knowledge_cards WHERE id = :id"),
                {"id": card_id}
            ).fetchone()

            if not result or not result.generated_sections:
                raise HTTPException(status_code=404, detail="Knowledge card or sections not found.")

            generated_sections = json.loads(result.generated_sections)

            if section_name not in generated_sections:
                raise HTTPException(status_code=404, detail=f"Section '{section_name}' not found.")

            # Update the specific section
            generated_sections[section_name] = section.content

            # Save the updated generated_sections back to the database
            connection.execute(
                text("UPDATE knowledge_cards SET generated_sections = :sections, updated_at = NOW() WHERE id = :id"),
                {"sections": json.dumps(generated_sections), "id": card_id}
            )

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
            # Check if card exists
            existing_card = connection.execute(text("SELECT id FROM knowledge_cards WHERE id = :id"), {"id": card_id}).fetchone()
            if not existing_card:
                raise HTTPException(status_code=404, detail="Knowledge card not found.")

            connection.execute(
                text("""
                    UPDATE knowledge_cards
                    SET summary = :summary, template_name = :template_name,
                        donor_id = :donor_id, outcome_id = :outcome_id, field_context_id = :field_context_id,
                        updated_by = :user_id, updated_at = NOW()
                    WHERE id = :id
                """),
                {
                    "id": card_id,
                    "summary": card.summary,
                    "template_name": card.template_name,
                    "donor_id": card.donor_id,
                    "outcome_id": card.outcome_id,
                    "field_context_id": card.field_context_id,
                    "user_id": user_id
                }
            )
            # Delete existing references and add new ones
            connection.execute(text("DELETE FROM knowledge_card_references WHERE knowledge_card_id = :kcid"), {"kcid": card_id})
            if card.references:
                for ref in card.references:
                    connection.execute(
                        text("""
                            INSERT INTO knowledge_card_references (knowledge_card_id, url, reference_type, summary, created_by, updated_by, created_at, updated_at)
                            VALUES (:kcid, :url, :reference_type, :summary, :user_id, :user_id, NOW(), NOW())
                        """),
                        {"kcid": card_id, "url": ref.url, "reference_type": ref.reference_type, "summary": ref.summary, "user_id": user_id}
                    )
            # Fetch the generated_sections again to get the updated state
            updated_card = connection.execute(text("SELECT generated_sections FROM knowledge_cards WHERE id = :id"), {"id": card_id}).fetchone()
            generated_sections = updated_card.generated_sections if updated_card and updated_card.generated_sections else {}
            create_knowledge_card_history_entry(connection, card_id, generated_sections, user_id)
        return {"message": "Knowledge card updated successfully.", "knowledge_card_id": card_id}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"[UPDATE KNOWLEDGE CARD ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update knowledge card.")


@router.post("/knowledge-cards/{card_id}/references")
async def create_knowledge_card_reference(card_id: uuid.UUID, reference: KnowledgeCardReferenceIn, current_user: dict = Depends(get_current_user)):
    """
    Creates a new reference for a knowledge card.
    """
    user_id = current_user['user_id']
    try:
        with get_engine().begin() as connection:
            result = connection.execute(
                text("""
                    INSERT INTO knowledge_card_references (knowledge_card_id, url, reference_type, summary, created_by, updated_by, created_at, updated_at)
                    VALUES (:kcid, :url, :reference_type, :summary, :user_id, :user_id, NOW(), NOW())
                    RETURNING id, url, reference_type, summary
                """),
                {"kcid": card_id, "url": reference.url, "reference_type": reference.reference_type, "summary": reference.summary, "user_id": user_id}
            )
            new_reference = result.fetchone()
        return {"reference": dict(new_reference)}
    except Exception as e:
        logger.error(f"[CREATE KC REFERENCE ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create reference.")


@router.put("/knowledge-cards/references/{reference_id}")
async def update_knowledge_card_reference(reference_id: uuid.UUID, reference: KnowledgeCardReferenceIn, current_user: dict = Depends(get_current_user)):
    """
    Updates an existing reference for a knowledge card.
    """
    user_id = current_user['user_id']
    try:
        with get_engine().begin() as connection:
            connection.execute(
                text("""
                    UPDATE knowledge_card_references
                    SET url = :url, reference_type = :reference_type, summary = :summary, updated_by = :user_id, updated_at = NOW()
                    WHERE id = :id
                """),
                {"id": reference_id, "url": reference.url, "reference_type": reference.reference_type, "summary": reference.summary, "user_id": user_id}
            )
        return {"message": "Reference updated successfully."}
    except Exception as e:
        logger.error(f"[UPDATE KC REFERENCE ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update reference.")


@router.delete("/knowledge-cards/references/{reference_id}")
async def delete_knowledge_card_reference(reference_id: uuid.UUID, current_user: dict = Depends(get_current_user)):
    """
    Deletes an existing reference for a knowledge card.
    """
    try:
        with get_engine().begin() as connection:
            connection.execute(
                text("DELETE FROM knowledge_card_references WHERE id = :id"),
                {"id": reference_id}
            )
        return {"message": "Reference deleted successfully."}
    except Exception as e:
        logger.error(f"[DELETE KC REFERENCE ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete reference.")


def get_embedding(chunk, model, embedder_config):
    response = litellm.embedding(
        model=model,
        input=[chunk],
        max_retries=3,
        **embedder_config
    )
    return chunk, response.data[0]['embedding']

async def _process_and_store_text(reference_id: uuid.UUID, text_content: str, connection, progress_callback=None):
    """
    Chunks text, creates embeddings, and stores them for a given reference.
    """
    def _report_progress(message):
        if progress_callback:
            progress_callback(message)
        logger.info(message)

    # For now, we will clear old vectors before adding new ones
    connection.execute(
        text("DELETE FROM knowledge_card_reference_vectors WHERE reference_id = :ref_id"),
        {"ref_id": reference_id}
    )

    # Chunk the text
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_text(text_content.replace('\x00', ''))
    _report_progress(f"Content chunked into {len(chunks)} chunks.")

    # Get the embedding configuration
    embedder_config = get_embedder_config()["config"]
    model = f"azure/{embedder_config.pop('deployment_id')}"
    # The 'model' key in the config is just the deployment name, which is not needed anymore.
    embedder_config.pop('model', None)


    # Generate and store embeddings in parallel
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(get_embedding, chunk, model, embedder_config) for chunk in chunks]
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            chunk, embedding = future.result()
            _report_progress(f"Embedding for chunk {i+1}/{len(chunks)} completed.")
            connection.execute(
                text("""
                    INSERT INTO knowledge_card_reference_vectors (reference_id, text_chunk, embedding)
                    VALUES (:ref_id, :chunk, :embedding)
                """),
                {"ref_id": reference_id, "chunk": chunk, "embedding": str(embedding)}
            )

    # Update scraped_at timestamp
    connection.execute(
        text("UPDATE knowledge_card_references SET scraped_at = NOW(), scraping_error = FALSE WHERE id = :id"),
        {"id": reference_id}
    )

async def ingest_reference_content(reference_id: uuid.UUID, force_scrape: bool = False, connection=None, progress_callback=None):
    """
    Ingests content from a reference URL, creates embeddings, and stores them.
    """
    def _report_progress(message):
        if progress_callback:
            progress_callback(message)
        logger.info(message)

    if connection is None:
        with get_engine().begin() as new_connection:
            return await ingest_reference_content(reference_id, force_scrape, new_connection, progress_callback)

    reference = connection.execute(
        text("SELECT id, url, scraped_at FROM knowledge_card_references WHERE id = :id"),
        {"id": reference_id}
    ).fetchone()

    if not reference:
        logger.error(f"Reference with id {reference_id} not found.")
        return {"status": "error", "message": "Reference not found."}

    _report_progress(f"Attempting to ingest reference: {reference.url}")

    logger.info(f"Checking reference {reference.id}: scraped_at={reference.scraped_at}, force_scrape={force_scrape}")
    if reference.scraped_at and not force_scrape and datetime.utcnow() - reference.scraped_at < timedelta(days=7):
        _report_progress(f"Reference {reference.id} was scraped recently. Skipping.")
        return {"status": "skipped", "message": "Scraped recently."}

    content = scrape_url(reference.url)

    if not content:
        logger.warning(f"Failed to scrape content from {reference.url}")
        connection.execute(
            text("UPDATE knowledge_card_references SET scraping_error = TRUE, updated_at = NOW() WHERE id = :id"),
            {"id": reference.id}
        )
        return {"status": "error", "message": "Failed to scrape content."}

    _report_progress(f"Successfully scraped content from {reference.url}")
    await _process_and_store_text(reference.id, content, connection, progress_callback)
    return {"status": "success", "message": "Content ingested successfully."}


@router.post("/knowledge-cards/references/{reference_id}/upload-pdf")
async def upload_pdf_reference(reference_id: uuid.UUID, file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
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

        with get_engine().begin() as connection:
            await _process_and_store_text(reference_id, text_content, connection)

        return {"status": "success", "message": "PDF content ingested successfully."}
    except Exception as e:
        logger.error(f"Error processing PDF for reference {reference_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process PDF file.")


def _update_progress(card_id: uuid.UUID, message: str, progress: int):
    progress_data = json.dumps({"message": message, "progress": progress})
    redis_client.set(f"knowledge_card_generation:{card_id}", progress_data)
    if not isinstance(redis_client, DictStorage):
        redis_client.publish(f"knowledge_card_generation_channel:{card_id}", progress_data)

async def generate_content_background(card_id: uuid.UUID):
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
                text("SELECT donor_id, outcome_id, field_context_id FROM knowledge_cards WHERE id = :id"),
                {"id": card_id}
            ).fetchone()

        if card.donor_id:
            template_name = "knowledge_card_donor_template.json"
        elif card.outcome_id:
            template_name = "knowledge_card_outcome_template.json"
        elif card.field_context_id:
            template_name = "knowledge_card_field_context_template.json"
        else:
            raise Exception("Knowledge card is not linked to any entity.")

        template = load_proposal_template(template_name)
        generated_sections = {}
        crew = ContentGenerationCrew()

        num_sections = len(template.get("sections", []))
        for i, section in enumerate(template.get("sections", [])):
            progress = 50 + int(((i + 1) / num_sections) * 50)
            section_name = section.get("section_name")
            instructions = section.get("instructions")
            _update_progress(card_id, f"Generating section {i+1}/{num_sections}: {section_name}", progress)

            inputs = {
                "section_name": section_name,
                "instructions": instructions,
                "knowledge_card_id": str(card_id),
            }

            result = crew.create_crew().kickoff(inputs=inputs)
            generated_sections[section_name] = str(result)

        with get_engine().begin() as connection:
            _update_progress(card_id, "Content generation complete.", 100)
            connection.execute(
                text("UPDATE knowledge_cards SET generated_sections = :sections, status = 'approved', updated_at = NOW() WHERE id = :id"),
                {"sections": json.dumps(generated_sections), "id": card_id}
            )
            # Create a history entry
            # Since this is a background task, we don't have the current user.
            # We'll attribute this to the system or the user who created the card.
            # For now, let's fetch the user who created the card.
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
    async def ingest_references_background(card_id: uuid.UUID):
        with get_engine().begin() as connection:
            references = connection.execute(
                text("SELECT id FROM knowledge_card_references WHERE knowledge_card_id = :card_id"),
                {"card_id": card_id}
            ).fetchall()

            for ref in references:
                await ingest_reference_content(ref.id, connection=connection)

    background_tasks.add_task(ingest_references_background, card_id)
    return {"message": "Reference ingestion started in the background."}


@router.post("/knowledge-cards/{card_id}/generate")
async def generate_knowledge_card_content(card_id: uuid.UUID, background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    """
    Starts the generation of content for a knowledge card in the background.
    """
    background_tasks.add_task(generate_content_background, card_id)
    return {"message": "Knowledge card content generation started in the background."}

@router.get("/knowledge-cards/{card_id}/status")
async def get_knowledge_card_status(card_id: uuid.UUID, current_user: dict = Depends(get_current_user)):
    """
    Streams the status of a knowledge card generation task using SSE.
    """
    async def event_generator():
        # Check if we are using the fallback in-memory storage or actual Redis
        if isinstance(redis_client, DictStorage):
            # Fallback for in-memory storage: polling
            logger.info(f"Using polling for knowledge card {card_id} status.")
            last_message = None
            try:
                while True:
                    progress_data = redis_client.get(f"knowledge_card_generation:{card_id}")
                    if progress_data and progress_data != last_message:
                        last_message = progress_data
                        yield f"data: {progress_data}\n\n"
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
                    await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                logger.info(f"Client disconnected from {card_id} status stream.")
            finally:
                await pubsub.unsubscribe(channel)
                await pubsub.close()

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.post("/knowledge-cards/{card_id}/identify-references")
async def identify_references(card_id: uuid.UUID, data: IdentifyReferencesIn, current_user: dict = Depends(get_current_user)):
    """
    Identifies references for a knowledge card based on its title, summary, and linked element,
    and stores them in the database.
    """
    logger.info(f"Identifying references for query: {data.title}")

    try:
        crew = ReferenceIdentificationCrew()
        topic = data.title
        if data.summary:
            topic += f"\n{data.summary}"
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
            # First, clear any existing references for this card
            connection.execute(
                text("DELETE FROM knowledge_card_references WHERE knowledge_card_id = :kcid"),
                {"kcid": card_id}
            )
            # Then, insert the new references
            for ref in references:
                connection.execute(
                    text("""
                        INSERT INTO knowledge_card_references (knowledge_card_id, url, reference_type, summary, created_by, updated_by, created_at, updated_at)
                        VALUES (:kcid, :url, :reference_type, :summary, :user_id, :user_id, NOW(), NOW())
                    """),
                    {
                        "kcid": card_id,
                        "url": ref.get("url"),
                        "reference_type": ref.get("reference_type"),
                        "summary": ref.get("summary"),
                        "user_id": user_id
                    }
                )
            # Fetch the current generated_sections to create a history entry
            result = connection.execute(
                text("SELECT generated_sections FROM knowledge_cards WHERE id = :id"),
                {"id": card_id}
            ).fetchone()
            generated_sections = json.loads(result.generated_sections) if result and result.generated_sections else {}
            create_knowledge_card_history_entry(connection, card_id, generated_sections, user_id)

        return {"references": references}
    except Exception as e:
        logger.error(f"[IDENTIFY REFERENCES ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to identify references.")
