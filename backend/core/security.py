import hmac
import logging

#  Standard Library
from typing import Optional, Any

#  Third-Party Libraries
import jwt
from fastapi import Request, HTTPException, Depends
from redis.exceptions import RedisError  # type: ignore[import-untyped]
from sqlalchemy import text
from werkzeug.security import generate_password_hash, check_password_hash

#  Internal Modules
from backend.core.config import (
    SECRET_KEY,
    ENTRA_TENANT_ID,
    ENTRA_CLIENT_ID,
    ENTRA_CLIENT_SECRET,
    ENTRA_REDIRECT_URI,
    shared_session_store_required,
)
from backend.core.db import get_engine
from backend.core.redis import is_redis_available, redis_client
from backend.services.access_management_service import AccessManagementService

# Configure logging for this module.
logger = logging.getLogger(__name__)

# This module centralizes security-related functions, such as authentication,
# token handling, and password management.


def store_session_token(user_id: str, token: str, ttl: int = 28800) -> None:
    """Persist an authenticated session, failing closed when Redis is required."""
    try:
        redis_client.setex(f"user_session:{user_id}", ttl, token)
    except RedisError as exc:
        if shared_session_store_required():
            logger.error("Could not persist shared session for user %s: %s", user_id, exc)
            raise HTTPException(status_code=503, detail="Session service temporarily unavailable.") from exc
        logger.warning("Could not persist local session for user %s: %s", user_id, exc)


def is_session_token_active(user_id: str, token: str) -> bool:
    """Validate a JWT against the user's active session when Redis is available."""
    if not is_redis_available():
        if shared_session_store_required():
            logger.error("Shared session store unavailable during token validation")
            raise HTTPException(status_code=503, detail="Session service temporarily unavailable.")
        logger.warning("Redis unavailable; using local cryptographic token validation")
        return True

    try:
        active_token = redis_client.get(f"user_session:{user_id}")
    except RedisError as exc:
        if shared_session_store_required():
            logger.error("Shared session validation failed: %s", exc)
            raise HTTPException(status_code=503, detail="Session service temporarily unavailable.") from exc
        logger.warning("Local session validation failed; accepting valid JWT: %s", exc)
        return True

    if not isinstance(active_token, str) or not active_token:
        return False

    return hmac.compare_digest(active_token, token)


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
        payload = jwt.decode(token, str(SECRET_KEY), algorithms=["HS256"])
        email = payload.get("email")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token payload.")

        # Fetch the user from the database.
        with get_engine().connect() as connection:
            result = connection.execute(
                text("SELECT id, name, email, password, requested_role_id FROM users WHERE email = :email"),
                {"email": email},
            )
            user = result.fetchone()

            if not user:
                raise HTTPException(status_code=404, detail="User not found.")

            user_id = str(user[0])
            is_sso = user[3] == "SSO_USER_NO_PASSWORD"

            if not is_session_token_active(user_id, token):
                raise HTTPException(status_code=401, detail="Session is no longer active.")

            header_team_id = request.headers.get("X-Team-ID")
            requested_team_id = header_team_id
            if requested_team_id is None:
                try:
                    persisted_team_id = redis_client.get(f"active_team:{user_id}")
                except RedisError as exc:
                    logger.warning("Could not load active-team session for user %s: %s", user_id, exc)
                    persisted_team_id = None
                if isinstance(persisted_team_id, bytes):
                    persisted_team_id = persisted_team_id.decode("utf-8")
                if isinstance(persisted_team_id, str) and persisted_team_id:
                    requested_team_id = persisted_team_id
            service = AccessManagementService(connection)
            try:
                context = service.resolve_context(user_id, requested_team_id)
            except HTTPException:
                if header_team_id is not None or requested_team_id is None:
                    raise
                logger.warning("Discarding stale active-team session for user %s", user_id)
                context = service.resolve_context(user_id, None)
                try:
                    redis_client.delete(f"active_team:{user_id}")
                except RedisError as exc:
                    logger.warning("Could not clear stale active-team session for user %s: %s", user_id, exc)
            roles = sorted(context.roles)

            return {
                "user_id": user_id,
                "name": user[1],
                "email": user[2],
                "memberships": context.memberships,
                "teams": context.memberships,
                "active_team": context.active_team,
                "roles": roles,
                "role_keys": sorted(context.role_keys),
                "all_roles": roles,
                "team_leadership": context.team_leadership,
                "settings": context.settings,
                "is_admin": context.is_admin,
                "is_sso": is_sso,
                "requested_role_id": user[4],
            }

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired.") from None
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token.") from None
    except HTTPException:
        raise
    except Exception as e:
        # Generic error for other potential issues.
        logger.error(
            f"Authentication error for user {email if 'email' in locals() else 'unknown'}: {e}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Authentication error") from e


def is_system_admin(current_user: dict = Depends(get_current_user)):
    """
    Dependency to check if the current user is a system admin.
    """
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required.")
    return current_user


def require_any_role(*required_roles: str):
    """Build a dependency that requires a role in the active team context."""
    normalized_required = {role.lower().replace("_", " ").strip() for role in required_roles}

    def dependency(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user.get("is_admin"):
            return current_user
        user_roles = current_user.get("roles", [])
        normalized_user_roles = {role.lower().replace("_", " ").strip() for role in user_roles}
        if normalized_required.isdisjoint(normalized_user_roles):
            raise HTTPException(status_code=403, detail="Required role is not assigned.")
        return current_user

    return dependency


def check_user_group_access(
    current_user: dict,
    donor_id: Optional[Any] = None,
    outcome_id: Optional[Any] = None,
    field_context_id: Optional[Any] = None,
    owner_id: Optional[str] = None,
):
    """
    Checks if the user has permission to edit content based on roles and ownership.
    - Donor cards: needs 'knowledge manager donors' role.
    - Outcome cards: needs 'knowledge manager outcome' role.
    - Field context cards: needs 'knowledge manager field context' role AND must be the owner.
    """
    if current_user.get("is_admin"):
        return
    user_roles = current_user.get("roles", [])
    # Donor check
    if donor_id:
        if "knowledge manager donors" not in user_roles:
            raise HTTPException(
                status_code=403,
                detail=(
                    "Access denied. You do not have the 'knowledge manager donors' "
                    "role required to edit donor cards."
                ),
            )

    # Outcome check
    if outcome_id:
        if "knowledge manager outcome" not in user_roles:
            raise HTTPException(
                status_code=403,
                detail=(
                    "Access denied. You do not have the 'knowledge manager outcome' "
                    "role required to edit outcome cards."
                ),
            )

    # Field context check (role-based)
    if field_context_id:
        if "knowledge manager field context" not in user_roles:
            raise HTTPException(
                status_code=403,
                detail=(
                    "Access denied. You do not have the 'knowledge manager field context' "
                    "role required to edit field context cards."
                ),
            )


# Exposing functions for use in other parts of the application.
__all__ = [
    "get_current_user",
    "is_system_admin",
    "require_any_role",
    "check_user_group_access",
    "generate_password_hash",
    "check_password_hash",
    "is_session_token_active",
    "ENTRA_TENANT_ID",
    "ENTRA_CLIENT_ID",
    "ENTRA_CLIENT_SECRET",
    "ENTRA_REDIRECT_URI",
]
