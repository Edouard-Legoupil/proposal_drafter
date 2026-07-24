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

import json

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from functools import wraps
from typing import Callable, Optional, Any, TypeVar, Dict, Union
from sqlalchemy import text

# Import existing security functions
from backend.core.security import get_current_user as _get_current_user_from_security
from backend.core.db import get_engine
from backend.core.dependencies import get_db_session

# Import models for ORM-based queries
from backend.models.proposal import Proposal
from backend.models.knowledge_card import KnowledgeCard
from backend.models.template import Template
from backend.models.team import TeamMember


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


def get_user_roles_with_inheritance(current_user: CurrentUser) -> list:
    """Get all roles from current_user dict, including inherited roles."""
    return current_user.get("all_roles", current_user.get("roles", []))


def has_permission(current_user: CurrentUser, permission: str) -> bool:
    """Check if current_user has a specific permission (including inherited roles)."""
    if is_admin(current_user):
        return True

    # Check both direct roles and inherited roles
    all_roles = get_user_roles_with_inheritance(current_user)
    return permission in all_roles


# =============================================================================
# Database Query Helpers
# =============================================================================


def get_db_connection():
    """Get a database connection from the existing engine."""
    return get_engine().connect()


def _has_explicit_resource_grant(
    object_type: str,
    object_id: Union[str, int],
    user_id: str,
    required_permission: str,
) -> bool:
    """Check direct and active-team grants stored by the admin access API."""
    resource_types = {
        "proposal": "proposals",
        "knowledge_card": "knowledge-cards",
        "template": "templates",
    }
    resource_type = resource_types[object_type]
    with get_db_connection() as connection:
        rows = (
            connection.execute(
                text(
                    "SELECT g.permissions FROM resource_access_grants g "
                    "WHERE g.resource_type = :resource_type AND g.resource_id = :resource_id "
                    "AND ((g.subject_type = 'user' AND g.subject_id = :user_id) "
                    "OR (g.subject_type = 'team' AND g.subject_id IN ("
                    "SELECT tm.team_id FROM team_members tm "
                    "WHERE tm.user_id = :user_id AND tm.status = 'ACTIVE')))"
                ),
                {"resource_type": resource_type, "resource_id": str(object_id), "user_id": user_id},
            )
            .scalars()
            .all()
        )
        for value in rows:
            permissions = json.loads(value) if isinstance(value, str) else value
            if required_permission in (permissions or []):
                return True

        if object_type == "template" and required_permission == "read":
            visibility = connection.execute(
                text(
                    "SELECT visibility FROM resource_access_settings "
                    "WHERE resource_type = 'templates' AND resource_id = :resource_id"
                ),
                {"resource_id": str(object_id)},
            ).scalar()
            return visibility == "organization"
    return False


async def get_db_connection_async():
    """Get an async database connection."""
    # For now, use sync connection wrapped in async
    # TODO: Migrate to async SQLAlchemy
    return get_db_connection()


# =============================================================================
# Ownership Verification
# =============================================================================


