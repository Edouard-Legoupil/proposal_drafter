#  Standard Library
import json
import re
import uuid
from datetime import datetime 
import logging
from typing import Optional

#  Third-Party Libraries
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError 

#  Internal Modules
from backend.core.db import get_engine
from backend.core.redis import redis_client
from backend.core.security import get_current_user
from backend.core.config import SECTIONS, get_available_templates, load_proposal_template
from backend.models.schemas import (
    SectionRequest,
    RegenerateRequest,
    SaveDraftRequest,
    FinalizeProposalRequest
)
from backend.utils.proposal_logic import regenerate_section_logic
from backend.utils.crew import ProposalCrew

# This router handles all endpoints related to the lifecycle of a proposal,
# from creation and editing to listing and deletion.
router = APIRouter()

# Configure logging
logger = logging.getLogger(__name__)


@router.get("/templates")
async def get_templates():
    """
    Returns a list of available proposal templates.
    """
    templates = get_available_templates()
    return {"templates": templates}


@router.post("/process_section/{session_id}")
async def process_section(session_id: str, request: SectionRequest, current_user: dict = Depends(get_current_user)):
    """
    Processes a single section of a proposal by running the generation crew.
    If the initial output is flagged, it automatically triggers a regeneration.
    """
    logger.info(f"Processing section {request.section} for proposal {request.proposal_id}")
    logger.info(f"Type of proposal_id: {type(request.proposal_id)}")

    session_data_str = redis_client.get(session_id)
    if not session_data_str:
        raise HTTPException(status_code=400, detail="Session data not found.")

    # Prevent editing of finalized proposals.
    with get_engine().connect() as connection:
        res = connection.execute(
            text("SELECT is_accepted FROM proposals WHERE id = :id AND user_id = :uid"),
            {"id": request.proposal_id, "uid": current_user["user_id"]}
        ).scalar()
        if res:
            raise HTTPException(status_code=403, detail="This proposal is finalized and cannot be modified.")

    session_data = json.loads(session_data_str)
    form_data = session_data["form_data"]
    project_description = session_data["project_description"]

    #  Get proposal template from session data
    proposal_template = session_data.get("proposal_template")
    if not proposal_template:
        raise HTTPException(status_code=400, detail="Proposal template not found in session.")

    section_config = next((s for s in proposal_template["sections"] if s["section_name"] == request.section), None)
    if not section_config:
        raise HTTPException(status_code=400, detail=f"Invalid section name: {request.section}")

    # Initialize and run the generation crew.
    crew_instance = ProposalCrew().generate_proposal_crew()
    result = crew_instance.kickoff(inputs={
        "section": request.section,
        "form_data": form_data,
        "project_description": project_description,
        "instructions": section_config.get("instructions", ""),
        "word_limit": section_config.get("word_limit", 350)
    })

    # Parse and handle crew output.
    #raw_output = result.raw.replace("`", "")
    #raw_output = re.sub(r'[\x00-\x1F\x7F]', '', raw_output)
    #parsed = json.loads(raw_output)
    try:
        raw_output = result.raw if hasattr(result, 'raw') and result.raw else ""
        logger.debug(
            f"[CREWAI RAW OUTPUT] Proposal {request.proposal_id}, "
            f"Session {session_id}, Section {request.section} :: {raw_output[:1000]}..."
        )
        clean_output = re.sub(r'[`\x00-\x1F\x7F]', '', raw_output)
        logger.debug(
            f"[CREWAI CLEANED OUTPUT] Proposal {request.proposal_id}, "
            f"Session {session_id}, Section {request.section} :: {clean_output[:1000]}..."
        )
        parsed = json.loads(clean_output)
    except (AttributeError, json.JSONDecodeError) as e:
        print(f"[CREWAI PARSE ERROR] {e}")
        raise HTTPException(status_code=500, detail="Failed to parse CrewAI output. It may not be valid JSON.")


    generated_text = parsed.get("generated_content", "").strip()
    evaluation_status = parsed.get("evaluation_status", "")
    feedback = parsed.get("feedback", "")

    if not generated_text:
        logger.warning(
            f"[CREWAI MISSING CONTENT] No 'generated_content' for Proposal {request.proposal_id}, "
            f"Session {session_id}, Section {request.section} :: Parsed Keys: {list(parsed.keys())}"
        )
    
    if evaluation_status.lower() == "flagged" and feedback:
        # If flagged, automatically regenerate with feedback.
        generated_text = regenerate_section_logic(
            session_id, request.section, feedback, request.proposal_id
        )
        message = f"Initial content flagged. Regenerated using evaluator feedback for {request.section}"
    else:
        message = f"Content generated for {request.section}"

    # Persist the generated text to the database.
    try:
        with get_engine().begin() as conn:
            db_res = conn.execute(text("SELECT generated_sections FROM proposals WHERE id = :id"), {"id": request.proposal_id}).scalar()

            # The database driver is already converting JSON to a dict,
            # so we can use db_res directly if it exists.
            sections = db_res if db_res else {}
            if not isinstance(sections, dict):
                logger.warning(
                    f"[DB TYPE MISMATCH] Expected dict for generated_sections but got {type(sections)} "
                    f"for Proposal {request.proposal_id}. Converting..."
                )
                try:
                    sections = json.loads(sections)
                except Exception:
                    logger.error(
                        f"[DB CONVERSION ERROR] Failed to load generated_sections JSON for Proposal {request.proposal_id}"
                    )
                    sections = {}

           # sections = json.loads(db_res) if db_res else {}
            
            sections[request.section] = generated_text
            conn.execute(
                text("UPDATE proposals SET generated_sections = :sections, updated_at = NOW() WHERE id = :id"),
                {"sections": json.dumps(sections), "id": request.proposal_id}
            )
    except Exception as e:
        logger.exception(
            f"[DB UPDATE ERROR - process_section] Proposal {request.proposal_id}, "
            f"Session {session_id}, Section {request.section} :: {e}"
        )
        raise HTTPException(status_code=500, detail="Failed to save section to database.")

    return {"message": message, "generated_text": generated_text}


