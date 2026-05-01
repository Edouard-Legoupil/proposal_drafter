"""
SharePoint API Endpoints
========================

This module provides API endpoints for SharePoint integration, including:
- Uploading documents to SharePoint
- Getting SharePoint file URLs for Word Online viewing
"""

import io
import logging
import os
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy import text

from backend.core.db import get_engine
from backend.core.security import get_current_user
from backend.utils.sharepoint_connector import SharePointConnector

router = APIRouter()
logger = logging.getLogger(__name__)


# Initialize SharePoint connector (will be lazily initialized on first use)
_sharepoint_connector: Optional[SharePointConnector] = None


def get_sharepoint_connector() -> SharePointConnector:
    """
    Get or create the SharePoint connector instance.
    
    Returns:
        SharePointConnector: Connected SharePoint connector instance.
    """
    global _sharepoint_connector
    if _sharepoint_connector is None:
        try:
            _sharepoint_connector = SharePointConnector()
            _sharepoint_connector.connect()
            logger.info("SharePoint connector initialized")
        except Exception as e:
            logger.error(f"Failed to initialize SharePoint connector: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"SharePoint connection failed: {str(e)}"
            )
    return _sharepoint_connector


@router.post("/upload-to-sharepoint/")
async def upload_document_to_sharepoint(
    file: UploadFile = File(...),
    folder_path: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
) -> JSONResponse:
    """
    Upload a document to SharePoint and return the URL for Word Online viewing.
    
    Args:
        file: The document file to upload (DOCX format expected)
        folder_path: Optional SharePoint folder path (uses default from config if not provided)
        current_user: Authenticated user information
    
    Returns:
        JSONResponse: Contains the SharePoint URL for the uploaded file
    
    Raises:
        HTTPException: If upload fails or SharePoint is not configured
    """
    try:
        # Validate file is a DOCX
        if not file.filename.lower().endswith('.docx'):
            raise HTTPException(
                status_code=400,
                detail="Only DOCX files are supported for SharePoint upload"
            )
        
        # Get the connector
        connector = get_sharepoint_connector()
        
        # Read the file content
        content = await file.read()
        
        # Generate a unique filename
        # Use original filename or generate one
        filename = file.filename
        
        # Upload to SharePoint
        connector.upload_file(filename, content, folder_path)
        
        # Get the file metadata to retrieve the web URL
        metadata = connector.get_file_metadata(filename, folder_path)
        web_url = metadata.get('webUrl')
        
        if not web_url:
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve SharePoint file URL"
            )
        
        # Convert to Word Online URL
        # SharePoint web URLs can be opened directly in Word Online
        word_online_url = web_url
        
        logger.info(f"Document uploaded to SharePoint: {word_online_url}")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "url": word_online_url,
                "filename": filename,
                "message": "Document uploaded successfully"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading to SharePoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload document to SharePoint: {str(e)}"
        )


@router.post("/upload-proposal-to-sharepoint/{proposal_id}")
async def upload_proposal_to_sharepoint(
    proposal_id: str,
    format: str = "docx",
    folder_path: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
) -> JSONResponse:
    """
    Generate a proposal document and upload it to SharePoint.
    
    This endpoint:
    1. Generates the proposal document (DOCX or PDF)
    2. Uploads it to SharePoint
    3. Returns the SharePoint URL for Word Online viewing
    
    Args:
        proposal_id: The ID of the proposal to generate
        format: Document format ('docx' or 'pdf')
        folder_path: Optional SharePoint folder path
        current_user: Authenticated user information
    
    Returns:
        JSONResponse: Contains the SharePoint URL for the uploaded file
    """
    from backend.utils.doc_export import create_word_from_sections, create_pdf_from_sections
    from backend.core.config import load_proposal_template
    
    try:
        # Validate UUID
        try:
            UUID(proposal_id)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid proposal_id: {proposal_id}")
        
        user_id = current_user["user_id"]
        
        # Fetch the proposal data from the database
        with get_engine().connect() as connection:
            result = connection.execute(
                text("""
                    SELECT form_data, project_description, generated_sections, template_name
                    FROM proposals
                    WHERE id = :proposal_id AND user_id = :user_id
                """),
                {"proposal_id": proposal_id, "user_id": user_id}
            )
            draft = result.fetchone()
        
        if not draft:
            raise HTTPException(status_code=404, detail="Proposal not found for this user.")
        
        form_data, _, generated_sections, template_name = draft
        form_data = form_data if isinstance(form_data, dict) else {}
        generated_sections = generated_sections if isinstance(generated_sections, dict) else {}
        
        # Resolve UUIDs to names
        with get_engine().connect() as connection:
            if form_data.get("Targeted Donor"):
                donor_id = form_data["Targeted Donor"]
                donor_name = connection.execute(
                    text("SELECT name FROM donors WHERE id = :id"), 
                    {"id": donor_id}
                ).scalar()
                form_data["Targeted Donor"] = donor_name or form_data["Targeted Donor"]
            
            if form_data.get("Main Outcome"):
                outcome_ids = form_data["Main Outcome"]
                if outcome_ids:
                    outcome_uuids = [UUID(oid) for oid in outcome_ids]
                    outcome_names = connection.execute(
                        text("SELECT name FROM outcomes WHERE id = ANY(:ids)"), 
                        {"ids": outcome_uuids}
                    ).scalars().all()
                    form_data["Main Outcome"] = ", ".join(outcome_names) if outcome_names else form_data["Main Outcome"]
            
            if form_data.get("Country / Location(s)"):
                fc_id = form_data["Country / Location(s)"]
                fc_name = connection.execute(
                    text("SELECT name FROM field_contexts WHERE id = :id"), 
                    {"id": fc_id}
                ).scalar()
                form_data["Country / Location(s)"] = fc_name or form_data["Country / Location(s)"]
        
        # Load the template
        if not template_name:
            template_name = "proposal_template_unhcr.json"
            logger.warning(f"Proposal {proposal_id} has no template_name, falling back to default.")
        
        proposal_template = load_proposal_template(template_name)
        template_sections = [s.get("section_name") for s in proposal_template.get("sections", [])]
        ordered_sections = {section: generated_sections.get(section, "") for section in template_sections}
        
        # Generate filename
        from slugify import slugify
        project_title = form_data.get("Project Draft Short name") or form_data.get("Project title", "Untitled Proposal")
        sanitized_filename = slugify(project_title)
        
        # Generate document
        if format == "pdf":
            buffer = io.BytesIO(create_pdf_from_sections(form_data, ordered_sections))
            filename = f"{sanitized_filename}.pdf"
        else:
            doc = create_word_from_sections(form_data, proposal_template, ordered_sections)
            buffer = io.BytesIO()
            doc.save(buffer)
            buffer.seek(0)
            filename = f"{sanitized_filename}.docx"
        
        # Get SharePoint connector
        connector = get_sharepoint_connector()
        
        # Upload to SharePoint
        content = buffer.getvalue()
        connector.upload_file(filename, content, folder_path)
        
        # Get the file metadata to retrieve the web URL
        metadata = connector.get_file_metadata(filename, folder_path)
        web_url = metadata.get('webUrl')
        
        if not web_url:
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve SharePoint file URL"
            )
        
        logger.info(f"Proposal uploaded to SharePoint: {web_url}")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "url": web_url,
                "filename": filename,
                "message": "Proposal uploaded to SharePoint successfully"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading proposal to SharePoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload proposal to SharePoint: {str(e)}"
        )


