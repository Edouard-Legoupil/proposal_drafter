#  Standard Library
import json
import re
import uuid
from datetime import datetime 
import logging

#  Third-Party Libraries
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy import text

#  Internal Modules
from backend.core.db import engine
from backend.core.redis import redis_client
from backend.core.security import get_current_user
from backend.core.config import proposal_data, SECTIONS
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




@router.post("/process_section/{session_id}")
async def process_section(session_id: str, request: SectionRequest, current_user: dict = Depends(get_current_user)):
    """
    Processes a single section of a proposal by running the generation crew.
    If the initial output is flagged, it automatically triggers a regeneration.
    """
    session_data_str = redis_client.get(session_id)
    if not session_data_str:
        raise HTTPException(status_code=400, detail="Session data not found.")

    # Prevent editing of finalized proposals.
    with engine.connect() as connection:
        res = connection.execute(
            text("SELECT is_accepted FROM proposals WHERE id = :id AND user_id = :uid"),
            {"id": request.proposal_id, "uid": current_user["user_id"]}
        ).scalar()
        if res:
            raise HTTPException(status_code=403, detail="This proposal is finalized and cannot be modified.")

    session_data = json.loads(session_data_str)
    form_data = session_data["form_data"]
    project_description = session_data["project_description"]

    section_config = next((s for s in proposal_data["sections"] if s["section_name"] == request.section), None)
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
        with engine.begin() as conn:
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
    with engine.connect() as connection:
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
    proposal_id = request.proposal_id or str(uuid.uuid4())

    try:
        with engine.begin() as connection:
            existing = connection.execute(
                text("SELECT id FROM proposals WHERE id = :id AND user_id = :uid"),
                {"id": proposal_id, "uid": user_id}
            ).fetchone()

            if existing:
                # Update an existing draft.
                connection.execute(
                    text("""
                        UPDATE proposals
                        SET form_data = :form, project_description = :desc,
                        generated_sections = :sections, status = :status, donor = :donor,
                        field_context = :field_context, outcome = :outcome, updated_at = NOW()
                        WHERE id = :id
                    """),
                    {
                        "form": json.dumps(request.form_data),
                        "desc": request.project_description,
                        "sections": json.dumps(request.generated_sections),
                        "status": request.status,
                        "donor": request.donor,
                        "field_context": request.field_context,
                        "outcome": request.outcome,
                        "id": proposal_id
                    }
                )
                message = "Draft updated successfully"
            else:
                # Insert a new draft.
                connection.execute(
                    text("""
                        INSERT INTO proposals (id, user_id, form_data, project_description, generated_sections, status, donor, field_context, outcome)
                        VALUES (:id, :uid, :form, :desc, :sections, :status, :donor, :field_context, :outcome)
                    """),
                    {
                        "id": proposal_id,
                        "uid": user_id,
                        "form": json.dumps(request.form_data),
                        "desc": request.project_description,
                        "sections": json.dumps(request.generated_sections),
                        "status": request.status,
                        "donor": request.donor,
                        "field_context": request.field_context,
                        "outcome": request.outcome,
                    }
                )
                message = "Draft created successfully"

        return {"message": message, "proposal_id": proposal_id}
    except Exception as e:
        print(f"[SAVE DRAFT ERROR] {e}")
        raise HTTPException(status_code=500, detail="Failed to save draft")


