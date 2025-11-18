#  Standard Library
import uuid
from typing import Optional

#  Third-Party Libraries
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

#  Internal Modules
from backend.core.db import get_engine
from backend.core.security import get_current_user
from backend.core.config import get_available_templates, load_proposal_template
from backend.models.schemas import (
    CreateDonorRequest,
    CreateOutcomeRequest,
    CreateFieldContextRequest
)
import logging

from backend.repository.proposal_meta_repository import ProposalMetaRepository

logger = logging.getLogger(__name__)

router = APIRouter()

proposal_meta_repository = ProposalMetaRepository()

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

@router.get("/donors")
async def get_donors():
    """
    Fetches all donors from the database.
    """
    try:
        donors = proposal_meta_repository.get_donors()
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
        outcomes = proposal_meta_repository.get_outcomes()
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
        field_contexts = proposal_meta_repository.get_field_contexts(geographic_coverage)
        return {"field_contexts": field_contexts}
    except Exception as e:
        logger.error(f"[GET FIELD CONTEXTS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch field contexts.")

@router.post("/donors", status_code=201)
async def create_donor(request: CreateDonorRequest, current_user: dict = Depends(get_current_user)):
    """
    Creates a new donor.
    """
    try:
        new_id = proposal_meta_repository.create_donor(request.name, current_user["user_id"])
        return {"id": str(new_id), "name": request.name}
    except Exception as e:
        logger.error(f"[CREATE DONOR ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create donor.")

@router.post("/outcomes", status_code=201)
async def create_outcome(request: CreateOutcomeRequest, current_user: dict = Depends(get_current_user)):
    """
    Creates a new outcome.
    """
    try:
        new_id = proposal_meta_repository.create_outcome(request.name, current_user["user_id"])
        return {"id": str(new_id), "name": request.name}
    except Exception as e:
        logger.error(f"[CREATE OUTCOME ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create outcome.")

@router.post("/field-contexts", status_code=201)
async def create_field_context(request: CreateFieldContextRequest, current_user: dict = Depends(get_current_user)):
    """
    Creates a new field context.
    """
    try:
        new_id = proposal_meta_repository.create_field_context(request.name, request.category, request.geographic_coverage, current_user["user_id"])
        return {"id": str(new_id), "name": request.name, "geographic_coverage": request.geographic_coverage}
    except Exception as e:
        logger.error(f"[CREATE FIELD CONTEXT ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create field context.")
