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
from backend.core.config import get_available_templates, load_proposal_template
from backend.models.schemas import (
    SectionRequest,
    RegenerateRequest,
    SaveDraftRequest,
    FinalizeProposalRequest,
    CreateSessionRequest,
    UpdateSectionRequest,
    SubmitPeerReviewRequest,
    SubmitReviewRequest
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

            # Log the initial 'draft' status
            connection.execute(
                text("INSERT INTO proposal_status_history (proposal_id, status) VALUES (:pid, 'draft')"),
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
                    p.id, d.name, fc.name, u.name
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
                    p.user_id = :uid
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

@router.post("/proposals/{proposal_id}/request-submission")
async def request_submission(proposal_id: uuid.UUID, current_user: dict = Depends(get_current_user)):
    """
    Requests submission of a proposal.
    """
    user_id = current_user["user_id"]
    try:
        with get_engine().begin() as connection:
            connection.execute(
                text("UPDATE proposals SET status = 'submission', updated_at = NOW() WHERE id = :id AND user_id = :uid"),
                {"id": proposal_id, "uid": user_id}
            )
            # Log the status change
            connection.execute(
                text("INSERT INTO proposal_status_history (proposal_id, status) VALUES (:pid, 'submission')"),
                {"pid": proposal_id}
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
            connection.execute(
                text("UPDATE proposals SET status = 'submitted', updated_at = NOW() WHERE id = :id AND user_id = :uid"),
                {"id": proposal_id, "uid": user_id}
            )
            # Log the status change
            connection.execute(
                text("INSERT INTO proposal_status_history (proposal_id, status) VALUES (:pid, 'submitted')"),
                {"pid": proposal_id}
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
            connection.execute(
                text("UPDATE proposals SET is_accepted = TRUE, status = 'approved', updated_at = NOW() WHERE id = :id AND user_id = :uid"),
                {"id": request.proposal_id, "uid": current_user["user_id"]}
            )
            # Log the status change
            connection.execute(
                text("INSERT INTO proposal_status_history (proposal_id, status) VALUES (:pid, 'approved')"),
                {"pid": request.proposal_id}
            )
        return {"message": "Proposal finalized.", "proposal_id": request.proposal_id, "is_accepted": True}
    except Exception as e:
        print(f"[FINALIZE ERROR] {e}")
        raise HTTPException(status_code=500, detail="Failed to finalize proposal.")


@router.post("/proposals/{proposal_id}/review")
async def submit_review(proposal_id: uuid.UUID, request: SubmitReviewRequest, current_user: dict = Depends(get_current_user)):
    """
    Submits a peer review for a proposal.
    """
    user_id = current_user["user_id"]
    try:
        with get_engine().begin() as connection:
            # Check if the user is assigned to review this proposal
            review_assignment = connection.execute(
                text("SELECT id FROM proposal_peer_reviews WHERE proposal_id = :proposal_id AND user_id = :user_id AND status = 'pending'"),
                {"proposal_id": proposal_id, "user_id": user_id}
            ).fetchone()

            if not review_assignment:
                raise HTTPException(status_code=403, detail="You are not assigned to review this proposal.")

            # Get existing reviews and append the new one
            existing_reviews = connection.execute(
                text("SELECT reviews FROM proposals WHERE id = :id"),
                {"id": proposal_id}
            ).scalar() or []

            new_review = {
                "reviewer_id": user_id,
                "review_data": request.review_data,
                "created_at": datetime.utcnow().isoformat()
            }
            existing_reviews.append(new_review)

            # Update the reviews in the proposals table
            connection.execute(
                text("UPDATE proposals SET reviews = :reviews, updated_at = NOW() WHERE id = :id"),
                {"reviews": json.dumps(existing_reviews), "id": proposal_id}
            )

            # Update the status in the proposal_peer_reviews table
            connection.execute(
                text("UPDATE proposal_peer_reviews SET status = 'completed', updated_at = NOW() WHERE id = :id"),
                {"id": review_assignment[0]}
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

            # Update the proposal status
            connection.execute(
                text("UPDATE proposals SET status = 'in_review', updated_at = NOW() WHERE id = :id"),
                {"id": proposal_id}
            )

            # Log the status change
            connection.execute(
                text("INSERT INTO proposal_status_history (proposal_id, status) VALUES (:pid, 'in_review')"),
                {"pid": proposal_id}
            )

            # Add the peer reviewers
            for reviewer_id in request.user_ids:
                connection.execute(
                    text("INSERT INTO proposal_peer (proposal_id, user_id) VALUES (:proposal_id, :user_id)"),
                    {"proposal_id": proposal_id, "user_id": reviewer_id}
                )

        return {"message": "Proposal submitted for peer review."}
    except Exception as e:
        logger.error(f"[SUBMIT FOR REVIEW ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to submit for review.")


@router.get("/donors")
async def get_donors():
    """
    Fetches all donors from the database.
    """
    try:
        with get_engine().connect() as connection:
            result = connection.execute(text("SELECT id, name FROM donors ORDER BY name"))
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
            result = connection.execute(text("SELECT id, name FROM outcomes ORDER BY name"))
            outcomes = [{"id": str(row[0]), "name": row[1]} for row in result.fetchall()]
        return {"outcomes": outcomes}
    except Exception as e:
        logger.error(f"[GET OUTCOMES ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch outcomes.")


@router.get("/field-contexts")
async def get_field_contexts():
    """
    Fetches all field contexts from the database.
    """
    try:
        with get_engine().connect() as connection:
            result = connection.execute(text("SELECT id, name, geographic_coverage FROM field_contexts ORDER BY name"))
            field_contexts = [{"id": str(row[0]), "name": row[1], "geographic_coverage": row[2]} for row in result.fetchall()]
        return {"field_contexts": field_contexts}
    except Exception as e:
        logger.error(f"[GET FIELD CONTEXTS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch field contexts.")


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
