import json
import uuid
from datetime import datetime
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Body

from sqlalchemy import text, func
from sqlalchemy.exc import SQLAlchemyError 

#  Internal Modules
from backend.core.db import get_engine
 
from backend.core.redis import redis_client
from backend.core.security import get_current_user
from backend.core.config import proposal_data, SECTIONS
from backend.models.schemas import (
    SectionRequest,
    RegenerateRequest,
    SaveDraftRequest,
    FinalizeProposalRequest,
    KnowledgeCard,
    ProposalOut
)
from backend.utils.proposal_logic import regenerate_section_logic
from backend.utils.crew import ProposalCrew

router = APIRouter()
logger = logging.getLogger(__name__)

# Helper function to get or create IDs for donors and outcomes
def get_or_create_ids(connection, table_name: str, names: List[str]) -> List[int]:
    ids = []
    for name in names:
        # Check if the name exists
        result = connection.execute(text(f"SELECT id FROM {table_name} WHERE name = :name"), {"name": name}).scalar()
        if result:
            ids.append(result)
        else:
            # If not, create it and get the new ID
            new_id = connection.execute(
                text(f"INSERT INTO {table_name} (name) VALUES (:name) RETURNING id"),
                {"name": name}
            ).scalar()
            ids.append(new_id)
    return ids

