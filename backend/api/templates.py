from fastapi import APIRouter, Depends, HTTPException, Body, BackgroundTasks
from sqlalchemy import text
from typing import List, Optional, Dict, Any
import uuid
import json
import datetime
import time
import logging
import os

from backend.core.db import get_engine
from backend.core.security import get_current_user
from backend.core.config import (
    get_available_templates,
    load_proposal_template,
    TEMPLATES_DIR,
)
from backend.utils.incident_service import IncidentService
from backend.models.schemas import (
    DonorTemplateRequestCreate,
    DonorTemplateCommentCreate,
    DonorTemplateStatusUpdate,
    ArtifactType,
    AuthorResponseRequest,
)

router = APIRouter()
logger = logging.getLogger(__name__)


def _run_auto_analysis(artifact_type: ArtifactType, review_id: str):
    try:
        with get_engine().begin() as connection:
            service = IncidentService(connection)
            # 1. Immediate acknowledgment
            initial_msg = "Your feedback has been received and is currently being analyzed by our AI agents. A detailed response will follow shortly."
            service.repo.update_template_comment(
                review_id, initial_msg, "acknowledged", response_author="system"
            )

        # 2. Wait for 30 seconds
        time.sleep(30)

        # 3. Trigger full analysis
        with get_engine().begin() as connection:
            service = IncidentService(connection)
            service.auto_analyze_review(artifact_type, review_id)
    except Exception as e:
        logger.error(
            f"Background auto-analysis failed for {artifact_type}/{review_id}: {e}",
            exc_info=True,
        )


@router.get("/published/{template_name}")
async def get_published_template(
    template_name: str,
    current_user: dict = Depends(get_current_user),
    engine=Depends(get_engine),
):
    """
    Fetch the full content of a published JSON template.
    """
    try:
        template_data = load_proposal_template(template_name)

        # Also fetch comments for this published template
        with engine.connect() as connection:
            comments_query = text("""
                SELECT tc.*, u.name as user_name
                FROM donor_template_comments tc
                JOIN users u ON tc.user_id = u.id
                WHERE tc.template_name = :name
                ORDER BY tc.created_at ASC
            """)
            comments_result = (
                connection.execute(comments_query, {"name": template_name})
                .mappings()
                .fetchall()
            )
            comments = [
                {
                    "id": str(c["id"]),
                    "user": c["user_name"],
                    "text": c["comment_text"],
                    "section_name": c["section_name"],
                    "rating": c["rating"],
                    "severity": c["severity"],
                    "type_of_comment": c.get("type_of_comment", "Donor Template"),
                    "created_at": _to_iso(c["created_at"]),
                }
                for c in comments_result
            ]

            # Wrap in a structure that the frontend expects
            return {
                **template_data,
                "id": template_name,
                "name": template_data.get("template_name", template_name),
                "status": "published",
                "type": "file",
                "template_type": template_data.get("template_type", "Proposal"),
                "configuration": {
                    "instructions": template_data.get("special_requirements", {}).get(
                        "instructions", []
                    ),
                    "sections": template_data.get("sections", []),
                },
                "comments": comments,
            }
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(
            f"Error loading published template {template_name}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to load template content.")


@router.get("/{template_name}/sections")
async def get_template_sections(template_name: str):
    """
    Returns the list of sections for a given template.
    """
    try:
        proposal_template = load_proposal_template(template_name)
        return {"sections": proposal_template.get("sections", [])}
    except Exception as e:
        logger.error(f"Error loading sections for {template_name}: {e}")
        return {"sections": []}


def _to_iso(dt):
    if dt is None:
        return None
    if isinstance(dt, str):
        return dt
    return dt.isoformat()


def _parse_json(data):
    if data is None:
        return None
    if isinstance(data, (dict, list)):
        return data
    try:
        return json.loads(data)
    except:
        return data


