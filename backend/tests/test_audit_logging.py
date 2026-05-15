#!/usr/bin/env python3
"""
Test suite for comprehensive audit logging.
Tests TASK-SEC-008: Implement Comprehensive Audit Logging
"""

import pytest
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from backend.core.audit_logging import (
    AuditLogger,
    AuditEvent,
    setup_audit_logging,
)


@pytest.fixture
def audit_logger():
    """Create an audit logger instance for testing."""
    return AuditLogger()


def test_audit_logger_initialization(audit_logger):
    """Test that AuditLogger initializes correctly."""
    assert audit_logger is not None
    assert hasattr(audit_logger, "log_events")
    assert hasattr(audit_logger, "security_events")


def test_audit_event_creation():
    """Test creation of audit events."""
    event = AuditEvent(
        event_type="security.login.success",
        user_id="test_user",
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0",
        metadata={"attempts": 1, "method": "password"},
    )

    assert event.event_type == "security.login.success"
    assert event.user_id == "test_user"
    assert event.ip_address == "192.168.1.1"
    assert event.user_agent == "Mozilla/5.0"
    assert event.timestamp is not None
    assert isinstance(event.timestamp, datetime)

    # Check that original metadata is preserved
    assert event.metadata["attempts"] == 1
    assert event.metadata["method"] == "password"

    # Check that compliance tags were added automatically
    assert "security_context" in event.metadata
    assert "compliance_tags" in event.metadata["security_context"]
    assert len(event.metadata["security_context"]["compliance_tags"]) > 0


def test_security_event_logging(audit_logger):
    """Test logging of security events."""
    with patch.object(audit_logger, "_write_log") as mock_write:
        audit_logger.log_security_event(
            user_id="test_user",
            event_type="login.attempt",
            success=True,
            ip_address="192.168.1.1",
            metadata={"attempts": 1},
        )

        # Verify the log was written
        mock_write.assert_called_once()

        # Check the event was stored
        assert len(audit_logger.security_events) == 1
        event = audit_logger.security_events[0]
        assert event.event_type == "security.login.attempt"
        assert event.user_id == "test_user"
        assert event.metadata["success"] is True


def test_api_call_logging(audit_logger):
    """Test logging of API calls."""
    with patch.object(audit_logger, "_write_log") as mock_write:
        audit_logger.log_api_call(
            user_id="test_user",
            endpoint="/api/proposals",
            method="POST",
            status_code=201,
            ip_address="192.168.1.1",
            response_time_ms=150,
        )

        mock_write.assert_called_once()
        assert len(audit_logger.log_events) == 1


def test_data_access_logging(audit_logger):
    """Test logging of data access events."""
    with patch.object(audit_logger, "_write_log") as mock_write:
        audit_logger.log_data_access(
            user_id="test_user",
            resource_type="proposal",
            resource_id="prop_123",
            action="read",
            ip_address="192.168.1.1",
            metadata={"fields_accessed": ["title", "status"]},
        )

        mock_write.assert_called_once()
        assert len(audit_logger.log_events) == 1


def test_system_event_logging(audit_logger):
    """Test logging of system events."""
    with patch.object(audit_logger, "_write_log") as mock_write:
        audit_logger.log_system_event(
            event_type="system.startup",
            component="api_server",
            status="success",
            metadata={"version": "1.0.0", "environment": "production"},
        )

        mock_write.assert_called_once()
        assert len(audit_logger.log_events) == 1


def test_audit_log_format():
    """Test that audit logs are formatted correctly."""
    logger = AuditLogger()

    with patch.object(logger, "_write_log") as mock_write:
        logger.log_security_event(
            user_id="test_user",
            event_type="login.success",
            success=True,
            ip_address="192.168.1.1",
        )

        # Get the log call arguments
        call_args = mock_write.call_args[0]
        log_entry = call_args[0]

        # Verify JSON format
        parsed_log = json.loads(log_entry)
        assert "timestamp" in parsed_log
        assert "event_type" in parsed_log
        assert "user_id" in parsed_log
        assert "ip_address" in parsed_log
        assert "level" in parsed_log
        assert parsed_log["level"] == "INFO"


