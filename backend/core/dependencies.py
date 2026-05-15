"""
FastAPI Dependency Injection Utilities for Proposal Drafter

Centralized dependency providers for FastAPI endpoints. This module consolidates
common dependencies used across the application.

Usage:
    from backend.core.dependencies import (
        get_db_session,
        get_current_user,
        get_optional_user,
    )

    @router.get("/api/protected")
    async def protected_endpoint(
        current_user: User = Depends(get_current_user),
        db_session: AsyncSession = Depends(get_db_session),
    ):
        ...
"""

from typing import Annotated, AsyncGenerator, Optional
from fastapi import Depends, HTTPException, Query, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession


# Import models (lazy import to avoid circular dependencies)
def get_user_model():
    from backend.models.user import User

    return User


def get_db_model():
    from backend.database import Base, async_session_maker

    return Base, async_session_maker


# =============================================================================
# Database Session Dependencies
# =============================================================================


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.

    This is the primary database session dependency for all endpoints.
    The session is automatically committed on success and rolled back on failure.

    Usage:
        @router.get("/api/users")
        async def list_users(
            db_session: AsyncSession = Depends(get_db_session)
        ):
            ...

    Yields:
        AsyncSession: SQLAlchemy async database session
    """
    from backend.database import async_session_maker

    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Alternative name for consistency with authorization.py
async def get_db_session_dependency() -> AsyncGenerator[AsyncSession, None]:
    """
    Alternative name for get_db_session for consistency.

    This is the same as get_db_session but with a different name to match
    the convention used in authorization.py.
    """
    async for session in get_db_session():
        yield session


# =============================================================================
# Authentication Dependencies
# =============================================================================

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> Optional[object]:
    """
    Dependency that provides the current authenticated user.

    Extracts the user from the JWT token in the Authorization header.

    Usage:
        @router.get("/api/protected")
        async def protected_endpoint(
            current_user: User = Depends(get_current_user)
        ):
            ...

    Args:
        token: JWT token from Authorization header

    Returns:
        User object for the authenticated user

    Raises:
        HTTPException(401): If token is missing, expired, or invalid
        HTTPException(401): If user does not exist
    """
    from backend.core.authorization import get_current_user as _get_current_user

    return await _get_current_user(token)


async def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme),
) -> Optional[object]:
    """
    Dependency that provides the current user if authenticated, None otherwise.

    Unlike get_current_user, this does not raise an exception if the token
    is missing. It returns None instead.

    Usage:
        @router.get("/api/public")
        async def public_endpoint(
            current_user: Optional[User] = Depends(get_optional_user)
        ):
            # current_user is None if not authenticated
            ...

    Args:
        token: Optional JWT token from Authorization header

    Returns:
        User object if authenticated, None otherwise
    """
    if token is None:
        return None

    try:
        from backend.core.authorization import get_current_user as _get_current_user

        return await _get_current_user(token)
    except HTTPException:
        return None


# =============================================================================
# Authorization Dependencies
# =============================================================================


async def require_admin(current_user: object = Depends(get_current_user)) -> object:
    """
    Dependency that ensures the current user is an admin.

    Usage:
        @router.get("/api/admin")
        async def admin_endpoint(
            current_user: User = Depends(require_admin)
        ):
            # Only admin users can reach here
            ...

    Args:
        current_user: User object from get_current_user

    Returns:
        User object (guaranteed to be admin)

    Raises:
        HTTPException(403): If user is not an admin
    """
    if hasattr(current_user, "is_admin") and current_user.is_admin:
        return current_user

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")


async def require_authenticated(
    current_user: Optional[object] = Depends(get_optional_user),
) -> object:
    """
    Dependency that ensures the user is authenticated.

    Unlike get_current_user, this returns a 401 if not authenticated rather
    than raising an exception.

    Usage:
        @router.get("/api/authenticated")
        async def authenticated_endpoint(
            current_user: User = Depends(require_authenticated)
        ):
            # User is guaranteed to be authenticated
            ...

    Args:
        current_user: User object or None from get_optional_user

    Returns:
        User object (guaranteed to be authenticated)

    Raises:
        HTTPException(401): If user is not authenticated
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return current_user


# =============================================================================
# Rate Limiting Dependencies
# =============================================================================


