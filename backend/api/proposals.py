#  Standard Library
import json
import re
import uuid
from datetime import datetime 
import logging
import tempfile
import os
from typing import Optional

#  Third-Party Libraries
import pdfplumber
from fastapi import APIRouter, Depends, HTTPException, Body, UploadFile, File, BackgroundTasks
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError 
from slugify import slugify

#  Internal Modules
from backend.core.db import get_engine
from backend.core.redis import redis_client
from backend.core.security import get_current_user
from backend.core.config import get_available_templates, load_proposal_template
from backend.utils.crew_actions import handle_text_format, handle_fixed_text_format, handle_number_format, handle_table_format
from backend.models.schemas import (
    SectionRequest,
    RegenerateRequest,
    SaveDraftRequest,
    FinalizeProposalRequest,
    CreateSessionRequest,
    UpdateSectionRequest,
    SubmitPeerReviewRequest,
    SubmitReviewRequest,
    CreateDonorRequest,
    CreateOutcomeRequest,
    CreateFieldContextRequest,
    UpdateProposalStatusRequest,
    TransferOwnershipRequest,
    AuthorResponseRequest,
    SaveContributionIdRequest
)
from backend.utils.proposal_logic import regenerate_section_logic
from backend.utils.crew_proposal  import ProposalCrew
from backend.api.knowledge import _save_knowledge_card_content_to_file

# This router handles all endpoints related to the lifecycle of a proposal,
# from creation and editing to listing and deletion.
router = APIRouter()

# Configure logging
logger = logging.getLogger(__name__)


@router.get("/templates")
async def get_templates():
    """
    Returns a dictionary mapping donor names to template filenames.
    This allows the frontend to populate a dropdown with donor names, making the
    backend the single source of truth for template selection.
    """
    try:
        templates_map = get_available_templates()
        return {"templates": templates_map}
    except Exception as e:
        logger.error(f"[GET TEMPLATES ERROR] Failed to get available templates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not retrieve proposal templates.")


@router.get("/templates/{template_name}")
async def get_template(template_name: str):
    """
    Loads and returns the content of a specific template file.
    """
    try:
        template_data = load_proposal_template(template_name)
        return template_data
    except HTTPException as http_exc:
        # Re-raise HTTP exceptions from load_proposal_template
        raise http_exc
    except Exception as e:
        logger.error(f"Failed to load template '{template_name}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while loading the template.")


@router.post("/create-session")
async def create_session(request: CreateSessionRequest, current_user: dict = Depends(get_current_user)):
    """
    Creates a new proposal session and a corresponding draft in the database.
    This single endpoint replaces the frontend's previous multi-step process
    of saving a draft and then immediately reloading it to start a session.

    The process is as follows:
    1.  Determine the template name from the form data's "Targeted Donor".
    2.  Generate a new UUID for the proposal.
    3.  Create an initial record in the 'proposals' database table and link relational data.
    4.  Load the full proposal template from the determined file.
    5.  Store all relevant data (form data, template, etc.) in a new Redis session.
    6.  Return the new session_id and proposal_id to the client.
    """
    user_id = current_user["user_id"]
    proposal_id = uuid.uuid4()
    session_id = str(uuid.uuid4())

    try:
        templates_map = get_available_templates()
        donor_id = request.form_data.get("Targeted Donor")
        template_name = "proposal_template_unhcr.json"  # Default template

        with get_engine().begin() as connection:
            if donor_id:
                # Get donor name from ID to determine the template
                donor_name_result = connection.execute(
                    text("SELECT name FROM donors WHERE id = :id"),
                    {"id": donor_id}
                ).scalar()
                if donor_name_result:
                    template_name = templates_map.get(donor_name_result, "proposal_template_unhcr.json")

            # Create the main proposal record
            connection.execute(
                text("""
                    INSERT INTO proposals (id, user_id, created_by, updated_by, form_data, project_description, template_name, generated_sections)
                    VALUES (:id, :uid, :uid, :uid, :form, :desc, :template, '{}')
                """),
                {
                    "id": proposal_id,
                    "uid": user_id,
                    "form": json.dumps(request.form_data),
                    "desc": request.project_description,
                    "template": template_name,
                }
            )

            # Log the initial 'draft' status with an empty sections snapshot
            connection.execute(
                text("INSERT INTO proposal_status_history (proposal_id, status, generated_sections_snapshot) VALUES (:pid, 'draft', '{}'::jsonb)"),
                {"pid": proposal_id}
            )

            # Insert into join tables
            outcome_ids = request.form_data.get("Main Outcome", [])
            # The frontend might send an ID for "Geographical Scope" or "Country / Location(s)"
            field_context_id = request.form_data.get("Country / Location(s)") or request.form_data.get("Geographical Scope")

            if donor_id:
                connection.execute(
                    text("INSERT INTO proposal_donors (proposal_id, donor_id) VALUES (:pid, :did)"),
                    {"pid": proposal_id, "did": donor_id}
                )

            if outcome_ids and isinstance(outcome_ids, list):
                for outcome_id in outcome_ids:
                    if outcome_id: # Ensure outcome_id is not empty
                        connection.execute(
                            text("INSERT INTO proposal_outcomes (proposal_id, outcome_id) VALUES (:pid, :oid)"),
                            {"pid": proposal_id, "oid": outcome_id}
                        )

            if field_context_id:
                connection.execute(
                    text("INSERT INTO proposal_field_contexts (proposal_id, field_context_id) VALUES (:pid, :fid)"),
                    {"pid": proposal_id, "fid": field_context_id}
                )

        # Load the full proposal template.
        proposal_template = load_proposal_template(template_name)

        # Create the Redis session payload.
        redis_payload = {
            "user_id": user_id,
            "proposal_id": str(proposal_id),
            "form_data": request.form_data,
            "project_description": request.project_description,
            "associated_knowledge_cards": request.associated_knowledge_cards,
            "template_name": template_name,
            "proposal_template": proposal_template,
            "generated_sections": {},
            "is_sample": False,
            "is_accepted": False
        }

        # Store the payload in Redis.
        redis_client.setex(session_id, 3600, json.dumps(redis_payload, default=str))

        # Return the new IDs.
        return {"session_id": session_id, "proposal_id": str(proposal_id), "proposal_template": proposal_template}

    except HTTPException as http_exc:
        logger.error(f"[CREATE SESSION HTTP ERROR] {http_exc.detail}", exc_info=True)
        raise http_exc
    except Exception as e:
        logger.error(f"[CREATE SESSION ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create a new proposal session.")


