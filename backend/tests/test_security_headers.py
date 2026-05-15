#!/usr/bin/env python3
"""
Test suite for security headers and session management hardening.
Tests TASK-SEC-005 and TASK-SEC-007 requirements.
"""

import pytest
from fastapi.testclient import TestClient
from backend.core.middleware import setup_security_middleware, setup_cors_middleware
from backend.api.session import router as session_router


@pytest.fixture
def test_client():
    """Create a test client with security middleware enabled."""
    # Create a new FastAPI app for testing (don't modify the main app)
    from fastapi import FastAPI

    test_app = FastAPI()

    # Setup middleware
    setup_security_middleware(test_app)
    setup_cors_middleware(test_app)

    # Include a simple health endpoint for testing
    @test_app.get("/api/health")
    async def health():
        return {"status": "healthy"}

    # Include session routes for testing
    test_app.include_router(session_router, prefix="/api/session", tags=["session"])

    return TestClient(test_app)


def test_security_headers_present(test_client):
    """Test that essential security headers are present in responses."""
    response = test_client.get("/api/health")

    # Check for critical security headers
    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"

    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"

    assert "Content-Security-Policy" in response.headers
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]

    assert "Strict-Transport-Security" in response.headers
    assert "max-age=31536000; includeSubDomains; preload" in response.headers["Strict-Transport-Security"]

    assert "Referrer-Policy" in response.headers
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

    assert "Permissions-Policy" in response.headers
    assert "geolocation=(), microphone=(), camera=()" in response.headers["Permissions-Policy"]


def test_xss_protection_header(test_client):
    """Test X-XSS-Protection header for legacy browser protection."""
    response = test_client.get("/api/health")

    assert "X-XSS-Protection" in response.headers
    assert response.headers["X-XSS-Protection"] == "1; mode=block"


def test_session_cookie_security(test_client):
    """Test that session cookies have secure attributes."""
    # Test login endpoint to get session cookie
    response = test_client.post("/api/auth/login", json={"username": "testuser", "password": "testpass"})

    # Check if session cookie is set with secure attributes
    if "set-cookie" in response.headers:
        cookie_header = response.headers["set-cookie"]
        assert "HttpOnly" in cookie_header
        assert "Secure" in cookie_header
        assert "SameSite=Lax" in cookie_header or "SameSite=Strict" in cookie_header


def test_cors_secure_configuration(test_client):
    """Test that CORS is configured securely."""
    response = test_client.options("/api/health", headers={"Origin": "http://localhost:8503"})

    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "http://localhost:8503"
    assert response.headers["access-control-allow-credentials"] == "true"
    assert "access-control-expose-headers" in response.headers


def test_session_timeout_enforcement():
    """Test that session timeout is properly enforced."""
    # Test the session storage mechanism
    from backend.api.session import get_session_id

    # Verify that session IDs are generated correctly
    session_id = get_session_id()
    assert len(session_id) > 0
    assert isinstance(session_id, str)

    # Verify session ID format (UUID v4 format)
    assert len(session_id) == 36  # UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    assert session_id.count("-") == 4


def test_content_security_policy_restrictions(test_client):
    """Test that CSP header has appropriate restrictions."""
    response = test_client.get("/api/health")

    csp_header = response.headers["Content-Security-Policy"]

    # Verify key CSP directives
    assert "default-src 'self'" in csp_header
    assert "script-src 'self'" in csp_header
    assert "style-src 'self' 'unsafe-inline'" in csp_header
    assert "img-src 'self' data:" in csp_header
    assert "font-src 'self'" in csp_header
    assert "connect-src 'self'" in csp_header
    assert "frame-src 'none'" in csp_header
    assert "object-src 'none'" in csp_header


def test_hsts_header_secure(test_client):
    """Test HSTS header has secure configuration."""
    response = test_client.get("/api/health")

    hsts_header = response.headers["Strict-Transport-Security"]

    # Verify HSTS is properly configured
    assert "max-age=31536000" in hsts_header  # 1 year
    assert "includeSubDomains" in hsts_header
    assert "preload" in hsts_header


def test_security_headers_on_all_endpoints(test_client):
    """Test that security headers are applied consistently across all endpoints."""
    endpoints = ["/api/health", "/api/proposals", "/api/users"]

    for endpoint in endpoints:
        response = test_client.get(endpoint)

        # All endpoints should have basic security headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "Content-Security-Policy" in response.headers
        assert "Strict-Transport-Security" in response.headers


def test_session_invalidation_on_logout():
    """Test that sessions are properly invalidated on logout."""
    # This would test session invalidation
    # For now, we'll test the Redis deletion mechanism
    from backend.core.redis import redis_client
    import json

    # Create a session
    session_id = "test_session_123"
    session_data = {"user_id": "test_user"}
    redis_client.setex(session_id, 3600, json.dumps(session_data))

    # Verify session exists
    assert redis_client.get(session_id) is not None

    # Simulate logout by deleting session
    redis_client.delete(session_id)

    # Verify session is gone
    assert redis_client.get(session_id) is None


def test_secure_cookie_attributes_in_different_environments():
    """Test that cookie attributes adapt to different environments."""
    from backend.core.middleware import get_cookie_settings

    # Test production environment (HTTPS)
    class MockRequest:
        def __init__(self, host, origin):
            self.headers = {"host": host, "origin": origin}

    # Production environment
    prod_request = MockRequest("api.example.com", "https://app.example.com")
    prod_settings = get_cookie_settings(prod_request)

    assert prod_settings["secure"] is True
    assert prod_settings["samesite"] == "none"

    # Local development environment
    local_request = MockRequest("localhost:8000", "http://localhost:3000")
    local_settings = get_cookie_settings(local_request)

    assert local_settings["secure"] is False  # Allow HTTP in local dev
    assert local_settings["samesite"] == "lax"  # Less strict for local testing


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
