import json
import uuid
from datetime import datetime
import logging
from typing import List, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text, func, select, insert, update, delete
from sqlalchemy.orm import Session

from backend.core.db import engine
from backend.core.init_db import proposals, donors, outcomes, proposal_donors, proposal_outcomes
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

def get_db():
    with engine.connect() as connection:
        yield connection

def get_or_create_ids(connection, table, names: List[str]) -> List[str]:
    ids = []
    for name in names:
        result = connection.execute(select(table.c.id).where(table.c.name == name)).scalar()
        if result:
            ids.append(result)
        else:
            new_id = str(uuid.uuid4())
            connection.execute(insert(table).values(id=new_id, name=name))
            ids.append(new_id)
    return ids

@router.post("/save-draft")
async def save_draft(request: SaveDraftRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user["user_id"]
    proposal_id = request.proposal_id or str(uuid.uuid4())

    field_contexts_str = ",".join(request.field_contexts) if request.field_contexts else ""

    with db.begin():
        existing = db.execute(
            select(proposals.c.id).where(proposals.c.id == proposal_id).where(proposals.c.user_id == user_id)
        ).fetchone()

        if existing:
            db.execute(
                update(proposals).where(proposals.c.id == proposal_id).values(
                    form_data=json.dumps(request.form_data),
                    project_description=request.project_description,
                    generated_sections=json.dumps(request.generated_sections),
                    status=request.status,
                    field_contexts=field_contexts_str
                )
            )
            db.execute(delete(proposal_donors).where(proposal_donors.c.proposal_id == proposal_id))
            db.execute(delete(proposal_outcomes).where(proposal_outcomes.c.proposal_id == proposal_id))
            message = "Draft updated successfully"
        else:
            db.execute(
                insert(proposals).values(
                    id=proposal_id,
                    user_id=user_id,
                    form_data=json.dumps(request.form_data),
                    project_description=request.project_description,
                    generated_sections=json.dumps(request.generated_sections),
                    status=request.status,
                    field_contexts=field_contexts_str
                )
            )
            message = "Draft created successfully"

        if request.donors:
            donor_ids = get_or_create_ids(db, donors, request.donors)
            for donor_id in donor_ids:
                db.execute(insert(proposal_donors).values(proposal_id=proposal_id, donor_id=donor_id))

        if request.outcomes:
            outcome_ids = get_or_create_ids(db, outcomes, request.outcomes)
            for outcome_id in outcome_ids:
                db.execute(insert(proposal_outcomes).values(proposal_id=proposal_id, outcome_id=outcome_id))

    return {"message": message, "proposal_id": proposal_id}


@router.get("/list-drafts", response_model=List[ProposalOut])
async def list_drafts(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user["user_id"]

    # Fetch proposals for the user
    prop_query = select(proposals).where(proposals.c.user_id == user_id).order_by(proposals.c.updated_at.desc())
    proposals_result = db.execute(prop_query).fetchall()

    # Fetch all donors and outcomes for the user's proposals
    proposal_ids = [p.id for p in proposals_result]
    donors_query = select(proposal_donors.c.proposal_id, donors.c.name).join(donors).where(proposal_donors.c.proposal_id.in_(proposal_ids))
    outcomes_query = select(proposal_outcomes.c.proposal_id, outcomes.c.name).join(outcomes).where(proposal_outcomes.c.proposal_id.in_(proposal_ids))

    donors_result = db.execute(donors_query).fetchall()
    outcomes_result = db.execute(outcomes_query).fetchall()

    # Map donors and outcomes to proposals
    donors_map: Dict[str, List[str]] = {}
    for pid, name in donors_result:
        donors_map.setdefault(pid, []).append(name)

    outcomes_map: Dict[str, List[str]] = {}
    for pid, name in outcomes_result:
        outcomes_map.setdefault(pid, []).append(name)

    draft_list = []
    for row in proposals_result:
        form_data = json.loads(row.form_data) if row.form_data else {}
        sections = json.loads(row.generated_sections) if row.generated_sections else {}
        field_contexts = row.field_contexts.split(',') if row.field_contexts else []

        draft_list.append(ProposalOut(
            proposal_id=str(row.id),
            project_title=form_data.get("Project title", "Untitled Proposal"),
            summary=sections.get("Summary", ""),
            created_at=row.created_at,
            updated_at=row.updated_at,
            is_accepted=row.is_accepted,
            status=row.status,
            field_contexts=field_contexts,
            donors=donors_map.get(row.id, []),
            outcomes=outcomes_map.get(row.id, [])
        ))

    return draft_list

@router.get("/proposals/reviews", response_model=List[ProposalOut])
async def get_reviews(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    # This logic is simplified; in a real app, you'd likely have a more complex review assignment system.
    prop_query = select(proposals).where(proposals.c.status == 'review').order_by(proposals.c.updated_at.desc())
    proposals_result = db.execute(prop_query).fetchall()

    proposal_ids = [p.id for p in proposals_result]
    donors_query = select(proposal_donors.c.proposal_id, donors.c.name).join(donors).where(proposal_donors.c.proposal_id.in_(proposal_ids))
    outcomes_query = select(proposal_outcomes.c.proposal_id, outcomes.c.name).join(outcomes).where(proposal_outcomes.c.proposal_id.in_(proposal_ids))

    donors_result = db.execute(donors_query).fetchall()
    outcomes_result = db.execute(outcomes_query).fetchall()

    donors_map: Dict[str, List[str]] = {}
    for pid, name in donors_result:
        donors_map.setdefault(pid, []).append(name)

    outcomes_map: Dict[str, List[str]] = {}
    for pid, name in outcomes_result:
        outcomes_map.setdefault(pid, []).append(name)

    review_list = []
    for row in proposals_result:
        form_data = json.loads(row.form_data) if row.form_data else {}
        sections = json.loads(row.generated_sections) if row.generated_sections else {}
        field_contexts = row.field_contexts.split(',') if row.field_contexts else []

        review_list.append(ProposalOut(
            proposal_id=str(row.id),
            project_title=form_data.get("Project title", "Untitled Proposal"),
            summary=sections.get("Summary", ""),
            created_at=row.created_at,
            updated_at=row.updated_at,
            is_accepted=row.is_accepted,
            status=row.status,
            field_contexts=field_contexts,
            donors=donors_map.get(row.id, []),
            outcomes=outcomes_map.get(row.id, [])
        ))
    return review_list

@router.post("/proposals/{proposal_id}/submit-for-review")
async def submit_for_review(proposal_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user["user_id"]
    with db.begin():
        result = db.execute(
            update(proposals).where(proposals.c.id == proposal_id, proposals.c.user_id == user_id).values(status='review')
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Proposal not found or you don't have permission to edit it.")
    return {"message": "Proposal submitted for review.", "proposal_id": proposal_id}
