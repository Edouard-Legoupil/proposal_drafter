# Standard Library
from unittest.mock import MagicMock

# Third-Party Libraries
import pytest
from fastapi import HTTPException

# Local Imports
from backend.core.error_handlers import (
    ErrorHandler,
    SecurityError,
    ErrorResponse,
    get_error_handler,
    llm_circuit_breaker,
)


class TestSecurityError:
    """Test suite for SecurityError class."""

    def test_security_error_creation(self):
        """Test SecurityError creation with all parameters."""
        error = SecurityError(
            status_code=403,
            error_code="AUTHZ_001",
            message="Access denied",
            details="User 123 attempted to access proposal 456",
            log_level="WARNING",
        )

        assert error.status_code == 403
        assert error.error_code == "AUTHZ_001"
        assert error.message == "Access denied"
        assert error.details == "User 123 attempted to access proposal 456"
        assert error.log_level == "WARNING"

    def test_security_error_defaults(self):
        """Test SecurityError with default parameters."""
        error = SecurityError(status_code=401, error_code="AUTH_001", message="Invalid credentials")

        assert error.status_code == 401
        assert error.error_code == "AUTH_001"
        assert error.message == "Invalid credentials"
        assert error.details is None
        assert error.log_level == "ERROR"


class TestErrorResponse:
    """Test suite for ErrorResponse class."""

    def test_error_response_creation(self):
        """Test ErrorResponse creation."""
        response = ErrorResponse(
            error_code="AUTH_001",
            message="Invalid credentials",
            status_code=401,
            request_id="test-123",
        )

        assert response.error_code == "AUTH_001"
        assert response.message == "Invalid credentials"
        assert response.status_code == 401
        assert response.request_id == "test-123"
        assert "timestamp" in response.to_dict()["error"]

    def test_error_response_to_dict(self):
        """Test ErrorResponse serialization."""
        response = ErrorResponse(error_code="AUTHZ_001", message="Access denied", status_code=403)

        result = response.to_dict()

        assert "error" in result
        assert result["error"]["code"] == "AUTHZ_001"
        assert result["error"]["message"] == "Access denied"
        assert result["error"]["status_code"] == 403
        assert "timestamp" in result["error"]
        assert "request_id" in result["error"]


class TestErrorHandler:
    """Test suite for ErrorHandler class."""

    def test_error_handler_initialization(self):
        """Test ErrorHandler initialization."""
        handler = ErrorHandler()

        # LLM circuit breaker should be initialized automatically
        assert "llm" in handler.circuit_breakers
        assert handler.rate_limiters == {}

        cb = handler.circuit_breakers["llm"]
        assert cb["state"] == "closed"
        assert cb["failure_count"] == 0

    def test_create_security_error(self):
        """Test creating security errors."""
        handler = ErrorHandler()

        # Test various error types
        error1 = handler.create_security_error("invalid_credentials")
        assert error1.error_code == "AUTH_001"
        assert error1.status_code == 401

        error2 = handler.create_security_error("access_denied")
        assert error2.error_code == "AUTHZ_001"
        assert error2.status_code == 403

        error3 = handler.create_security_error("llm_unavailable")
        assert error3.error_code == "LLM_001"
        assert error3.status_code == 503

    def test_sanitize_error_message(self):
        """Test error message sanitization."""
        handler = ErrorHandler()

        # Test sensitive information removal
        dirty_message = "Error at line 42 in /app/secrets.py: secret=abc123, key=def456"
        clean_message = handler.sanitize_error_message(dirty_message)

        assert "[REDACTED]" in clean_message
        assert "line 42" not in clean_message
        assert "/app/secrets.py" not in clean_message
        assert "abc123" not in clean_message
        assert "def456" not in clean_message

        # Test length limiting
        long_message = "A" * 250
        limited_message = handler.sanitize_error_message(long_message)
        assert len(limited_message) <= 203  # 200 chars + "..."
        assert limited_message.endswith("...")

    def test_handle_security_error(self):
        """Test handling of SecurityError."""
        handler = ErrorHandler()

        # Create a mock request
        mock_request = MagicMock()
        mock_request.url.path = "/api/test"

        # Create a security error
        security_error = SecurityError(
            status_code=403,
            error_code="AUTHZ_001",
            message="Access denied",
            details="User 123 tried to access resource 456",
        )

        # Handle the error
        response = handler.handle_error(mock_request, security_error, {"request_id": "test-123"})

        assert response.status_code == 403
        response_data = response.body.decode("utf-8")
        # Verify the response contains the error structure but not sensitive details
        assert "AUTHZ_001" in response_data
        assert "Access denied" in response_data
        assert "User 123 tried to access resource 456" not in response_data  # Details should not be exposed

    def test_handle_http_exception(self):
        """Test handling of HTTPException."""
        handler = ErrorHandler()

        # Create a mock request
        mock_request = MagicMock()
        mock_request.url.path = "/api/test"

        # Create an HTTP exception
        http_error = HTTPException(status_code=404, detail="Resource not found")

        # Handle the error
        response = handler.handle_error(mock_request, http_error, {"request_id": "test-123"})

        assert response.status_code == 404
        response_data = response.body.decode("utf-8")
        assert "AUTHZ_002" in response_data  # Should map to resource not found

    def test_handle_generic_error(self):
        """Test handling of generic exceptions."""
        handler = ErrorHandler()

        # Create a mock request
        mock_request = MagicMock()
        mock_request.url.path = "/api/test"

        # Create a generic exception
        generic_error = ValueError("Something went wrong")

        # Handle the error
        response = handler.handle_error(mock_request, generic_error, {"request_id": "test-123"})

        assert response.status_code == 500
        response_data = response.body.decode("utf-8")
        assert "GEN_001" in response_data  # Should map to internal server error
        assert "Internal server error" in response_data
        # Original error message should not be exposed
        assert "Something went wrong" not in response_data


