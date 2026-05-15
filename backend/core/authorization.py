"""
Object-Level Authorization Middleware for Proposal Drafter

Implements decorators and verification functions for FastAPI endpoints to enforce
object-level access control. This module addresses OWASP A01:2025-Broken Access
Control and CWE-284: Improper Access Control.

This module integrates with the existing security system:
- Uses get_current_user from backend.core.security
- Works with both sync and async database operations
- Compatible with the existing JWT cookie-based authentication

Usage:
    from backend.core.authorization import (
        require_ownership,
        require_permission,
        require_team_membership,
        check_proposal_access,
        check_knowledge_card_access,
        check_template_access,
    )
    from backend.core.security import get_current_user

    @router.get("/api/proposals/{id}")
    async def get_proposal(
        id: int,
        current_user: dict = Depends(get_current_user)
    ):
        # Use helper functions for authorization checks
        await check_proposal_access(id, current_user)
        ...

    # Or use decorators (when using Bearer token auth):
    @router.get("/api/proposals/{id}")
    @require_ownership('proposal')
    async def get_proposal(
        id: int,
        current_user: dict = Depends(get_current_user)
    ):
        ...
"""

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from functools import wraps
from typing import Callable, Optional, Any, TypeVar, Dict
from sqlalchemy import text

# Import existing security functions
from backend.core.security import get_current_user as _get_current_user_from_security
from backend.core.db import get_engine

# Type for current user - dict from existing system
CurrentUser = Dict[str, Any]

# OAuth2 scheme for Bearer token extraction (alternative to cookie-based auth)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Type variable for generic function return types
T = TypeVar("T")


# =============================================================================
# User Helper Functions (for dict-based current_user)
# =============================================================================


def get_user_id(current_user: CurrentUser) -> str:
    """Extract user_id from current_user dict."""
    user_id = current_user.get("user_id") or current_user.get("id")
    if user_id is None:
        raise ValueError("User ID not found in current_user")
    return str(user_id)


def is_admin(current_user: CurrentUser) -> bool:
    """Check if current_user is an admin."""
    return current_user.get("is_admin", False)


def get_user_roles(current_user: CurrentUser) -> list:
    """Get roles from current_user dict."""
    return current_user.get("roles", [])


def has_permission(current_user: CurrentUser, permission: str) -> bool:
    """Check if current_user has a specific permission."""
    if is_admin(current_user):
        return True
    return permission in get_user_roles(current_user)


# =============================================================================
# Database Query Helpers
# =============================================================================


def get_db_connection():
    """Get a database connection from the existing engine."""
    return get_engine().connect()


async def get_db_connection_async():
    """Get an async database connection."""
    # For now, use sync connection wrapped in async
    # TODO: Migrate to async SQLAlchemy
    return get_db_connection()


# =============================================================================
# Ownership Verification
# =============================================================================