@router.post("/upload-knowledge-card-to-sharepoint/{card_id}")
async def upload_knowledge_card_to_sharepoint(
    card_id: str,
    format: str = "docx",
    folder_path: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
) -> JSONResponse:
    """
    Generate a knowledge card document and upload it to SharePoint.
    
    Args:
        card_id: The ID of the knowledge card
        format: Document format ('docx' or 'pdf')
        folder_path: Optional SharePoint folder path
        current_user: Authenticated user information
    
    Returns:
        JSONResponse: Contains the SharePoint URL for the uploaded file
    """
    import uuid
    from backend.utils.doc_export import create_word_from_sections, create_pdf_from_sections
    from backend.core.config import load_proposal_template
    
    try:
        # Validate UUID
        try:
            card_uuid = uuid.UUID(card_id)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid card_id: {card_id}")
        
        # Fetch the knowledge card data
        with get_engine().connect() as connection:
            result = connection.execute(
                text("""
                    SELECT
                        kc.id,
                        kc.summary,
                        kc.template_name,
                        kc.generated_sections,
                        kc.donor_id,
                        kc.outcome_id,
                        kc.field_context_id,
                        d.name as donor_name,
                        o.name as outcome_name,
                        fc.name as field_context_name
                    FROM
                        knowledge_cards kc
                    LEFT JOIN
                        donors d ON kc.donor_id = d.id
                    LEFT JOIN
                        outcomes o ON kc.outcome_id = o.id
                    LEFT JOIN
                        field_contexts fc ON kc.field_context_id = fc.id
                    WHERE
                        kc.id = :card_id
                """),
                {"card_id": card_uuid}
            )
            card = result.mappings().fetchone()
        
        if not card:
            raise HTTPException(status_code=404, detail="Knowledge card not found")
        
        card_dict = dict(card)
        generated_sections = card_dict.get("generated_sections") or {}
        
        # Build form data for template
        form_data = {
            "Targeted Donor": card_dict.get("donor_name"),
            "Main Outcome": card_dict.get("outcome_name"),
            "Country / Location(s)": card_dict.get("field_context_name"),
            "Project title": card_dict.get("summary", "Untitled Knowledge Card")
        }
        
        # Load the template
        template_name = card_dict.get("template_name") or "proposal_template_unhcr.json"
        proposal_template = load_proposal_template(template_name)
        template_sections = [s.get("section_name") for s in proposal_template.get("sections", [])]
        ordered_sections = {section: generated_sections.get(section, "") for section in template_sections}
        
        # Generate filename
        from slugify import slugify
        project_title = card_dict.get("summary", "Untitled Knowledge Card")
        sanitized_filename = slugify(project_title)
        
        # Generate document
        if format == "pdf":
            buffer = io.BytesIO(create_pdf_from_sections(form_data, ordered_sections))
            filename = f"{sanitized_filename}.pdf"
        else:
            doc = create_word_from_sections(form_data, proposal_template, ordered_sections)
            buffer = io.BytesIO()
            doc.save(buffer)
            buffer.seek(0)
            filename = f"{sanitized_filename}.docx"
        
        # Get SharePoint connector
        connector = get_sharepoint_connector()
        
        # Upload to SharePoint
        content = buffer.getvalue()
        connector.upload_file(filename, content, folder_path)
        
        # Get the file metadata to retrieve the web URL
        metadata = connector.get_file_metadata(filename, folder_path)
        web_url = metadata.get('webUrl')
        
        if not web_url:
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve SharePoint file URL"
            )
        
        logger.info(f"Knowledge card uploaded to SharePoint: {web_url}")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "url": web_url,
                "filename": filename,
                "message": "Knowledge card uploaded to SharePoint successfully"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading knowledge card to SharePoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload knowledge card to SharePoint: {str(e)}"
        )