async def verify_ownership(
    resource_type: str, resource_id: int, current_user: CurrentUser
) -> Dict[str, Any]:  # type: ignore[return]
    """
    Verify that the current user owns the specified resource using safe ORM queries.

    This function prevents Insecure Direct Object Reference (IDOR) vulnerabilities
    by explicitly checking ownership before granting access to a resource.

    Replaced raw SQL queries with SQLAlchemy ORM to prevent SQL injection (SEC-001)

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

    # Map resource types to SQLAlchemy models (SEC-001: Use ORM instead of raw SQL)
    model_map = {
        "proposal": Proposal,
        "knowledge_card": KnowledgeCard,
        "template": Template,
    }

    model = model_map.get(resource_type)
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown resource type: {resource_type}",
        )

    # Use SQLAlchemy ORM for safe querying (SEC-001: SQL Injection fix)
    try:
        async for session in get_db_session():
            resource = await session.get(model, resource_id)

            # Resource not found - return 404 (NOT 403) to avoid information leakage
            if resource is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{resource_type.replace('_', ' ').title()} not found",
                )

            # Check ownership (SEC-001: Safe attribute access)
            if str(resource.user_id) != user_id:  # type: ignore[attr-defined]
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

            return {
                "id": str(getattr(resource, "id", "")),
                "owner_id": str(getattr(resource, "user_id", "")),
            }

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database session unavailable",
        )
    except HTTPException:
        raise
    except Exception as e:
        import logging

        logger = logging.getLogger("security.authorization")
        logger.error(f"Database error in verify_ownership: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


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
                ) from None

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
                ) from None

            # Query the resource to get its team_id
            # Try multiple resource types (SEC-001: Use ORM instead of raw SQL)
            team_id = None
            for resource_type in ["proposal", "knowledge_card", "template"]:
                model_map = {
                    "proposal": Proposal,
                    "knowledge_card": KnowledgeCard,
                    "template": Template,
                }
                model = model_map.get(resource_type)
                if model is None:
                    continue

                try:
                    async for session in get_db_session():
                        resource = await session.get(model, resource_id)
                        if resource and hasattr(resource, "team_id") and resource.team_id is not None:
                            team_id = resource.team_id
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
                ) from None

            # Query the resource to get its donor_group_id (SEC-001: Use ORM instead of raw SQL)
            donor_group_id = None
            for resource_type in ["proposal", "knowledge_card", "template"]:
                model_map = {
                    "proposal": Proposal,
                    "knowledge_card": KnowledgeCard,
                    "template": Template,
                }
                model = model_map.get(resource_type)
                if model is None:
                    continue

                try:
                    async for session in get_db_session():
                        resource = await session.get(model, resource_id)
                        if resource and hasattr(resource, "donor_group_id") and resource.donor_group_id is not None:
                            donor_group_id = resource.donor_group_id
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


async def check_proposal_access(
    proposal_id: Union[str, int], current_user: CurrentUser, db_connection=None
) -> Dict[str, Any]:
    """
    Combined check for proposal access using the new object-level access control.

    This function uses the new check_object_access function that implements
    the object-level access control specified in the access management spec.

    Args:
        proposal_id: ID of the proposal to check
        current_user: Current user dictionary from get_current_user
        db_connection: Optional existing database connection (deprecated)

    Returns:
        The proposal data as a dictionary

    Raises:
        HTTPException(404): If proposal doesn't exist
        HTTPException(403): If user doesn't have access
    """
    # Use the new object-level access control
    try:
        await check_object_access("proposal", proposal_id, current_user, "read")

        try:
            with get_db_connection() as connection:
                result = connection.execute(
                    text("SELECT id, user_id, team_id FROM proposals WHERE id = CAST(:id AS UUID)"),
                    {"id": str(proposal_id)},
                )
                proposal = result.fetchone()

                if proposal is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Proposal not found",
                    )

                return {
                    "id": proposal[0],
                    "owner_id": str(proposal[1]),
                    "team_id": str(proposal[2]) if proposal[2] else None,
                }
        except HTTPException:
            raise
        except Exception as e:
            import logging

            logger = logging.getLogger("security.authorization")
            logger.error(f"Database error in check_proposal_access: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            ) from e
    except HTTPException:
        raise


async def check_knowledge_card_access(knowledge_card_id: int, current_user: CurrentUser) -> Dict[str, Any]:
    """
    Check knowledge card access using object-level access control.
    """
    try:
        await check_object_access("knowledge_card", knowledge_card_id, current_user, "read")

        try:
            with get_db_connection() as connection:
                result = connection.execute(
                    text("SELECT id, created_by, team_id FROM knowledge_cards WHERE id = :id"),
                    {"id": knowledge_card_id},
                )
                knowledge_card = result.fetchone()

                if knowledge_card is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Knowledge card not found",
                    )

                return {
                    "id": knowledge_card[0],
                    "created_by": str(knowledge_card[1]),
                    "team_id": str(knowledge_card[2]) if knowledge_card[2] else None,
                }
        except HTTPException:
            raise
        except Exception as e:
            import logging

            logger = logging.getLogger("security.authorization")
            logger.error(f"Database error in check_knowledge_card_access: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            ) from e
    except HTTPException:
        raise


async def check_object_access(
    object_type: str,
    object_id: Union[str, int],
    current_user: CurrentUser,
    required_permission: str = "read",
) -> bool:
    """
    Check object-level access control for proposals, knowledge cards, and templates.

    This function implements the object-level access control specified in the access management spec.
    It checks:
    1. Admin users have full access
    2. Owners have full access
    3. Team members have access based on team permissions
    4. Specific access rules defined in the object's access_rules field

    Args:
        object_type: Type of object ('proposal', 'knowledge_card', 'template')
        object_id: ID of the object to check
        current_user: Current user dictionary from get_current_user
        required_permission: Required permission ('read', 'write', 'delete')

    Returns:
        True if user has access, False otherwise

    Raises:
        HTTPException(404): If object doesn't exist
        HTTPException(403): If user doesn't have access
    """
    user_id = get_user_id(current_user)

    # Admin bypass
    if is_admin(current_user):
        return True

    # Map object types to models
    model_map = {
        "proposal": Proposal,
        "knowledge_card": KnowledgeCard,
        "template": Template,
    }

    model = model_map.get(object_type)
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown object type: {object_type}",
        )

    try:
        async for session in get_db_session():
            # Get the object
            object_record = await session.get(model, str(object_id))

            if object_record is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{object_type.replace('_', ' ').title()} not found",
                )

            # Check ownership
            owner_id = getattr(object_record, "user_id", None) or getattr(object_record, "created_by", None)
            if str(owner_id) == user_id:
                return True  # Owners have full access

            if _has_explicit_resource_grant(object_type, object_id, user_id, required_permission):
                return True

            # Check team membership and team-level permissions
            team_id = getattr(object_record, "team_id", None)
            if team_id:
                # Check if user is active team member
                is_team_member = await TeamMember.is_active_member(session, str(team_id), user_id)

                if is_team_member:
                    # Check access_rules for specific permissions
                    access_rules = getattr(object_record, "access_rules", [])

                    if not access_rules or access_rules == []:
                        # Default: team members have read access
                        if required_permission == "read":
                            return True
                    else:
                        # Check if team has the required permission in access_rules
                        for rule in access_rules:
                            if rule.get("team_id") == str(team_id):
                                permissions = rule.get("permissions", [])
                                if required_permission in permissions:
                                    return True

            # Additional checks could go here (donor group membership, etc.)

            # No access granted
            import logging

            logger = logging.getLogger("security.authorization")
            logger.warning(
                f"Unauthorized {object_type} access attempt",
                extra={
                    "user_id": user_id,
                    "object_type": object_type,
                    "object_id": object_id,
                    "required_permission": required_permission,
                    "action": f"{object_type}_access_check",
                    "result": "denied",
                },
            )

            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database session unavailable",
        )
    except HTTPException:
        raise
    except Exception as e:
        import logging

        logger = logging.getLogger("security.authorization")
        logger.error(f"Database error in check_object_access: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


async def check_template_access(
    template_id: Union[str, int],
    current_user: CurrentUser,
    required_permission: str = "read",
) -> Dict[str, Any]:
    """
    Check template access using object-level access control.
    """
    try:
        await check_object_access("template", template_id, current_user, required_permission)

        try:
            with get_db_connection() as connection:
                result = connection.execute(
                    text("SELECT id, created_by, team_id FROM templates WHERE id = :id"),
                    {"id": str(template_id)},
                )
                template = result.fetchone()

                if template is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Template not found",
                    )

                return {
                    "id": template[0],
                    "created_by": str(template[1]),
                    "team_id": str(template[2]) if template[2] else None,
                }
        except HTTPException:
            raise
        except Exception as e:
            import logging

            logger = logging.getLogger("security.authorization")
            logger.error(f"Database error in check_template_access: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            ) from e
    except HTTPException:
        raise


async def check_incident_access(
    incident_id: str, current_user: CurrentUser, required_permission: str = "read"
) -> Dict[str, Any]:
    """
    Check access to an incident analysis result.

    Args:
        incident_id: ID of the incident to check
        current_user: Current user dictionary from get_current_user
        required_permission: Required permission level ('read', 'write', 'delete', 'manage')

    Returns:
        The incident data as a dictionary

    Raises:
        HTTPException(404): If incident doesn't exist
        HTTPException(403): If user doesn't have access
    """
    user_id = get_user_id(current_user)
    import logging

    logger = logging.getLogger("security.authorization")

    # Log the access attempt
    logger.info(
        "Incident access attempt",
        extra={
            "user_id": user_id,
            "incident_id": incident_id,
            "required_permission": required_permission,
            "action": "incident_access_check",
        },
    )

    # Admin bypass
    if is_admin(current_user):
        try:
            with get_db_connection() as connection:
                result = connection.execute(
                    text("SELECT * FROM incident_analysis_results WHERE id = :id"),
                    {"id": incident_id},
                )
                incident = result.fetchone()
                if incident is None:
                    logger.warning(
                        "Incident not found",
                        extra={
                            "user_id": user_id,
                            "incident_id": incident_id,
                            "action": "incident_access_check",
                            "result": "not_found",
                        },
                    )
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Incident not found",
                    )

                logger.info(
                    "Incident access authorized - admin",
                    extra={
                        "user_id": user_id,
                        "incident_id": incident_id,
                        "action": "incident_access_check",
                        "result": "allowed",
                        "reason": "admin_access",
                    },
                )
                return dict(incident)
        except Exception as e:
            logger.error(f"Database error in check_incident_access (admin): {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            ) from e

    # Check if user is the creator of the incident
    try:
        with get_db_connection() as connection:
            result = connection.execute(
                text(
                    """
                    SELECT
                        id, artifact_type, source_review_id, created_by,
                        proposal_id, knowledge_card_id, template_request_id
                    FROM incident_analysis_results
                    WHERE id = :id
                """
                ),
                {"id": incident_id},
            )
            incident = result.fetchone()

            if incident is None:
                logger.warning(
                    "Incident not found",
                    extra={
                        "user_id": user_id,
                        "incident_id": incident_id,
                        "action": "incident_access_check",
                        "result": "not_found",
                    },
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Incident not found",
                )

            incident_data = {
                "id": str(incident[0]),
                "artifact_type": incident[1],
                "source_review_id": str(incident[2]),
                "created_by": str(incident[3]),
                "proposal_id": str(incident[4]) if incident[4] else None,
                "knowledge_card_id": str(incident[5]) if incident[5] else None,
                "template_request_id": str(incident[6]) if incident[6] else None,
            }

            # Check if current user is the creator
            if incident_data["created_by"] == user_id:
                logger.info(
                    "Incident access authorized - creator",
                    extra={
                        "user_id": user_id,
                        "incident_id": incident_id,
                        "action": "incident_access_check",
                        "result": "allowed",
                        "reason": "creator_access",
                    },
                )
                return incident_data

            # Check access based on the associated artifact
            # If the incident is related to a proposal, knowledge card, or template,
            # check if the user has access to that artifact
            artifact_id = None
            artifact_type = incident_data["artifact_type"]

            if artifact_type == "proposal" and incident_data["proposal_id"]:
                artifact_id = int(incident_data["proposal_id"])
                try:
                    await check_proposal_access(artifact_id, current_user)
                    logger.info(
                        "Incident access authorized - proposal access",
                        extra={
                            "user_id": user_id,
                            "incident_id": incident_id,
                            "proposal_id": artifact_id,
                            "action": "incident_access_check",
                            "result": "allowed",
                            "reason": "proposal_access",
                        },
                    )
                    return incident_data
                except HTTPException:
                    # User doesn't have access to the proposal, continue to next check
                    pass

            elif artifact_type == "knowledge_card" and incident_data["knowledge_card_id"]:
                artifact_id = int(incident_data["knowledge_card_id"])
                try:
                    await check_knowledge_card_access(artifact_id, current_user)
                    logger.info(
                        "Incident access authorized - knowledge card access",
                        extra={
                            "user_id": user_id,
                            "incident_id": incident_id,
                            "knowledge_card_id": artifact_id,
                            "action": "incident_access_check",
                            "result": "allowed",
                            "reason": "knowledge_card_access",
                        },
                    )
                    return incident_data
                except HTTPException:
                    # User doesn't have access to the knowledge card, continue to next check
                    pass

            elif artifact_type == "template" and incident_data["template_request_id"]:
                artifact_id = int(incident_data["template_request_id"])
                try:
                    await check_template_access(artifact_id, current_user, required_permission)
                    logger.info(
                        "Incident access authorized - template access",
                        extra={
                            "user_id": user_id,
                            "incident_id": incident_id,
                            "template_request_id": artifact_id,
                            "action": "incident_access_check",
                            "result": "allowed",
                            "reason": "template_access",
                        },
                    )
                    return incident_data
                except HTTPException:
                    # User doesn't have access to the template, continue to next check
                    pass

            # No access granted through any path
            logger.warning(
                "Unauthorized incident access attempt",
                extra={
                    "user_id": user_id,
                    "incident_id": incident_id,
                    "required_permission": required_permission,
                    "artifact_type": artifact_type,
                    "artifact_id": artifact_id,
                    "action": "incident_access_check",
                    "result": "denied",
                    "reason": "no_access_to_artifact",
                },
            )

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: you do not have permission to access this incident",
            )

    except Exception as e:
        logger.error(f"Database error in check_incident_access: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e