async def verify_ownership(resource_type: str, resource_id: int, current_user: CurrentUser) -> Dict[str, Any]:
    """
    Verify that the current user owns the specified resource.

    This function prevents Insecure Direct Object Reference (IDOR) vulnerabilities
    by explicitly checking ownership before granting access to a resource.

    Args:
        resource_type: Type of resource ('proposal', 'knowledge_card', 'template')
        resource_id: ID of the resource to check
        current_user: Current user dictionary from get_current_user

    Returns:
        The resource data as a dictionary

    Raises:
        HTTPException(400): If resource_type is unknown
        HTTPException(404): If resource doesn't exist (not 403 to avoid info leakage)
        HTTPException(403): If user doesn't own the resource
    """
    user_id = get_user_id(current_user)

    # Admin users bypass ownership check
    if is_admin(current_user):
        return {}

    # Map resource types to table names
    table_map = {
        "proposal": "proposals",
        "knowledge_card": "knowledge_cards",
        "template": "templates",
    }

    table_name = table_map.get(resource_type)
    if table_name is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown resource type: {resource_type}",
        )

    # Query the resource from database
    try:
        with get_db_connection() as connection:
            result = connection.execute(
                text(f"SELECT id, owner_id FROM {table_name} WHERE id = :id"),
                {"id": resource_id},
            )
            resource = result.fetchone()

            # Resource not found - return 404 (NOT 403) to avoid information leakage
            if resource is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{resource_type.replace('_', ' ').title()} not found",
                )

            # Check ownership
            owner_id = str(resource[1])  # owner_id column
            if owner_id != user_id:
                # Log the unauthorized access attempt
                import logging

                logger = logging.getLogger("security.authorization")
                logger.warning(
                    "Unauthorized ownership access attempt",
                    extra={
                        "user_id": user_id,
                        "resource_type": resource_type,
                        "resource_id": resource_id,
                        "action": "ownership_check",
                        "result": "denied",
                    },
                )

                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

            return {"id": resource[0], "owner_id": owner_id}

    except Exception as e:
        import logging

        logger = logging.getLogger("security.authorization")
        logger.error(f"Database error in verify_ownership: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


# =============================================================================
# Permission Verification
# =============================================================================


async def verify_permission(permission: str, current_user: CurrentUser) -> bool:
    """
    Verify that the current user has the specified RBAC permission.

    Args:
        permission: Permission to check ('read', 'write', 'delete', 'admin')
        current_user: Current user dictionary from get_current_user

    Returns:
        True if user has the permission

    Raises:
        HTTPException(403): If user doesn't have the required permission
    """
    if has_permission(current_user, permission):
        return True

    # Log the permission denial
    import logging

    logger = logging.getLogger("security.authorization")
    logger.warning(
        "Unauthorized permission access attempt",
        extra={
            "user_id": get_user_id(current_user),
            "required_permission": permission,
            "action": "permission_check",
            "result": "denied",
        },
    )

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


# =============================================================================
# Team Membership Verification
# =============================================================================


async def verify_team_membership(team_id: Optional[int], current_user: CurrentUser) -> bool:
    """
    Verify that the current user is a member of the specified team.

    Args:
        team_id: ID of the team to check
        current_user: Current user dictionary from get_current_user

    Returns:
        True if user is a team member (or admin)

    Raises:
        HTTPException(400): If team_id is None
        HTTPException(403): If user is not a team member
    """
    # Admin users bypass team membership check
    if is_admin(current_user):
        return True

    if team_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team ID required for team membership verification",
        )

    user_id = get_user_id(current_user)

    # Check team_members table
    try:
        with get_db_connection() as connection:
            result = connection.execute(
                text("SELECT 1 FROM team_members WHERE team_id = :team_id AND user_id = :user_id"),
                {"team_id": team_id, "user_id": user_id},
            )
            membership = result.fetchone()

            if membership is not None:
                return True
    except Exception as e:
        import logging

        logger = logging.getLogger("security.authorization")
        logger.error(f"Database error in verify_team_membership: {e}")

    # Log the team membership denial
    import logging

    logger = logging.getLogger("security.authorization")
    logger.warning(
        "Unauthorized team access attempt",
        extra={
            "user_id": user_id,
            "team_id": team_id,
            "action": "team_membership_check",
            "result": "denied",
        },
    )

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


# =============================================================================
# Donor Group Membership Verification
# =============================================================================


async def verify_donor_group_membership(donor_group_id: Optional[int], current_user: CurrentUser) -> bool:
    """
    Verify that the current user is a member of the specified donor group.

    Args:
        donor_group_id: ID of the donor group to check
        current_user: Current user dictionary from get_current_user

    Returns:
        True if user is a donor group member (or admin)

    Raises:
        HTTPException(400): If donor_group_id is None
        HTTPException(403): If user is not a donor group member
    """
    # Admin users bypass donor group membership check
    if is_admin(current_user):
        return True

    if donor_group_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Donor group ID required for donor group membership verification",
        )

    user_id = get_user_id(current_user)

    # Check donor_group_members table
    try:
        with get_db_connection() as connection:
            result = connection.execute(
                text("SELECT 1 FROM donor_group_members WHERE donor_group_id = :donor_group_id AND user_id = :user_id"),
                {"donor_group_id": donor_group_id, "user_id": user_id},
            )
            membership = result.fetchone()

            if membership is not None:
                return True
    except Exception as e:
        import logging

        logger = logging.getLogger("security.authorization")
        logger.error(f"Database error in verify_donor_group_membership: {e}")

    # Log the donor group membership denial
    import logging

    logger = logging.getLogger("security.authorization")
    logger.warning(
        "Unauthorized donor group access attempt",
        extra={
            "user_id": user_id,
            "donor_group_id": donor_group_id,
            "action": "donor_group_membership_check",
            "result": "denied",
        },
    )

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