async def get_client_ip(request: Request) -> str:
    """
    Dependency that extracts the client IP address from the request.

    Handles X-Forwarded-For headers for reverse proxy setups.

    Usage:
        @router.get("/api/limited")
        async def limited_endpoint(
            client_ip: str = Depends(get_client_ip)
        ):
            # Use client_ip for rate limiting
            ...

    Args:
        request: FastAPI Request object

    Returns:
        Client IP address as a string
    """
    # Check for X-Forwarded-For header (common in reverse proxy setups)
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        # Take the first IP in the list
        return x_forwarded_for.split(",")[0].strip()

    # Check for X-Real-IP header
    x_real_ip = request.headers.get("X-Real-IP")
    if x_real_ip:
        return x_real_ip.strip()

    # Fall back to client host
    if request.client:
        return request.client.host

    return "unknown"


# =============================================================================
# Request Context Dependencies
# =============================================================================


async def get_request_id(request: Request) -> str:
    """
    Dependency that generates or retrieves a unique request ID.

    This can be used for tracing and logging.

    Usage:
        @router.get("/api/traced")
        async def traced_endpoint(
            request_id: str = Depends(get_request_id)
        ):
            # Use request_id for logging and tracing
            ...

    Args:
        request: FastAPI Request object

    Returns:
        Unique request ID as a string
    """
    # Check for existing request ID in headers
    request_id = request.headers.get("X-Request-ID")
    if request_id:
        return request_id

    # Generate a new UUID
    import uuid

    return str(uuid.uuid4())


async def get_user_agent(request: Request) -> str:
    """
    Dependency that extracts the User-Agent header from the request.

    Usage:
        @router.get("/api/analyzed")
        async def analyzed_endpoint(
            user_agent: str = Depends(get_user_agent)
        ):
            # Use user_agent for analytics or logging
            ...

    Args:
        request: FastAPI Request object

    Returns:
        User-Agent string from the request headers
    """
    return request.headers.get("User-Agent", "")


# =============================================================================
# Correlation Dependencies
# =============================================================================


async def get_correlation_id(request: Request) -> str:
    """
    Dependency that generates or retrieves a correlation ID for distributed tracing.

    Usage:
        @router.get("/api/correlated")
        async def correlated_endpoint(
            correlation_id: str = Depends(get_correlation_id)
        ):
            # Use correlation_id for distributed tracing
            ...

    Args:
        request: FastAPI Request object

    Returns:
        Correlation ID as a string
    """
    # Check for existing correlation ID in headers
    correlation_id = request.headers.get("X-Correlation-ID")
    if correlation_id:
        return correlation_id

    # Generate a new UUID
    import uuid

    return str(uuid.uuid4())


# =============================================================================
# Pagination Dependencies
# =============================================================================

# Default pagination parameters
DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


async def get_pagination(
    page: Annotated[int, Query(ge=1)] = DEFAULT_PAGE,
    page_size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
) -> tuple[int, int]:
    """
    Dependency that provides pagination parameters.

    Validates that page and page_size are within acceptable ranges.

    Usage:
        @router.get("/api/items")
        async def list_items(
            page: int, page_size: int = Depends(get_pagination)
        ):
            # Use page and page_size for pagination
            ...

    Args:
        page: Page number (1-based, >= 1)
        page_size: Number of items per page (1 to MAX_PAGE_SIZE)

    Returns:
        Tuple of (page, page_size)
    """
    return page, page_size


# =============================================================================
# Sorting Dependencies
# =============================================================================


async def get_sorting(
    sort_by: Optional[str] = Query(None),
    sort_order: Annotated[str, Query(pattern="^(asc|desc)$")] = "asc",
) -> tuple[Optional[str], str]:
    """
    Dependency that provides sorting parameters.

    Validates that sort_order is either 'asc' or 'desc'.

    Usage:
        @router.get("/api/items")
        async def list_items(
            sort_by: Optional[str], sort_order: str = Depends(get_sorting)
        ):
            # Use sort_by and sort_order for sorting
            ...

    Args:
        sort_by: Field name to sort by (optional)
        sort_order: Sort direction ('asc' or 'desc')

    Returns:
        Tuple of (sort_by, sort_order)
    """
    return sort_by, sort_order