def generate_all_sections_background(session_id: str, proposal_id: str, user_id: str):
    """
    Runs the proposal generation process for all sections in the background.
    """
    logger.info(f"Starting background generation for proposal {proposal_id}")
    knowledge_file_paths = []
    try:
        with get_engine().begin() as connection:
            connection.execute(
                text("UPDATE proposals SET status = 'generating_sections', updated_at = CURRENT_TIMESTAMP WHERE id = :id"),
                {"id": proposal_id}
            )

        session_data_str = redis_client.get(session_id)
        if not session_data_str:
            raise Exception("Session data not found in Redis.")

        session_data = json.loads(session_data_str)
        proposal_template = session_data.get("proposal_template")
        if not proposal_template or "sections" not in proposal_template:
            raise Exception("Proposal template or sections not found in session.")

        form_data = session_data["form_data"]
        project_description = session_data["project_description"]
        associated_knowledge_cards = session_data.get("associated_knowledge_cards")
        all_sections = {}


        # Get the absolute path to the knowledge directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        knowledge_dir = os.path.join(current_dir, "..",   "knowledge")
        
        # Ensure the knowledge directory exists
        os.makedirs(knowledge_dir, exist_ok=True)

        if associated_knowledge_cards:
            with get_engine().connect() as connection:
                for card in associated_knowledge_cards:
                    card_id = card.get("id")
                    if not card_id:
                        logger.warning("Associated knowledge card missing 'id', skipping.")
                        continue

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
                            LEFT JOIN donors d ON kc.donor_id = d.id
                            LEFT JOIN outcomes o ON kc.outcome_id = o.id
                            LEFT JOIN field_contexts fc ON kc.field_context_id = fc.id
                            WHERE kc.id = :card_id
                        """),
                        {"card_id": str(card_id)}
                    ).fetchone()

                    if not card_details:
                        logger.warning(f"Knowledge card with id {card_id} not found, skipping.")
                        continue

                    card_summary = card_details.summary
                    link_type, link_id = None, None
                    if card_details.donor_id:
                        link_type, link_id = "donor", card_details.donor_id
                        link_label = card_details.donor_name
                    elif card_details.outcome_id:
                        link_type, link_id = "outcome", card_details.outcome_id
                        link_label = card_details.outcome_name
                    elif card_details.field_context_id:
                        link_type, link_id = "field_context", card_details.field_context_id
                        link_label = card_details.field_context_name

                    # Create the filename
                    filename = f"{link_type}-{slugify(link_label)}-{slugify(card_summary)}.json" if link_type and link_id else f"{slugify(card_summary)}.json"
                    
                    # Construct the full path to the knowledge file
                    filepath = os.path.join(knowledge_dir, filename)
                    
                    logger.info(f"Associating knowledge file: {filename} / {filepath} for proposal {proposal_id}")

                    if not os.path.exists(filepath):
                        logger.warning(f"Knowledge file not found at path: {filepath}. Attempting to create it.")
                        # Fetch the generated_sections for the card
                        card_content_result = connection.execute(
                            text("SELECT generated_sections FROM knowledge_cards WHERE id = :card_id"),
                            {"card_id": str(card_id)}
                        ).fetchone()

                        if card_content_result and card_content_result.generated_sections:
                            generated_sections = card_content_result.generated_sections
                            if isinstance(generated_sections, str):
                                generated_sections = json.loads(generated_sections)
                            
                            # This function needs the raw DB connection
                            _save_knowledge_card_content_to_file(connection, uuid.UUID(card_id), generated_sections)
                            
                            # Verify file was created
                            if os.path.exists(filepath):
                                logger.info(f"Successfully created knowledge file: {filepath}")
                                knowledge_file_paths.append(filename)
                            else:
                                logger.error(f"Failed to create knowledge file: {filepath}")
                        else:
                            logger.warning(f"No content found for knowledge card {card_id} to create file.")
                    else:
                        knowledge_file_paths.append(filename)
                        
        # The JSONKnowledgeSource expects relative paths from the `knowledge` directory
        crew_instance = ProposalCrew(knowledge_file_paths=knowledge_file_paths).generate_proposal_crew()

        # Extract special_requirements from the template
        special_requirements_obj = proposal_template.get("special_requirements", {})
        special_requirements_list = special_requirements_obj.get("instructions", [])
        # Format as a string (bulleted list)
        special_requirements_str = "\n".join([f"- {req}" for req in special_requirements_list]) if special_requirements_list else "None"

        for section_config in proposal_template["sections"]:
            section_name = section_config["section_name"]
            format_type = section_config.get("format_type", "text")
            logger.info(f"Generating section: {section_name} with format_type: {format_type} for proposal {proposal_id}")

            generated_text = ""
            if format_type == "text":
                generated_text = handle_text_format(section_config, crew_instance, form_data, project_description, session_id, proposal_id, special_requirements=special_requirements_str)
            elif format_type == "fixed_text":
                generated_text = handle_fixed_text_format(section_config)
            elif format_type == "number":
                generated_text = handle_number_format(section_config, crew_instance, form_data, project_description, special_requirements=special_requirements_str)
            elif format_type == "table":
                generated_text = handle_table_format(section_config, crew_instance, form_data, project_description, special_requirements=special_requirements_str)

            all_sections[section_name] = generated_text

             # --- PARTIAL SAVE: Update DB after each section ---
            try:
                with get_engine().begin() as connection:
                    connection.execute(
                        text("UPDATE proposals SET generated_sections = :sections, updated_at = CURRENT_TIMESTAMP WHERE id = :id"),
                        {"sections": json.dumps(all_sections), "id": proposal_id}
                    )
            except Exception as db_save_error:
                logger.error(f"Failed to save partial progress for section {section_name}: {db_save_error}")
            # ----------------------------------------------------

        with get_engine().begin() as connection:
            connection.execute(
                text("UPDATE proposals SET generated_sections = :sections, status = 'draft', updated_at = CURRENT_TIMESTAMP WHERE id = :id"),
                {"sections": json.dumps(all_sections), "id": proposal_id}
            )
        logger.info(f"Successfully generated all sections for proposal {proposal_id}")

    except Exception as e:
        logger.error(f"Error during background proposal generation for {proposal_id}: {e}", exc_info=True)
        try:
            with get_engine().begin() as connection:
                connection.execute(
                    text("UPDATE proposals SET status = 'failed', updated_at = CURRENT_TIMESTAMP WHERE id = :id"),
                    {"id": proposal_id}
                )
        except Exception as db_error:
            logger.error(f"Failed to update proposal status to 'failed' for {proposal_id}: {db_error}", exc_info=True)
    finally:
        pass

@router.post("/generate-proposal-sections/{session_id}", status_code=202)
async def generate_proposal_sections(session_id: str, background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    """
    Triggers the asynchronous generation of all proposal sections in the background.
    """
    session_data_str = redis_client.get(session_id)
    if not session_data_str:
        raise HTTPException(status_code=404, detail="Session not found.")

    session_data = json.loads(session_data_str)
    proposal_id = session_data.get("proposal_id")
    user_id = current_user["user_id"]

    if not proposal_id:
        raise HTTPException(status_code=400, detail="Proposal ID not found in session.")

    background_tasks.add_task(generate_all_sections_background, session_id, proposal_id, user_id)

    return {"message": "Proposal generation started."}


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

    session_data = json.loads(session_data_str)

    # Update session with the latest data from the request to prevent stale data issues.
    session_data["form_data"] = request.form_data
    session_data["project_description"] = request.project_description

    # Persist the updated session back to Redis.
    redis_client.setex(session_id, 3600, json.dumps(session_data, default=str))

    # Prevent editing of finalized proposals.
    with get_engine().connect() as connection:
        res = connection.execute(
            text("SELECT is_accepted FROM proposals WHERE id = :id AND user_id = :uid"),
            {"id": request.proposal_id, "uid": current_user["user_id"]}
        ).scalar()
        if res:
            raise HTTPException(status_code=403, detail="This proposal is finalized and cannot be modified.")

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

    # Extract special_requirements from the template
    special_requirements_obj = proposal_template.get("special_requirements", {})
    special_requirements_list = special_requirements_obj.get("instructions", [])
    special_requirements_str = "\n".join([f"- {req}" for req in special_requirements_list]) if special_requirements_list else "None"

    format_type = section_config.get("format_type", "text")
    logger.info(f"Generating section: {request.section} with format_type: {format_type} for proposal {request.proposal_id}")

    generated_text = ""
    if format_type == "text":
        generated_text = handle_text_format(section_config, crew_instance, form_data, project_description, session_id, request.proposal_id, special_requirements=special_requirements_str)
    elif format_type == "fixed_text":
        generated_text = handle_fixed_text_format(section_config)
    elif format_type == "number":
        generated_text = handle_number_format(section_config, crew_instance, form_data, project_description, special_requirements=special_requirements_str)
    elif format_type == "table":
        generated_text = handle_table_format(section_config, crew_instance, form_data, project_description, special_requirements=special_requirements_str)

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
                text("UPDATE proposals SET generated_sections = :sections, updated_at = CURRENT_TIMESTAMP WHERE id = :id"),
                {"sections": json.dumps(sections), "id": request.proposal_id}
            )
    except Exception as e:
        logger.exception(
            f"[DB UPDATE ERROR - process_section] Proposal {request.proposal_id}, "
            f"Session {session_id}, Section {request.section} :: {e}"
        )
        raise HTTPException(status_code=500, detail="Failed to save section to database.")

    return {"message": message, "generated_text": generated_text}


@router.post("/regenerate_section/{proposal_id}")
async def regenerate_section(proposal_id: str, request: RegenerateRequest, current_user: dict = Depends(get_current_user)):
    """
    Manually regenerates a section using concise user input.
    """
    # Prevent editing of finalized proposals.
    with get_engine().connect() as connection:
        res = connection.execute(
            text("SELECT is_accepted FROM proposals WHERE id = :id AND user_id = :uid"),
            {"id": proposal_id, "uid": current_user["user_id"]}
        ).scalar()
        if res:
            raise HTTPException(status_code=403, detail="This proposal is finalized and cannot be modified.")

    # Create a temporary session for the regeneration process
    session_id = str(uuid.uuid4())

    with get_engine().connect() as connection:
        # Get the template name from the proposal
        template_name = connection.execute(
            text("SELECT template_name FROM proposals WHERE id = :id"),
            {"id": proposal_id}
        ).scalar() or "proposal_template_unhcr.json"

    proposal_template = load_proposal_template(template_name)

    session_data = {
        "user_id": current_user["user_id"],
        "proposal_id": proposal_id,
        "form_data": request.form_data,
        "project_description": request.project_description,
        "proposal_template": proposal_template,
    }
    redis_client.setex(session_id, 3600, json.dumps(session_data, default=str))

    generated_text = regenerate_section_logic(
        session_id, request.section, request.concise_input, proposal_id
    )
    return {"message": f"Content regenerated for {request.section}", "generated_text": generated_text}


@router.post("/update-section-content")
async def update_section_content(request: UpdateSectionRequest, current_user: dict = Depends(get_current_user)):
    """
    Directly updates the content of a specific section in the database.
    This is used for saving manually edited content without invoking the AI.
    """
    user_id = current_user["user_id"]
    try:
        with get_engine().begin() as conn:
            # First, verify the proposal belongs to the user and is not finalized.
            proposal_check = conn.execute(
                text("SELECT is_accepted FROM proposals WHERE id = :id AND user_id = :uid"),
                {"id": request.proposal_id, "uid": user_id}
            ).scalar()

            if proposal_check is None:
                raise HTTPException(status_code=404, detail="Proposal not found.")
            if proposal_check:
                raise HTTPException(status_code=403, detail="Cannot modify a finalized proposal.")

            # Use jsonb_set to update the specific key in the generated_sections JSON object.
            # The path '{request.section}' targets the key to be updated.
            # The third parameter is the new value, wrapped in to_jsonb to ensure it's a valid JSON value.
            conn.execute(
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
                    "section": request.section,
                    "content": request.content,
                    "id": request.proposal_id
                }
            )
        return {"message": f"Section '{request.section}' updated successfully."}
    except SQLAlchemyError as db_error:
        logger.error(f"[UPDATE SECTION DB ERROR] {db_error}", exc_info=True)
        raise HTTPException(status_code=500, detail="A database error occurred while updating the section.")
    except Exception as e:
        logger.error(f"[UPDATE SECTION ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while updating the section.")


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
                            template_name = :template_name, updated_at = CURRENT_TIMESTAMP
                        WHERE id = :id
                    """),
                    {
                        "form": json.dumps(request.form_data),
                        "desc": request.project_description,
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
                        INSERT INTO proposals (id, user_id, created_by, updated_by, form_data, project_description, generated_sections, template_name)
                        VALUES (:id, :uid, :uid, :uid, :form, :desc, :sections, :template_name)
                    """),
                    {
                        "id": proposal_id,
                        "uid": user_id,
                        "form": json.dumps(request.form_data),
                        "desc": request.project_description,
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


@router.get("/proposals/reviews")
async def get_proposals_for_review(current_user: dict = Depends(get_current_user)):
    """
    Lists all proposals assigned to the current user for review, both pending and completed.
    """
    user_id = current_user["user_id"]
    if "project reviewer" not in current_user.get("roles", []):
        return {"message": "User is not a project reviewer.", "reviews": []}

    try:
        with get_engine().connect() as connection:
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
            rows = result.mappings().fetchall()
            review_list = []

            for row in rows:
                form_data = json.loads(row['form_data']) if isinstance(row['form_data'], str) else row['form_data']

                review_status = "pending"
                if row['is_completed']:
                    review_status = "completed"
                elif row['is_draft']:
                    review_status = "draft"

                review_list.append({
                    "proposal_id": row['id'],
                    "project_title": form_data.get("Project Draft Short name") or form_data.get("Project title", "Untitled Proposal"),
                    "summary": row['project_description'] or "",
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                    "updated_at": row['updated_at'].isoformat() if row['updated_at'] else None,
                    "is_accepted": row['is_accepted'],
                    "status": row['status'],
                    "requester_name": row['requester_name'],
                    "deadline": row['deadline'].isoformat() if row['deadline'] else None,
                    "is_sample": False,
                    "donor": row['donor_name'],
                    "country": row['country_name'],
                    "outcomes": row['outcome_names'].split(', ') if row['outcome_names'] else [],
                    "budget": form_data.get("Budget Range", "N/A"),
                    "review_status": review_status,
                    "review_completed_at": row['review_completed_at'].isoformat() if row['review_completed_at'] else None
                })
        return {"message": "Proposals for review fetched successfully.", "reviews": review_list}
    except Exception as e:
        logger.error(f"[GET PROPOSALS FOR REVIEW ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch proposals for review.")


@router.get("/list-drafts")
async def list_drafts(current_user: dict = Depends(get_current_user)):
    """
    Lists all drafts for the current user, including sample templates.
    """
    if "proposal writer" not in current_user.get("roles", []):
        return {"message": "User is not a proposal writer.", "drafts": []}

    logger.info(f"Attempting to list drafts for user: {current_user['user_id']}")
    user_id = current_user["user_id"]
    draft_list = []

    # Fetch user's drafts from the database.
    try:  # Fixed: This was indented incorrectly (had extra spaces)
        logger.info("Attempting database connection...")
        engine = get_engine()
        logger.info(f"Engine type: {type(engine)}")
        
        with engine.connect() as connection:
            logger.info("Database connection established")

            # This query now joins with related tables to fetch names instead of relying on form_data
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
            rows = result.mappings().fetchall() # Use .mappings() to get dict-like rows
            logger.info(f"Found {len(rows)} drafts in database")
            
            for row in rows:
                form_data = json.loads(row['form_data']) if isinstance(row['form_data'], str) else row['form_data']
                
                draft_list.append({
                    "proposal_id": row['id'],
                    "project_title": form_data.get("Project Draft Short name") or form_data.get("Project title", "Untitled Proposal"),
                    "summary": row['project_description'] or "",
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                    "updated_at": row['updated_at'].isoformat() if row['updated_at'] else None,
                    "is_accepted": row['is_accepted'],
                    "status": row['status'],
                    "is_sample": False,
                    # New relational fields
                    "donor": row['donor_name'],
                    "country": row['country_name'],
                    "outcomes": row['outcome_names'].split(', ') if row['outcome_names'] else [],
                    "budget": form_data.get("Budget Range", "N/A")
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
        sections = [section.get("section_name") for section in default_template.get("sections", [])]
        return {"sections": sections}
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
                               is_accepted, created_at, updated_at, status, contribution_id
                        FROM proposals
                        WHERE id = :id AND user_id = :uid
                    """),
                    {"id": proposal_id, "uid": user_id}
                ).fetchone()
                if not draft:
                    raise HTTPException(status_code=404, detail="Draft not found.")

                # This query finds all knowledge cards linked to the same donor, outcomes, or field context as the proposal.
                associated_cards_result = conn.execute(
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

                associated_knowledge_cards = [dict(card) for card in associated_cards_result]

                template_name = draft.template_name or "unhcr_proposal_template.json" # Default if null
                proposal_template = load_proposal_template(template_name)
                section_names = [s.get("section_name") for s in proposal_template.get("sections", [])]

                form_data = draft.form_data if draft.form_data else {}
                sections = draft.generated_sections if draft.generated_sections else {}
                project_description = draft.project_description
                
                data_to_load = {
                    "form_data": form_data,
                    "project_description": project_description,
                    "generated_sections": {sec: sections.get(sec) for sec in section_names},
                    "is_accepted": draft.is_accepted,
                    "status": draft.status,
                    "created_at": draft.created_at.isoformat() if draft.created_at else None,
                    "updated_at": draft.updated_at.isoformat() if draft.updated_at else None,
                    "is_sample": False,
                    "template_name": template_name,
                    "proposal_template": proposal_template,
                    "proposal_id": str(proposal_id),
                    "associated_knowledge_cards": associated_knowledge_cards,
                    "contribution_id": draft.contribution_id
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

@router.post("/proposals/{proposal_id}/submit")
async def submit_proposal(proposal_id: uuid.UUID, current_user: dict = Depends(get_current_user)):
    """
    Submits a proposal.
    """
    user_id = current_user["user_id"]
    try:
        with get_engine().begin() as connection:
            # Get the current sections to create a snapshot
            sections = connection.execute(
                text("SELECT generated_sections FROM proposals WHERE id = :id"),
                {"id": proposal_id}
            ).scalar() or {}

            connection.execute(
                text("UPDATE proposals SET status = 'submitted', updated_at = CURRENT_TIMESTAMP WHERE id = :id AND user_id = :uid"),
                {"id": proposal_id, "uid": user_id}
            )
            # Log the status change
            connection.execute(
                text("INSERT INTO proposal_status_history (proposal_id, status, generated_sections_snapshot) VALUES (:pid, 'submitted', :snapshot)"),
                {"pid": proposal_id, "snapshot": json.dumps(sections)}
            )
        return {"message": "Proposal submitted."}
    except Exception as e:
        logger.error(f"[SUBMIT PROPOSAL ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to submit proposal.")


@router.post("/proposals/{proposal_id}/save-contribution-id")
async def save_contribution_id(proposal_id: uuid.UUID, request: SaveContributionIdRequest, current_user: dict = Depends(get_current_user)):
    """
    Saves the contribution ID for a submitted proposal.
    """
    user_id = current_user["user_id"]
    try:
        with get_engine().begin() as connection:
            # Verify the user owns the proposal and it is in 'submitted' state
            proposal_status = connection.execute(
                text("SELECT status FROM proposals WHERE id = :id AND user_id = :uid"),
                {"id": proposal_id, "uid": user_id}
            ).scalar()

            if not proposal_status:
                raise HTTPException(status_code=404, detail="Proposal not found.")

            if proposal_status != 'submitted':
                raise HTTPException(status_code=403, detail="Contribution ID can only be added to submitted proposals.")

            connection.execute(
                text("UPDATE proposals SET contribution_id = :contribution_id, updated_at = CURRENT_TIMESTAMP WHERE id = :id"),
                {"contribution_id": request.contribution_id, "id": proposal_id}
            )
        return {"message": "Contribution ID saved successfully."}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"[SAVE CONTRIBUTION ID ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save contribution ID.")


@router.post("/proposals/{proposal_id}/upload-submitted-pdf")
async def upload_submitted_pdf(proposal_id: uuid.UUID, file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """
    Uploads a PDF for a submitted proposal, parses its content, and updates the proposal sections.
    """
    user_id = current_user["user_id"]

    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDFs are allowed.")

    try:
        with get_engine().begin() as connection:
            # Verify the user owns the proposal
            owner_id = connection.execute(
                text("SELECT user_id FROM proposals WHERE id = :id"),
                {"id": proposal_id}
            ).scalar()

            if not owner_id or owner_id != user_id:
                raise HTTPException(status_code=403, detail="You do not have permission to modify this proposal.")

            # Get the proposal template to know which sections to look for
            template_name = connection.execute(
                text("SELECT template_name FROM proposals WHERE id = :id"),
                {"id": proposal_id}
            ).scalar() or "unhcr_proposal_template.json"

            proposal_template = load_proposal_template(template_name)
            section_titles = [section['section_name'] for section in proposal_template.get('sections', [])]

            # Read the PDF content
            pdf_content = await file.read()

            # Use a temporary file to work with pdfplumber
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
                temp_pdf.write(pdf_content)
                temp_pdf_path = temp_pdf.name

            # Process the PDF with pdfplumber
            extracted_sections = {}
            with pdfplumber.open(temp_pdf_path) as pdf:
                full_text = ""
                for page in pdf.pages:
                    full_text += page.extract_text() + "\n"

            # This is a simple parsing strategy: find a section title and capture text until the next title
            for i, title in enumerate(section_titles):
                start_index = full_text.find(title)
                if start_index != -1:
                    next_title_index = -1
                    # Find the start of the next section
                    if i + 1 < len(section_titles):
                        next_title = section_titles[i+1]
                        next_title_index = full_text.find(next_title, start_index)

                    content_start = start_index + len(title)
                    if next_title_index != -1:
                        extracted_sections[title] = full_text[content_start:next_title_index].strip()
                    else:
                        extracted_sections[title] = full_text[content_start:].strip()

            # Clean up the temporary file
            os.unlink(temp_pdf_path)

            if not extracted_sections:
                raise HTTPException(status_code=400, detail="Could not extract any matching sections from the PDF.")

            # Update the proposal in the database
            connection.execute(
                text("""
                    UPDATE proposals
                    SET generated_sections = :sections, status = 'submitted', updated_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                """),
                {"sections": json.dumps(extracted_sections), "id": proposal_id}
            )

            # Log the status change
            connection.execute(
                text("INSERT INTO proposal_status_history (proposal_id, status, generated_sections_snapshot) VALUES (:pid, 'submitted', :snapshot)"),
                {"pid": proposal_id, "snapshot": json.dumps(extracted_sections)}
            )

        return {"message": "PDF processed and proposal updated successfully.", "extracted_sections": extracted_sections}

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"[PDF UPLOAD ERROR] {e}", exc_info=True)
        # Clean up temp file in case of error
        if 'temp_pdf_path' in locals() and os.path.exists(temp_pdf_path):
            os.unlink(temp_pdf_path)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


@router.post("/proposals/{proposal_id}/save-draft-review")
async def save_draft_review(proposal_id: uuid.UUID, request: SubmitReviewRequest, current_user: dict = Depends(get_current_user)):
    """
    Saves a draft of a peer review for a proposal.
    """
    user_id = current_user["user_id"]
    try:
        with get_engine().begin() as connection:
            # Check if the user is assigned to review this proposal
            reviewer_id_from_db = connection.execute(
                text("SELECT reviewer_id FROM proposal_peer_reviews WHERE proposal_id = :proposal_id AND reviewer_id = :user_id AND (status = 'pending' OR status = 'draft')"),
                {"proposal_id": proposal_id, "user_id": user_id}
            ).scalar()

            if not reviewer_id_from_db:
                raise HTTPException(status_code=403, detail="You are not assigned to review this proposal or the review is already completed.")

            # Get the latest 'in_review' status history ID
            history_id = connection.execute(
                text("SELECT id FROM proposal_status_history WHERE proposal_id = :pid AND status = 'in_review' ORDER BY created_at DESC LIMIT 1"),
                {"pid": proposal_id}
            ).scalar()

            # Delete existing draft comments for this user and proposal
            connection.execute(
                text("DELETE FROM proposal_peer_reviews WHERE proposal_id = :proposal_id AND reviewer_id = :user_id AND status = 'draft'"),
                {"proposal_id": proposal_id, "user_id": user_id}
            )

            # Insert each comment as a new row with 'draft' status
            for comment in request.comments:
                if comment.review_text: # Only save comments that have text
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

        return {"message": "Draft review saved successfully."}
    except Exception as e:
        logger.error(f"[SAVE DRAFT REVIEW ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save draft review.")


@router.post("/proposals/{proposal_id}/review")
async def submit_review(proposal_id: uuid.UUID, request: SubmitReviewRequest, current_user: dict = Depends(get_current_user)):
    """
    Submits a peer review for a proposal, with comments for each section.
    """
    user_id = current_user["user_id"]
    try:
        with get_engine().begin() as connection:
            # Check if the user is assigned to review this proposal
            reviewer_id_from_db = connection.execute(
                text("SELECT reviewer_id FROM proposal_peer_reviews WHERE proposal_id = :proposal_id AND reviewer_id = :user_id AND (status = 'pending' OR status = 'draft')"),
                {"proposal_id": proposal_id, "user_id": user_id}
            ).scalar()

            if not reviewer_id_from_db:
                raise HTTPException(status_code=403, detail="You are not assigned to review this proposal or the review is already completed.")

            # Get the latest 'in_review' status history ID
            history_id = connection.execute(
                text("SELECT id FROM proposal_status_history WHERE proposal_id = :pid AND status = 'in_review' ORDER BY created_at DESC LIMIT 1"),
                {"pid": proposal_id}
            ).scalar()

            # Delete existing draft/pending comments for this user and proposal
            connection.execute(
                text("DELETE FROM proposal_peer_reviews WHERE proposal_id = :proposal_id AND reviewer_id = :user_id AND (status = 'pending' OR status = 'draft')"),
                {"proposal_id": proposal_id, "user_id": user_id}
            )

            # Insert each comment as a new row
            for comment in request.comments:
                if comment.review_text: # Only save comments that have text
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

            # Check if all reviews are completed
            pending_reviews = connection.execute(
                text("SELECT COUNT(*) FROM proposal_peer_reviews WHERE proposal_id = :proposal_id AND status = 'pending'"),
                {"proposal_id": proposal_id}
            ).scalar()

            if pending_reviews == 0:
                connection.execute(
                    text("UPDATE proposals SET status = 'pre_submission', updated_at = CURRENT_TIMESTAMP WHERE id = :id"),
                    {"id": proposal_id}
                )

        return {"message": "Review submitted successfully."}
    except Exception as e:
        logger.error(f"[SUBMIT REVIEW ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to submit review.")


@router.post("/proposals/{proposal_id}/submit-for-review")
async def submit_for_review(proposal_id: uuid.UUID, request: SubmitPeerReviewRequest, current_user: dict = Depends(get_current_user)):
    """
    Submits a proposal for peer review.
    """
    user_id = current_user["user_id"]
    try:
        with get_engine().begin() as connection:
            # Check if the proposal exists and belongs to the user
            proposal = connection.execute(
                text("SELECT id FROM proposals WHERE id = :id AND user_id = :uid"),
                {"id": proposal_id, "uid": user_id}
            ).fetchone()
            if not proposal:
                raise HTTPException(status_code=404, detail="Proposal not found.")

            # Get the current sections to create a snapshot
            sections = connection.execute(
                text("SELECT generated_sections FROM proposals WHERE id = :id"),
                {"id": proposal_id}
            ).scalar() or {}

            # Update the proposal status
            connection.execute(
                text("UPDATE proposals SET status = 'in_review', updated_at = CURRENT_TIMESTAMP WHERE id = :id"),
                {"id": proposal_id}
            )

            # Log the status change with the snapshot
            connection.execute(
                text("INSERT INTO proposal_status_history (proposal_id, status, generated_sections_snapshot) VALUES (:pid, 'in_review', :snapshot)"),
                {"pid": proposal_id, "snapshot": json.dumps(sections)}
            )

            # Add the peer reviewers
            for reviewer_info in request.reviewers:
                # Check if a pending review already exists for this reviewer and proposal
                pending_review = connection.execute(
                    text("""
                        SELECT id FROM proposal_peer_reviews
                        WHERE proposal_id = :proposal_id AND reviewer_id = :reviewer_id AND status = 'pending'
                    """),
                    {"proposal_id": proposal_id, "reviewer_id": reviewer_info.user_id}
                ).fetchone()

                if pending_review:
                    # If a pending review exists, update its deadline
                    connection.execute(
                        text("""
                            UPDATE proposal_peer_reviews
                            SET deadline = :deadline, updated_at = CURRENT_TIMESTAMP
                            WHERE id = :id
                        """),
                        {"deadline": reviewer_info.deadline, "id": pending_review.id}
                    )
                else:
                    # Otherwise, insert a new pending review
                    connection.execute(
                        text("""
                            INSERT INTO proposal_peer_reviews (proposal_id, reviewer_id, deadline, status)
                            VALUES (:proposal_id, :reviewer_id, :deadline, 'pending')
                        """),
                        {"proposal_id": proposal_id, "reviewer_id": reviewer_info.user_id, "deadline": reviewer_info.deadline}
                    )

        return {"message": "Proposal submitted for peer review."}
    except Exception as e:
        logger.error(f"[SUBMIT FOR REVIEW ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to submit for review.")


@router.put("/proposals/{proposal_id}/status")
async def update_proposal_status(proposal_id: uuid.UUID, request: UpdateProposalStatusRequest, current_user: dict = Depends(get_current_user)):
    """
    Updates the status of a proposal.
    """
    user_id = current_user["user_id"]
    new_status = request.status
    # Add validation for allowed statuses if needed
    allowed_statuses = ['draft', 'in_review', 'pre_submission', 'submitted']
    if new_status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="Invalid status value.")

    try:
        with get_engine().begin() as connection:
            # Check if the proposal exists and belongs to the user
            proposal = connection.execute(
                text("SELECT status FROM proposals WHERE id = :id AND user_id = :uid"),
                {"id": proposal_id, "uid": user_id}
            ).fetchone()
            if not proposal:
                raise HTTPException(status_code=404, detail="Proposal not found.")

            # Add logic here to restrict status transitions, e.g., cannot revert from "approved"
            if proposal.status == 'approved':
                raise HTTPException(status_code=403, detail="Cannot change status of an approved proposal.")

            # Get the current sections to create a snapshot
            sections = connection.execute(
                text("SELECT generated_sections FROM proposals WHERE id = :id"),
                {"id": proposal_id}
            ).scalar() or {}

            # Update the proposal status
            connection.execute(
                text("UPDATE proposals SET status = :status, updated_at = CURRENT_TIMESTAMP WHERE id = :id"),
                {"status": new_status, "id": proposal_id}
            )

            # Log the status change
            connection.execute(
                text("INSERT INTO proposal_status_history (proposal_id, status, generated_sections_snapshot) VALUES (:pid, :status, :snapshot)"),
                {"pid": proposal_id, "status": new_status, "snapshot": json.dumps(sections)}
            )

        return {"message": f"Proposal status updated to {new_status}."}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"[UPDATE STATUS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update proposal status.")