# =============================================================================
# Decorator Factories
# =============================================================================


def require_ownership(resource_type: str) -> Callable:
    """
    Decorator factory to require that the current user owns the resource.

    This decorator verifies ownership before allowing access to the endpoint.
    It automatically extracts the resource_id from path parameters.

    Args:
        resource_type: Type of resource ('proposal', 'knowledge_card', 'template')

    Returns:
        Decorator function that can be applied to FastAPI endpoints

    Usage:
        @router.get("/api/proposals/{id}")
        @require_ownership('proposal')
        async def get_proposal(id: int, current_user: dict = Depends(get_current_user)):
            ...

    Note:
        The endpoint MUST have a path parameter named 'id'
        The endpoint MUST accept current_user via Depends(get_current_user)
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            *args: Any,
            request: Request,
            current_user: CurrentUser = Depends(_get_current_user_from_security),
            **kwargs: Any,
        ) -> Any:
            # Extract resource_id from path parameters
            resource_id = kwargs.get("id")
            if resource_id is None:
                resource_id = request.path_params.get("id")

            if resource_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Resource ID required in path parameters",
                )

            # Convert to int if it's a string
            try:
                resource_id = int(resource_id)
            except (ValueError, TypeError):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Resource ID must be an integer",
                )

            # Verify ownership
            await verify_ownership(resource_type, resource_id, current_user)

            # Call the original endpoint
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_permission(permission: str) -> Callable:
    """
    Decorator factory to require that the current user has the specified RBAC permission.

    This decorator verifies the user has the required permission before allowing
    access to the endpoint.

    Args:
        permission: Permission to check ('read', 'write', 'delete', 'admin')

    Returns:
        Decorator function that can be applied to FastAPI endpoints

    Usage:
        @router.get("/api/templates/{id}")
        @require_permission('read')
        async def get_template(id: int, current_user: dict = Depends(get_current_user)):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            *args: Any,
            current_user: CurrentUser = Depends(_get_current_user_from_security),
            **kwargs: Any,
        ) -> Any:
            # Verify permission
            await verify_permission(permission, current_user)

            # Call the original endpoint
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_team_membership() -> Callable:
    """
    Decorator factory to require that the current user is a member of the resource's team.

    This decorator automatically extracts the resource_id from path parameters,
    queries the resource to get its team_id, and verifies the user is a team member.

    Returns:
        Decorator function that can be applied to FastAPI endpoints

    Usage:
        @router.get("/api/proposals/{id}")
        @require_team_membership()
        async def get_proposal(id: int, current_user: dict = Depends(get_current_user)):
            ...

    Note:
        The resource must have a team_id column
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            *args: Any,
            request: Request,
            current_user: CurrentUser = Depends(_get_current_user_from_security),
            **kwargs: Any,
        ) -> Any:
            # Extract resource_id from path parameters
            resource_id = kwargs.get("id")
            if resource_id is None:
                resource_id = request.path_params.get("id")

            if resource_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Resource ID required in path parameters",
                )

            # Convert to int
            try:
                resource_id = int(resource_id)
            except (ValueError, TypeError):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Resource ID must be an integer",
                )

            # Query the resource to get its team_id
            # Try multiple resource types
            team_id = None
            for resource_type in ["proposal", "knowledge_card", "template"]:
                table_name = resource_type.replace("_", "") + "s"
                try:
                    with get_db_connection() as connection:
                        result = connection.execute(
                            text(f"SELECT team_id FROM {table_name} WHERE id = :id"),
                            {"id": resource_id},
                        )
                        row = result.fetchone()
                        if row and row[0] is not None:
                            team_id = row[0]
                            break
                except Exception:
                    continue

            if team_id is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

            # Verify team membership
            await verify_team_membership(team_id, current_user)

            # Call the original endpoint
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_donor_group_membership() -> Callable:
    """
    Decorator factory to require that the current user is a member of the resource's donor group.

    Returns:
        Decorator function that can be applied to FastAPI endpoints

    Usage:
        @router.get("/api/proposals/{id}")
        @require_donor_group_membership()
        async def get_proposal(id: int, current_user: dict = Depends(get_current_user)):
            ...

    Note:
        The resource must have a donor_group_id column
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            *args: Any,
            request: Request,
            current_user: CurrentUser = Depends(_get_current_user_from_security),
            **kwargs: Any,
        ) -> Any:
            # Extract resource_id from path parameters
            resource_id = kwargs.get("id")
            if resource_id is None:
                resource_id = request.path_params.get("id")

            if resource_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Resource ID required in path parameters",
                )

            # Convert to int
            try:
                resource_id = int(resource_id)
            except (ValueError, TypeError):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Resource ID must be an integer",
                )

            # Query the resource to get its donor_group_id
            donor_group_id = None
            for resource_type in ["proposal", "knowledge_card", "template"]:
                table_name = resource_type.replace("_", "") + "s"
                try:
                    with get_db_connection() as connection:
                        result = connection.execute(
                            text(f"SELECT donor_group_id FROM {table_name} WHERE id = :id"),
                            {"id": resource_id},
                        )
                        row = result.fetchone()
                        if row and row[0] is not None:
                            donor_group_id = row[0]
                            break
                except Exception:
                    continue

            if donor_group_id is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

            # Verify donor group membership
            await verify_donor_group_membership(donor_group_id, current_user)

            # Call the original endpoint
            return await func(*args, **kwargs)

        return wrapper

    return decorator


