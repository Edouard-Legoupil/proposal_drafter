#  Standard Library
import logging

#  Third-Party Libraries
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

#  Internal Modules
from backend.core.db import get_engine
from backend.core.security import get_current_user

# This router handles all endpoints related to users.
router = APIRouter()

# Configure logging
logger = logging.getLogger(__name__)


@router.get("/users")
async def get_users(current_user: dict = Depends(get_current_user)):
    """
    Returns a list of all users in the system.
    This is used to populate the peer review selection modal.
    """
    try:
        with get_engine().connect() as connection:
            result = connection.execute(text("SELECT id, name, email FROM users"))
            users = [{"id": str(row[0]), "name": row[1], "email": row[2]} for row in result]
            # Exclude the current user from the list of potential reviewers
            users = [user for user in users if user["id"] != current_user["user_id"]]
            return {"users": users}
    except Exception as e:
        logger.error(f"[GET USERS ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not retrieve users.")