def test_sensitive_data_redaction():
    """Test that sensitive data is redacted from logs."""
    logger = AuditLogger()

    sensitive_metadata = {
        "password": "secret123",
        "api_key": "sk-123456",
        "credit_card": "4111-1111-1111-1111",
        "safe_data": "ok",
    }

    with patch.object(logger, "_write_log") as mock_write:
        logger.log_api_call(
            user_id="test_user",
            endpoint="/api/login",
            method="POST",
            status_code=200,
            metadata=sensitive_metadata,
        )

        call_args = mock_write.call_args[0]
        log_entry = call_args[0]
        parsed_log = json.loads(log_entry)

        # Verify sensitive data is redacted
        assert parsed_log["metadata"]["password"] == "[REDACTED]"
        assert parsed_log["metadata"]["api_key"] == "[REDACTED]"
        assert parsed_log["metadata"]["credit_card"] == "[REDACTED]"
        assert parsed_log["metadata"]["safe_data"] == "ok"


def test_audit_log_rotation():
    """Test that audit logs rotate properly."""
    logger = AuditLogger(max_log_size=100, max_log_files=3)

    # Mock the file operations
    with patch("builtins.open", create=True) as mock_open:
        mock_file = MagicMock()
        mock_file.tell.return_value = 200  # Simulate large log
        mock_open.return_value.__enter__.return_value = mock_file

        # Force log rotation
        for i in range(5):
            logger.log_system_event(event_type=f"test.event.{i}", component="test", status="success")

        # Verify rotation happened
        assert mock_open.call_count >= 2  # Original file + rotated files


def test_audit_log_search():
    """Test searching through audit logs."""
    logger = AuditLogger()

    # Add some test events
    logger.log_security_event(user_id="user1", event_type="login.success", success=True)
    logger.log_security_event(user_id="user2", event_type="login.failed", success=False)
    logger.log_api_call(user_id="user1", endpoint="/api/proposals", method="GET")

    # Search for user1 events
    user1_events = logger.search_events(user_id="user1")
    assert len(user1_events) == 2

    # Search for security events
    security_events = logger.search_events(event_type="security")
    assert len(security_events) == 2

    # Search with time range
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    recent_events = logger.search_events(after=one_hour_ago)
    assert len(recent_events) >= 3


def test_audit_log_export():
    """Test exporting audit logs."""
    logger = AuditLogger()

    # Add test events
    logger.log_security_event(user_id="test_user", event_type="login.success", success=True)
    logger.log_api_call(user_id="test_user", endpoint="/api/proposals", method="POST")

    # Export logs
    with patch("builtins.open", create=True) as mock_open:
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        export_path = "/tmp/audit_export.json"
        logger.export_logs(export_path)

        # Verify export was attempted
        mock_open.assert_called_with(export_path, "w", encoding="utf-8")
        mock_file.write.assert_called()


def test_middleware_integration():
    """Test audit logging middleware integration."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    # Create test app
    app = FastAPI()
    setup_audit_logging(app)

    @app.get("/test")
    async def test_endpoint():
        return {"message": "hello"}

    client = TestClient(app)

    # Make request
    response = client.get("/test")
    assert response.status_code == 200

    # Verify audit log was created
    assert hasattr(app.state, "audit_logger")
    assert len(app.state.audit_logger.log_events) > 0


def test_security_event_thresholds():
    """Test security event threshold alerts."""
    logger = AuditLogger(failed_login_threshold=3)

    # Add failed login attempts
    for i in range(3):
        logger.log_security_event(
            user_id="attacker",
            event_type="login.failed",
            success=False,
            ip_address="192.168.1.100",
        )

    # Third attempt should trigger alert
    with patch.object(logger, "_trigger_alert") as mock_alert:
        logger.log_security_event(
            user_id="attacker",
            event_type="login.failed",
            success=False,
            ip_address="192.168.1.100",
        )

        mock_alert.assert_called_once()
        call_args = mock_alert.call_args[0]
        assert "Brute force attempt detected" in call_args[0]


def test_compliance_reporting():
    """Test generation of compliance reports."""
    logger = AuditLogger()

    # Add various events
    logger.log_security_event(user_id="user1", event_type="login.success", success=True)
    logger.log_security_event(user_id="user2", event_type="login.failed", success=False)
    logger.log_api_call(user_id="user1", endpoint="/api/sensitive", method="GET")
    logger.log_data_access(user_id="user1", resource_type="proposal", action="read")

    # Generate compliance report
    report = logger.generate_compliance_report()

    assert "total_events" in report
    assert "security_events" in report
    assert "api_calls" in report
    assert "data_access" in report
    assert "users" in report
    assert report["total_events"] >= 4


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
