#  Standard Library
import json
import re
import uuid
from datetime import datetime

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
from backend.crew import ProposalCrew

# This router handles all endpoints related to the lifecycle of a proposal,
# from creation and editing to listing and deletion.
router = APIRouter()


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
    raw_output = result.raw.replace("`", "")
    raw_output = re.sub(r'[\x00-\x1F\x7F]', '', raw_output)
    parsed = json.loads(raw_output)

    generated_text = parsed.get("generated_content", "").strip()
    evaluation_status = parsed.get("evaluation_status", "")
    feedback = parsed.get("feedback", "")

    if evaluation_status.lower() == "flagged" and feedback:
        # If flagged, automatically regenerate with feedback.
        generated_text = regenerate_section_logic(
            session_id, request.section, feedback, request.proposal_id
        )
        message = f"Initial content flagged. Regenerated using evaluator feedback for {request.section}"
    else:
        # Persist the generated text to the database.
        try:
            with engine.begin() as conn:
                db_res = conn.execute(text("SELECT generated_sections FROM proposals WHERE id = :id"), {"id": request.proposal_id}).scalar()
                sections = json.loads(db_res) if db_res else {}
                sections[request.section] = generated_text
                conn.execute(
                    text("UPDATE proposals SET generated_sections = :sections, updated_at = NOW() WHERE id = :id"),
                    {"sections": json.dumps(sections), "id": request.proposal_id}
                )
        except Exception as e:
            print(f"[DB UPDATE ERROR - process_section] {e}")

        message = f"Content generated for {request.section}"

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
                        UPDATE proposals SET form_data = :form, project_description = :desc,
                        generated_sections = :sections, updated_at = NOW() WHERE id = :id
                    """),
                    {
                        "form": json.dumps(request.form_data),
                        "desc": request.project_description,
                        "sections": json.dumps(request.generated_sections),
                        "id": proposal_id
                    }
                )
                message = "Draft updated successfully"
            else:
                # Insert a new draft.
                connection.execute(
                    text("""
                        INSERT INTO proposals (id, user_id, form_data, project_description, generated_sections)
                        VALUES (:id, :uid, :form, :desc, :sections)
                    """),
                    {
                        "id": proposal_id,
                        "uid": user_id,
                        "form": json.dumps(request.form_data),
                        "desc": request.project_description,
                        "sections": json.dumps(request.generated_sections)
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
        with open("config/templates/sample_templates.json", "r", encoding="utf-8") as f:
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
                text("SELECT id, form_data, generated_sections, created_at, updated_at, is_accepted FROM proposals WHERE user_id = :uid ORDER BY updated_at DESC"),
                {"uid": user_id}
            )
            for row in result.fetchall():
                form_data = json.loads(row[1]) if row[1] else {}
                sections = json.loads(row[2]) if row[2] else {}
                draft_list.append({
                    "proposal_id": row[0],
                    "project_title": form_data.get("Project title", "Untitled Proposal"),
                    "summary": sections.get("Summary", ""),
                    "created_at": row[3].isoformat() if row[3] else None,
                    "updated_at": row[4].isoformat() if row[4] else None,
                    "is_accepted": row[5],
                    "is_sample": False
                })
        return {"message": "Drafts fetched successfully.", "drafts": draft_list}
    except Exception as e:
        print(f"[LIST DRAFTS ERROR] {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch drafts")


@router.get("/load-draft/{proposal_id}")
async def load_draft(proposal_id: str, current_user: dict = Depends(get_current_user)):
    """
    Loads a specific draft, whether it's a user-created one or a sample.
    It creates a new Redis session for the loaded draft.
    """
    user_id = current_user["user_id"]

    # Handle sample drafts, which are loaded from a JSON file.
    if proposal_id.startswith("sample-"):
        try:
            with open("config/templates/sample_templates.json", "r") as f:
                samples = json.load(f)
            sample = next((s for s in samples if s["proposal_id"] == proposal_id), None)
            if not sample:
                raise HTTPException(status_code=404, detail="Sample not found.")

            data_to_load = sample
            data_to_load["is_sample"] = True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to load sample: {e}")
    else:
        # Handle user drafts, loaded from the database.
        with engine.connect() as conn:
            draft = conn.execute(
                text("SELECT * FROM proposals WHERE id = :id AND user_id = :uid"),
                {"id": proposal_id, "uid": user_id}
            ).fetchone()
            if not draft:
                raise HTTPException(status_code=404, detail="Draft not found.")

            form_data = json.loads(draft['form_data']) if draft['form_data'] else {}
            sections = json.loads(draft['generated_sections']) if draft['generated_sections'] else {}
            data_to_load = {
                "form_data": form_data,
                "project_description": draft['project_description'],
                "generated_sections": {sec: sections.get(sec) for sec in SECTIONS},
                "is_accepted": draft['is_accepted'],
                "created_at": draft['created_at'].isoformat() if draft['created_at'] else None,
                "updated_at": draft['updated_at'].isoformat() if draft['updated_at'] else None,
                "is_sample": False
            }

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
