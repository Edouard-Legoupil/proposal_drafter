"""
SharePoint API Endpoints
========================

This module provides API endpoints for SharePoint integration, including:
- Uploading documents to SharePoint
- Getting SharePoint file URLs for Word Online viewing
- Storing and retrieving SharePoint links from the database
- Retry mechanism for failed uploads
"""

import io
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import JSONResponse
from sqlalchemy import text

from backend.core.db import get_engine
from backend.core.security import get_current_user
from backend.utils.sharepoint_connector import SharePointConnector

router = APIRouter()
logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 5
SHAREPOINT_URL_EXPIRY_HOURS = 24  # URLs are considered valid for 24 hours


# =============================================================================

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _normalize_expires_at(expires_at: Optional[Any]) -> Optional[datetime]:
    """Normalize expires_at value to a datetime object."""
    if expires_at is None:
        return None
    if isinstance(expires_at, datetime):
        # Strip timezone info if present to make it naive
        if hasattr(expires_at, 'tzinfo') and expires_at.tzinfo is not None:
            return expires_at.replace(tzinfo=None)
        return expires_at
    if isinstance(expires_at, str):
        try:
            return datetime.fromisoformat(expires_at.replace('T', ' ').replace('Z', ''))
        except ValueError:
            return datetime.fromisoformat(expires_at)
    return None


def _serialize_datetime_for_json(dt: Optional[Any]) -> Optional[str]:
    """Serialize a datetime object to an ISO format string for JSON."""
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt.isoformat()
    return dt

# SHAREPOINT CONNECTOR MANAGEMENT
# =============================================================================

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


