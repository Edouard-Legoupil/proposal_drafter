#  Standard Library
import json
import re
import uuid
from datetime import datetime 
import logging
from typing import Optional

#  Third-Party Libraries
from fastapi import APIRouter, Depends, HTTPException, Body, UploadFile, File
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError 

#  Internal Modules
from backend.core.db import get_engine
from backend.core.redis import redis_client
from backend.core.security import get_current_user
from backend.core.config import get_available_templates, load_proposal_template
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
    AuthorResponseRequest
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
        template_name = "unhcr_proposal_template.json"  # Default template

        with get_engine().begin() as connection:
            if donor_id:
                # Get donor name from ID to determine the template
                donor_name_result = connection.execute(
                    text("SELECT name FROM donors WHERE id = :id"),
                    {"id": donor_id}
                ).scalar()
                if donor_name_result:
                    template_name = templates_map.get(donor_name_result, "unhcr_proposal_template.json")

            # Create the main proposal record
            connection.execute(
                text("""
                    INSERT INTO proposals (id, user_id, form_data, project_description, template_name, generated_sections)
                    VALUES (:id, :uid, :form, :desc, :template, '{}')
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

    # Load session data and update it with fresh data from the request.
    session_data_str = redis_client.get(session_id)
    if not session_data_str:
        raise HTTPException(status_code=400, detail="Session data not found for regeneration.")

    session_data = json.loads(session_data_str)
    session_data["form_data"] = request.form_data
    session_data["project_description"] = request.project_description
    redis_client.setex(session_id, 3600, json.dumps(session_data, default=str))

    generated_text = regenerate_section_logic(
        session_id, request.section, request.concise_input, request.proposal_id
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
                    updated_at = NOW()
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


@router.get("/proposals/reviews")
async def get_proposals_for_review(current_user: dict = Depends(get_current_user)):
    """
    Lists all proposals assigned to the current user for review.
    """
    user_id = current_user["user_id"]
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
                    pp.deadline,
                    d.name AS donor_name,
                    fc.name AS country_name,
                    string_agg(o.name, ', ') AS outcome_names,
                    u.name AS requester_name
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
                    pp.reviewer_id = :uid AND pp.status = 'pending'
                GROUP BY
                    p.id, pp.deadline, d.name, fc.name, u.name, p.form_data, p.project_description, p.status, p.created_at, p.updated_at, p.is_accepted
                ORDER BY
                    p.updated_at DESC
            """)

            result = connection.execute(query, {"uid": user_id})
            rows = result.mappings().fetchall()
            review_list = []

            for row in rows:
                form_data = json.loads(row['form_data']) if isinstance(row['form_data'], str) else row['form_data']

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
                    "budget": form_data.get("Budget Range", "N/A")
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
                               is_accepted, created_at, updated_at, status
                        FROM proposals
                        WHERE id = :id AND user_id = :uid
                    """),
                    {"id": proposal_id, "uid": user_id}
                ).fetchone()
                if not draft:
                    raise HTTPException(status_code=404, detail="Draft not found.")

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

@router.post("/proposals/{proposal_id}/request-submission")
async def request_submission(proposal_id: uuid.UUID, current_user: dict = Depends(get_current_user)):
    """
    Requests submission of a proposal.
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
                text("UPDATE proposals SET status = 'submission', updated_at = NOW() WHERE id = :id AND user_id = :uid"),
                {"id": proposal_id, "uid": user_id}
            )
            # Log the status change
            connection.execute(
                text("INSERT INTO proposal_status_history (proposal_id, status, generated_sections_snapshot) VALUES (:pid, 'submission', :snapshot)"),
                {"pid": proposal_id, "snapshot": json.dumps(sections)}
            )
        return {"message": "Proposal submitted for submission."}
    except Exception as e:
        logger.error(f"[REQUEST SUBMISSION ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to request submission.")

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
                text("UPDATE proposals SET status = 'submitted', updated_at = NOW() WHERE id = :id AND user_id = :uid"),
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