@router.get("/list-drafts")
async def list_drafts(current_user: dict = Depends(get_current_user)):
    """
    Lists all drafts for the current user, including sample templates.
    """
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
    except Exception as e:
        print(f"[TEMPLATE LOAD ERROR] {e}")

    # Fetch user's drafts from the database.
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("SELECT id, form_data, generated_sections, created_at, updated_at, is_accepted, status, donor, field_context, outcome FROM proposals WHERE user_id = :uid ORDER BY updated_at DESC"),
                {"uid": user_id}
            )
            for row in result.fetchall():
                form_data = row[1] if row[1] else {}
                sections = row[2] if row[2] else {}

                draft_list.append({
                    "proposal_id": row[0],
                    "project_title": form_data.get("Project title", "Untitled Proposal"),
                    "summary": sections.get("Summary", ""),
                    "created_at": row[3].isoformat() if row[3] else None,
                    "updated_at": row[4].isoformat() if row[4] else None,
                    "is_accepted": row[5],
                    "status": row[6],
                    "donor": row[7],
                    "field_context": row[8],
                    "outcome": row[9],
                    "is_sample": False
                })
        return {"message": "Drafts fetched successfully.", "drafts": draft_list}
    except Exception as e:
        print(f"[LIST DRAFTS ERROR] {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch drafts")


@router.get("/sections")
async def get_sections():
    """
    Returns the list of sections and their config (name, instructions, word_limit).
    """
    return {"sections": proposal_data.get("sections", [])}

@router.get("/load-draft/{proposal_id}")
async def load_draft(proposal_id: str, current_user: dict = Depends(get_current_user)):
    """
    Loads a specific draft, whether it's a user-created one or a sample.
    It creates a new Redis session for the loaded draft.
    """
    user_id = current_user["user_id"]

    # Extract section names from JSON template (dynamic structure).
    section_names = [s.get("section_name") for s in proposal_data.get("sections", [])]
    

    # Handle user drafts, loaded from the database.
    if not proposal_id.startswith("sample-"):
        with engine.connect() as conn:
            # === Corrected SELECT statement with specific columns ===
            # The order of columns here is important and must match the indices below.
            draft = conn.execute(
                text("SELECT form_data, generated_sections, project_description, is_accepted, created_at, updated_at FROM proposals WHERE id = :id AND user_id = :uid"),
                {"id": proposal_id, "uid": user_id}
            ).fetchone()
            if not draft:
                raise HTTPException(status_code=404, detail="Draft not found.")

            # === Corrected access using integer indices ===
            # Access columns by their position (0-based) from the SELECT statement.
            form_data = draft[0] if draft[0] else {}
            sections = draft[1] if draft[1] else {}
            project_description = draft[2]
            
            data_to_load = {
                "form_data": form_data,
                "project_description": project_description,
                "generated_sections": {sec: sections.get(sec) for sec in SECTIONS},
                "is_accepted": draft[3],
                "created_at": draft[4].isoformat() if draft[4] else None,
                "updated_at": draft[5].isoformat() if draft[5] else None,
                "is_sample": False
            }
    else:
        # Handle sample drafts, which are loaded from a JSON file.
        try:
            with open("templates/sample_templates.json", "r") as f:
                samples = json.load(f)
            sample = next((s for s in samples if s["proposal_id"] == proposal_id), None)
            if not sample:
                raise HTTPException(status_code=404, detail="Sample not found.")

            data_to_load = sample
            data_to_load["is_sample"] = True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to load sample: {e}")

    # Create a new Redis session for the loaded draft.
    session_id = str(uuid.uuid4())
    redis_payload = {
        "user_id": user_id,
        "proposal_id": proposal_id,
        **data_to_load
    }
    redis_client.setex(session_id, 3600, json.dumps(redis_payload))

    return {"session_id": session_id, **data_to_load}

@router.post("/finalize-proposal")
async def finalize_proposal(request: FinalizeProposalRequest, current_user: dict = Depends(get_current_user)):
    """
    Marks a proposal as 'accepted', making it read-only.
    """
    try:
        with engine.begin() as connection:
            connection.execute(
                text("UPDATE proposals SET is_accepted = TRUE, updated_at = NOW() WHERE id = :id AND user_id = :uid"),
                {"id": request.proposal_id, "uid": current_user["user_id"]}
            )
        return {"message": "Proposal finalized.", "proposal_id": request.proposal_id, "is_accepted": True}
    except Exception as e:
        print(f"[FINALIZE ERROR] {e}")
        raise HTTPException(status_code=500, detail="Failed to finalize proposal.")