@router.post("/regenerate_section/{session_id}")
async def regenerate_section(session_id: str, request: RegenerateRequest, current_user: dict = Depends(get_current_user)):
    """
    Manually regenerates a section using concise user input.
    """
    # Prevent editing of finalized proposals.
    with get_engine().connect() as connection:
        res = connection.execute(
            text("SELECT is_accepted FROM proposals WHERE id = :id AND user_id = :uid"),
            {"id": request.proposal_id, "uid": current_user["user_id"]}
        ).scalar()
        if res:
            raise HTTPException(status_code=403, detail="This proposal is finalized and cannot be modified.")

    generated_text = regenerate_section_logic(
        session_id, request.section, request.concise_input, request.proposal_id
    )
    return {"message": f"Content regenerated for {request.section}", "generated_text": generated_text}


@router.post("/save-draft")
async def save_draft(request: SaveDraftRequest, current_user: dict = Depends(get_current_user)):
    """
    Saves a new draft or updates an existing one in the database.
    """
    user_id = current_user["user_id"]
    # If proposal_id is not provided in the request, generate a new one.
    proposal_id = request.proposal_id or uuid.uuid4()
    # If proposal_id is not provided in the request, generate a new one.
    proposal_id = request.proposal_id or uuid.uuid4()

    try:
        with get_engine().begin() as connection:
            # Check if a draft with this ID already exists for the user.
            # Check if a draft with this ID already exists for the user.
            existing = connection.execute(
                text("SELECT id FROM proposals WHERE id = :id AND user_id = :uid"),
                {"id": proposal_id, "uid": user_id}
            ).fetchone()

            # Prepare the data for insertion/update.
            # The 'generated_sections' are now expected to be a dict of Pydantic models,
            # so we need to convert them to a JSON-serializable dict.
            sections_to_save = {
                key: value.dict() for key, value in request.generated_sections.items()
            } if request.generated_sections else {}

            # Prepare the data for insertion/update.
            # The 'generated_sections' are now expected to be a dict of Pydantic models,
            # so we need to convert them to a JSON-serializable dict.
            sections_to_save = {
                key: value.dict() for key, value in request.generated_sections.items()
            } if request.generated_sections else {}

            if existing:
                # Update an existing draft.
                connection.execute(
                    text("""
                        UPDATE proposals
                        SET form_data = :form, project_description = :desc, generated_sections = :sections,
                            template_name = :template_name, updated_at = NOW()
                        WHERE id = :id
                    """),
                    {
                        "form": json.dumps(request.form_data),
                        "desc": request.project_description,
                        "sections": json.dumps(sections_to_save),
                        "sections": json.dumps(sections_to_save),
                        "id": proposal_id,
                        "template_name": request.template_name
                    }
                )
                message = "Draft updated successfully"
            else:
                # Insert a new draft.
                connection.execute(
                    text("""
                        INSERT INTO proposals (id, user_id, form_data, project_description, generated_sections, template_name)
                        VALUES (:id, :uid, :form, :desc, :sections, :template_name)
                    """),
                    {
                        "id": proposal_id,
                        "uid": user_id,
                        "form": json.dumps(request.form_data),
                        "desc": request.project_description,
                        "sections": json.dumps(sections_to_save),
                        "sections": json.dumps(sections_to_save),
                        "template_name": request.template_name
                    }
                )
                message = "Draft created successfully"

        # Return the proposal_id as a string for JSON serialization.
        return {"message": message, "proposal_id": str(proposal_id)}
    except SQLAlchemyError as db_error:
        logger.error(f"[SAVE DRAFT DB ERROR] {db_error}", exc_info=True)
        raise HTTPException(status_code=500, detail="A database error occurred while saving the draft.")
        # Return the proposal_id as a string for JSON serialization.
        return {"message": message, "proposal_id": str(proposal_id)}
    except SQLAlchemyError as db_error:
        logger.error(f"[SAVE DRAFT DB ERROR] {db_error}", exc_info=True)
        raise HTTPException(status_code=500, detail="A database error occurred while saving the draft.")
    except Exception as e:
        logger.error(f"[SAVE DRAFT ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while saving the draft.")
        logger.error(f"[SAVE DRAFT ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while saving the draft.")


