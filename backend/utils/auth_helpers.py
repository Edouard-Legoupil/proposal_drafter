"""
Authorization Helper Functions for Proposal Drafter

Utility functions that support the authorization middleware. These helpers
provide reusable logic for common authorization patterns.

This module uses sync SQLAlchemy to match the existing backend/core/db.py setup.

Usage:
    from backend.utils.auth_helpers import (
        get_resource_owner,
        is_resource_owner,
        has_resource_access,
        is_team_member,
        is_donor_group_member,
        has_permission,
        is_admin,
    )
"""

import logging
from typing import Any, Optional, Dict, List
from sqlalchemy import text
from sqlalchemy.orm import Session

# Configure logger for authorization
logger = logging.getLogger("security.authorization")

# =============================================================================
# Resource Type Configuration
# =============================================================================

# Map resource types to their table names and owner column names
RESOURCE_CONFIG = {
    "proposal": {
        "table": "proposals",
        "owner_column": "user_id",  # proposals use user_id as owner
    },
    "knowledge_card": {
        "table": "knowledge_cards",
        "owner_column": "created_by",  # knowledge_cards use created_by as owner
    },
    "template": {
        "table": "templates",
        "owner_column": "created_by",  # templates use created_by as owner
    },
}


def get_resource_config(resource_type: str) -> Dict[str, str]:
    """
    Get the database configuration for a resource type.

    Args:
        resource_type: Type of resource ('proposal', 'knowledge_card', 'template')

    Returns:
        Dictionary with 'table' and 'owner_column' keys

    Raises:
        ValueError: If resource_type is unknown
    """
    config = RESOURCE_CONFIG.get(resource_type)
    if config is None:
        raise ValueError(f"Unknown resource type: {resource_type}")
    return config


# =============================================================================
# Ownership Verification
# =============================================================================


def get_resource_owner(resource_type: str, resource_id: Any, session: Optional[Session] = None) -> Optional[str]:
    """
    Get the owner_id of a resource by querying the database.

    Args:
        resource_type: Type of resource ('proposal', 'knowledge_card', 'template')
        resource_id: ID of the resource
        session: Optional SQLAlchemy session (uses get_engine() if not provided)

    Returns:
        The owner_id of the resource as a string, or None if resource doesn't exist
    """
    config = get_resource_config(resource_type)

    try:
        if session:
            result = session.execute(
                text(f"SELECT {config['owner_column']} FROM {config['table']} WHERE id = :id"),
                {"id": resource_id},
            )
        else:
            from backend.core.db import get_engine

            with get_engine().connect() as connection:
                result = connection.execute(
                    text(f"SELECT {config['owner_column']} FROM {config['table']} WHERE id = :id"),
                    {"id": resource_id},
                )

        row = result.fetchone()
        if row and row[0]:
            return str(row[0])
        return None
    except Exception as e:
        logger.error(f"Error getting owner for {resource_type} {resource_id}: {e}")
        return None


def is_resource_owner(
    resource_type: str,
    resource_id: Any,
    user_id: str,
    session: Optional[Session] = None,
) -> bool:
    """
    Check if a user is the owner of a resource.

    Args:
        resource_type: Type of resource ('proposal', 'knowledge_card', 'template')
        resource_id: ID of the resource
        user_id: ID of the user to check
        session: Optional SQLAlchemy session

    Returns:
        True if user is the owner, False otherwise
    """
    owner_id = get_resource_owner(resource_type, resource_id, session)
    return owner_id == user_id


# =============================================================================
# Team Membership Verification
# =============================================================================


def is_team_member(user_id: str, team_id: Any, session: Optional[Session] = None) -> bool:
    """
    Check if a user is a member of a team.

    Args:
        user_id: ID of the user
        team_id: ID of the team to check
        session: Optional SQLAlchemy session

    Returns:
        True if user is a team member, False otherwise
    """
    try:
        if session:
            result = session.execute(
                text("SELECT 1 FROM team_members WHERE team_id = :team_id AND user_id = :user_id"),
                {"team_id": team_id, "user_id": user_id},
            )
        else:
            from backend.core.db import get_engine

            with get_engine().connect() as connection:
                result = connection.execute(
                    text("SELECT 1 FROM team_members WHERE team_id = :team_id AND user_id = :user_id"),
                    {"team_id": team_id, "user_id": user_id},
                )

        return result.fetchone() is not None
    except Exception as e:
        logger.error(f"Error checking team membership for user {user_id}, team {team_id}: {e}")
        return False


