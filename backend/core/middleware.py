#  Standard Library
from datetime import datetime, timedelta, timezone
import logging
import uuid

#  Third-Party Libraries
from fastapi import Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import text

#  Internal Modules
from backend.core.config import APP_ENV, allowed_hosts, origins
from backend.core.db import engine

logger = logging.getLogger(__name__)

# This module contains all custom middleware, exception handlers, and background tasks.


def setup_security_middleware(app):
    """
    Configures and adds security-related middleware to the app.
    This includes security headers, trusted host middleware, and other security enhancements.
    """
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

    # Add security headers middleware
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        """
        Adds comprehensive security headers to all responses.
        Implements TASK-SEC-007: Add Security HTTP Headers
        """
        request.state.request_id = str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id

        # Content Security Policy - strict policy to prevent XSS
        # Allow external resources needed by the frontend
        csp_parts = [
            "default-src 'self'",
            "script-src 'self'",
            ("style-src 'self' 'unsafe-inline' " "https://cdnjs.cloudflare.com " "https://fonts.googleapis.com"),
            "img-src 'self' data: https://texturegenerator.sirv.com",
            "font-src 'self' https://fonts.gstatic.com https://fonts.googleapis.com https://cdnjs.cloudflare.com data:",
            "connect-src 'self'",
            "frame-src 'none'",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
        csp = "; ".join(csp_parts)
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

        # Cache immutable build assets while preventing caching of API and SPA responses.
        if request.url.path.startswith("/assets/") and response.status_code == 200:
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        elif not response.headers.get("Cache-Control"):
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

    Cookies remain same-site so browser requests cannot attach the session to
    cross-site state-changing requests.
    """
    host = request.headers.get("host", "")
    is_localhost = "localhost" in host or "127.0.0.1" in host

    settings = {
        "secure": APP_ENV != "development" or not is_localhost,
        "samesite": "lax",
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
    request_id = str(getattr(request.state, "request_id", uuid.uuid4()))
    headers = dict(exc.headers or {})
    headers["X-Request-ID"] = request_id
    if exc.status_code >= 500:
        logger.error(
            "HTTP %s failure on %s (request_id=%s): %s",
            exc.status_code,
            request.url.path,
            request_id,
            exc.detail,
        )
        content = {"detail": "Internal server error", "request_id": request_id}
    else:
        content = {"detail": exc.detail}
    response = JSONResponse(status_code=exc.status_code, content=content, headers=headers)
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