@router.get("/proposals/{proposal_id}/status")
async def get_proposal_status(proposal_id: uuid.UUID, current_user: dict = Depends(get_current_user)):
    """
    Gets the current status and generated sections of a proposal.
    """
    user_id = current_user["user_id"]
    try:
        with get_engine().connect() as connection:
            result = connection.execute(
                text("SELECT status, generated_sections, template_name FROM proposals WHERE id = :id AND user_id = :uid"),
                {"id": proposal_id, "uid": user_id}
            ).fetchone()

            if not result:
                raise HTTPException(status_code=404, detail="Proposal not found.")

            status, generated_sections, template_name = result
            
            # Robust JSON parsing for generated_sections
            if isinstance(generated_sections, str):
                try:
                    generated_sections = json.loads(generated_sections)
                except Exception:
                    logger.error(f"Failed to parse generated_sections JSON for {proposal_id}")
                    generated_sections = {}

            # Count expected sections for progress tracking
            expected_sections = 0
            if template_name:
                try:
                    template_data = load_proposal_template(template_name)
                    expected_sections = len(template_data.get("sections", []))
                except Exception as e:
                    logger.warning(f"Failed to load template {template_name} for section count: {e}")

            return {
                "status": status, 
                "generated_sections": generated_sections or {},
                "expected_sections": expected_sections
            }

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"[GET PROPOSAL STATUS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get proposal status.")


