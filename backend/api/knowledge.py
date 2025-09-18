# backend/api/knowledge.py
import json
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, Body, UploadFile, File, BackgroundTasks
from sqlalchemy import text
import litellm
import pypdf
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime, timedelta

from backend.core.db import get_engine
from backend.core.redis import redis_client
from backend.core.security import get_current_user
from backend.core.config import load_proposal_template
from backend.utils.reference_identification_crew import ReferenceIdentificationCrew
from backend.utils.content_generation_crew import ContentGenerationCrew
from backend.utils.scraper import scrape_url
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
                    VALUES (:id, :title, :summary, :template_name, 'draft', :donor_id, :outcome_id, :field_context_id, :user_id, :user_id, NOW(), NOW())
                """),
                {
                    "id": card_id,
                    "title": card.title,
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
                    kc.title,
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
                    card['generated_sections'] = json.loads(card['generated_sections'])
                else:
                    card['generated_sections'] = {}
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
                    SET title = :title, summary = :summary, template_name = :template_name,
                        donor_id = :donor_id, outcome_id = :outcome_id, field_context_id = :field_context_id,
                        updated_by = :user_id, updated_at = NOW()
                    WHERE id = :id
                """),
                {
                    "id": card_id,
                    "title": card.title,
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
        return {"message": "Knowledge card updated successfully.", "knowledge_card_id": card_id}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"[UPDATE KNOWLEDGE CARD ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update knowledge card.")


async def _process_and_store_text(reference_id: uuid.UUID, text_content: str, connection):
    """
    Chunks text, creates embeddings, and stores them for a given reference.
    """
    # For now, we will clear old vectors before adding new ones
    connection.execute(
        text("DELETE FROM knowledge_card_reference_vectors WHERE reference_id = :ref_id"),
        {"ref_id": reference_id}
    )

    # Chunk the text
    chunks = [chunk for chunk in text_content.split("\n") if chunk.strip()]

    # Generate and store embeddings
    for chunk in chunks:
        response = litellm.embedding(
            model=os.getenv("AZURE_EMBEDDING_MODEL", "text-embedding-ada-002"),
            input=[chunk]
        )
        embedding = response.data[0]['embedding']
        connection.execute(
            text("""
                INSERT INTO knowledge_card_reference_vectors (reference_id, text_chunk, embedding)
                VALUES (:ref_id, :chunk, :embedding)
            """),
            {"ref_id": reference_id, "chunk": chunk, "embedding": embedding}
        )

    # Update scraped_at timestamp
    connection.execute(
        text("UPDATE knowledge_card_references SET scraped_at = NOW(), scraping_error = FALSE WHERE id = :id"),
        {"id": reference_id}
    )

async def ingest_reference_content(reference_id: uuid.UUID, force_scrape: bool = False):
    """
    Ingests content from a reference URL, creates embeddings, and stores them.
    """
    with get_engine().begin() as connection:
        reference = connection.execute(
            text("SELECT id, url, scraped_at FROM knowledge_card_references WHERE id = :id"),
            {"id": reference_id}
        ).fetchone()

        if not reference:
            logger.error(f"Reference with id {reference_id} not found.")
            return {"status": "error", "message": "Reference not found."}

        if reference.scraped_at and not force_scrape and datetime.utcnow() - reference.scraped_at < timedelta(days=7):
            logger.info(f"Reference {reference.id} was scraped recently. Skipping.")
            return {"status": "skipped", "message": "Scraped recently."}

        content = scrape_url(reference.url)

        if not content:
            connection.execute(
                text("UPDATE knowledge_card_references SET scraping_error = TRUE, updated_at = NOW() WHERE id = :id"),
                {"id": reference.id}
            )
            return {"status": "error", "message": "Failed to scrape content."}

        await _process_and_store_text(reference.id, content, connection)
        return {"status": "success", "message": "Content ingested successfully."}


@router.post("/knowledge-cards/references/{reference_id}/upload-pdf")
async def upload_pdf_reference(reference_id: uuid.UUID, file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """
    Uploads a PDF for a reference, extracts text, and stores embeddings.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF.")

    try:
        pdf_reader = pypdf.PdfReader(file.file)
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
    redis_client.set(f"knowledge_card_generation:{card_id}", json.dumps({"message": message, "progress": progress}))

async def generate_content_background(card_id: uuid.UUID):
    try:
        with get_engine().begin() as connection:
            _update_progress(card_id, "Starting content generation...", 0)
            connection.execute(
                text("UPDATE knowledge_cards SET status = 'generating_sections' WHERE id = :id"),
                {"id": card_id}
            )

            references = connection.execute(
                text("SELECT id, url FROM knowledge_card_references WHERE knowledge_card_id = :card_id"),
                {"card_id": card_id}
            ).fetchall()

            num_references = len(references)
            for i, ref in enumerate(references):
                progress = int(((i + 1) / (num_references + 1)) * 50)
                _update_progress(card_id, f"Processing reference {i+1}/{num_references}: {ref.url}", progress)
                result = await ingest_reference_content(ref.id)
                if result["status"] == "error":
                    _update_progress(card_id, f"Failed to scrape {ref.url}. Please upload a PDF.", progress)
                    # For now, we will just log and continue. A more robust solution would be to wait for user action.

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
                generated_sections[section_name] = result

            _update_progress(card_id, "Content generation complete.", 100)
            connection.execute(
                text("UPDATE knowledge_cards SET generated_sections = :sections, status = 'completed', updated_at = NOW() WHERE id = :id"),
                {"sections": json.dumps(generated_sections), "id": card_id}
            )
    except Exception as e:
        logger.error(f"[BACKGROUND KC GENERATION ERROR] {e}", exc_info=True)
        _update_progress(card_id, f"An unexpected error occurred: {e}", -1)
        with get_engine().begin() as connection:
            connection.execute(
                text("UPDATE knowledge_cards SET status = 'failed' WHERE id = :id"),
                {"id": card_id}
            )

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
    Gets the status of a knowledge card generation task.
    """
    try:
        progress_data = redis_client.get(f"knowledge_card_generation:{card_id}")
        if progress_data:
            return json.loads(progress_data)

        # If no progress data, check the database for final status
        with get_engine().connect() as connection:
            result = connection.execute(
                text("SELECT status, generated_sections FROM knowledge_cards WHERE id = :id"),
                {"id": card_id}
            ).fetchone()

            if not result:
                raise HTTPException(status_code=404, detail="Knowledge card not found.")

            if result.status == 'completed':
                return {"status": "completed", "progress": 100, "generated_sections": json.loads(result.generated_sections) if result.generated_sections else None}
            elif result.status == 'failed':
                return {"status": "failed", "progress": -1}
            else:
                return {"status": result.status, "progress": 0}

    except Exception as e:
        logger.error(f"[GET KC STATUS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get knowledge card status.")

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
                        INSERT INTO knowledge_card_references (knowledge_card_id, url, reference_type, summary)
                        VALUES (:kcid, :url, :reference_type, :summary)
                    """),
                    {
                        "kcid": card_id,
                        "url": ref.get("url"),
                        "reference_type": ref.get("reference_type"),
                        "summary": ref.get("summary")
                    }
                )

        return {"references": references}
    except Exception as e:
        logger.error(f"[IDENTIFY REFERENCES ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to identify references.")
