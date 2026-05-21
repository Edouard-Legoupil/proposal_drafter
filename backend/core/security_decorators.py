# Standard Library
from functools import wraps
from typing import Callable, Any
import logging

# Third-Party Libraries
from fastapi import HTTPException, status

# Internal Modules
from backend.core.dependencies import get_db_session
from backend.core.authorization import check_proposal_access
from backend.models.proposal import Proposal
from backend.models.knowledge_card import KnowledgeCard
from backend.models.template import Template

# Configure logger
logger = logging.getLogger("security.decorators")


def secure_proposal_access(resource_param: str = "proposal_id") -> Callable:
    """
    Decorator to ensure secure access to proposal resources.

    This decorator:
    1. Validates that the resource ID is a valid UUID
    2. Checks that the current user has access to the resource using check_proposal_access
    3. Provides the resource object to the endpoint function

    Usage:
        @router.get("/proposals/{proposal_id}")
        @secure_proposal_access()
        async def get_proposal(
            proposal_id: str,
            current_user: dict = Depends(get_current_user),
            proposal: Proposal = None  # Injected by decorator
        ):
            # proposal is guaranteed to be accessible by current_user
            return proposal
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Extract current_user from kwargs
            current_user = kwargs.get("current_user")
            if not current_user:
                # Try to get from request
                request = kwargs.get("request")
                if request and hasattr(request.state, "user"):
                    current_user = request.state.user
                else:
                    logger.warning("secure_proposal_access: No current_user found")
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

            # Get resource ID from path parameters
            resource_id = kwargs.get(resource_param)
            if not resource_id:
                # Try to get from request path params
                request = kwargs.get("request")
                if request:
                    resource_id = request.path_params.get(resource_param)

            if not resource_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Resource ID parameter '{resource_param}' is required",
                )

            # Validate UUID format
            try:
                import uuid

                uuid.UUID(str(resource_id))
            except (ValueError, TypeError):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid {resource_param} format: '{resource_id}'"
                )

            # Check authorization using ORM (prevents SQL injection)
            try:
                await check_proposal_access(int(resource_id), current_user)

                # Get the resource object using ORM (safe from SQL injection)
                async for session in get_db_session():
                    resource = await session.get(Proposal, resource_id)
                    if resource:
                        # Add resource to kwargs for the endpoint to use
                        kwargs["proposal"] = resource
                        break
            except HTTPException:
                # Re-raise authorization errors
                raise
            except Exception as e:
                logger.error(f"secure_proposal_access error for {resource_param} {resource_id}: {e}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

            # Call the original function
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def secure_resource_access(resource_type: str, resource_param: str = "id") -> Callable:
    """
    Generic decorator for secure access to any resource type.

    Supports: 'proposal', 'knowledge_card', 'template'

    Usage:
        @router.get("/knowledge-cards/{id}")
        @secure_resource_access("knowledge_card")
        async def get_knowledge_card(
            id: str,
            current_user: dict = Depends(get_current_user),
            knowledge_card: KnowledgeCard = None
        ):
            return knowledge_card
    """

    # Map resource types to models
    MODEL_MAP = {
        "proposal": Proposal,
        "knowledge_card": KnowledgeCard,
        "template": Template,
    }

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Extract current_user from kwargs
            current_user = kwargs.get("current_user")
            if not current_user:
                logger.warning("secure_resource_access: No current_user found")
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

            # Get resource ID from parameters
            resource_id = kwargs.get(resource_param)
            if not resource_id:
                request = kwargs.get("request")
                if request:
                    resource_id = request.path_params.get(resource_param)

            if not resource_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Resource ID parameter '{resource_param}' is required",
                )

            # Get the model class
            model_class = MODEL_MAP.get(resource_type)
            if not model_class:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported resource type: {resource_type}"
                )

            # Check authorization and get resource
            try:
                async for session in get_db_session():
                    resource = await session.get(model_class, resource_id)
                    if not resource:
                        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{resource_type} not found")

                    # For proposals, use the existing authorization check
                    if resource_type == "proposal":
                        await check_proposal_access(int(resource_id), current_user)
                    # For other resources, check ownership
                    elif hasattr(resource, "user_id"):
                        if str(resource.user_id) != str(current_user["user_id"]):
                            logger.warning(
                                "Unauthorized resource access attempt",
                                extra={
                                    "user_id": current_user["user_id"],
                                    "resource_type": resource_type,
                                    "resource_id": resource_id,
                                },
                            )
                            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
                    elif hasattr(resource, "created_by"):
                        if str(resource.created_by) != str(current_user["user_id"]):
                            logger.warning(
                                "Unauthorized resource access attempt",
                                extra={
                                    "user_id": current_user["user_id"],
                                    "resource_type": resource_type,
                                    "resource_id": resource_id,
                                },
                            )
                            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

                    # Add resource to kwargs
                    kwargs[resource_type.replace("_", "")] = resource
                    break

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"secure_resource_access error for {resource_type} {resource_id}: {e}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

            return await func(*args, **kwargs)

        return wrapper

    return decorator


# Alias for common use cases
secure_proposal_access = secure_resource_access("proposal")
secure_knowledge_card_access = secure_resource_access("knowledge_card")
secure_template_access = secure_resource_access("template")