@router.get("/")
async def list_templates(
    current_user: dict = Depends(get_current_user), engine=Depends(get_engine)
):
    """
    Returns all published templates from files and current requests from DB.
    """
    try:
        # File-based templates
        published = []
        seen_files = set()

        # Scan both directories for all JSON files
        dirs_to_scan = [
            os.path.join(TEMPLATES_DIR, "proposal_template"),
            os.path.join(TEMPLATES_DIR, "concept_note_template"),
        ]

        for scan_dir in dirs_to_scan:
            if not os.path.exists(scan_dir):
                continue
            for filename in os.listdir(scan_dir):
                if filename.endswith(".json") and filename not in seen_files:
                    seen_files.add(filename)
                    try:
                        t_data = load_proposal_template(filename)
                        t_type = t_data.get("template_type", "Proposal")
                        # Normalize type for frontend: 'proposal' or 'concept_note'
                        t_type_norm = t_type.lower().replace(" ", "_")

                        # Try to get a nice display name from the template itself
                        donor_display = (
                            " / ".join(t_data.get("donors", []))
                            if t_data.get("donors")
                            else filename
                        )

                        published.append(
                            {
                                "id": filename,
                                "name": f"Published: {donor_display}",
                                "status": "published",
                                "type": "file",
                                "template_type": t_type_norm,
                            }
                        )
                    except Exception as e:
                        logger.warning(f"Error indexing template file {filename}: {e}")

        # DB-based requests (update query to include donor_ids and template_type)
        with engine.connect() as connection:
            query = text("""
                SELECT tr.id, tr.name, tr.status, tr.created_at, tr.template_type, tr.donor_ids, u.name as creator_name, d.name as donor_name
                FROM donor_template_requests tr
                JOIN users u ON tr.created_by = u.id
                LEFT JOIN donors d ON tr.donor_id = d.id
                ORDER BY tr.created_at DESC
            """)
            result = connection.execute(query).mappings().fetchall()

            db_templates = []
            for row in result:
                db_templates.append(
                    {
                        "id": str(row["id"]),
                        "name": row["name"],
                        "status": row["status"],
                        "template_type": row["template_type"],
                        "creator": row["creator_name"],
                        "donor": row["donor_name"]
                        or ("Multiple" if row["donor_ids"] else None),
                        "donor_ids": [str(d) for d in row["donor_ids"]]
                        if row["donor_ids"]
                        else [],
                        "created_at": _to_iso(row["created_at"]),
                        "type": "db",
                    }
                )

        return {"published": published, "requests": db_templates}
    except Exception as e:
        logger.error(f"Error listing templates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list templates.")


@router.post("/request")
async def create_template_request(
    request: DonorTemplateRequestCreate,
    current_user: dict = Depends(get_current_user),
    engine=Depends(get_engine),
):
    """
    Submit a new donor template request.
    """
    user_id = current_user["user_id"]
    try:
        sections = request.configuration.get("sections", [])
        high_level_instructions = request.configuration.get("instructions", [])
        template_type = request.template_type or "proposal"

        # Build a draft initial file content that mirrors the real JSON template format
        initial_file_content = {
            "template_name": request.name,
            "template_type": "Proposal"
            if template_type == "proposal"
            else "Concept Note",
            "donors": [request.name],
            "special_requirements": {"instructions": high_level_instructions},
            "section_sequence": [
                s.get("section_name", s) if isinstance(s, dict) else s
                for s in sorted(
                    sections,
                    key=lambda s: s.get("generation_sequence", 999)
                    if isinstance(s, dict)
                    else 999,
                )
            ],
            "sections": sections,
        }

        with engine.begin() as connection:
            connection.execute(
                text("""
                    INSERT INTO donor_template_requests (id, name, donor_id, donor_ids, template_type, configuration, initial_file_content, created_by)
                    VALUES (:id, :name, :did, :dids, :ttype, :conf, :file, :uid)
                """),
                {
                    "id": str(uuid.uuid4()),
                    "name": request.name,
                    "did": request.donor_id,
                    "dids": request.donor_ids if request.donor_ids else None,
                    "ttype": template_type,
                    "conf": json.dumps(request.configuration),
                    "file": json.dumps(initial_file_content),
                    "uid": user_id,
                },
            )
        return {"message": "Template request submitted successfully."}
    except Exception as e:
        logger.error(
            f"[CREATE TEMPLATE REQUEST ERROR] Failed to submit template request: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail="Failed to submit template request."
        )


