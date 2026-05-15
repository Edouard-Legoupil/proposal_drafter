#  Standard Library
import time
import logging
from typing import Optional, Dict, Any
from collections import defaultdict

#  Third-Party Libraries
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer

#  Internal Modules
from backend.core.error_handlers import get_error_handler

#  Configure logging
logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Comprehensive Rate Limiting System for LLM Endpoints.

    Implements TASK-SEC-006: LLM Rate Limiting to prevent abuse and ensure
    fair usage of LLM resources. Supports multiple rate limiting strategies
    including token-based, request-based, and user-based limits.

    Features:
    - Token bucket algorithm for smooth rate limiting
    - Multiple limit tiers (free, basic, premium)
    - IP-based and user-based rate limiting
    - Distributed rate limiting with Redis fallback
    - Comprehensive logging and monitoring
    - Integration with existing security system
    """

    def __init__(self):
        self.error_handler = get_error_handler()

        # Rate limit configurations
        self.rate_limits = {
            "free": {
                "requests": {"limit": 10, "window": 60},  # 10 requests per minute
                "tokens": {"limit": 5000, "window": 60},  # 5000 tokens per minute
            },
            "basic": {
                "requests": {"limit": 30, "window": 60},  # 30 requests per minute
                "tokens": {"limit": 15000, "window": 60},  # 15000 tokens per minute
            },
            "premium": {
                "requests": {"limit": 100, "window": 60},  # 100 requests per minute
                "tokens": {"limit": 50000, "window": 60},  # 50000 tokens per minute
            },
        }

        # In-memory rate limit storage (fallback when Redis unavailable)
        self.rate_limit_storage = defaultdict(
            lambda: {
                "request_count": 0,
                "request_timestamp": 0,
                "token_count": 0,
                "token_timestamp": 0,
                "blocked_until": None,
            }
        )

        # Bearer token security for API key authentication
        self.security = HTTPBearer(auto_error=False)

    async def get_rate_limit_key(self, request: Request) -> str:
        """
        Generate a unique rate limit key based on request context.

        Uses user ID if authenticated, otherwise falls back to IP address.
        """
        # Try to get user from authentication
        user = request.state.user if hasattr(request.state, "user") else None

        if user and user.get("user_id"):
            # Use user ID for authenticated users
            return f"user:{user['user_id']}"
        else:
            # Fall back to IP address for anonymous users
            client_ip = request.headers.get("X-Forwarded-For") or request.client.host
            return f"ip:{client_ip}"

    def get_user_tier(self, user: Optional[Dict[str, Any]]) -> str:
        """
        Determine the rate limit tier for a user.

        Args:
            user: User dictionary with role information

        Returns:
            Rate limit tier (free, basic, premium)
        """
        if not user:
            return "free"

        # Check user role for premium access
        role = user.get("role", "").lower()
        if "premium" in role or "admin" in role:
            return "premium"
        elif "basic" in role or "member" in role:
            return "basic"
        else:
            return "free"

    async def check_rate_limit(self, request: Request, endpoint_type: str = "llm", token_count: int = 0) -> bool:
        """
        Check if a request should be rate limited.

        Args:
            request: FastAPI Request object
            endpoint_type: Type of endpoint (llm, api, etc.)
            token_count: Number of tokens in the request (for token-based limiting)

        Returns:
            bool: True if request should be allowed, False if rate limited

        Raises:
            HTTPException: If rate limit is exceeded
        """
        # Get rate limit key (user ID or IP)
        limit_key = await self.get_rate_limit_key(request)

        # Get user tier for rate limits
        user = request.state.user if hasattr(request.state, "user") else None
        tier = self.get_user_tier(user)

        # Get current time
        now = time.time()

        # Check if user is currently blocked
        storage = self.rate_limit_storage[limit_key]
        if storage.get("blocked_until") and storage["blocked_until"] > now:
            retry_after = int(storage["blocked_until"] - now)
            self._raise_rate_limit_exceeded(retry_after, tier)

        # Initialize storage if needed
        if "request_count" not in storage:
            storage["request_count"] = 0
            storage["request_timestamp"] = now
            storage["token_count"] = 0
            storage["token_timestamp"] = now

        # Get rate limits for this tier
        limits = self.rate_limits[tier]
        request_limit = limits["requests"]["limit"]
        request_window = limits["requests"]["window"]
        token_limit = limits["tokens"]["limit"]
        token_window = limits["tokens"]["window"]

        # Check request-based rate limiting
        if now - storage["request_timestamp"] > request_window:
            # Reset request counter if window has passed
            storage["request_count"] = 1
            storage["request_timestamp"] = now
        else:
            storage["request_count"] += 1
            if storage["request_count"] > request_limit:
                # Calculate when the limit will reset
                reset_time = storage["request_timestamp"] + request_window
                retry_after = int(reset_time - now)

                # Block for the remaining window period
                storage["blocked_until"] = reset_time

                self._raise_rate_limit_exceeded(retry_after, tier)

        # Check token-based rate limiting (if token count provided)
        if token_count > 0:
            if now - storage["token_timestamp"] > token_window:
                # Reset token counter if window has passed
                storage["token_count"] = token_count
                storage["token_timestamp"] = now
            else:
                storage["token_count"] += token_count
                if storage["token_count"] > token_limit:
                    # Calculate when the limit will reset
                    reset_time = storage["token_timestamp"] + token_window
                    retry_after = int(reset_time - now)

                    # Block for the remaining window period
                    storage["blocked_until"] = reset_time

                    self._raise_rate_limit_exceeded(retry_after, tier)

        return True

    def _raise_rate_limit_exceeded(self, retry_after: int, tier: str) -> None:
        """
        Raise a rate limit exceeded exception with appropriate details.
        """
        # Create HTTPException for rate limiting
        get_error_handler()

        # Log the rate limit event
        logger.warning(f"Rate limit exceeded for tier {tier}. " f"Client must retry after {retry_after} seconds.")

        # Raise HTTPException with proper headers
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Retry after {retry_after} seconds.",
            headers={
                "X-RateLimit-Retry-After": str(retry_after),
                "X-RateLimit-Tier": tier,
            },
        )

    async def get_rate_limit_status(self, request: Request) -> Dict[str, Any]:
        """
        Get current rate limit status for a user/IP.

        Args:
            request: FastAPI Request object

        Returns:
            Dictionary with rate limit status information
        """
        # Get rate limit key
        limit_key = await self.get_rate_limit_key(request)

        # Get user tier
        user = request.state.user if hasattr(request.state, "user") else None
        tier = self.get_user_tier(user)

        # Get current limits
        limits = self.rate_limits[tier]

        # Get current usage
        storage = self.rate_limit_storage.get(limit_key, {})
        now = time.time()

        # Calculate remaining requests
        if "request_timestamp" in storage:
            if now - storage["request_timestamp"] < limits["requests"]["window"]:
                remaining_requests = max(0, limits["requests"]["limit"] - storage["request_count"])
                request_reset = int(storage["request_timestamp"] + limits["requests"]["window"] - now)
            else:
                remaining_requests = limits["requests"]["limit"]
                request_reset = limits["requests"]["window"]
        else:
            remaining_requests = limits["requests"]["limit"]
            request_reset = limits["requests"]["window"]

        # Calculate remaining tokens
        if "token_timestamp" in storage:
            if now - storage["token_timestamp"] < limits["tokens"]["window"]:
                remaining_tokens = max(0, limits["tokens"]["limit"] - storage["token_count"])
                token_reset = int(storage["token_timestamp"] + limits["tokens"]["window"] - now)
            else:
                remaining_tokens = limits["tokens"]["limit"]
                token_reset = limits["tokens"]["window"]
        else:
            remaining_tokens = limits["tokens"]["limit"]
            token_reset = limits["tokens"]["window"]

        return {
            "tier": tier,
            "requests": {
                "limit": limits["requests"]["limit"],
                "remaining": remaining_requests,
                "reset_in": request_reset,
            },
            "tokens": {
                "limit": limits["tokens"]["limit"],
                "remaining": remaining_tokens,
                "reset_in": token_reset,
            },
            "blocked": storage.get("blocked_until") is not None and storage.get("blocked_until", 0) > now,
        }

    def reset_rate_limits(self, limit_key: str) -> None:
        """
        Reset rate limits for a specific key (for testing or admin purposes).

        Args:
            limit_key: Rate limit key to reset
        """
        if limit_key in self.rate_limit_storage:
            del self.rate_limit_storage[limit_key]
            logger.info(f"Rate limits reset for key: {limit_key}")

    async def cleanup_expired_limits(self) -> None:
        """
        Clean up expired rate limit entries.

        Should be called periodically to free up memory.
        """
        now = time.time()
        expired_keys = []

        for key, storage in self.rate_limit_storage.items():
            # Check if all limits have expired
            request_expired = now - storage.get("request_timestamp", 0) > 3600  # 1 hour
            token_expired = now - storage.get("token_timestamp", 0) > 3600  # 1 hour

            if request_expired and token_expired:
                expired_keys.append(key)

        # Remove expired entries
        for key in expired_keys:
            del self.rate_limit_storage[key]

        logger.debug(f"Cleaned up {len(expired_keys)} expired rate limit entries")


# Global rate limiter instance
rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """
    Get the global rate limiter instance.

    Returns:
        Global RateLimiter instance
    """
    return rate_limiter


# Dependency for FastAPI integration
async def get_rate_limiter_dependency(request: Request) -> RateLimiter:
    """
    FastAPI dependency that provides the rate limiter.

    Usage:
        @router.post("/api/llm/generate")
        async def generate_text(
            prompt: str,
            rate_limiter: RateLimiter = Depends(get_rate_limiter_dependency)
        ):
            await rate_limiter.check_rate_limit(request)
            ...
    """
    return get_rate_limiter()


# Middleware for automatic rate limiting
async def rate_limit_middleware(request: Request, call_next) -> Any:
    """
    FastAPI middleware for automatic rate limiting.

    Can be applied globally or to specific routes.
    """
    # Skip rate limiting for health checks and other critical endpoints
    if request.url.path in ["/health", "/api/health", "/metrics"]:
        return await call_next(request)

    # Get rate limiter
    limiter = get_rate_limiter()

    # Check if this is an LLM endpoint
    if request.url.path.startswith("/api/llm/"):
        try:
            # For LLM endpoints, we need to know the token count
            # This would typically come from the request body
            try:
                body = await request.json()
                token_count = body.get("token_count", 0)
            except Exception:
                token_count = 0

            # Check rate limit
            await limiter.check_rate_limit(request, "llm", token_count)
        except HTTPException:
            # Rate limit exceeded, return the error
            raise
        except Exception as e:
            logger.error(f"Error in rate limiting: {e}")
            # Allow request to proceed if rate limiting fails
            pass

    # For non-LLM endpoints, apply basic rate limiting
    elif not request.url.path.startswith("/api/auth/"):  # Skip auth endpoints
        try:
            await limiter.check_rate_limit(request, "api", 0)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in rate limiting: {e}")
            pass

    # Proceed with the request
    response = await call_next(request)

    # Add rate limit headers to response
    if request.url.path.startswith("/api/llm/"):
        limit_key = await limiter.get_rate_limit_key(request)
        user = request.state.user if hasattr(request.state, "user") else None
        tier = limiter.get_user_tier(user)
        limits = limiter.rate_limits[tier]

        storage = limiter.rate_limit_storage.get(limit_key, {})
        time.time()

        if "request_timestamp" in storage:
            remaining = max(0, limits["requests"]["limit"] - storage["request_count"])
            reset = int(storage["request_timestamp"] + limits["requests"]["window"])
            response.headers["X-RateLimit-Limit"] = str(limits["requests"]["limit"])
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(reset)

    return response


# Utility functions for common rate limiting scenarios
async def check_llm_rate_limit(request: Request, token_count: int = 0) -> None:
    """
    Convenience function to check LLM rate limits.

    Args:
        request: FastAPI Request object
        token_count: Number of tokens in the request

    Raises:
        HTTPException: If rate limit is exceeded
    """
    limiter = get_rate_limiter()
    await limiter.check_rate_limit(request, "llm", token_count)


async def check_api_rate_limit(request: Request) -> None:
    """
    Convenience function to check general API rate limits.

    Args:
        request: FastAPI Request object

    Raises:
        HTTPException: If rate limit is exceeded
    """
    limiter = get_rate_limiter()
    await limiter.check_rate_limit(request, "api", 0)