@router.post("/save-draft")
async def save_draft(request: SaveDraftRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    proposal_id = request.proposal_id or str(uuid.uuid4())

    with engine.begin() as connection:
        # Check if proposal exists
        existing = connection.execute(
            text("SELECT id FROM proposals WHERE id = :id AND user_id = :uid"),
            {"id": proposal_id, "uid": user_id}
        ).fetchone()

        if existing:
            # Update existing draft
            connection.execute(
                text("""
                    UPDATE proposals
                    SET form_data = :form,
                        project_description = :desc,
                        generated_sections = :sections,
                        status = :status,
                        field_contexts = :field_contexts,
                        updated_at = NOW()
                    WHERE id = :id
                """),
                {
                    "form": json.dumps(request.form_data),
                    "desc": request.project_description,
                    "sections": json.dumps(request.generated_sections),
                    "status": request.status,
                    "field_contexts": request.field_contexts,
                    "id": proposal_id
                }
            )
            # Clear old associations
            connection.execute(text("DELETE FROM proposal_donors WHERE proposal_id = :pid"), {"pid": proposal_id})
            connection.execute(text("DELETE FROM proposal_outcomes WHERE proposal_id = :pid"), {"pid": proposal_id})
            message = "Draft updated successfully"
        else:
            # Insert new draft
            connection.execute(
                text("""
                    INSERT INTO proposals (id, user_id, form_data, project_description, generated_sections, status, field_contexts)
                    VALUES (:id, :uid, :form, :desc, :sections, :status, :field_contexts)
                """),
                {
                    "id": proposal_id,
                    "uid": user_id,
                    "form": json.dumps(request.form_data),
                    "desc": request.project_description,
                    "sections": json.dumps(request.generated_sections),
                    "status": request.status,
                    "field_contexts": request.field_contexts
                }
            )
            message = "Draft created successfully"

        # Handle donors
        if request.donors:
            donor_ids = get_or_create_ids(connection, "donors", request.donors)
            for donor_id in donor_ids:
                connection.execute(
                    text("INSERT INTO proposal_donors (proposal_id, donor_id) VALUES (:pid, :did) ON CONFLICT DO NOTHING"),
                    {"pid": proposal_id, "did": donor_id}
                )

        # Handle outcomes
        if request.outcomes:
            outcome_ids = get_or_create_ids(connection, "outcomes", request.outcomes)
            for outcome_id in outcome_ids:
                connection.execute(
                    text("INSERT INTO proposal_outcomes (proposal_id, outcome_id) VALUES (:pid, :oid) ON CONFLICT DO NOTHING"),
                    {"pid": proposal_id, "oid": outcome_id}
                )

    return {"message": message, "proposal_id": proposal_id}


@router.get("/list-drafts", response_model=List[ProposalOut])
async def list_drafts(current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]

    query = text("""
        SELECT
            p.id,
            p.form_data,
            p.generated_sections,
            p.created_at,
            p.updated_at,
            p.is_accepted,
            p.status,
            p.field_contexts,
            ARRAY_AGG(DISTINCT d.name) as donors,
            ARRAY_AGG(DISTINCT o.name) as outcomes
        FROM proposals p
        LEFT JOIN proposal_donors pd ON p.id = pd.proposal_id
        LEFT JOIN donors d ON pd.donor_id = d.id
        LEFT JOIN proposal_outcomes po ON p.id = po.proposal_id
        LEFT JOIN outcomes o ON po.outcome_id = o.id
        WHERE p.user_id = :uid
        GROUP BY p.id
        ORDER BY p.updated_at DESC
    """)

    with engine.connect() as connection:
        result = connection.execute(query, {"uid": user_id}).fetchall()

    draft_list = []
    for row in result:
        form_data = row[1] if row[1] else {}
        sections = row[2] if row[2] else {}
        draft_list.append(ProposalOut(
            proposal_id=str(row[0]),
            project_title=form_data.get("Project title", "Untitled Proposal"),
            summary=sections.get("Summary", ""),
            created_at=row[3].isoformat(),
            updated_at=row[4].isoformat(),
            is_accepted=row[5],
            status=row[6],
            field_contexts=row[7] or [],
            donors=[d for d in row[8] if d is not None],
            outcomes=[o for o in row[9] if o is not None]
        ))

    return draft_list

@router.get("/knowledge", response_model=List[KnowledgeCard])
async def get_knowledge_cards():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT id, category, title, summary, updated_at FROM knowledge_cards")).fetchall()

    return [
        KnowledgeCard(
            id=row[0],
            category=row[1],
            title=row[2],
            summary=row[3],
            last_updated=row[4].isoformat()
        ) for row in result
    ]

@router.post("/proposals/{proposal_id}/submit-for-review")
async def submit_for_review(proposal_id: str, current_user: dict = Depends(get_current_user)):
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
        logger.error(f"[SUBMIT FOR REVIEW ERROR] {e}")
        raise HTTPException(status_code=500, detail="Failed to submit for review.")

@router.get("/proposals/reviews", response_model=List[ProposalOut])
async def get_reviews(current_user: dict = Depends(get_current_user)):
    query = text("""
        SELECT
            p.id,
            p.form_data,
            p.generated_sections,
            p.created_at,
            p.updated_at,
            p.is_accepted,
            p.status,
            p.field_contexts,
            ARRAY_AGG(DISTINCT d.name) as donors,
            ARRAY_AGG(DISTINCT o.name) as outcomes
        FROM proposals p
        LEFT JOIN proposal_donors pd ON p.id = pd.proposal_id
        LEFT JOIN donors d ON pd.donor_id = d.id
        LEFT JOIN proposal_outcomes po ON p.id = po.proposal_id
        LEFT JOIN outcomes o ON po.outcome_id = o.id
        WHERE p.status = 'review'
        GROUP BY p.id
        ORDER BY p.updated_at DESC
    """)
    with engine.connect() as connection:
        result = connection.execute(query).fetchall()

    review_list = []
    for row in result:
        form_data = row[1] if row[1] else {}
        sections = row[2] if row[2] else {}
        review_list.append(ProposalOut(
            proposal_id=str(row[0]),
            project_title=form_data.get("Project title", "Untitled Proposal"),
            summary=sections.get("Summary", ""),
            created_at=row[3].isoformat(),
            updated_at=row[4].isoformat(),
            is_accepted=row[5],
            status=row[6],
            field_contexts=row[7] or [],
            donors=[d for d in row[8] if d is not None],
            outcomes=[o for o in row[9] if o is not None]
        ))
    return review_list

 
@router.post("/process_section/{session_id}")
async def process_section(session_id: str, request: SectionRequest, current_user: dict = Depends(get_current_user)):
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
    section_config = next((s for s in proposal_data["sections"] if s["section_name"] == request.section), None)
    if not section_config:
        raise HTTPException(status_code=400, detail=f"Invalid section name: {request.section}")
    crew_instance = ProposalCrew().generate_proposal_crew()
    result = crew_instance.kickoff(inputs={
        "section": request.section,
        "form_data": form_data,
        "project_description": project_description,
        "instructions": section_config.get("instructions", ""),
        "word_limit": section_config.get("word_limit", 350)
    })
    try:
        raw_output = result.raw if hasattr(result, 'raw') and result.raw else ""
        clean_output = re.sub(r'[`\x00-\x1F\x7F]', '', raw_output)
        parsed = json.loads(clean_output)
    except (AttributeError, json.JSONDecodeError) as e:
        raise HTTPException(status_code=500, detail="Failed to parse CrewAI output. It may not be valid JSON.")
    generated_text = parsed.get("generated_content", "").strip()
    evaluation_status = parsed.get("evaluation_status", "")
    feedback = parsed.get("feedback", "")
    if evaluation_status.lower() == "flagged" and feedback:
        generated_text = regenerate_section_logic(
            session_id, request.section, feedback, request.proposal_id
        )
        message = f"Initial content flagged. Regenerated using evaluator feedback for {request.section}"
    else:
        message = f"Content generated for {request.section}"
    try:
        with get_engine().begin() as conn:
            db_res = conn.execute(text("SELECT generated_sections FROM proposals WHERE id = :id"), {"id": request.proposal_id}).scalar()
            sections = db_res if db_res else {}
            if not isinstance(sections, dict):
                try:
                    sections = json.loads(sections)
                except Exception:
                    sections = {}
            sections[request.section] = generated_text
            conn.execute(
                text("UPDATE proposals SET generated_sections = :sections, updated_at = NOW() WHERE id = :id"),
                {"sections": json.dumps(sections), "id": request.proposal_id}
            )
    except Exception as e:
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
    proposal_id = request.proposal_id or str(uuid.uuid4())

    try:
        with get_engine().begin() as connection:
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
    return {"sections": proposal_data.get("sections", [])}

@router.get("/load-draft/{proposal_id}")
async def load_draft(proposal_id: str, current_user: dict = Depends(get_current_user)):
 
    # This endpoint will need to be updated to handle the new data structure
    # For now, I'll leave it as is and focus on the main dashboard functionality
    raise HTTPException(status_code=501, detail="Not implemented")
 
    """
    Loads a specific draft, whether it's a user-created one or a sample.
    It creates a new Redis session for the loaded draft.
    """
    user_id = current_user["user_id"]

    # Extract section names from JSON template (dynamic structure).
    section_names = [s.get("section_name") for s in proposal_data.get("sections", [])]
    

    # Handle user drafts, loaded from the database.
    if not proposal_id.startswith("sample-"):
        with get_engine().connect() as conn:
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
    try:
        with get_engine().begin() as connection:
            connection.execute(
                text("UPDATE proposals SET is_accepted = TRUE, updated_at = NOW() WHERE id = :id AND user_id = :uid"),
                {"id": request.proposal_id, "uid": current_user["user_id"]}
            )
        return {"message": "Proposal finalized.", "proposal_id": request.proposal_id, "is_accepted": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to finalize proposal.")

@router.delete("/delete-draft/{proposal_id}")
async def delete_draft(proposal_id: str, current_user: dict = Depends(get_current_user)):
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
        raise HTTPException(status_code=500, detail="Failed to delete draft.")