@router.get("/list-drafts")
async def list_drafts(current_user: dict = Depends(get_current_user)):
    """
    Lists all drafts for the current user, including sample templates.
    """
    logger.info(f"Attempting to list drafts for user: {current_user['user_id']}")
    user_id = current_user["user_id"]
    draft_list = []

    # Load sample templates from file.
    try:
        with open("templates/sample_templates.json", "r", encoding="utf-8") as f:
            sample_templates = json.load(f)
        for sample in sample_templates:
            sample["project_title"] = sample.get("form_data", {}).get("Project title", "Untitled Sample")
            sample["summary"] = sample.get("generated_sections", {}).get("Summary", "")
            sample["is_sample"] = True
        draft_list.extend(sample_templates)
        logger.info(f"Loaded {len(sample_templates)} sample templates")
    except Exception as e:
        logger.error(f"[TEMPLATE LOAD ERROR] {e}")  # Changed print to logger

    # Fetch user's drafts from the database.
    try:  # Fixed: This was indented incorrectly (had extra spaces)
        logger.info("Attempting database connection...")
        engine = get_engine()
        logger.info(f"Engine type: {type(engine)}")
        
        with engine.connect() as connection:
            logger.info("Database connection established")
            result = connection.execute(
                text("SELECT id, form_data, generated_sections, created_at, updated_at, is_accepted FROM proposals WHERE user_id = :uid ORDER BY updated_at DESC"),
                {"uid": user_id}
            )
            rows = result.fetchall()
            logger.info(f"Found {len(rows)} drafts in database")
            
            for row in rows:
                # Handle JSON fields properly - they might be strings or already parsed dicts
                form_data = row[1]
                if isinstance(form_data, str):
                    try:
                        form_data = json.loads(form_data)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse form_data JSON for proposal {row[0]}")
                        form_data = {}
                
                sections = row[2]
                if isinstance(sections, str):
                    try:
                        sections = json.loads(sections)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse generated_sections JSON for proposal {row[0]}")
                        sections = {}

                draft_list.append({
                    "proposal_id": row[0],
                    "project_title": form_data.get("Project title", "Untitled Proposal") if form_data else "Untitled Proposal",
                    "summary": sections.get("Summary", "") if sections else "",
                    "created_at": row[3].isoformat() if row[3] else None,
                    "updated_at": row[4].isoformat() if row[4] else None,
                    "is_accepted": row[5],
                    "is_sample": False
                })
                
        logger.info(f"Total drafts (samples + user): {len(draft_list)}")
        return {"message": "Drafts fetched successfully.", "drafts": draft_list}
        
    except SQLAlchemyError as db_error:
        logger.error(f"[DATABASE ERROR - list_drafts] {db_error}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    except Exception as e:
        logger.error(f"[LIST DRAFTS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch drafts")

@router.get("/sections")
async def get_sections():
    """
    Returns the list of sections for the default template.
    DEPRECATED: Use /templates/{template_name}/sections instead.
    """
    try:
        default_template = load_proposal_template("unhcr_proposal_template.json")
        return {"sections": default_template.get("sections", [])}
    except HTTPException as e:
        # Handle case where default template is not found
        logger.error(f"Could not load default template: {e.detail}")
        return {"sections": []}

@router.get("/templates/{template_name}/sections")
async def get_template_sections(template_name: str):
    """
    Returns the list of sections for a given template.
    """
    proposal_template = load_proposal_template(template_name)
    return {"sections": proposal_template.get("sections", [])}

@router.get("/load-draft/{proposal_id}")
async def load_draft(proposal_id: str, current_user: dict = Depends(get_current_user)):
    """
    Loads a specific draft, whether it's a user-created one or a sample.
    It creates a new Redis session for the loaded draft.
    """
    user_id = current_user["user_id"]
    
    try:
        # Handle user drafts, loaded from the database.
        if not proposal_id.startswith("sample-"):
            # Manually validate if the proposal_id is a valid UUID for non-sample drafts.
            try:
                uuid.UUID(proposal_id)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid proposal ID format: '{proposal_id}'.")

            with get_engine().connect() as conn:
                draft = conn.execute(
                    text("""
                        SELECT template_name, form_data, generated_sections, project_description,
                               is_accepted, created_at, updated_at
                        FROM proposals
                        WHERE id = :id AND user_id = :uid
                    """),
                    {"id": proposal_id, "uid": user_id}
                ).fetchone()
                if not draft:
                    raise HTTPException(status_code=404, detail="Draft not found.")

                template_name = draft[0] or "unhcr_proposal_template.json" # Default if null
                proposal_template = load_proposal_template(template_name)
                section_names = [s.get("section_name") for s in proposal_template.get("sections", [])]

                form_data = draft[1] if draft[1] else {}
                sections = draft[2] if draft[2] else {}
                project_description = draft[3]
                
                data_to_load = {
                    "form_data": form_data,
                    "project_description": project_description,
                    "generated_sections": {sec: sections.get(sec) for sec in section_names},
                    "is_accepted": draft[4],
                    "created_at": draft[5].isoformat() if draft[5] else None,
                    "updated_at": draft[6].isoformat() if draft[6] else None,
                    "is_sample": False,
                    "template_name": template_name,
                    "proposal_template": proposal_template,
                    "proposal_id": str(proposal_id)
                }
        else:
            # Handle sample drafts, which are loaded from a JSON file.
            with open("templates/sample_templates.json", "r") as f:
                samples = json.load(f)
            sample = next((s for s in samples if s["proposal_id"] == proposal_id), None)
            if not sample:
                raise HTTPException(status_code=404, detail="Sample not found.")

            template_name = sample.get("template_name", "unhcr_proposal_template.json")
            proposal_template = load_proposal_template(template_name)

            data_to_load = sample
            data_to_load["is_sample"] = True
            data_to_load["proposal_template"] = proposal_template
            data_to_load["template_name"] = template_name

    except HTTPException as http_exc:
        # Re-raise HTTP exceptions to be handled by FastAPI's default handler.
        raise http_exc
    except Exception as e:
        # Catch any other unexpected errors during draft loading.
        logger.error(f"[LOAD DRAFT ERROR] Failed to load draft {proposal_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while loading the draft: {e}")

    # Create a new Redis session for the loaded draft.
    session_id = str(uuid.uuid4())
    redis_payload = {
        "user_id": user_id,
        "proposal_id": str(proposal_id),  # Ensure proposal_id is a string for Redis
        **data_to_load
    }

    # The proposal_template is already a dict, which is JSON serializable.
    redis_client.setex(session_id, 3600, json.dumps(redis_payload, default=str))

    return {"session_id": session_id, **data_to_load}

@router.post("/finalize-proposal")
async def finalize_proposal(request: FinalizeProposalRequest, current_user: dict = Depends(get_current_user)):
    """
    Marks a proposal as 'accepted', making it read-only.
    """
    try:
        with get_engine().begin() as connection:
            connection.execute(
                text("UPDATE proposals SET is_accepted = TRUE, updated_at = NOW() WHERE id = :id AND user_id = :uid"),
                {"id": request.proposal_id, "uid": current_user["user_id"]}
            )
        return {"message": "Proposal finalized.", "proposal_id": request.proposal_id, "is_accepted": True}
    except Exception as e:
        print(f"[FINALIZE ERROR] {e}")
        raise HTTPException(status_code=500, detail="Failed to finalize proposal.")


@router.delete("/delete-draft/{proposal_id}")
async def delete_draft(proposal_id: uuid.UUID, current_user: dict = Depends(get_current_user)):
    """
    Deletes a draft proposal from the database.
    """
    user_id = current_user["user_id"]
    try:
        with get_engine().begin() as connection:
            result = connection.execute(
                text("DELETE FROM proposals WHERE id = :id AND user_id = :uid AND is_accepted = FALSE RETURNING id"),
                {"id": proposal_id, "uid": user_id}
            )
            if not result.fetchone():
                raise HTTPException(status_code=404, detail="Draft not found or is finalized.")

        return {"message": f"Draft '{proposal_id}' deleted successfully."}
    except Exception as e:
        logger.error(f"[DELETE DRAFT ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete draft.")