# =============================================================================
# Donor Group Membership Verification
# =============================================================================


def is_donor_group_member(user_id: str, donor_group: str, session: Optional[Session] = None) -> bool:
    """
    Check if a user is a member of a donor group.

    Note: The database schema uses `user_donor_groups` table with `donor_group` as TEXT,
    not a separate donor_groups table.

    Args:
        user_id: ID of the user
        donor_group: Name of the donor group to check
        session: Optional SQLAlchemy session

    Returns:
        True if user is a donor group member, False otherwise
    """
    try:
        if session:
            result = session.execute(
                text("SELECT 1 FROM user_donor_groups WHERE user_id = :user_id AND donor_group = :donor_group"),
                {"user_id": user_id, "donor_group": donor_group},
            )
        else:
            from backend.core.db import get_engine

            with get_engine().connect() as connection:
                result = connection.execute(
                    text("SELECT 1 FROM user_donor_groups WHERE user_id = :user_id AND donor_group = :donor_group"),
                    {"user_id": user_id, "donor_group": donor_group},
                )

        return result.fetchone() is not None
    except Exception as e:
        logger.error(f"Error checking donor group membership for user {user_id}, group {donor_group}: {e}")
        return False


# =============================================================================
# Permission Checking
# =============================================================================


def get_user_roles(user_id: str, session: Optional[Session] = None) -> List[str]:
    """
    Get all role names for a user.

    Args:
        user_id: ID of the user
        session: Optional SQLAlchemy session

    Returns:
        List of role names
    """
    try:
        if session:
            result = session.execute(
                text(
                    """
                    SELECT r.name
                    FROM roles r
                    JOIN user_roles ur ON r.id = ur.role_id
                    WHERE ur.user_id = :user_id
                """
                ),
                {"user_id": user_id},
            )
        else:
            from backend.core.db import get_engine

            with get_engine().connect() as connection:
                result = connection.execute(
                    text(
                        """
                        SELECT r.name
                        FROM roles r
                        JOIN user_roles ur ON r.id = ur.role_id
                        WHERE ur.user_id = :user_id
                    """
                    ),
                    {"user_id": user_id},
                )

        return [str(row[0]) for row in result.fetchall()]
    except Exception as e:
        logger.error(f"Error getting roles for user {user_id}: {e}")
        return []


def has_permission(user_id: str, permission: str, session: Optional[Session] = None) -> bool:
    """
    Check if a user has a specific permission.

    This is a simplified implementation that checks if the permission string
    is in the user's role names. For more complex RBAC, you would have a
    separate permissions table.

    Args:
        user_id: ID of the user
        permission: Permission to check (e.g., 'read', 'write', 'delete', 'admin')
        session: Optional SQLAlchemy session

    Returns:
        True if user has the permission, False otherwise
    """
    roles = get_user_roles(user_id, session)
    return permission in roles


def is_admin(user_id: str, session: Optional[Session] = None) -> bool:
    """
    Check if a user has admin privileges.

    Args:
        user_id: ID of the user
        session: Optional SQLAlchemy session

    Returns:
        True if user is an admin, False otherwise
    """
    return has_permission(user_id, "system admin", session)


# =============================================================================
# Combined Access Check
# =============================================================================