@router.get("/proposals/reviews")
async def get_reviews(current_user: dict = Depends(get_current_user)):
    """
    Fetches proposals that are in 'review' status.
    In a real-world scenario, this would likely be more complex,
    perhaps involving a separate 'reviewers' table.
    For this implementation, we'll just fetch proposals with the 'review' status.
    """
    user_id = current_user["user_id"]
    review_list = []
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("SELECT id, form_data, status, donor, field_context, outcome, updated_at FROM proposals WHERE status = 'review' ORDER BY updated_at DESC"),
            )
            for row in result.fetchall():
                form_data = row[1] if row[1] else {}
                review_list.append({
                    "proposal_id": row[0],
                    "project_title": form_data.get("Project title", "Untitled Proposal"),
                    "status": row[2],
                    "donor": row[3],
                    "field_context": row[4],
                    "outcome": row[5],
                    "updated_at": row[6].isoformat() if row[6] else None,
                })
        return {"message": "Review proposals fetched successfully.", "reviews": review_list}
    except Exception as e:
        print(f"[GET REVIEWS ERROR] {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch reviews")

@router.post("/proposals/{proposal_id}/submit-for-review")
async def submit_for_review(proposal_id: str, current_user: dict = Depends(get_current_user)):
    """
    Updates a proposal's status to 'review'.
    """
    user_id = current_user["user_id"]
    try:
        with engine.begin() as connection:
            result = connection.execute(
                text("UPDATE proposals SET status = 'review', updated_at = NOW() WHERE id = :id AND user_id = :uid RETURNING id"),
                {"id": proposal_id, "uid": user_id}
            )
            if not result.fetchone():
                raise HTTPException(status_code=404, detail="Proposal not found or you don't have permission to edit it.")
        return {"message": "Proposal submitted for review.", "proposal_id": proposal_id}
    except Exception as e:
        print(f"[SUBMIT FOR REVIEW ERROR] {e}")
        raise HTTPException(status_code=500, detail="Failed to submit for review.")

@router.get("/knowledge")
async def get_knowledge_cards(current_user: dict = Depends(get_current_user)):
    """
    Returns a static list of knowledge cards.
    In a real application, this data would come from a database.
    """
    knowledge_cards = [
        {"id": "kc-1", "category": "Donor Insights", "title": "ECHO", "summary": "Key compliance and funding priorities for this donor.", "last_updated": "2025-08-05"},
        {"id": "kc-2", "category": "Donor Insights", "title": "CERF", "summary": "Key compliance and funding priorities for this donor.", "last_updated": "2025-08-05"},
        {"id": "kc-3", "category": "Field Context", "title": "Country A", "summary": "Recent situational updates.", "last_updated": "2025-08-05"},
        {"id": "kc-4", "category": "Field Context", "title": "Route Based Approach - West Africa", "summary": "Recent situational updates.", "last_updated": "2025-08-05"},
        {"id": "kc-5", "category": "Outcome Lessons", "title": "Shelter", "summary": "Extracted insights from Policies, Guidance and related Past Evaluation Recommmandation.", "last_updated": "2025-08-05"},
    ]
    return {"message": "Knowledge cards fetched successfully.", "knowledge_cards": knowledge_cards}

@router.delete("/delete-draft/{proposal_id}")
async def delete_draft(proposal_id: str, current_user: dict = Depends(get_current_user)):
    """
    Deletes a draft proposal from the database.
    """
    user_id = current_user["user_id"]
    try:
        with engine.begin() as connection:
            result = connection.execute(
                text("DELETE FROM proposals WHERE id = :id AND user_id = :uid AND is_accepted = FALSE RETURNING id"),
                {"id": proposal_id, "uid": user_id}
            )
            if not result.fetchone():
                raise HTTPException(status_code=404, detail="Draft not found or is finalized.")

        return {"message": f"Draft '{proposal_id}' deleted successfully."}
    except Exception as e:
        print(f"[DELETE DRAFT ERROR] {e}")
        raise HTTPException(status_code=500, detail="Failed to delete draft.")
