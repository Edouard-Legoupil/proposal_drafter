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
from backend.core.exceptions import ProposalNotFound, PermissionDenied
from backend.utils.crew_actions import handle_text_format, handle_fixed_text_format, handle_number_format, handle_table_format
from backend.models.schemas import (
    SectionRequest,
    RegenerateRequest,
    SaveDraftRequest,
    FinalizeProposalRequest,
    CreateSessionRequest,
    UpdateSectionRequest,
    UpdateProposalStatusRequest,
    TransferOwnershipRequest,
    SaveContributionIdRequest
)
from backend.utils.proposal_logic import regenerate_section_logic
from backend.utils.crew_proposal  import ProposalCrew
from backend.api.knowledge import _save_knowledge_card_content_to_file
from backend.repository.proposal_repository import ProposalRepository

# This router handles all endpoints related to the lifecycle of a proposal,
# from creation and editing to listing and deletion.
router = APIRouter()

# Configure logging
logger = logging.getLogger(__name__)

proposal_repository = ProposalRepository()

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
        # Get the available templates and determine which one to use based on the donor.
        templates_map = get_available_templates()
        donor_id = request.form_data.get("Targeted Donor")
        template_name = "proposal_template_unhcr.json"  # Default template

        if donor_id:
            donor_name = proposal_repository.get_donor_name_by_id(donor_id)
            if donor_name:
                template_name = templates_map.get(donor_name, "proposal_template_unhcr.json")

        # Create the proposal and its initial status history.
        proposal_repository.create_proposal(proposal_id, user_id, request.form_data, request.project_description, template_name)
        proposal_repository.create_proposal_status_history(proposal_id, "draft")

        # Create the proposal's associations with other entities.
        outcome_ids = request.form_data.get("Main Outcome", [])
        field_context_id = request.form_data.get("Country / Location(s)") or request.form_data.get("Geographical Scope")

        if donor_id:
            proposal_repository.create_proposal_donor(proposal_id, donor_id)

        if outcome_ids and isinstance(outcome_ids, list):
            for outcome_id in outcome_ids:
                if outcome_id:
                    proposal_repository.create_proposal_outcome(proposal_id, outcome_id)

        if field_context_id:
            proposal_repository.create_proposal_field_context(proposal_id, field_context_id)


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