@router.get("/request/{request_id}")
async def get_template_request(
    request_id: str,
    current_user: dict = Depends(get_current_user),
    engine=Depends(get_engine),
):
    """
    Get detailed information about a template request.
    """
    try:
        with engine.connect() as connection:
            query = text("""
                SELECT tr.*, u.name as creator_name, d.name as donor_name
                FROM donor_template_requests tr
                JOIN users u ON tr.created_by = u.id
                LEFT JOIN donors d ON tr.donor_id = d.id
                WHERE tr.id = :id
            """)
            row = connection.execute(query, {"id": request_id}).mappings().fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="Request not found.")

            donor_names = []
            if row["donor_ids"]:
                donor_names_query = text("SELECT name FROM donors WHERE id = ANY(:ids)")
                donor_names_result = connection.execute(
                    donor_names_query, {"ids": row["donor_ids"]}
                ).fetchall()
                donor_names = [r[0] for r in donor_names_result]
            elif row["donor_name"]:
                donor_names = [row["donor_name"]]

            # Fetch comments
            comments_query = text("""
                SELECT tc.*, u.name as user_name
                FROM donor_template_comments tc
                JOIN users u ON tc.user_id = u.id
                WHERE tc.template_request_id = :id
                ORDER BY tc.created_at ASC
            """)
            comments_result = (
                connection.execute(comments_query, {"id": request_id})
                .mappings()
                .fetchall()
            )
            comments = []
            for c in comments_result:
                comments.append(
                    {
                        "id": str(c["id"]),
                        "user": c["user_name"],
                        "user_id": str(c["user_id"]),
                        "text": c["comment_text"],
                        "section_name": c["section_name"],
                        "rating": c["rating"],
                        "severity": c["severity"],
                        "status": c.get("status", "pending"),
                        "type_of_comment": c.get("type_of_comment", "Donor Template"),
                        "created_at": _to_iso(c["created_at"]),
                    }
                )

            return {
                "id": str(row["id"]),
                "name": row["name"],
                "donor": donor_names[0]
                if donor_names and len(donor_names) == 1
                else ("Multiple" if len(donor_names) > 1 else None),
                "donor_names": donor_names,
                "donor_id": str(row["donor_id"]) if row["donor_id"] else None,
                "donor_ids": [str(did) for did in row["donor_ids"]]
                if row["donor_ids"]
                else [],
                "template_type": row.get("template_type", "proposal"),
                "configuration": _parse_json(row["configuration"]),
                "initial_file_content": _parse_json(row["initial_file_content"]),
                "status": row["status"],
                "creator": row["creator_name"],
                "created_at": _to_iso(row["created_at"]),
                "comments": comments,
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching template request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch template request.")


@router.put("/request/{request_id}/status")
async def update_request_status(
    request_id: str,
    req: DonorTemplateStatusUpdate,
    current_user: dict = Depends(get_current_user),
    engine=Depends(get_engine),
):
    """
    Update request status (Admin only).
    """
    # Simplified RBAC: any user with 'admin' or 'knowledge manager' role
    roles = current_user.get("roles", [])
    if not any(role in ["admin", "knowledge manager donors"] for role in roles):
        raise HTTPException(
            status_code=403,
            detail="Only admins or knowledge managers can update status.",
        )

    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE donor_template_requests SET status = :status, updated_at = CURRENT_TIMESTAMP WHERE id = :id"
                ),
                {"status": req.status, "id": request_id},
            )
        return {"message": f"Status updated to {req.status}."}
    except Exception as e:
        logger.error(f"Error updating status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update status.")