def log_upload_event(
    event_type: str,
    artifact_type: str,
    artifact_id: UUID,
    user_id: UUID,
    sharepoint_link_id: Optional[UUID] = None,
    status: Optional[str] = None,
    error_type: Optional[str] = None,
    error_message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a SharePoint upload event to the database.
    
    Args:
        event_type: Type of event (upload_started, upload_success, upload_failed, etc.)
        artifact_type: Type of artifact (proposal, knowledge_card)
        artifact_id: ID of the artifact
        user_id: ID of the user
        sharepoint_link_id: Optional ID of the SharePoint link record
        status: Optional status
        error_type: Optional error type
        error_message: Optional error message
        metadata: Optional additional metadata
    """
    try:
        with get_engine().connect() as connection:
            connection.execute(
                text("""
                    INSERT INTO sharepoint_upload_events 
                    (event_type, artifact_type, artifact_id, user_id, sharepoint_link_id, 
                     status, error_type, error_message, metadata)
                    VALUES (:event_type, :artifact_type, :artifact_id, :user_id, :sharepoint_link_id,
                            :status, :error_type, :error_message, :metadata)
                """),
                {
                    "event_type": event_type,
                    "artifact_type": artifact_type,
                    "artifact_id": artifact_id,
                    "user_id": user_id,
                    "sharepoint_link_id": sharepoint_link_id,
                    "status": status,
                    "error_type": error_type,
                    "error_message": error_message,
                    "metadata": json.dumps(metadata) if metadata else None
                }
            )
            connection.commit()
    except Exception as e:
        logger.error(f"Failed to log SharePoint event: {e}")


# =============================================================================
# DATABASE HELPER FUNCTIONS
# =============================================================================

def get_existing_link(artifact_type: str, artifact_id: UUID, user_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Get an existing SharePoint link for an artifact and user.
    
    Args:
        artifact_type: 'proposal' or 'knowledge_card'
        artifact_id: The artifact ID
        user_id: The user ID
    
    Returns:
        Dictionary with link information or None if not found
    """
    try:
        table_map = {
            'proposal': 'proposal_sharepoint_links',
            'knowledge_card': 'knowledge_card_sharepoint_links'
        }
        
        if artifact_type not in table_map:
            return None
        
        table = table_map[artifact_type]
        id_column = f"{artifact_type}_id"
        
        with get_engine().connect() as connection:
            result = connection.execute(
                text(f"""
                    SELECT id, sharepoint_url, filename, folder_path, status, 
                           error_type, error_message, retry_count, uploaded_at, expires_at
                    FROM {table}
                    WHERE {id_column} = :artifact_id AND user_id = :user_id
                    ORDER BY created_at DESC
                    LIMIT 1
                """),
                {"artifact_id": artifact_id, "user_id": user_id}
            )
            row = result.fetchone()
            
            if row:
                return dict(row._mapping) if hasattr(row, '_mapping') else dict(row)
            return None
    except Exception as e:
        logger.error(f"Error fetching existing link: {e}")
        return None


def save_sharepoint_link(
    artifact_type: str,
    artifact_id: UUID,
    user_id: UUID,
    sharepoint_url: str,
    filename: str,
    folder_path: Optional[str] = None,
    file_id: Optional[str] = None,
    file_version: Optional[str] = None,
    status: str = 'uploaded'
) -> UUID:
    """
    Save a SharePoint link to the database.
    
    Args:
        artifact_type: 'proposal' or 'knowledge_card'
        artifact_id: The artifact ID
        user_id: The user ID
        sharepoint_url: The SharePoint URL
        filename: The filename
        folder_path: Optional folder path
        file_id: Optional SharePoint file ID
        file_version: Optional file version
        status: Link status
    
    Returns:
        The ID of the created link record
    """
    try:
        table_map = {
            'proposal': 'proposal_sharepoint_links',
            'knowledge_card': 'knowledge_card_sharepoint_links'
        }
        
        if artifact_type not in table_map:
            raise ValueError(f"Invalid artifact type: {artifact_type}")
        
        table = table_map[artifact_type]
        id_column = f"{artifact_type}_id"
        
        with get_engine().connect() as connection:
            result = connection.execute(
                text(f"""
                    INSERT INTO {table} 
                    ({id_column}, user_id, sharepoint_url, filename, folder_path, 
                     file_id, file_version, status, uploaded_at, expires_at)
                    VALUES (:artifact_id, :user_id, :sharepoint_url, :filename, :folder_path,
                            :file_id, :file_version, :status, CURRENT_TIMESTAMP, 
                            CURRENT_TIMESTAMP + INTERVAL '24 hours')
                    ON CONFLICT ({id_column}, user_id)
                    DO UPDATE SET
                        sharepoint_url = EXCLUDED.sharepoint_url,
                        filename = EXCLUDED.filename,
                        folder_path = EXCLUDED.folder_path,
                        file_id = EXCLUDED.file_id,
                        file_version = EXCLUDED.file_version,
                        status = EXCLUDED.status,
                        error_type = NULL,
                        error_message = NULL,
                        retry_count = 0,
                        uploaded_at = CURRENT_TIMESTAMP,
                        expires_at = CURRENT_TIMESTAMP + INTERVAL '24 hours',
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING id
                """),
                {
                    "artifact_id": artifact_id,
                    "user_id": user_id,
                    "sharepoint_url": sharepoint_url,
                    "filename": filename,
                    "folder_path": folder_path,
                    "file_id": file_id,
                    "file_version": file_version,
                    "status": status
                }
            )
            link_id = result.fetchone()[0]
            connection.commit()
            return link_id
    except Exception as e:
        logger.error(f"Error saving SharePoint link: {e}")
        raise


def update_sharepoint_link_status(
    artifact_type: str,
    link_id: UUID,
    status: str,
    error_type: Optional[str] = None,
    error_message: Optional[str] = None,
    retry_count: Optional[int] = None
) -> None:
    """
    Update the status of a SharePoint link.
    
    Args:
        artifact_type: 'proposal' or 'knowledge_card'
        link_id: The link record ID
        status: New status
        error_type: Optional error type
        error_message: Optional error message
        retry_count: Optional retry count
    """
    try:
        table_map = {
            'proposal': 'proposal_sharepoint_links',
            'knowledge_card': 'knowledge_card_sharepoint_links'
        }
        
        if artifact_type not in table_map:
            return
        
        table = table_map[artifact_type]
        
        with get_engine().connect() as connection:
            connection.execute(
                text(f"""
                    UPDATE {table}
                    SET status = :status,
                        error_type = :error_type,
                        error_message = :error_message,
                        retry_count = COALESCE(:retry_count, retry_count),
                        last_attempt_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = :link_id
                """),
                {
                    "status": status,
                    "error_type": error_type,
                    "error_message": error_message,
                    "retry_count": retry_count,
                    "link_id": link_id
                }
            )
            connection.commit()
    except Exception as e:
        logger.error(f"Error updating SharePoint link status: {e}")


# =============================================================================
# UPLOAD ENDPOINTS
# =============================================================================

@router.post("/upload-to-sharepoint/")
async def upload_document_to_sharepoint(
    file: UploadFile = File(...),
    folder_path: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
) -> JSONResponse:
    """
    Upload a document to SharePoint and return the URL for Word Online viewing.
    
    This is a general endpoint for uploading any document file to SharePoint.
    
    Args:
        file: The document file to upload (DOCX format expected)
        folder_path: Optional SharePoint folder path (uses default from config if not provided)
        current_user: Authenticated user information
    
    Returns:
        JSONResponse: Contains the SharePoint URL for the uploaded file
    
    Raises:
        HTTPException: If upload fails or SharePoint is not configured
    """
    user_id = current_user["user_id"]
    
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
        filename = file.filename
        
        # Log upload started
        log_upload_event(
            event_type='upload_started',
            artifact_type='document',
            artifact_id=UUID('00000000-0000-0000-0000-000000000000'),  # Not applicable for direct uploads
            user_id=user_id,
            status='uploading',
            metadata={'filename': filename, 'size': len(content)}
        )
        
        # Upload to SharePoint
        connector.upload_file(filename, content, folder_path)
        
        # Get the file metadata to retrieve the web URL
        metadata = connector.get_file_metadata(filename, folder_path)
        web_url = metadata.get('webUrl')
        file_id = metadata.get('id')
        file_version = metadata.get('version')
        
        if not web_url:
            error_msg = "Failed to retrieve SharePoint file URL"
            log_upload_event(
                event_type='upload_failed',
                artifact_type='document',
                artifact_id=UUID('00000000-0000-0000-0000-000000000000'),
                user_id=user_id,
                status='failed',
                error_type='metadata_error',
                error_message=error_msg
            )
            raise HTTPException(status_code=500, detail=error_msg)
        
        # Log success
        log_upload_event(
            event_type='upload_success',
            artifact_type='document',
            artifact_id=UUID('00000000-0000-0000-0000-000000000000'),
            user_id=user_id,
            status='uploaded',
            metadata={'url': web_url, 'file_id': file_id}
        )
        
        logger.info(f"Document uploaded to SharePoint: {web_url}")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "url": web_url,
                "filename": filename,
                "file_id": file_id,
                "file_version": file_version,
                "message": "Document uploaded successfully"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading to SharePoint: {e}", exc_info=True)
        log_upload_event(
            event_type='upload_failed',
            artifact_type='document',
            artifact_id=UUID('00000000-0000-0000-0000-000000000000'),
            user_id=user_id,
            status='failed',
            error_type='upload_error',
            error_message=str(e)
        )
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
    1. Checks if a valid SharePoint link already exists for this proposal/user
    2. If exists and valid, returns the existing URL
    3. If exists but needs retry, attempts to re-upload
    4. Otherwise, generates and uploads a new document
    5. Stores the link in the database
    6. Returns the SharePoint URL for Word Online viewing
    
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
    from slugify import slugify
    
    user_id = current_user["user_id"]
    
    try:
        # Validate UUID
        try:
            proposal_uuid = UUID(proposal_id)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid proposal_id: {proposal_id}")
        
        # Check for existing link
        existing_link = get_existing_link('proposal', proposal_uuid, user_id)
        
        if existing_link:
            # If link exists and is uploaded, return it directly
            if existing_link['status'] == 'uploaded':
                # Check if URL is still valid (not expired)
                expires_at = existing_link.get('expires_at')
                expiry_dt = _normalize_expires_at(expires_at)
                if expiry_dt and expiry_dt > datetime.utcnow():
                    log_upload_event(
                        event_type='url_retrieved',
                        artifact_type='proposal',
                        artifact_id=proposal_uuid,
                        user_id=user_id,
                        sharepoint_link_id=existing_link['id'],
                        status='uploaded',
                        metadata={'url': existing_link['sharepoint_url']}
                    )
                    return JSONResponse(
                        status_code=200,
                        content={
                            "success": True,
                            "url": existing_link['sharepoint_url'],
                            "filename": existing_link['filename'],
                            "from_cache": True,
                            "message": "Using existing SharePoint link"
                        }
                    )
            
            # If link exists but needs retry, we'll try again
            if existing_link['status'] == 'failed' and existing_link.get('retry_count', 0) >= MAX_RETRY_ATTEMPTS:
                log_upload_event(
                    event_type='access_error',
                    artifact_type='proposal',
                    artifact_id=proposal_uuid,
                    user_id=user_id,
                    sharepoint_link_id=existing_link['id'],
                    status='failed',
                    error_type='max_retries_exceeded',
                    error_message=f"Max retry attempts ({MAX_RETRY_ATTEMPTS}) exceeded"
                )
                raise HTTPException(
                    status_code=429,
                    detail=f"Max retry attempts exceeded for this document. Please try again later."
                )
        
        # Log upload started
        log_upload_event(
            event_type='upload_started',
            artifact_type='proposal',
            artifact_id=proposal_uuid,
            user_id=user_id,
            status='uploading',
            metadata={'format': format}
        )
        
        # Fetch the proposal data from the database
        with get_engine().connect() as connection:
            result = connection.execute(
                text("""
                    SELECT form_data, project_description, generated_sections, template_name
                    FROM proposals
                    WHERE id = :proposal_id AND user_id = :user_id
                """),
                {"proposal_id": proposal_uuid, "user_id": user_id}
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
        
        try:
            # Upload to SharePoint
            content = buffer.getvalue()
            connector.upload_file(filename, content, folder_path)
            
            # Get the file metadata to retrieve the web URL
            metadata = connector.get_file_metadata(filename, folder_path)
            web_url = metadata.get('webUrl')
            file_id = metadata.get('id')
            file_version = metadata.get('version')
            
            if not web_url:
                error_msg = "Failed to retrieve SharePoint file URL"
                log_upload_event(
                    event_type='upload_failed',
                    artifact_type='proposal',
                    artifact_id=proposal_uuid,
                    user_id=user_id,
                    status='failed',
                    error_type='metadata_error',
                    error_message=error_msg
                )
                raise HTTPException(status_code=500, detail=error_msg)
            
            # Save the link to database
            if existing_link:
                link_id = existing_link['id']
                update_sharepoint_link_status(
                    'proposal',
                    link_id,
                    'uploaded',
                    retry_count=existing_link.get('retry_count', 0) + 1
                )
            else:
                link_id = save_sharepoint_link(
                    'proposal',
                    proposal_uuid,
                    user_id,
                    web_url,
                    filename,
                    folder_path,
                    file_id,
                    file_version,
                    'uploaded'
                )
            
            # Log success
            log_upload_event(
                event_type='upload_success',
                artifact_type='proposal',
                artifact_id=proposal_uuid,
                user_id=user_id,
                sharepoint_link_id=link_id,
                status='uploaded',
                metadata={'url': web_url, 'file_id': file_id}
            )
            
            logger.info(f"Proposal uploaded to SharePoint: {web_url}")
            
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "url": web_url,
                    "filename": filename,
                    "link_id": str(link_id),
                    "from_cache": False,
                    "message": "Proposal uploaded to SharePoint successfully"
                }
            )
        
        except Exception as upload_error:
            # Handle upload failure with retry logic
            error_type = 'upload_error'
            error_message = str(upload_error)
            
            # Determine if we should retry
            new_retry_count = (existing_link.get('retry_count', 0) if existing_link else 0) + 1
            should_retry = new_retry_count <= MAX_RETRY_ATTEMPTS
            
            if existing_link:
                update_sharepoint_link_status(
                    'proposal',
                    existing_link['id'],
                    'failed',
                    error_type,
                    error_message,
                    new_retry_count
                )
            
            log_upload_event(
                event_type='upload_failed',
                artifact_type='proposal',
                artifact_id=proposal_uuid,
                user_id=user_id,
                sharepoint_link_id=existing_link['id'] if existing_link else None,
                status='failed',
                error_type=error_type,
                error_message=error_message
            )
            
            if should_retry:
                logger.warning(f"SharePoint upload failed for proposal {proposal_id}, retry {new_retry_count}/{MAX_RETRY_ATTEMPTS}")
                raise HTTPException(
                    status_code=503,
                    detail=f"Upload failed but will retry. Attempt {new_retry_count}/{MAX_RETRY_ATTEMPTS}. Error: {error_message}"
                )
            else:
                logger.error(f"SharePoint upload permanently failed for proposal {proposal_id}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to upload proposal to SharePoint after {MAX_RETRY_ATTEMPTS} attempts: {error_message}"
                )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading proposal to SharePoint: {e}", exc_info=True)
        log_upload_event(
            event_type='upload_failed',
            artifact_type='proposal',
            artifact_id=proposal_uuid,
            user_id=user_id,
            status='failed',
            error_type='unknown_error',
            error_message=str(e)
        )
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
    
    This endpoint:
    1. Checks if a valid SharePoint link already exists for this card/user
    2. If exists and valid, returns the existing URL
    3. If exists but needs retry, attempts to re-upload
    4. Otherwise, generates and uploads a new document
    5. Stores the link in the database
    6. Returns the SharePoint URL for Word Online viewing
    
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
    from slugify import slugify
    
    user_id = current_user["user_id"]
    
    try:
        # Validate UUID
        try:
            card_uuid = uuid.UUID(card_id)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid card_id: {card_id}")
        
        # Check for existing link
        existing_link = get_existing_link('knowledge_card', card_uuid, user_id)
        
        if existing_link:
            # If link exists and is uploaded, return it directly
            if existing_link['status'] == 'uploaded':
                # Check if URL is still valid (not expired)
                expires_at = existing_link.get('expires_at')
                expiry_dt = _normalize_expires_at(expires_at)
                if expiry_dt and expiry_dt > datetime.utcnow():
                    log_upload_event(
                        event_type='url_retrieved',
                        artifact_type='knowledge_card',
                        artifact_id=card_uuid,
                        user_id=user_id,
                        sharepoint_link_id=existing_link['id'],
                        status='uploaded',
                        metadata={'url': existing_link['sharepoint_url']}
                    )
                    return JSONResponse(
                        status_code=200,
                        content={
                            "success": True,
                            "url": existing_link['sharepoint_url'],
                            "filename": existing_link['filename'],
                            "from_cache": True,
                            "message": "Using existing SharePoint link"
                        }
                    )
            
            # If link exists but needs retry, we'll try again
            if existing_link['status'] == 'failed' and existing_link.get('retry_count', 0) >= MAX_RETRY_ATTEMPTS:
                log_upload_event(
                    event_type='access_error',
                    artifact_type='knowledge_card',
                    artifact_id=card_uuid,
                    user_id=user_id,
                    sharepoint_link_id=existing_link['id'],
                    status='failed',
                    error_type='max_retries_exceeded',
                    error_message=f"Max retry attempts ({MAX_RETRY_ATTEMPTS}) exceeded"
                )
                raise HTTPException(
                    status_code=429,
                    detail=f"Max retry attempts exceeded for this document. Please try again later."
                )
        
        # Log upload started
        log_upload_event(
            event_type='upload_started',
            artifact_type='knowledge_card',
            artifact_id=card_uuid,
            user_id=user_id,
            status='uploading',
            metadata={'format': format}
        )
        
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
        
        try:
            # Upload to SharePoint
            content = buffer.getvalue()
            connector.upload_file(filename, content, folder_path)
            
            # Get the file metadata to retrieve the web URL
            metadata = connector.get_file_metadata(filename, folder_path)
            web_url = metadata.get('webUrl')
            file_id = metadata.get('id')
            file_version = metadata.get('version')
            
            if not web_url:
                error_msg = "Failed to retrieve SharePoint file URL"
                log_upload_event(
                    event_type='upload_failed',
                    artifact_type='knowledge_card',
                    artifact_id=card_uuid,
                    user_id=user_id,
                    status='failed',
                    error_type='metadata_error',
                    error_message=error_msg
                )
                raise HTTPException(status_code=500, detail=error_msg)
            
            # Save the link to database
            if existing_link:
                link_id = existing_link['id']
                update_sharepoint_link_status(
                    'knowledge_card',
                    link_id,
                    'uploaded',
                    retry_count=existing_link.get('retry_count', 0) + 1
                )
            else:
                link_id = save_sharepoint_link(
                    'knowledge_card',
                    card_uuid,
                    user_id,
                    web_url,
                    filename,
                    folder_path,
                    file_id,
                    file_version,
                    'uploaded'
                )
            
            # Log success
            log_upload_event(
                event_type='upload_success',
                artifact_type='knowledge_card',
                artifact_id=card_uuid,
                user_id=user_id,
                sharepoint_link_id=link_id,
                status='uploaded',
                metadata={'url': web_url, 'file_id': file_id}
            )
            
            logger.info(f"Knowledge card uploaded to SharePoint: {web_url}")
            
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "url": web_url,
                    "filename": filename,
                    "link_id": str(link_id),
                    "from_cache": False,
                    "message": "Knowledge card uploaded to SharePoint successfully"
                }
            )
        
        except Exception as upload_error:
            # Handle upload failure with retry logic
            error_type = 'upload_error'
            error_message = str(upload_error)
            
            # Determine if we should retry
            new_retry_count = (existing_link.get('retry_count', 0) if existing_link else 0) + 1
            should_retry = new_retry_count <= MAX_RETRY_ATTEMPTS
            
            if existing_link:
                update_sharepoint_link_status(
                    'knowledge_card',
                    existing_link['id'],
                    'failed',
                    error_type,
                    error_message,
                    new_retry_count
                )
            
            log_upload_event(
                event_type='upload_failed',
                artifact_type='knowledge_card',
                artifact_id=card_uuid,
                user_id=user_id,
                sharepoint_link_id=existing_link['id'] if existing_link else None,
                status='failed',
                error_type=error_type,
                error_message=error_message
            )
            
            if should_retry:
                logger.warning(f"SharePoint upload failed for knowledge card {card_id}, retry {new_retry_count}/{MAX_RETRY_ATTEMPTS}")
                raise HTTPException(
                    status_code=503,
                    detail=f"Upload failed but will retry. Attempt {new_retry_count}/{MAX_RETRY_ATTEMPTS}. Error: {error_message}"
                )
            else:
                logger.error(f"SharePoint upload permanently failed for knowledge card {card_id}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to upload knowledge card to SharePoint after {MAX_RETRY_ATTEMPTS} attempts: {error_message}"
                )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading knowledge card to SharePoint: {e}", exc_info=True)
        log_upload_event(
            event_type='upload_failed',
            artifact_type='knowledge_card',
            artifact_id=card_uuid,
            user_id=user_id,
            status='failed',
            error_type='unknown_error',
            error_message=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload knowledge card to SharePoint: {str(e)}"
        )