@router.get("/review-proposal/{proposal_id}")
async def get_proposal_for_review(proposal_id: uuid.UUID, current_user: dict = Depends(get_current_user)):
    """
    Fetches a proposal for a user assigned to review it, allowing access to both pending and completed reviews.
    """
    user_id = current_user["user_id"]
    try:
        with get_engine().connect() as connection:
            # Check if the user is assigned to review this proposal, regardless of status
            review_assignment = connection.execute(
                text("SELECT status FROM proposal_peer_reviews WHERE proposal_id = :proposal_id AND reviewer_id = :user_id ORDER BY created_at DESC LIMIT 1"),
                {"proposal_id": proposal_id, "user_id": user_id}
            ).fetchone()

            if not review_assignment:
                raise HTTPException(status_code=403, detail="You are not assigned to review this proposal.")

            review_status = review_assignment.status

            # Fetch the proposal data
            draft = connection.execute(
                text("""
                    SELECT template_name, form_data, generated_sections, project_description,
                           is_accepted, created_at, updated_at, status
                    FROM proposals
                    WHERE id = :id
                """),
                {"id": proposal_id}
            ).fetchone()

            if not draft:
                raise HTTPException(status_code=404, detail="Proposal not found.")

            draft_comments = {}
            if review_status == 'draft':
                comments_result = connection.execute(
                    text("SELECT section_name, review_text, type_of_comment, severity FROM proposal_peer_reviews WHERE proposal_id = :proposal_id AND reviewer_id = :user_id AND status = 'draft'"),
                    {"proposal_id": proposal_id, "user_id": user_id}
                ).mappings().fetchall()
                for comment in comments_result:
                    draft_comments[comment['section_name']] = {
                        "review_text": comment['review_text'],
                        "type_of_comment": comment['type_of_comment'],
                        "severity": comment['severity']
                    }

            template_name = draft.template_name or "unhcr_proposal_template.json"
            proposal_template = load_proposal_template(template_name)
            section_names = [s.get("section_name") for s in proposal_template.get("sections", [])]

            form_data = draft.form_data if draft.form_data else {}
            sections = draft.generated_sections if draft.generated_sections else {}

            data_to_load = {
                "form_data": form_data,
                "project_description": draft.project_description,
                "generated_sections": {sec: sections.get(sec) for sec in section_names},
                "is_accepted": draft.is_accepted,
                "status": draft.status,
                "created_at": draft.created_at.isoformat() if draft.created_at else None,
                "updated_at": draft.updated_at.isoformat() if draft.updated_at else None,
                "review_status": review_status,
                "draft_comments": draft_comments
            }
        return data_to_load
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"[GET PROPOSAL FOR REVIEW ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch proposal for review.")


