"""
Custom Error Handling for Proposal Drafter API

This module provides standardized error handling for the Proposal Drafter API.
It includes custom exception classes and error response formatting.
"""

from fastapi import HTTPException, status
from typing import Any, Dict, Optional


class APIError(HTTPException):
    """
    Base class for all API errors.

    Provides standardized error responses with consistent structure.
    """

    def __init__(
        self,
        status_code: int,
        error_code: str,
        detail: str,
        headers: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a standardized API error.

        Args:
            status_code: HTTP status code
            error_code: Machine-readable error code
            detail: Human-readable error message
            headers: Optional headers to include in the response
        """
        super().__init__(
            status_code=status_code,
            detail={
                "error": {
                    "code": error_code,
                    "message": detail,
                    "status": status_code,
                }
            },
            headers=headers,
        )


class BadRequestError(APIError):
    """Error for invalid client requests (400)"""

    def __init__(self, error_code: str, detail: str):
        super().__init__(status.HTTP_400_BAD_REQUEST, error_code, detail)


class UnauthorizedError(APIError):
    """Error for authentication failures (401)"""

    def __init__(self, error_code: str, detail: str):
        super().__init__(status.HTTP_401_UNAUTHORIZED, error_code, detail)


class ForbiddenError(APIError):
    """Error for authorization failures (403)"""

    def __init__(self, error_code: str, detail: str):
        super().__init__(status.HTTP_403_FORBIDDEN, error_code, detail)


class NotFoundError(APIError):
    """Error for resource not found (404)"""

    def __init__(self, error_code: str, detail: str):
        super().__init__(status.HTTP_404_NOT_FOUND, error_code, detail)


class ConflictError(APIError):
    """Error for conflict situations (409)"""

    def __init__(self, error_code: str, detail: str):
        super().__init__(status.HTTP_409_CONFLICT, error_code, detail)


class InternalServerError(APIError):
    """Error for server-side failures (500)"""

    def __init__(self, error_code: str, detail: str):
        super().__init__(status.HTTP_500_INTERNAL_SERVER_ERROR, error_code, detail)


class ValidationError(APIError):
    """Error for validation failures (422)"""

    def __init__(self, error_code: str, detail: str):
        super().__init__(status.HTTP_422_UNPROCESSABLE_ENTITY, error_code, detail)


# Standard Error Codes
ERROR_CODES = {
    # Authentication errors
    "AUTH_INVALID_CREDENTIALS": "auth_001",
    "AUTH_TOKEN_EXPIRED": "auth_002",
    "AUTH_TOKEN_INVALID": "auth_003",
    "AUTH_PERMISSION_DENIED": "auth_004",
    # Validation errors
    "VALIDATION_FAILED": "val_001",
    "INVALID_INPUT": "val_002",
    "MISSING_REQUIRED_FIELD": "val_003",
    # Resource errors
    "RESOURCE_NOT_FOUND": "res_001",
    "RESOURCE_ALREADY_EXISTS": "res_002",
    "RESOURCE_ACCESS_DENIED": "res_003",
    # Database errors
    "DATABASE_ERROR": "db_001",
    "DATABASE_CONNECTION_FAILED": "db_002",
    # Business logic errors
    "OPERATION_NOT_ALLOWED": "bus_001",
    "INVALID_STATE": "bus_002",
    "LIMIT_EXCEEDED": "bus_003",
    # Integration errors
    "EXTERNAL_SERVICE_ERROR": "int_001",
    "EXTERNAL_API_ERROR": "int_002",
}


def handle_database_error(e: Exception) -> APIError:
    """
    Handle database-related errors and return appropriate API error.
    """
    error_detail = str(e)

    # Check for specific database errors
    if "connection" in error_detail.lower():
        return InternalServerError(ERROR_CODES["DATABASE_CONNECTION_FAILED"], "Database connection failed")
    else:
        return InternalServerError(ERROR_CODES["DATABASE_ERROR"], "A database error occurred")


def handle_validation_error(field: str, message: str) -> APIError:
    """
    Create a validation error with field-specific information.
    """
    return ValidationError(ERROR_CODES["VALIDATION_FAILED"], f"Validation failed for field '{field}': {message}")


def handle_not_found_error(resource_type: str, identifier: str) -> APIError:
    """
    Create a not found error for a specific resource.
    """
    return NotFoundError(ERROR_CODES["RESOURCE_NOT_FOUND"], f"{resource_type} with identifier '{identifier}' not found")


def handle_access_denied_error(resource_type: str, action: str) -> APIError:
    """
    Create an access denied error for a specific resource and action.
    """
    return ForbiddenError(ERROR_CODES["RESOURCE_ACCESS_DENIED"], f"Access denied: cannot {action} {resource_type}")


def standardize_error_response(exc: Exception) -> Dict[str, Any]:
    """
    Standardize error responses for consistent API behavior.
    """
    if isinstance(exc, APIError):
        # Already a standardized error
        return exc.detail
    elif isinstance(exc, HTTPException):
        # Convert FastAPI HTTPException to standardized format
        return {
            "error": {
                "code": "generic_error",
                "message": exc.detail,
                "status": exc.status_code,
            }
        }
    else:
        # Generic error for unexpected exceptions
        return {
            "error": {
                "code": "unexpected_error",
                "message": "An unexpected error occurred",
                "status": 500,
            }
        }