# =============================================================================
# RETRY ENDPOINT
# =============================================================================

@router.post("/retry-sharepoint-upload/{artifact_type}/{artifact_id}")
async def retry_sharepoint_upload(
    artifact_type: str,
    artifact_id: str,
    current_user: dict = Depends(get_current_user)
) -> JSONResponse:
    """
    Retry a failed SharePoint upload.
    
    This endpoint allows manual retry of a failed SharePoint upload attempt.
    It will attempt to re-upload the document and update the link status.
    
    Args:
        artifact_type: 'proposal' or 'knowledge_card'
        artifact_id: The ID of the artifact
        current_user: Authenticated user information
    
    Returns:
        JSONResponse: Contains the status and potentially a new URL
    """
    user_id = current_user["user_id"]
    
    if artifact_type not in ['proposal', 'knowledge_card']:
        raise HTTPException(status_code=400, detail=f"Invalid artifact_type: {artifact_type}")
    
    try:
        artifact_uuid = UUID(artifact_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid artifact_id: {artifact_id}")
    
    # Get existing link
    existing_link = get_existing_link(artifact_type, artifact_uuid, user_id)
    
    if not existing_link:
        raise HTTPException(
            status_code=404,
            detail=f"No SharePoint link found for {artifact_type} {artifact_id} and user {user_id}"
        )
    
    if existing_link['status'] != 'failed':
        raise HTTPException(
            status_code=400,
            detail=f"Link is not in failed state (current: {existing_link['status']})"
        )
    
    if existing_link.get('retry_count', 0) >= MAX_RETRY_ATTEMPTS:
        raise HTTPException(
            status_code=429,
            detail=f"Max retry attempts ({MAX_RETRY_ATTEMPTS}) already reached"
        )
    
    # Log retry attempt
    log_upload_event(
        event_type='retry_attempt',
        artifact_type=artifact_type,
        artifact_id=artifact_uuid,
        user_id=user_id,
        sharepoint_link_id=existing_link['id'],
        status='uploading',
        metadata={'previous_error': existing_link.get('error_message')}
    )
    
    # Update status to uploading
    update_sharepoint_link_status(
        artifact_type,
        existing_link['id'],
        'uploading',
        retry_count=existing_link.get('retry_count', 0) + 1
    )
    
    # Call the appropriate upload endpoint based on artifact type
    if artifact_type == 'proposal':
        # Forward to proposal upload
        from fastapi import Request
        # We need to regenerate the document, so call the upload endpoint
        return await upload_proposal_to_sharepoint(
            proposal_id=str(artifact_uuid),
            format="docx",
            folder_path=existing_link.get('folder_path'),
            current_user=current_user
        )
    else:  # knowledge_card
        return await upload_knowledge_card_to_sharepoint(
            card_id=str(artifact_uuid),
            format="docx",
            folder_path=existing_link.get('folder_path'),
            current_user=current_user
        )


# =============================================================================
# STATUS CHECK ENDPOINT
# =============================================================================

@router.get("/sharepoint-link-status/{artifact_type}/{artifact_id}")
async def get_sharepoint_link_status(
    artifact_type: str,
    artifact_id: str,
    current_user: dict = Depends(get_current_user)
) -> JSONResponse:
    """
    Get the status of a SharePoint link for an artifact.
    
    Args:
        artifact_type: 'proposal' or 'knowledge_card'
        artifact_id: The ID of the artifact
        current_user: Authenticated user information
    
    Returns:
        JSONResponse: Contains the link status and information
    """
    user_id = current_user["user_id"]
    
    if artifact_type not in ['proposal', 'knowledge_card']:
        raise HTTPException(status_code=400, detail=f"Invalid artifact_type: {artifact_type}")
    
    try:
        artifact_uuid = UUID(artifact_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid artifact_id: {artifact_id}")
    
    existing_link = get_existing_link(artifact_type, artifact_uuid, user_id)
    
    if not existing_link:
        return JSONResponse(
            status_code=200,
            content={
                "has_link": False,
                "status": None,
                "message": "No SharePoint link found"
            }
        )
    
    # Check if expired
    expires_at = existing_link.get('expires_at')
    expiry_dt = _normalize_expires_at(expires_at)
    is_expired = expiry_dt and expiry_dt <= datetime.utcnow()
    
    return JSONResponse(
        status_code=200,
        content={
            "has_link": True,
            "link_id": str(existing_link['id']),
            "url": existing_link['sharepoint_url'],
            "filename": existing_link['filename'],
            "status": existing_link['status'],
            "error_type": existing_link.get('error_type'),
            "error_message": existing_link.get('error_message'),
            "retry_count": existing_link.get('retry_count', 0),
            "uploaded_at": _serialize_datetime_for_json(existing_link.get('uploaded_at')),
            "expires_at": _serialize_datetime_for_json(existing_link.get('expires_at')),
            "is_expired": is_expired,
            "can_retry": existing_link['status'] == 'failed' and existing_link.get('retry_count', 0) < MAX_RETRY_ATTEMPTS,
            "max_retries": MAX_RETRY_ATTEMPTS
        }
    )