@router.get("/donors")
async def get_donors():
    """
    Fetches all donors from the database.
    """
    try:
        with get_engine().connect() as connection:
            result = connection.execute(text("SELECT id, name FROM donors ORDER BY id"))
            donors = [{"id": str(row[0]), "name": row[1]} for row in result.fetchall()]
        return {"donors": donors}
    except Exception as e:
        logger.error(f"[GET DONORS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch donors.")


@router.get("/outcomes")
async def get_outcomes():
    """
    Fetches all outcomes from the database.
    """
    try:
        with get_engine().connect() as connection:
            result = connection.execute(text("SELECT id, name FROM outcomes ORDER BY id"))
            outcomes = [{"id": str(row[0]), "name": row[1]} for row in result.fetchall()]
        return {"outcomes": outcomes}
    except Exception as e:
        logger.error(f"[GET OUTCOMES ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch outcomes.")


@router.get("/field-contexts")
async def get_field_contexts(geographic_coverage: Optional[str] = None):
    """
    Fetches field contexts from the database, optionally filtered by geographic coverage.
    """
    try:
        with get_engine().connect() as connection:
            if geographic_coverage:
                query = text("SELECT id, name, geographic_coverage FROM field_contexts WHERE geographic_coverage = :geo ORDER BY id")
                result = connection.execute(query, {"geo": geographic_coverage})
            else:
                query = text("SELECT id, name, geographic_coverage FROM field_contexts ORDER BY id")
                result = connection.execute(query)

            field_contexts = [{"id": str(row[0]), "name": row[1], "geographic_coverage": row[2]} for row in result.fetchall()]
        return {"field_contexts": field_contexts}
    except Exception as e:
        logger.error(f"[GET FIELD CONTEXTS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch field contexts.")


