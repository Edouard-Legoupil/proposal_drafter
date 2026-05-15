#  Standard Library
from datetime import datetime, timedelta, timezone

#  Third-Party Libraries
from fastapi import Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import text

#  Internal Modules
from backend.core.config import origins
from backend.core.db import engine

# This module contains all custom middleware, exception handlers, and background tasks.


def setup_security_middleware(app):
    """
    Configures and adds security-related middleware to the app.
    This includes security headers, trusted host middleware, and other security enhancements.
    """
    # Add TrustedHostMiddleware to prevent HTTP Host header attacks
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=origins)

    # Add security headers middleware
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        """
        Adds comprehensive security headers to all responses.
        Implements TASK-SEC-007: Add Security HTTP Headers
        """
        response = await call_next(request)

        # Content Security Policy - strict policy to prevent XSS
        csp = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "  # Allow inline styles for now
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-src 'none'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        response.headers["Content-Security-Policy"] = csp

        # X-Content-Type-Options - prevent MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-Frame-Options - prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # X-XSS-Protection - legacy XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Strict-Transport-Security - enforce HTTPS
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        # Referrer-Policy - control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions-Policy - control browser features
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=(), payment=()"

        # Cache-Control - prevent caching of sensitive responses
        if not response.headers.get("Cache-Control"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        return response

    return app


def setup_cors_middleware(app):
    """
    Configures and adds the Cross-Origin Resource Sharing (CORS) middleware to the app.
    CORS allows the frontend application (on a different domain) to communicate with this API.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition"],
    )


def get_cookie_settings(request: Request) -> dict:
    """
    Dynamically configures secure cookie settings based on the request's origin.
    This helps handle different environments (e.g., localhost vs. production).

    - In production (HTTPS), cookies are set with `Secure` and `SameSite=None`.
    - In local development (HTTP), these restrictions are relaxed.
    """
    host = request.headers.get("host", "")
    origin = request.headers.get("origin", "")

    # Detect if running in a strict localhost environment.
    is_strict_localhost = all(
        [
            any(["localhost" in host, "127.0.0.1" in host]),
            any(["localhost" in (origin or ""), "127.0.0.1" in (origin or "")]),
        ]
    )

    settings = {
        "secure": not is_strict_localhost,
        "samesite": "lax" if is_strict_localhost else "none",
        "domain": None,
    }
    return settings


async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """
    A custom exception handler to ensure that even error responses include
    the necessary CORS headers. Without this, frontend applications might
    not be able to read error messages from the API.
    """
    origin = request.headers.get("origin")
    response = JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    if origin in origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


def delete_old_proposals():
    """
    A background task that periodically deletes old, non-finalized proposals
    from the database to keep the system clean.
    """
    try:
        # Define the age threshold for deletion (e.g., 90 days).
        threshold = datetime.now(timezone.utc) - timedelta(days=90)
        with engine.begin() as connection:
            connection.execute(
                text("DELETE FROM proposals WHERE created_at < :threshold AND is_accepted = FALSE"),
                {"threshold": threshold},
            )
            print(f"[CLEANUP] Deleted proposals older than {threshold}")
    except Exception as e:
        print(f"[CLEANUP ERROR] {e}")


def setup_scheduler():
    """
    Initializes and starts the background scheduler for periodic tasks.
    """
    scheduler = BackgroundScheduler()
    # Schedule the cleanup job to run at a set interval.
    scheduler.add_job(delete_old_proposals, "interval", days=1)
    scheduler.start()
    return scheduler