@router.post("/finalize-proposal")
async def finalize_proposal(request: FinalizeProposalRequest, current_user: dict = Depends(get_current_user)):
    """
    Marks a proposal as 'accepted', making it read-only.
    """
    try:
        with get_engine().begin() as connection:
            # Get the current sections to create a snapshot
            sections = connection.execute(
                text("SELECT generated_sections FROM proposals WHERE id = :id"),
                {"id": request.proposal_id}
            ).scalar() or {}

            connection.execute(
                text("UPDATE proposals SET is_accepted = TRUE, status = 'approved', updated_at = NOW() WHERE id = :id AND user_id = :uid"),
                {"id": request.proposal_id, "uid": current_user["user_id"]}
            )
            # Log the status change
            connection.execute(
                text("INSERT INTO proposal_status_history (proposal_id, status, generated_sections_snapshot) VALUES (:pid, 'approved', :snapshot)"),
                {"pid": request.proposal_id, "snapshot": json.dumps(sections)}
            )
        return {"message": "Proposal finalized.", "proposal_id": request.proposal_id, "is_accepted": True}
    except Exception as e:
        print(f"[FINALIZE ERROR] {e}")
        raise HTTPException(status_code=500, detail="Failed to finalize proposal.")


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
                text("SELECT reviewer_id FROM proposal_peer_reviews WHERE proposal_id = :proposal_id AND reviewer_id = :user_id AND status = 'pending'"),
                {"proposal_id": proposal_id, "user_id": user_id}
            ).scalar()

            if not reviewer_id_from_db:
                raise HTTPException(status_code=403, detail="You are not assigned to review this proposal or the review is already completed.")

            # Get the latest 'in_review' status history ID
            history_id = connection.execute(
                text("SELECT id FROM proposal_status_history WHERE proposal_id = :pid AND status = 'in_review' ORDER BY created_at DESC LIMIT 1"),
                {"pid": proposal_id}
            ).scalar()

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

            # Mark the original review request as completed by deleting it, since comments are now individual rows
            connection.execute(
                text("DELETE FROM proposal_peer_reviews WHERE proposal_id = :proposal_id AND reviewer_id = :user_id AND status = 'pending'"),
                {"proposal_id": proposal_id, "user_id": user_id}
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
                text("UPDATE proposals SET status = 'in_review', updated_at = NOW() WHERE id = :id"),
                {"id": proposal_id}
            )

            # Log the status change with the snapshot
            connection.execute(
                text("INSERT INTO proposal_status_history (proposal_id, status, generated_sections_snapshot) VALUES (:pid, 'in_review', :snapshot)"),
                {"pid": proposal_id, "snapshot": json.dumps(sections)}
            )

            # Add the peer reviewers
            for reviewer_info in request.reviewers:
                connection.execute(
                    text("""
                        INSERT INTO proposal_peer_reviews (proposal_id, reviewer_id, deadline, status)
                        VALUES (:proposal_id, :reviewer_id, :deadline, 'pending')
                        ON CONFLICT (proposal_id, reviewer_id) DO UPDATE SET
                            deadline = EXCLUDED.deadline,
                            status = 'pending',
                            updated_at = NOW()
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
    allowed_statuses = ['draft', 'in_review', 'submission', 'submitted', 'approved']
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
                text("UPDATE proposals SET status = :status, updated_at = NOW() WHERE id = :id"),
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


@router.get("/review-proposal/{proposal_id}")
async def get_proposal_for_review(proposal_id: uuid.UUID, current_user: dict = Depends(get_current_user)):
    """
    Fetches a proposal for a user assigned to review it.
    """
    user_id = current_user["user_id"]
    try:
        with get_engine().connect() as connection:
            # Check if the user is assigned to review this proposal
            review_assignment = connection.execute(
                text("SELECT id FROM proposal_peer_reviews WHERE proposal_id = :proposal_id AND reviewer_id = :user_id AND status = 'pending'"),
                {"proposal_id": proposal_id, "user_id": user_id}
            ).fetchone()

            if not review_assignment:
                raise HTTPException(status_code=403, detail="You are not assigned to review this proposal or the review is already completed.")

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
                text("INSERT INTO field_contexts (id, name, geographic_coverage, created_by) VALUES (:id, :name, :geo, :user_id)"),
                {"id": new_id, "name": request.name, "geo": request.geographic_coverage, "user_id": current_user["user_id"]}
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
                text("UPDATE proposals SET status = 'deleted', updated_at = NOW() WHERE id = :id AND user_id = :uid RETURNING id"),
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
                text("UPDATE proposals SET user_id = :new_owner_id, updated_at = NOW() WHERE id = :id AND user_id = :uid RETURNING id"),
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
                    SET status = :status, generated_sections = :snapshot, updated_at = NOW()
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
            # First, verify the user has access to the proposal
            proposal_owner = connection.execute(
                text("SELECT user_id FROM proposals WHERE id = :id"),
                {"id": proposal_id}
            ).scalar()

            if not proposal_owner or proposal_owner != user_id:
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
            # Verify user has access
            proposal_owner = connection.execute(
                text("SELECT user_id FROM proposals WHERE id = :id"),
                {"id": proposal_id}
            ).scalar()
            if not proposal_owner or proposal_owner != user_id:
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
                text("UPDATE proposal_peer_reviews SET author_response = :response, updated_at = NOW() WHERE id = :rid"),
                {"response": request.author_response, "rid": review_id}
            )

        return {"message": "Response saved successfully."}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"[SAVE AUTHOR RESPONSE ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save author response.")


@router.post("/proposals/{proposal_id}/upload-approved-document")
async def upload_approved_document(proposal_id: uuid.UUID, file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """
    Uploads the final approved document for a proposal.
    """
    user_id = current_user["user_id"]
    try:
        with get_engine().connect() as connection:
            # Verify that the user is the author of the proposal and it is approved
            proposal = connection.execute(
                text("SELECT user_id, status FROM proposals WHERE id = :id"),
                {"id": proposal_id}
            ).fetchone()

            if not proposal:
                raise HTTPException(status_code=404, detail="Proposal not found.")

            if proposal.user_id != user_id:
                raise HTTPException(status_code=403, detail="You do not have permission to upload documents for this proposal.")

            if proposal.status != 'approved':
                raise HTTPException(status_code=400, detail="Proposal is not approved yet.")

            # In a real application, you would save the file to a secure location (e.g., S3)
            # and store the path/URL in the database.
            # For this example, we'll just return a success message.
            # a new column would be needed in the proposals table to store the document path.

        return {"message": f"File '{file.filename}' uploaded successfully for proposal '{proposal_id}'."}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"[UPLOAD DOCUMENT ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to upload document.")