@router.post("/donors", status_code=201)
async def create_donor(request: CreateDonorRequest, current_user: dict = Depends(get_current_user)):
    """
    Creates a new donor.
    """
    new_id = uuid.uuid4()
    try:
        with get_engine().begin() as connection:
            connection.execute(
                text("INSERT INTO donors (id, name, created_by) VALUES (:id, :name, :user_id)"),
                {"id": new_id, "name": request.name, "user_id": current_user["user_id"]}
            )
        return {"id": str(new_id), "name": request.name}
    except Exception as e:
        logger.error(f"[CREATE DONOR ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create donor.")

@router.post("/outcomes", status_code=201)
async def create_outcome(request: CreateOutcomeRequest, current_user: dict = Depends(get_current_user)):
    """
    Creates a new outcome.
    """
    new_id = uuid.uuid4()
    try:
        with get_engine().begin() as connection:
            connection.execute(
                text("INSERT INTO outcomes (id, name, created_by) VALUES (:id, :name, :user_id)"),
                {"id": new_id, "name": request.name, "user_id": current_user["user_id"]}
            )
        return {"id": str(new_id), "name": request.name}
    except Exception as e:
        logger.error(f"[CREATE OUTCOME ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create outcome.")

@router.post("/field-contexts", status_code=201)
async def create_field_context(request: CreateFieldContextRequest, current_user: dict = Depends(get_current_user)):
    """
    Creates a new field context.
    """
    new_id = uuid.uuid4()
    try:
        with get_engine().begin() as connection:
            connection.execute(
                text("INSERT INTO field_contexts (id, title, name, category, geographic_coverage, created_by) VALUES (:id, :title, :name, :category, :geo, :user_id)"),
                {
                    "id": new_id,
                    "title": request.name,
                    "name": request.name,
                    "category": request.category,
                    "geo": request.geographic_coverage,
                    "user_id": current_user["user_id"]
                }
            )
        return {"id": str(new_id), "name": request.name, "geographic_coverage": request.geographic_coverage}
    except Exception as e:
        logger.error(f"[CREATE FIELD CONTEXT ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create field context.")


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


