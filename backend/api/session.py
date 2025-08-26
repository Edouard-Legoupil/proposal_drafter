#  Standard Library
import json
import uuid

#  Third-Party Libraries
from fastapi import APIRouter, Depends, HTTPException

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
async def store_base_data(request: BaseDataRequest, current_user: dict = Depends(get_current_user)):
    """
    Stores the initial proposal data (form data and project description)
    in a temporary Redis session. The session is set to expire.
    """
    session_id = get_session_id()
    data = {
        "form_data": request.form_data,
        "project_description": request.project_description,
        "user_id": current_user["user_id"],
        "template_name": request.template_name
    }
    # Store in Redis with a 1-hour expiration (3600 seconds).
    redis_client.setex(session_id, 3600, json.dumps(data))

    return {"message": "Base data stored successfully", "session_id": session_id}

@router.get("/get_base_data/{session_id}")
async def get_base_data(session_id: str):
    """
    Retrieves the base proposal data from the specified Redis session.
    """
    data = redis_client.get(session_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Session data not found or expired.")

    return json.loads(data)