# =============================================================================
# Combined Access Check Functions (Recommended for Proposals)
# =============================================================================


async def check_proposal_access(proposal_id: int, current_user: CurrentUser, db_connection=None) -> Dict[str, Any]:
    """
    Combined check for proposal access: ownership, team membership, or donor group membership.

    This function checks multiple access paths for proposals:
    1. Admin users have full access
    2. Owner can access
    3. Team members can access (if proposal has team_id)
    4. Donor group members can access (read-only, if proposal has donor_group_id)

    Args:
        proposal_id: ID of the proposal to check
        current_user: Current user dictionary from get_current_user
        db_connection: Optional existing database connection

    Returns:
        The proposal data as a dictionary

    Raises:
        HTTPException(404): If proposal doesn't exist
        HTTPException(403): If user doesn't have access
    """
    user_id = get_user_id(current_user)

    # Admin bypass
    if is_admin(current_user):
        try:
            with get_db_connection() as connection:
                result = connection.execute(text("SELECT * FROM proposals WHERE id = :id"), {"id": proposal_id})
                proposal = result.fetchone()
                if proposal is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Proposal not found",
                    )
                return dict(proposal)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    # Query the proposal
    try:
        with get_db_connection() as connection:
            result = connection.execute(
                text("SELECT id, owner_id, team_id, donor_group_id FROM proposals WHERE id = :id"),
                {"id": proposal_id},
            )
            proposal = result.fetchone()

            if proposal is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")

            proposal_data = {
                "id": proposal[0],
                "owner_id": str(proposal[1]),
                "team_id": proposal[2],
                "donor_group_id": proposal[3],
            }

            # Check ownership
            if proposal_data["owner_id"] == user_id:
                return proposal_data

            # Check team membership
            if proposal_data["team_id"] is not None:
                try:
                    await verify_team_membership(proposal_data["team_id"], current_user)
                    return proposal_data
                except HTTPException:
                    pass  # Continue to next check

            # Check donor group membership (read-only access)
            if proposal_data["donor_group_id"] is not None:
                try:
                    await verify_donor_group_membership(proposal_data["donor_group_id"], current_user)
                    return proposal_data
                except HTTPException:
                    pass

            # No access granted
            import logging

            logger = logging.getLogger("security.authorization")
            logger.warning(
                "Unauthorized proposal access attempt",
                extra={
                    "user_id": user_id,
                    "proposal_id": proposal_id,
                    "action": "proposal_access_check",
                    "result": "denied",
                },
            )

            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    except Exception as e:
        import logging

        logger = logging.getLogger("security.authorization")
        logger.error(f"Database error in check_proposal_access: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


async def check_knowledge_card_access(knowledge_card_id: int, current_user: CurrentUser) -> Dict[str, Any]:
    """
    Combined check for knowledge card access: ownership or shared access.

    Args:
        knowledge_card_id: ID of the knowledge card to check
        current_user: Current user dictionary from get_current_user

    Returns:
        The knowledge card data as a dictionary

    Raises:
        HTTPException(404): If knowledge card doesn't exist
        HTTPException(403): If user doesn't have access
    """
    user_id = get_user_id(current_user)

    # Admin bypass
    if is_admin(current_user):
        try:
            with get_db_connection() as connection:
                result = connection.execute(
                    text("SELECT * FROM knowledge_cards WHERE id = :id"),
                    {"id": knowledge_card_id},
                )
                knowledge_card = result.fetchone()
                if knowledge_card is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Knowledge card not found",
                    )
                return dict(knowledge_card)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    # Query the knowledge card
    try:
        with get_db_connection() as connection:
            result = connection.execute(
                text("SELECT id, created_by FROM knowledge_cards WHERE id = :id"),
                {"id": knowledge_card_id},
            )
            knowledge_card = result.fetchone()

            if knowledge_card is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Knowledge card not found",
                )

            kc_data = {"id": knowledge_card[0], "created_by": str(knowledge_card[1])}

            # Check ownership (shared_with feature not implemented in current schema)
            if kc_data["created_by"] == user_id:
                return kc_data

            # No access granted
            import logging

            logger = logging.getLogger("security.authorization")
            logger.warning(
                "Unauthorized knowledge card access attempt",
                extra={
                    "user_id": user_id,
                    "knowledge_card_id": knowledge_card_id,
                    "action": "knowledge_card_access_check",
                    "result": "denied",
                },
            )

            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    except HTTPException:
        # Re-raise HTTPExceptions (404, 403, etc.)
        raise
    except Exception as e:
        import logging

        logger = logging.getLogger("security.authorization")
        logger.error(f"Database error in check_knowledge_card_access: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


async def check_template_access(
    template_id: int, current_user: CurrentUser, required_permission: str = "read"
) -> Dict[str, Any]:
    """
    Combined check for template access: ownership, organization membership, or public.

    Args:
        template_id: ID of the template to check
        current_user: Current user dictionary from get_current_user
        required_permission: Required permission level ('read', 'write', 'delete')

    Returns:
        The template data as a dictionary

    Raises:
        HTTPException(404): If template doesn't exist
        HTTPException(403): If user doesn't have access
    """
    user_id = get_user_id(current_user)

    # Admin bypass
    if is_admin(current_user):
        try:
            with get_db_connection() as connection:
                result = connection.execute(text("SELECT * FROM templates WHERE id = :id"), {"id": template_id})
                template = result.fetchone()
                if template is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Template not found",
                    )
                return dict(template)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    # Query the template
    try:
        with get_db_connection() as connection:
            result = connection.execute(
                text("SELECT id, owner_id, organization_id, is_public FROM templates WHERE id = :id"),
                {"id": template_id},
            )
            template = result.fetchone()

            if template is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

            template_data = {
                "id": template[0],
                "owner_id": str(template[1]),
                "organization_id": template[2],
                "is_public": template[3],
            }

            # Check ownership (full access)
            if template_data["owner_id"] == user_id:
                return template_data

            # Check organization membership (for public templates or read access)
            if template_data["organization_id"] is not None:
                # Check if user is in the same organization
                try:
                    with get_db_connection() as conn:
                        result = conn.execute(
                            text(
                                "SELECT 1 FROM organization_members WHERE organization_id = :org_id AND user_id = :user_id"
                            ),
                            {
                                "org_id": template_data["organization_id"],
                                "user_id": user_id,
                            },
                        )
                        if result.fetchone() is not None and template_data["is_public"]:
                            # Public template accessible to organization members
                            if required_permission == "read":
                                return template_data
                except Exception:
                    pass

            # No access granted
            import logging

            logger = logging.getLogger("security.authorization")
            logger.warning(
                "Unauthorized template access attempt",
                extra={
                    "user_id": user_id,
                    "template_id": template_id,
                    "required_permission": required_permission,
                    "action": "template_access_check",
                    "result": "denied",
                },
            )

            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    except Exception as e:
        import logging

        logger = logging.getLogger("security.authorization")
        logger.error(f"Database error in check_template_access: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