@router.put("/proposals/{proposal_id}/delete")
async def delete_proposal(proposal_id: uuid.UUID, current_user: dict = Depends(get_current_user)):
    """
    Marks a proposal as 'deleted' but does not remove it from the database.
    """
    user_id = current_user["user_id"]
    try:
        with get_engine().begin() as connection:
            result = connection.execute(
                text("UPDATE proposals SET status = 'deleted', updated_at = CURRENT_TIMESTAMP WHERE id = :id AND user_id = :uid RETURNING id"),
                {"id": proposal_id, "uid": user_id}
            )
            if not result.fetchone():
                raise HTTPException(status_code=404, detail="Proposal not found.")
        return {"message": f"Proposal '{proposal_id}' marked as deleted."}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"[DELETE PROPOSAL ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to mark proposal as deleted.")


@router.put("/proposals/{proposal_id}/transfer")
async def transfer_ownership(proposal_id: uuid.UUID, request: TransferOwnershipRequest, current_user: dict = Depends(get_current_user)):
    """
    Transfers ownership of a proposal to another user.
    """
    user_id = current_user["user_id"]
    new_owner_id = request.new_owner_id

    try:
        with get_engine().begin() as connection:
            # First, check if the new owner exists
            new_owner_exists = connection.execute(
                text("SELECT id FROM users WHERE id = :id"),
                {"id": new_owner_id}
            ).scalar()

            if not new_owner_exists:
                raise HTTPException(status_code=404, detail="New owner not found.")

            # Then, update the proposal's user_id
            result = connection.execute(
                text("UPDATE proposals SET user_id = :new_owner_id, updated_at = CURRENT_TIMESTAMP WHERE id = :id AND user_id = :uid RETURNING id"),
                {"new_owner_id": new_owner_id, "id": proposal_id, "uid": user_id}
            )

            if not result.fetchone():
                raise HTTPException(status_code=404, detail="Proposal not found or you don't have permission to transfer it.")

        return {"message": f"Proposal '{proposal_id}' transferred to user '{new_owner_id}'."}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"[TRANSFER OWNERSHIP ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to transfer ownership.")


