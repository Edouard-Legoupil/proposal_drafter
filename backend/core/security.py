import logging
#  Standard Library
from datetime import datetime, timedelta
from typing import Optional, List, Any
import uuid

#  Third-Party Libraries
import jwt
from fastapi import Request, HTTPException
from sqlalchemy import text
from werkzeug.security import generate_password_hash, check_password_hash

#  Internal Modules
from backend.core.config import (
    SECRET_KEY,
    ENTRA_TENANT_ID,
    ENTRA_CLIENT_ID,
    ENTRA_CLIENT_SECRET,
)
from backend.core.db import get_engine

# Configure logging for this module.
logger = logging.getLogger(__name__)

# This module centralizes security-related functions, such as authentication,
# token handling, and password management.


def get_current_user(request: Request) -> dict:
    """
    Dependency function to retrieve and validate a user from a JWT token.

    This function is intended to be used with FastAPI's dependency injection system.
    It performs the following steps:
    1. Extracts the 'auth_token' from the request cookies.
    2. Decodes the JWT to get the user's email.
    3. Queries the database to find the corresponding user.
    4. Returns the user's information or raises an HTTPException on failure.

    Args:
        request: The incoming FastAPI request object.

    Returns:
        A dictionary containing the user's ID, name, and email.

    Raises:
        HTTPException: If the token is missing, invalid, expired, or the user is not found.
    """
    token = request.cookies.get("auth_token")
    if not token:
        raise HTTPException(status_code=401, detail="Authentication token missing.")

    try:
        # Decode the JWT token using the secret key.
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email = payload.get("email")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token payload.")

        # Fetch the user from the database.
        with get_engine().connect() as connection:
            result = connection.execute(
                text("SELECT id, name, email FROM users WHERE email = :email"),
                {"email": email}
            )
            user = result.fetchone()

            if not user:
                raise HTTPException(status_code=404, detail="User not found.")

            user_id = str(user[0])

            # Try to fetch roles, donor_groups, and outcomes, but handle empty results gracefully.
            # We use nested transactions (savepoints) to ensure that if one query fails, 
            # it doesn't poison the entire connection/transaction.
            roles = []
            try:
                with connection.begin_nested():
                    roles_query = text("SELECT r.name FROM roles r JOIN user_roles ur ON r.id = ur.role_id WHERE ur.user_id = :user_id")
                    roles_result = connection.execute(roles_query, {"user_id": user_id}).fetchall()
                    roles = [row[0] for row in roles_result] if roles_result else []
            except Exception as e:
                logger.warning(f"Failed to fetch roles for user {user_id}: {e}")

            # Return user data as a dictionary.
            return {
                "user_id": user_id,
                "name": user[1],
                "email": user[2],
                "roles": roles,
            }

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token.")
    except HTTPException:
        raise
    except Exception as e:
        # Generic error for other potential issues.
        logger.error(f"Authentication error for user {email if 'email' in locals() else 'unknown'}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Authentication error")


def check_user_group_access(current_user: dict, donor_id: Optional[Any] = None, outcome_id: Optional[Any] = None, field_context_id: Optional[Any] = None, owner_id: Optional[str] = None):
    """
    Checks if the user has permission to edit content based on roles and ownership.
    - Donor cards: needs 'knowledge manager donors' role.
    - Outcome cards: needs 'knowledge manager outcome' role.
    - Field context cards: needs 'knowledge manager field context' role AND must be the owner.
    """
    user_roles = current_user.get("roles", [])
    user_id = current_user.get("user_id")

    # Donor check
    if donor_id:
        if "knowledge manager donors" not in user_roles:
            raise HTTPException(
                status_code=403,
                detail="Access denied. You do not have the 'knowledge manager donors' role required to edit donor cards."
            )

    # Outcome check
    if outcome_id:
        if "knowledge manager outcome" not in user_roles:
            raise HTTPException(
                status_code=403,
                detail="Access denied. You do not have the 'knowledge manager outcome' role required to edit outcome cards."
            )

    # Field context check (with ownership)
    if field_context_id:
        if "knowledge manager field context" not in user_roles:
            raise HTTPException(
                status_code=403,
                detail="Access denied. You do not have the 'knowledge manager field context' role."
            )
        if owner_id and str(owner_id) != str(user_id):
            raise HTTPException(
                status_code=403,
                detail="Access denied. You can only edit field context cards that you created (ownership required)."
            )

# Exposing functions for use in other parts of the application.
__all__ = [
    "get_current_user",
    "check_user_group_access",
    "generate_password_hash",
    "check_password_hash",
    "ENTRA_TENANT_ID",
    "ENTRA_CLIENT_ID",
    "ENTRA_CLIENT_SECRET",
]