def has_resource_access(
    resource_type: str,
    resource_id: Any,
    user_id: str,
    session: Optional[Session] = None,
    permission: str = "read",
) -> bool:
    """
    Check if a user has access to a resource (ownership, team membership, or donor group).

    This is a convenience function that checks multiple access paths:
    1. Direct ownership
    2. Team membership (if resource has team_id)
    3. Donor group membership (if resource has donor_group_id)

    Args:
        resource_type: Type of resource ('proposal', 'knowledge_card', 'template')
        resource_id: ID of the resource
        user_id: ID of the user to check
        session: Optional SQLAlchemy session
        permission: Required permission level ('read', 'write', 'delete', 'admin')

    Returns:
        True if user has access, False otherwise
    """
    # Check direct ownership first
    if is_resource_owner(resource_type, resource_id, user_id, session):
        return True

    # Get the resource to check team and donor group
    config = get_resource_config(resource_type)

    try:
        if session:
            result = session.execute(
                text(f"SELECT team_id, donor_id FROM {config['table']} WHERE id = :id"),
                {"id": resource_id},
            )
        else:
            from backend.core.db import get_engine

            with get_engine().connect() as connection:
                result = connection.execute(
                    text(f"SELECT team_id, donor_id FROM {config['table']} WHERE id = :id"),
                    {"id": resource_id},
                )

        row = result.fetchone()
        if row is None:
            return False

        team_id = row[0] if row and len(row) > 0 else None
        donor_id = row[1] if row and len(row) > 1 else None

        # Check team membership
        if team_id is not None:
            if is_team_member(user_id, str(team_id), session):
                return True

        # Check donor group membership
        if donor_id is not None:
            # For donor_id, we need to get the donor_group from the donors table
            try:
                if session:
                    donor_result = session.execute(
                        text("SELECT donor_group FROM donors WHERE id = :id"),
                        {"id": donor_id},
                    )
                else:
                    from backend.core.db import get_engine

                    with get_engine().connect() as connection:
                        donor_result = connection.execute(
                            text("SELECT donor_group FROM donors WHERE id = :id"),
                            {"id": donor_id},
                        )

                donor_row = donor_result.fetchone()
                if donor_row and donor_row[0]:
                    donor_group = str(donor_row[0])
                    if is_donor_group_member(user_id, donor_group, session):
                        # For read permission, donor group membership is sufficient
                        if permission == "read":
                            return True
            except Exception as e:
                logger.error(f"Error checking donor group for resource {resource_type} {resource_id}: {e}")

        return False
    except Exception as e:
        logger.error(f"Error checking resource access for {resource_type} {resource_id}: {e}")
        return False


# =============================================================================
# User Helper Functions
# =============================================================================


def get_user_team_ids(user_id: str, session: Optional[Session] = None) -> List[str]:
    """
    Get all team IDs a user is a member of.

    Args:
        user_id: ID of the user
        session: Optional SQLAlchemy session

    Returns:
        List of team IDs
    """
    try:
        if session:
            result = session.execute(
                text("SELECT team_id FROM team_members WHERE user_id = :user_id"),
                {"user_id": user_id},
            )
        else:
            from backend.core.db import get_engine

            with get_engine().connect() as connection:
                result = connection.execute(
                    text("SELECT team_id FROM team_members WHERE user_id = :user_id"),
                    {"user_id": user_id},
                )

        return [str(row[0]) for row in result.fetchall()]
    except Exception as e:
        logger.error(f"Error getting team IDs for user {user_id}: {e}")
        return []


def get_user_donor_groups(user_id: str, session: Optional[Session] = None) -> List[str]:
    """
    Get all donor group names a user is a member of.

    Args:
        user_id: ID of the user
        session: Optional SQLAlchemy session

    Returns:
        List of donor group names
    """
    try:
        if session:
            result = session.execute(
                text("SELECT donor_group FROM user_donor_groups WHERE user_id = :user_id"),
                {"user_id": user_id},
            )
        else:
            from backend.core.db import get_engine

            with get_engine().connect() as connection:
                result = connection.execute(
                    text("SELECT donor_group FROM user_donor_groups WHERE user_id = :user_id"),
                    {"user_id": user_id},
                )

        return [str(row[0]) for row in result.fetchall()]
    except Exception as e:
        logger.error(f"Error getting donor groups for user {user_id}: {e}")
        return []


# =============================================================================
# Audit Logging Helpers
# =============================================================================


def log_authorization_attempt(
    user_id: str,
    resource_type: str,
    resource_id: Any,
    action: str,
    result: str,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log an authorization attempt for audit purposes.

    Args:
        user_id: ID of the user making the request
        resource_type: Type of resource being accessed
        resource_id: ID of the resource being accessed
        action: Type of action (e.g., 'read', 'write', 'ownership_check')
        result: Result of the check ('allowed', 'denied')
        details: Additional details to log
    """
    extra = {
        "user_id": user_id,
        "resource_type": resource_type,
        "resource_id": str(resource_id),
        "action": action,
        "result": result,
    }

    if details:
        extra.update(details)

    if result == "allowed":
        logger.info("Authorization allowed", extra=extra)
    else:
        logger.warning("Authorization denied", extra=extra)


# =============================================================================
# Error Response Helpers
# =============================================================================


def raise_forbidden() -> None:
    """Raise a 403 Forbidden HTTPException."""
    from fastapi import HTTPException, status

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


def raise_not_found(resource_type: str = "Resource") -> None:
    """Raise a 404 Not Found HTTPException."""
    from fastapi import HTTPException, status

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{resource_type} not found")


def raise_bad_request(message: str) -> None:
    """Raise a 400 Bad Request HTTPException."""
    from fastapi import HTTPException, status

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
