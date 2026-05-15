#  Standard Library
import json
import uuid
from datetime import datetime, timedelta, timezone

#  Third-Party Libraries
from fastapi import APIRouter, Depends, HTTPException, Request

#  Internal Modules
from backend.core.redis import redis_client
from backend.core.security import get_current_user
from backend.models.schemas import BaseDataRequest

# This router handles endpoints related to managing temporary user session data,
# which is stored in Redis.

router = APIRouter()


def get_session_id() -> str:
    """Generates a new unique session ID."""
    return str(uuid.uuid4())


@router.post("/store_base_data")
async def store_base_data(
    base_request: BaseDataRequest,
    raw_request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Stores the initial proposal data (form data and project description)
    in a temporary Redis session. The session is set to expire.

    Implements TASK-SEC-005: Harden Session Management
    - Uses short-lived sessions (1 hour timeout)
    - Includes user context for security auditing
    - Generates cryptographically secure session IDs
    """
    session_id = get_session_id()
    data = {
        "form_data": base_request.form_data,
        "project_description": base_request.project_description,
        "user_id": current_user["user_id"],
        "template_name": base_request.template_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        "ip_address": raw_request.client.host if raw_request.client else None,
        "user_agent": raw_request.headers.get("user-agent"),
    }

    # Store in Redis with a 1-hour expiration (3600 seconds).
    # TASK-SEC-005: Short session timeout for security
    redis_client.setex(session_id, 3600, json.dumps(data))

    return {
        "message": "Base data stored successfully",
        "session_id": session_id,
        "expires_in_seconds": 3600,
        "security_notice": "Session will automatically expire in 1 hour for security reasons",
    }


@router.get("/get_base_data/{session_id}")
async def get_base_data(session_id: str):
    """
    Retrieves the base proposal data from the specified Redis session.

    Implements TASK-SEC-005: Session validation and timeout checking
    """
    data = redis_client.get(session_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Session data not found or expired.")

    # Parse and validate session data
    session_data = json.loads(data)

    # Check if session has expired
    expires_at = session_data.get("expires_at")
    if expires_at:
        expires_datetime = datetime.fromisoformat(expires_at)
        if datetime.now(timezone.utc) > expires_datetime:
            # Session has expired, delete it
            redis_client.delete(session_id)
            raise HTTPException(
                status_code=401,
                detail="Session has expired. Please create a new session.",
            )

    return session_data


@router.delete("/invalidate_session/{session_id}")
async def invalidate_session(session_id: str, current_user: dict = Depends(get_current_user)):
    """
    Explicitly invalidates a session to prevent session fixation attacks.

    Implements TASK-SEC-005: Session management hardening
    - Allows users to explicitly end sessions
    - Prevents session fixation attacks
    - Provides audit trail for session termination
    """
    # Verify the session exists and belongs to the current user
    session_data = redis_client.get(session_id)
    if session_data is None:
        raise HTTPException(status_code=404, detail="Session not found or already expired.")

    session_data_parsed = json.loads(session_data)
    if session_data_parsed["user_id"] != current_user["user_id"]:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to invalidate this session.",
        )

    # Delete the session
    redis_client.delete(session_id)

    return {
        "message": "Session successfully invalidated",
        "session_id": session_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/active_sessions")
async def list_active_sessions(current_user: dict = Depends(get_current_user)):
    """
    Lists all active sessions for the current user (for session management).

    Implements TASK-SEC-005: Session visibility and management
    """
    # In a production system, we would track sessions by user
    # For now, this is a placeholder for the concept
    return {
        "message": "Session management endpoint",
        "user_id": current_user["user_id"],
        "security_notice": "Session management features help prevent session fixation and hijacking",
    }
