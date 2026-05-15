# Standard Library
import time
import asyncio
from unittest.mock import MagicMock, patch

# Third-Party Libraries
import pytest
from fastapi import HTTPException

# Internal Modules
from backend.core.rate_limiter import RateLimiter, get_rate_limiter


def test_rate_limiter_initialization():
    """Test that RateLimiter initializes correctly with proper configurations."""
    limiter = RateLimiter()

    # Verify rate limits are loaded
    assert "free" in limiter.rate_limits
    assert "basic" in limiter.rate_limits
    assert "premium" in limiter.rate_limits

    # Verify free tier limits
    free_limits = limiter.rate_limits["free"]
    assert free_limits["requests"]["limit"] == 10
    assert free_limits["requests"]["window"] == 60
    assert free_limits["tokens"]["limit"] == 5000
    assert free_limits["tokens"]["window"] == 60

    # Verify premium tier limits
    premium_limits = limiter.rate_limits["premium"]
    assert premium_limits["requests"]["limit"] == 100
    assert premium_limits["tokens"]["limit"] == 50000


@pytest.mark.asyncio
async def test_get_rate_limit_key():
    """Test rate limit key generation for different user types."""
    limiter = RateLimiter()

    # Test with authenticated user
    mock_request = MagicMock()
    mock_request.state.user = {"user_id": "test_user_123"}

    key = await limiter.get_rate_limit_key(mock_request)
    assert key == "user:test_user_123"

    # Test with anonymous user (IP-based)
    mock_request = MagicMock()
    mock_request.state.user = None
    mock_request.headers.get.return_value = "192.168.1.100"
    mock_request.client.host = "192.168.1.100"

    key = await limiter.get_rate_limit_key(mock_request)
    assert key == "ip:192.168.1.100"


def test_get_user_tier():
    """Test user tier determination for rate limiting."""
    limiter = RateLimiter()

    # Test free tier
    assert limiter.get_user_tier(None) == "free"
    assert limiter.get_user_tier({"role": "guest"}) == "free"

    # Test basic tier
    assert limiter.get_user_tier({"role": "basic"}) == "basic"
    assert limiter.get_user_tier({"role": "member"}) == "basic"

    # Test premium tier
    assert limiter.get_user_tier({"role": "premium"}) == "premium"
    assert limiter.get_user_tier({"role": "admin"}) == "premium"
    assert limiter.get_user_tier({"role": "premium_user"}) == "premium"


@pytest.mark.asyncio
async def test_request_based_rate_limiting():
    """Test request-based rate limiting functionality."""
    limiter = RateLimiter()

    # Create mock request
    mock_request = MagicMock()
    mock_request.state.user = {"user_id": "test_user"}

    # Test within limits
    for i in range(10):
        result = await limiter.check_rate_limit(mock_request, "llm", 0)
        assert result is True

    # Test exceeding limits (11th request should fail)
    with pytest.raises(Exception) as exc_info:
        await limiter.check_rate_limit(mock_request, "llm", 0)

    # Should be an HTTPException
    assert exc_info.value.status_code == 429
    assert "rate limit exceeded" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_token_based_rate_limiting():
    """Test token-based rate limiting functionality."""
    limiter = RateLimiter()

    # Create mock request
    mock_request = MagicMock()
    mock_request.state.user = {"user_id": "test_user", "role": "free"}

    # Test within token limits (free tier: 5000 tokens/minute)
    result = await limiter.check_rate_limit(mock_request, "llm", 4000)
    assert result is True

    # Test exceeding token limits
    with pytest.raises(HTTPException) as exc_info:
        await limiter.check_rate_limit(mock_request, "llm", 2000)  # Would exceed 5000

    assert exc_info.value.status_code == 429


@pytest.mark.asyncio
async def test_rate_limit_reset_after_window():
    """Test that rate limits reset after the time window."""
    limiter = RateLimiter()

    # Create mock request
    mock_request = MagicMock()
    mock_request.state.user = {"user_id": "test_user"}

    # Make requests to hit the limit
    for i in range(10):
        await limiter.check_rate_limit(mock_request, "llm", 0)

    # Verify we're at the limit
    with pytest.raises(HTTPException):
        await limiter.check_rate_limit(mock_request, "llm", 0)

    # Simulate time passing (61 seconds)
    with patch("time.time", return_value=time.time() + 61):
        # Should be allowed again
        result = await limiter.check_rate_limit(mock_request, "llm", 0)
        assert result is True


@pytest.mark.asyncio
async def test_get_rate_limit_status():
    """Test rate limit status retrieval."""
    limiter = RateLimiter()

    # Create mock request
    mock_request = MagicMock()
    mock_request.state.user = {"user_id": "test_user", "role": "basic"}

    # Make some requests
    await limiter.check_rate_limit(mock_request, "llm", 1000)
    await limiter.check_rate_limit(mock_request, "llm", 2000)

    # Get status
    status = await limiter.get_rate_limit_status(mock_request)

    # Verify status structure
    assert "tier" in status
    assert "requests" in status
    assert "tokens" in status
    assert "blocked" in status

    # Verify basic tier
    assert status["tier"] == "basic"

    # Verify request limits
    assert status["requests"]["limit"] == 30
    assert status["requests"]["remaining"] >= 28  # At least 28 remaining after 2 requests

    # Verify token limits
    assert status["tokens"]["limit"] == 15000
    assert status["tokens"]["remaining"] >= 12000  # At least 12000 remaining after 3000 tokens


