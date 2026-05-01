from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Optional, Dict, Any
import uuid
import logging

from backend.core.security import get_current_user
from backend.models.template_models import (
    TemplateCreate,
    TemplateUpdate,
    TemplateVersionCreate,
    TemplateVersionUpdate,
    TemplateResponse,
    TemplateVersionResponse,
    TemplateFullResponse
)
from backend.services.template_service import TemplateService
from backend.core.db import get_engine

router = APIRouter()
logger = logging.getLogger(__name__)


def get_template_service():
    """Dependency to get template service"""
    engine = get_engine()
    return TemplateService(engine)


@router.get("/templates", response_model=List[TemplateResponse])
async def get_all_templates(
    current_user: uuid.UUID = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service)
):
    """Get all templates with summary information"""
    try:
        templates = await service.get_all_templates()
        return templates
    except Exception as e:
        logger.error(f"Error getting templates: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving templates")


@router.get("/templates/{template_id}", response_model=TemplateFullResponse)
async def get_template_by_id(
    template_id: uuid.UUID,
    current_user: uuid.UUID = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service)
):
    """Get template by ID with full details"""
    try:
        template = await service.get_template_by_id(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        version = await service.get_active_template_version(template_id)
        donors = await service.get_template_donors(template_id)
        
        return {
            "template": template,
            "version": version,
            "template_data": version["template_data"] if version else None,
            "donors": donors
        }
    except Exception as e:
        logger.error(f"Error getting template: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving template")


@router.get("/templates/by-filename/{filename}", response_model=TemplateFullResponse)
async def get_template_by_filename(
    filename: str,
    current_user: uuid.UUID = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service)
):
    """Get template by filename (for backward compatibility)"""
    try:
        template_data = await service.get_template_by_filename(filename)
        if not template_data:
            raise HTTPException(status_code=404, detail="Template not found")
        
        template_id = template_data["id"]
        version = await service.get_active_template_version(template_id)
        donors = await service.get_template_donors(template_id)
        
        return {
            "template": template_data,
            "version": version,
            "template_data": version["template_data"] if version else None,
            "donors": donors
        }
    except Exception as e:
        logger.error(f"Error getting template by filename: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving template")


@router.post("/templates", response_model=Dict[str, Any])
async def create_template(
    template_data: TemplateCreate = Body(...),
    current_user: uuid.UUID = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service)
):
    """Create a new template"""
    try:
        result = await service.create_template(template_data, current_user)
        return {
            "message": "Template created successfully",
            "template": result["template"],
            "version": result["version"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        raise HTTPException(status_code=500, detail="Error creating template")


@router.put("/templates/{template_id}", response_model=TemplateResponse)
async def update_template_metadata(
    template_id: uuid.UUID,
    update_data: TemplateUpdate = Body(...),
    current_user: uuid.UUID = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service)
):
    """Update template metadata"""
    try:
        template = await service.update_template_metadata(template_id, update_data, current_user)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        return template
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating template: {e}")
        raise HTTPException(status_code=500, detail="Error updating template")


@router.post("/templates/{template_id}/versions", response_model=TemplateVersionResponse)
async def create_template_version(
    template_id: uuid.UUID,
    version_data: TemplateVersionCreate = Body(...),
    current_user: uuid.UUID = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service)
):
    """Create a new version of a template"""
    try:
        version = await service.create_template_version(template_id, version_data, current_user)
        return version
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating template version: {e}")
        raise HTTPException(status_code=500, detail="Error creating template version")


@router.get("/templates/{template_id}/versions", response_model=List[TemplateVersionResponse])
async def get_template_versions(
    template_id: uuid.UUID,
    current_user: uuid.UUID = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service)
):
    """Get all versions of a template"""
    try:
        # Implementation would go here
        # For now, return empty list as placeholder
        return []
    except Exception as e:
        logger.error(f"Error getting template versions: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving template versions")


@router.get("/templates/{template_id}/audit-log")
async def get_template_audit_log(
    template_id: uuid.UUID,
    current_user: uuid.UUID = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service)
):
    """Get audit log for a template"""
    try:
        # Implementation would go here
        # For now, return empty list as placeholder
        return []
    except Exception as e:
        logger.error(f"Error getting template audit log: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving audit log")