@router.post("/request/{request_id}/comment")
async def add_comment(
    request_id: str,
    req: DonorTemplateCommentCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    engine=Depends(get_engine),
):
    """
    Add a general or section-scoped comment to a template request.
    """
    user_id = current_user["user_id"]
    try:
        # Check if request_id is a valid UUID
        is_uuid = True
        try:
            uuid.UUID(request_id)
        except ValueError:
            is_uuid = False

        review_id = None
        with engine.begin() as connection:
            if is_uuid:
                result = connection.execute(
                    text("""
                        INSERT INTO donor_template_comments (id, template_request_id, user_id, comment_text, section_name, rating, severity, type_of_comment)
                        VALUES (:id, :tid, :uid, :text, :section, :rating, :severity, :type)
                        RETURNING id::text
                    """),
                    {
                        "id": str(uuid.uuid4()),
                        "tid": request_id,
                        "uid": user_id,
                        "text": req.comment_text,
                        "section": req.section_name,
                        "rating": req.rating,
                        "severity": req.severity,
                        "type": req.type_of_comment,
                    },
                )
                review_id = result.scalar()
            else:
                # Store as a file-based comment using template_name
                result = connection.execute(
                    text("""
                        INSERT INTO donor_template_comments (id, template_name, user_id, comment_text, section_name, rating, severity, type_of_comment)
                        VALUES (:id, :tname, :uid, :text, :section, :rating, :severity, :type)
                        RETURNING id::text
                    """),
                    {
                        "id": str(uuid.uuid4()),
                        "tname": request_id,
                        "uid": user_id,
                        "text": req.comment_text,
                        "section": req.section_name,
                        "rating": req.rating,
                        "severity": req.severity,
                        "type": req.type_of_comment,
                    },
                )
                review_id = result.scalar()

        # Trigger analysis in background
        if review_id:
            background_tasks.add_task(
                _run_auto_analysis, ArtifactType.template, review_id
            )

        return {"message": "Comment added successfully.", "comment_id": review_id}
    except Exception as e:
        logger.error(f"Error adding comment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to add comment.")


@router.post("/templates/request/{request_id}/reply")
async def reply_to_template_feedback(
    request_id: str,
    request: AuthorResponseRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Saves a reply to a donor template comment.
    """
    user_id = current_user["user_id"]
    try:
        with engine.begin() as connection:
            # Verify permissions (user should be the one who created the request, or admin)
            is_uuid = True
            try:
                uuid.UUID(request_id)
            except ValueError:
                is_uuid = False

            if is_uuid:
                owner_id = connection.execute(
                    text(
                        "SELECT created_by FROM donor_template_requests WHERE id = :rid"
                    ),
                    {"rid": request_id},
                ).scalar()
            else:
                # For file-based templates, we might not have a record in donor_template_requests
                # In this case, we check if the user is an admin or we allow replies for now
                owner_id = user_id  # Fallback

            # Simple check for now
            if str(owner_id) != str(user_id) and not current_user.get(
                "is_admin", False
            ):
                # Check if user is an admin via roles
                roles = current_user.get("roles", [])
                is_admin = any(
                    r == "admin" or (isinstance(r, dict) and r.get("name") == "admin")
                    for r in roles
                )
                if not is_admin:
                    raise HTTPException(status_code=403, detail="Permission denied.")

            # Update the author_response and status
            connection.execute(
                text(
                    "UPDATE donor_template_comments SET author_response = :response, author_response_by = :author, status = :status WHERE id = :rid"
                ),
                {
                    "response": request.author_response,
                    "status": request.status,
                    "rid": str(request.feedback_id),
                    "author": current_user.get("name", ""),
                },
            )

        return {"message": "Reply saved successfully."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving template reply: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save reply.")
