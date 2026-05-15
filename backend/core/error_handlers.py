# Standard Library
import logging
from typing import Optional, Dict, Any
from datetime import datetime

# Third-Party Libraries
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_429_TOO_MANY_REQUESTS,
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_503_SERVICE_UNAVAILABLE,
)

# Local Imports

# Configure logging
logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """
    Base security exception class for standardized error handling.

    Attributes:
        status_code: HTTP status code
        error_code: Application-specific error code
        message: User-facing message (sanitized)
        details: Internal details (not exposed to client)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """

    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: Optional[str] = None,
        log_level: str = "ERROR",
    ):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.details = details
        self.log_level = log_level
        super().__init__(message)


class ErrorResponse:
    """
    Standardized error response structure.

    Ensures consistent error format across all API endpoints while preventing
    sensitive information leakage.
    """

    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int,
        timestamp: Optional[str] = None,
        request_id: Optional[str] = None,
    ):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.timestamp = timestamp or datetime.utcnow().isoformat()
        self.request_id = request_id

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response."""
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "status_code": self.status_code,
                "timestamp": self.timestamp,
                "request_id": self.request_id,
            }
        }


class ErrorHandler:
    """
    Centralized error handling with security best practices.

    Features:
    - Standardized error responses
    - Sensitive information filtering
    - Comprehensive logging
    - Rate limiting protection
    - Circuit breaker integration
    """

    # Standard error codes
    ERROR_CODES = {
        # Authentication errors
        "AUTH_001": "Invalid credentials",
        "AUTH_002": "Token expired",
        "AUTH_003": "Token invalid",
        "AUTH_004": "Insufficient permissions",
        "AUTH_005": "Account locked",
        # Authorization errors
        "AUTHZ_001": "Access denied",
        "AUTHZ_002": "Resource not found",
        "AUTHZ_003": "Operation not permitted",
        # Validation errors
        "VAL_001": "Invalid input",
        "VAL_002": "Missing required field",
        "VAL_003": "Invalid format",
        # Rate limiting errors
        "RATE_001": "Too many requests",
        "RATE_002": "Rate limit exceeded",
        # LLM errors
        "LLM_001": "LLM service unavailable",
        "LLM_002": "LLM request failed",
        "LLM_003": "LLM rate limit exceeded",
        # Database errors
        "DB_001": "Database connection failed",
        "DB_002": "Database operation failed",
        # Generic errors
        "GEN_001": "Internal server error",
        "GEN_002": "Service unavailable",
        "GEN_003": "Bad request",
    }

    def __init__(self):
        self.circuit_breakers = {}
        self.rate_limiters = {}
        # Initialize LLM circuit breaker
        self._init_llm_circuit_breaker()

    def handle_error(
        self,
        request: Request,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None,
    ) -> JSONResponse:
        """
        Centralized error handling with security best practices.

        Args:
            request: FastAPI request object
            exception: Exception to handle
            context: Additional context for logging

        Returns:
            JSONResponse with standardized error format
        """
        context = context or {}
        request_id = str(context.get("request_id") or getattr(request.state, "request_id", "unknown"))

        # Handle SecurityError specifically
        if isinstance(exception, SecurityError):
            return self._handle_security_error(request, exception, request_id)

        # Handle HTTPException
        elif isinstance(exception, HTTPException):
            return self._handle_http_exception(request, exception, request_id)

        # Handle all other exceptions
        else:
            return self._handle_generic_error(request, exception, request_id)

    def _handle_security_error(self, request: Request, exception: SecurityError, request_id: str) -> JSONResponse:
        """Handle SecurityError with appropriate logging and response."""
        error_code = exception.error_code
        status_code = exception.status_code

        # Log sensitive details server-side only
        log_method = getattr(logger, exception.log_level.lower(), logger.error)
        log_method(
            f"Security error [{error_code}]: {exception.message}. "
            f"Details: {exception.details}. "
            f"Path: {request.url.path}. "
            f"Request ID: {request_id}"
        )

        # Create standardized response (sanitized)
        error_response = ErrorResponse(
            error_code=error_code,
            message=self.ERROR_CODES.get(error_code, "Security error"),
            status_code=status_code,
            request_id=request_id,
        )

        return JSONResponse(
            content=error_response.to_dict(),
            status_code=status_code,
            headers={"X-Request-ID": request_id},
        )

    def _handle_http_exception(self, request: Request, exception: HTTPException, request_id: str) -> JSONResponse:
        """Handle HTTPException with standardized format."""
        status_code = exception.status_code

        # Map common HTTP errors to our error codes
        error_code_map = {
            400: "GEN_003",  # Bad Request
            401: "AUTH_001",  # Unauthorized
            403: "AUTHZ_001",  # Forbidden
            404: "AUTHZ_002",  # Not Found
            429: "RATE_001",  # Too Many Requests
            500: "GEN_001",  # Internal Server Error
        }

        error_code = error_code_map.get(status_code, "GEN_001")

        # Log the original error details
        logger.warning(
            f"HTTP {status_code} error: {exception.detail}. " f"Path: {request.url.path}. " f"Request ID: {request_id}"
        )

        error_response = ErrorResponse(
            error_code=error_code,
            message=self.ERROR_CODES.get(error_code, "Request failed"),
            status_code=status_code,
            request_id=request_id,
        )

        return JSONResponse(
            content=error_response.to_dict(),
            status_code=status_code,
            headers={"X-Request-ID": request_id},
        )

    def _handle_generic_error(self, request: Request, exception: Exception, request_id: str) -> JSONResponse:
        """Handle generic exceptions with security best practices."""
        # Log full error details server-side
        logger.error(
            f"Unexpected error: {str(exception)}. "
            f"Type: {type(exception).__name__}. "
            f"Path: {request.url.path}. "
            f"Request ID: {request_id}",
            exc_info=True,
        )

        # Return generic error to client (no sensitive details)
        error_response = ErrorResponse(
            error_code="GEN_001",
            message="Internal server error",
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            request_id=request_id,
        )

        return JSONResponse(
            content=error_response.to_dict(),
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            headers={"X-Request-ID": request_id},
        )

    def create_security_error(
        self, error_type: str, details: Optional[str] = None, log_level: str = "ERROR"
    ) -> SecurityError:
        """Factory method for creating standardized security errors."""
        error_configs = {
            "invalid_credentials": {
                "code": "AUTH_001",
                "status": HTTP_401_UNAUTHORIZED,
                "message": "Invalid credentials",
            },
            "token_expired": {
                "code": "AUTH_002",
                "status": HTTP_401_UNAUTHORIZED,
                "message": "Token expired",
            },
            "token_invalid": {
                "code": "AUTH_003",
                "status": HTTP_401_UNAUTHORIZED,
                "message": "Token invalid",
            },
            "insufficient_permissions": {
                "code": "AUTH_004",
                "status": HTTP_403_FORBIDDEN,
                "message": "Insufficient permissions",
            },
            "access_denied": {
                "code": "AUTHZ_001",
                "status": HTTP_403_FORBIDDEN,
                "message": "Access denied",
            },
            "resource_not_found": {
                "code": "AUTHZ_002",
                "status": HTTP_404_NOT_FOUND,
                "message": "Resource not found",
            },
            "rate_limit_exceeded": {
                "code": "RATE_001",
                "status": HTTP_429_TOO_MANY_REQUESTS,
                "message": "Too many requests",
            },
            "llm_unavailable": {
                "code": "LLM_001",
                "status": HTTP_503_SERVICE_UNAVAILABLE,
                "message": "LLM service unavailable",
            },
            "invalid_input": {
                "code": "VAL_001",
                "status": HTTP_400_BAD_REQUEST,
                "message": "Invalid input",
            },
        }

        config = error_configs.get(error_type)
        if not config:
            config = error_configs["access_denied"]

        return SecurityError(
            status_code=config["status"],
            error_code=config["code"],
            message=config["message"],
            details=details,
            log_level=log_level,
        )

    def _init_llm_circuit_breaker(self):
        """Initialize circuit breaker for LLM services."""
        self.circuit_breakers["llm"] = {
            "state": "closed",  # closed, open, half-open
            "failure_count": 0,
            "failure_threshold": 5,  # Open after 5 failures
            "reset_timeout": 60,  # 60 seconds before half-open
            "last_failure_time": None,
            "half_open_attempts": 0,
            "half_open_success_threshold": 2,  # Successes to close
        }

    def check_llm_circuit_breaker(self) -> bool:
        """
        Check if LLM circuit breaker allows requests.

        Returns:
            True if request should proceed, False if blocked
        """
        cb = self.circuit_breakers["llm"]

        if cb["state"] == "open":
            # Check if timeout has elapsed
            if cb["last_failure_time"] and (datetime.utcnow() - cb["last_failure_time"]).seconds >= cb["reset_timeout"]:
                cb["state"] = "half-open"
                cb["half_open_attempts"] = 0
                logger.info("LLM circuit breaker transitioning to half-open state")
            else:
                logger.warning("LLM circuit breaker is OPEN - blocking request")
                return False

        return True

    def record_llm_failure(self):
        """Record an LLM failure and update circuit breaker state."""
        cb = self.circuit_breakers["llm"]

        if cb["state"] == "closed":
            cb["failure_count"] += 1
            cb["last_failure_time"] = datetime.utcnow()

            if cb["failure_count"] >= cb["failure_threshold"]:
                cb["state"] = "open"
                logger.error(f"LLM circuit breaker OPENED after {cb['failure_count']} failures")

        elif cb["state"] == "half-open":
            cb["half_open_attempts"] += 1
            cb["state"] = "open"
            cb["last_failure_time"] = datetime.utcnow()
            logger.warning("LLM circuit breaker re-opened after half-open failure")

    def record_llm_success(self):
        """Record an LLM success and update circuit breaker state."""
        cb = self.circuit_breakers["llm"]

        if cb["state"] == "half-open":
            cb["half_open_attempts"] += 1

            if cb["half_open_attempts"] >= cb["half_open_success_threshold"]:
                cb["state"] = "closed"
                cb["failure_count"] = 0
                cb["half_open_attempts"] = 0
                logger.info("LLM circuit breaker CLOSED after successful half-open phase")

    def get_llm_circuit_breaker_status(self) -> Dict[str, Any]:
        """Get current LLM circuit breaker status."""
        cb = self.circuit_breakers["llm"]
        return {
            "state": cb["state"],
            "failure_count": cb["failure_count"],
            "failure_threshold": cb["failure_threshold"],
            "reset_timeout": cb["reset_timeout"],
            "last_failure_time": cb["last_failure_time"].isoformat() if cb["last_failure_time"] else None,
            "half_open_attempts": cb["half_open_attempts"],
            "half_open_success_threshold": cb["half_open_success_threshold"],
        }

    def sanitize_error_message(self, message: str) -> str:
        """
        Sanitize error messages to prevent information leakage.

        Removes sensitive information like:
        - Stack traces
        - Internal paths
        - Database connection details
        - API keys and secrets
        """
        if not message:
            return "Request failed"

        # Remove common sensitive patterns
        sensitive_patterns = [
            r"secret\s*[=:]\s*[\w\-]+",
            r"key\s*[=:]\s*[\w\-]+",
            r"password\s*[=:]\s*[\w\-]+",
            r"token\s*[=:]\s*[\w\-]+",
            r"db\s*[=:]\s*[\w\-]+",
            r"api\s*[=:]\s*[\w\-]+",
            r"file\s*[=:]\s*[^\s]+",
            r"path\s*[=:]\s*[^\s]+",
            r"[/\\][\w\-\.]+",  # File paths
            r"\b(?:secret|key|password|token|db|api)\b\s*[=:]\s*\S+",
            r"traceback.*",
            r"at\s+[\w\.]+",
            r"line\s+\d+",
            r"\b(?:localhost|127\.0\.0\.1)\b",
            r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
            r"\b(?:[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\b",
        ]

        sanitized = message
        for pattern in sensitive_patterns:
            import re

            sanitized = re.sub(pattern, "[REDACTED]", sanitized, flags=re.IGNORECASE)

        # Limit length to prevent information leakage
        if len(sanitized) > 200:
            sanitized = sanitized[:200] + "..."

        return sanitized.strip() or "Request failed"


# Global error handler instance
error_handler = ErrorHandler()


def get_error_handler() -> ErrorHandler:
    """Get the global error handler instance."""
    return error_handler


def llm_circuit_breaker(func):
    """
    Decorator to protect LLM endpoints with circuit breaker pattern.

    Usage:
        @llm_circuit_breaker
        async def generate_proposal_section(*args, **kwargs):
            # Your LLM code here
            pass
    """

    async def wrapper(*args, **kwargs):
        handler = get_error_handler()

        # Check circuit breaker before proceeding
        if not handler.check_llm_circuit_breaker():
            # Circuit breaker is open - return immediate failure
            security_error = handler.create_security_error("llm_unavailable")
            raise security_error

        try:
            # Execute the LLM operation
            result = await func(*args, **kwargs)

            # Record success
            handler.record_llm_success()

            return result

        except Exception as e:
            # Record failure
            handler.record_llm_failure()

            # Create appropriate error
            if isinstance(e, SecurityError):
                raise e
            else:
                security_error = handler.create_security_error(
                    "llm_unavailable", details=f"LLM operation failed: {str(e)}"
                )
                raise security_error

    return wrapper


def register_error_handlers(app):
    """Register error handlers with FastAPI app."""

    @app.exception_handler(SecurityError)
    async def security_error_handler(request: Request, exc: SecurityError):
        return error_handler.handle_error(request, exc)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return error_handler.handle_error(request, exc)

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        return error_handler.handle_error(request, exc)