@router.put("/proposals/{proposal_id}/revert-to-status/{status}")
async def revert_to_status(proposal_id: uuid.UUID, status: str, current_user: dict = Depends(get_current_user)):
    """
    Reverts a proposal to a previous status and its corresponding content.
    """
    user_id = current_user["user_id"]
    try:
        with get_engine().begin() as connection:
            # Find the most recent snapshot for the given status
            history_entry = connection.execute(
                text("""
                    SELECT generated_sections_snapshot
                    FROM proposal_status_history
                    WHERE proposal_id = :pid AND status = :status
                    ORDER BY created_at DESC
                    LIMIT 1
                """),
                {"pid": proposal_id, "status": status}
            ).fetchone()

            if not history_entry:
                raise HTTPException(status_code=404, detail=f"No history found for status '{status}'.")

            snapshot = history_entry[0]

            # Update the proposal with the snapshot
            connection.execute(
                text("""
                    UPDATE proposals
                    SET status = :status, generated_sections = :snapshot, updated_at = CURRENT_TIMESTAMP
                    WHERE id = :id AND user_id = :uid
                """),
                {"status": status, "snapshot": json.dumps(snapshot), "id": proposal_id, "uid": user_id}
            )

        return {"message": f"Proposal reverted to '{status}'."}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"[REVERT STATUS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to revert proposal status.")


@router.get("/proposals/{proposal_id}/status-history")
async def get_status_history(proposal_id: uuid.UUID, current_user: dict = Depends(get_current_user)):
    """
    Gets the list of available statuses for a proposal from its history.
    """
    user_id = current_user["user_id"]
    try:
        with get_engine().connect() as connection:
            # Verify the user has access to the proposal (owner or reviewer)
            proposal_owner = connection.execute(
                text("SELECT user_id FROM proposals WHERE id = :id"),
                {"id": proposal_id}
            ).scalar()

            is_reviewer = connection.execute(
                text("SELECT 1 FROM proposal_peer_reviews WHERE proposal_id = :pid AND reviewer_id = :rid"),
                {"pid": proposal_id, "rid": user_id}
            ).scalar()

            if not proposal_owner:
                raise HTTPException(status_code=404, detail="Proposal not found.")

            if proposal_owner != user_id and not is_reviewer:
                raise HTTPException(status_code=403, detail="You do not have permission to view this proposal's history.")

            # Get distinct statuses from the history
            result = connection.execute(
                text("""
                    SELECT DISTINCT status
                    FROM proposal_status_history
                    WHERE proposal_id = :pid
                """),
                {"pid": proposal_id}
            )
            statuses = [row[0] for row in result.fetchall()]
            return {"statuses": statuses}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"[GET STATUS HISTORY ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get status history.")


@router.get("/proposals/{proposal_id}/peer-reviews")
async def get_peer_reviews(proposal_id: uuid.UUID, current_user: dict = Depends(get_current_user)):
    """
    Fetches all peer reviews for a given proposal.
    """
    user_id = current_user["user_id"]
    try:
        with get_engine().connect() as connection:
            # Verify the user has access to the proposal (owner, reviewer, or admin)
            proposal_owner = connection.execute(
                text("SELECT user_id FROM proposals WHERE id = :id"),
                {"id": proposal_id}
            ).scalar()

            is_reviewer = connection.execute(
                text("SELECT 1 FROM proposal_peer_reviews WHERE proposal_id = :pid AND reviewer_id = :rid"),
                {"pid": proposal_id, "rid": user_id}
            ).scalar()

            if not proposal_owner:
                raise HTTPException(status_code=404, detail="Proposal not found.")

            if str(proposal_owner) != user_id and not is_reviewer:
                raise HTTPException(status_code=403, detail="You do not have permission to view this proposal's reviews.")

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
            reviews = [
                {
                    "id": row.id,
                    "section_name": row.section_name,
                    "review_text": row.review_text,
                    "author_response": row.author_response,
                    "reviewer_name": row.reviewer_name
                }
                for row in result.mappings()
            ]
            return {"reviews": reviews}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"[GET PEER REVIEWS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch peer reviews.")


@router.put("/peer-reviews/{review_id}/response")
async def save_author_response(review_id: uuid.UUID, request: AuthorResponseRequest, current_user: dict = Depends(get_current_user)):
    """
    Saves the author's response to a peer review.
    """
    user_id = current_user["user_id"]
    try:
        with get_engine().begin() as connection:
            # Verify that the user is the author of the proposal
            proposal_id = connection.execute(
                text("SELECT proposal_id FROM proposal_peer_reviews WHERE id = :rid"),
                {"rid": review_id}
            ).scalar()

            if not proposal_id:
                raise HTTPException(status_code=404, detail="Review not found.")

            proposal_owner = connection.execute(
                text("SELECT user_id FROM proposals WHERE id = :pid"),
                {"pid": proposal_id}
            ).scalar()

            if not proposal_owner or proposal_owner != user_id:
                raise HTTPException(status_code=403, detail="You do not have permission to respond to this review.")

            # Update the author_response
            connection.execute(
                text("UPDATE proposal_peer_reviews SET author_response = :response, updated_at = CURRENT_TIMESTAMP WHERE id = :rid"),
                {"response": request.author_response, "rid": review_id}
            )

        return {"message": "Response saved successfully."}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"[SAVE AUTHOR RESPONSE ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save author response.")