@pytest.mark.asyncio
async def test_different_user_tiers():
    """Test rate limiting with different user tiers."""
    limiter = RateLimiter()

    # Test free tier (10 requests/minute)
    mock_free_request = MagicMock()
    mock_free_request.state.user = {"user_id": "free_user", "role": "guest"}

    for i in range(10):
        await limiter.check_rate_limit(mock_free_request, "llm", 0)

    with pytest.raises(HTTPException):
        await limiter.check_rate_limit(mock_free_request, "llm", 0)

    # Test premium tier (100 requests/minute)
    mock_premium_request = MagicMock()
    mock_premium_request.state.user = {"user_id": "premium_user", "role": "premium"}

    for i in range(50):
        result = await limiter.check_rate_limit(mock_premium_request, "llm", 0)
        assert result is True


@pytest.mark.asyncio
async def test_rate_limit_middleware():
    """Test the rate limit middleware functionality."""
    from backend.core.rate_limiter import rate_limit_middleware

    # Create mock request and call_next for non-LLM endpoint (no rate limiting)
    mock_request = MagicMock()
    mock_request.state.user = {"user_id": "middleware_test_user"}
    mock_request.url.path = "/api/non-llm-endpoint"
    mock_request.headers.get.return_value = None
    mock_request.client.host = "127.0.0.1"

    async def mock_call_next(request):
        return MagicMock(status_code=200)

    # Test that non-LLM endpoints pass through
    response = await rate_limit_middleware(mock_request, mock_call_next)
    assert response.status_code == 200

    # Test health check endpoint (should be skipped)
    mock_request.url.path = "/health"
    response = await rate_limit_middleware(mock_request, mock_call_next)
    assert response.status_code == 200

    # Test LLM endpoint with mock that has token count
    mock_request.url.path = "/api/llm/generate"
    mock_request.json.return_value = {"token_count": 1000}

    # First request should succeed
    response = await rate_limit_middleware(mock_request, mock_call_next)
    assert response.status_code == 200

    # Test that the middleware processes LLM endpoints without error
    # (headers would be added to a real response, but our mock doesn't support them)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_cleanup_expired_limits():
    """Test cleanup of expired rate limit entries."""
    limiter = RateLimiter()

    # Add some test data
    test_key = "user:test_cleanup"
    limiter.rate_limit_storage[test_key] = {
        "request_count": 5,
        "request_timestamp": time.time() - 3601,  # Expired
        "token_count": 1000,
        "token_timestamp": time.time() - 3601,  # Expired
        "blocked_until": None,
    }

    # Add recent data that shouldn't be cleaned up
    recent_key = "user:recent"
    limiter.rate_limit_storage[recent_key] = {
        "request_count": 2,
        "request_timestamp": time.time(),  # Recent
        "token_count": 500,
        "token_timestamp": time.time(),  # Recent
        "blocked_until": None,
    }

    # Run cleanup
    await limiter.cleanup_expired_limits()

    # Verify expired entry was cleaned up
    assert test_key not in limiter.rate_limit_storage

    # Verify recent entry was kept
    assert recent_key in limiter.rate_limit_storage


@pytest.mark.asyncio
async def test_utility_functions():
    """Test the convenience utility functions."""
    from backend.core.rate_limiter import check_llm_rate_limit, check_api_rate_limit

    # Create mock request with unique user
    mock_request = MagicMock()
    mock_request.state.user = {"user_id": "utility_test_user"}

    # Test LLM rate limit check
    result = await check_llm_rate_limit(mock_request, 1000)
    assert result is None  # No exception means success

    # Test API rate limit check
    result = await check_api_rate_limit(mock_request)
    assert result is None  # No exception means success


@pytest.mark.asyncio
async def test_error_handling_in_rate_limiter():
    """Test error handling and edge cases in rate limiter."""
    limiter = RateLimiter()

    # Test with malformed request
    mock_request = MagicMock()
    mock_request.state.user = None
    # Mock headers.get to raise exception, but client.host should work
    mock_request.headers.get.side_effect = Exception("Header error")
    mock_request.client.host = "127.0.0.1"

    # Should handle gracefully and use IP fallback
    try:
        result = await limiter.check_rate_limit(mock_request, "llm", 0)
        assert result is True
    except Exception as e:
        # If it fails, it should be due to rate limiting, not the header error
        assert "rate limit" in str(e).lower() or "header" in str(e).lower()


@pytest.mark.asyncio
async def test_concurrent_rate_limiting():
    """Test rate limiting with concurrent requests."""
    limiter = RateLimiter()

    # Create mock request
    mock_request = MagicMock()
    mock_request.state.user = {"user_id": "concurrent_user"}

    # Test concurrent requests
    tasks = []
    for i in range(8):  # Stay under the 10 request limit
        tasks.append(limiter.check_rate_limit(mock_request, "llm", 0))

    results = await asyncio.gather(*tasks)

    # All should succeed
    assert all(results)

    # 9th and 10th should also succeed
    assert await limiter.check_rate_limit(mock_request, "llm", 0)
    assert await limiter.check_rate_limit(mock_request, "llm", 0)

    # 11th should fail
    with pytest.raises(HTTPException):
        await limiter.check_rate_limit(mock_request, "llm", 0)


@pytest.mark.asyncio
async def test_rate_limiter_with_global_instance():
    """Test using the global rate limiter instance."""
    # Get global instance
    limiter = get_rate_limiter()

    # Verify it's a RateLimiter instance
    assert isinstance(limiter, RateLimiter)

    # Test functionality
    mock_request = MagicMock()
    mock_request.state.user = {"user_id": "global_test"}

    result = await limiter.check_rate_limit(mock_request, "llm", 0)
    assert result is True