class TestCircuitBreaker:
    """Test suite for circuit breaker functionality."""

    def test_llm_circuit_breaker_initialization(self):
        """Test LLM circuit breaker initialization."""
        handler = ErrorHandler()
        handler._init_llm_circuit_breaker()

        cb = handler.circuit_breakers["llm"]
        assert cb["state"] == "closed"
        assert cb["failure_count"] == 0
        assert cb["failure_threshold"] == 5
        assert cb["reset_timeout"] == 60

    def test_circuit_breaker_open_on_failures(self):
        """Test circuit breaker opens after threshold failures."""
        handler = ErrorHandler()
        handler._init_llm_circuit_breaker()

        # Simulate failures
        for i in range(5):
            handler.record_llm_failure()

        cb = handler.circuit_breakers["llm"]
        assert cb["state"] == "open"
        assert cb["failure_count"] == 5

    def test_circuit_breaker_blocks_when_open(self):
        """Test circuit breaker blocks requests when open."""
        handler = ErrorHandler()
        handler._init_llm_circuit_breaker()

        # Open the circuit breaker
        for i in range(5):
            handler.record_llm_failure()

        # Should block requests
        can_proceed = handler.check_llm_circuit_breaker()
        assert can_proceed is False

    def test_circuit_breaker_half_open_after_timeout(self):
        """Test circuit breaker transitions to half-open after timeout."""
        handler = ErrorHandler()
        handler._init_llm_circuit_breaker()

        # Open the circuit breaker
        for i in range(5):
            handler.record_llm_failure()

        # Mock the timeout by setting last_failure_time in the past
        from datetime import datetime, timedelta

        cb = handler.circuit_breakers["llm"]
        cb["last_failure_time"] = datetime.utcnow() - timedelta(seconds=61)

        # Should now allow requests (half-open state)
        can_proceed = handler.check_llm_circuit_breaker()
        assert can_proceed is True
        assert cb["state"] == "half-open"

    def test_circuit_breaker_closes_after_successes(self):
        """Test circuit breaker closes after successful half-open attempts."""
        handler = ErrorHandler()
        handler._init_llm_circuit_breaker()

        # Open and transition to half-open
        for i in range(5):
            handler.record_llm_failure()

        from datetime import datetime, timedelta

        cb = handler.circuit_breakers["llm"]
        cb["last_failure_time"] = datetime.utcnow() - timedelta(seconds=61)

        # Transition to half-open
        handler.check_llm_circuit_breaker()

        # Record successes
        for i in range(2):
            handler.record_llm_success()

        # Should now be closed
        assert cb["state"] == "closed"
        assert cb["failure_count"] == 0


class TestCircuitBreakerDecorator:
    """Test suite for circuit breaker decorator."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_decorator_success(self):
        """Test circuit breaker decorator allows successful operations."""
        handler = get_error_handler()
        handler._init_llm_circuit_breaker()

        @llm_circuit_breaker
        async def mock_llm_operation():
            return {"result": "success"}

        # Should succeed
        result = await mock_llm_operation()
        assert result["result"] == "success"

        # Check that success was recorded
        cb = handler.circuit_breakers["llm"]
        assert cb["state"] == "closed"

    @pytest.mark.asyncio
    async def test_circuit_breaker_decorator_failure(self):
        """Test circuit breaker decorator handles failures."""
        handler = get_error_handler()
        handler._init_llm_circuit_breaker()

        @llm_circuit_breaker
        async def mock_failing_llm_operation():
            raise Exception("LLM failed")

        # Should raise SecurityError
        with pytest.raises(SecurityError) as exc_info:
            await mock_failing_llm_operation()

        # Verify it's the right error type
        error = exc_info.value
        assert error.error_code == "LLM_001"
        assert error.status_code == 503

        # Check that failure was recorded
        cb = handler.circuit_breakers["llm"]
        assert cb["failure_count"] == 1

    @pytest.mark.asyncio
    async def test_circuit_breaker_decorator_blocks_when_open(self):
        """Test circuit breaker decorator blocks when circuit is open."""
        handler = get_error_handler()
        handler._init_llm_circuit_breaker()

        # Open the circuit breaker
        for i in range(5):
            handler.record_llm_failure()

        @llm_circuit_breaker
        async def mock_llm_operation():
            return {"result": "success"}

        # Should raise SecurityError immediately without calling the function
        with pytest.raises(SecurityError) as exc_info:
            await mock_llm_operation()

        error = exc_info.value
        assert error.error_code == "LLM_001"


class TestSecurityFocusedScenarios:
    """Test suite for security-focused error scenarios."""

    def test_information_leakage_prevention(self):
        """Test that sensitive information is not leaked in error responses."""
        handler = ErrorHandler()

        # Create an error with sensitive details
        sensitive_error = SecurityError(
            status_code=500,
            error_code="GEN_001",
            message="Internal server error",
            details="Database connection failed: user=admin, password=secret, host=localhost",
        )

        # Create a mock request
        mock_request = MagicMock()
        mock_request.url.path = "/api/test"

        # Handle the error
        response = handler.handle_error(mock_request, sensitive_error, {"request_id": "test-123"})

        # Verify response doesn't contain sensitive info
        response_data = response.body.decode("utf-8")
        assert "admin" not in response_data
        assert "secret" not in response_data
        assert "localhost" not in response_data
        assert "Database connection failed" not in response_data

    def test_consistent_auth_error_messages(self):
        """Test that authentication failures return consistent messages."""
        handler = ErrorHandler()

        # Test that invalid_credentials returns generic message for security
        error = handler.create_security_error("invalid_credentials")
        assert error.message == "Invalid credentials"
        assert error.status_code == 401

        # Other auth errors can have specific messages
        token_error = handler.create_security_error("token_expired")
        assert token_error.message == "Token expired"
        assert token_error.status_code == 401

        # Test access denied
        access_error = handler.create_security_error("access_denied")
        assert access_error.message == "Access denied"
        assert access_error.status_code == 403

    def test_error_response_consistency(self):
        """Test that all error responses have consistent structure."""
        handler = ErrorHandler()

        # Test different error scenarios
        errors = [
            handler.create_security_error("invalid_credentials"),
            handler.create_security_error("access_denied"),
            handler.create_security_error("llm_unavailable"),
        ]

        mock_request = MagicMock()
        mock_request.url.path = "/api/test"

        for error in errors:
            response = handler.handle_error(mock_request, error, {"request_id": "test-123"})
            response_data = response.body.decode("utf-8")

            # All responses should have the same structure
            assert '"error"' in response_data
            assert '"code"' in response_data
            assert '"message"' in response_data
            assert '"status_code"' in response_data
            assert '"timestamp"' in response_data
            assert '"request_id"' in response_data


# Clean up environment variables after tests
def teardown_function():
    """Clean up any test-specific environment variables."""
    # No specific cleanup needed for these tests
    pass
