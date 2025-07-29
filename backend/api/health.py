#  Third-Party Libraries
from fastapi import APIRouter, Request

# This module provides health check and debugging endpoints.
# These are useful for monitoring the application's status and for troubleshooting.

# Create a new router for health-related endpoints.
router = APIRouter()

@router.get("/health_check")
def health_check():
    """
    A simple endpoint to confirm that the API is running and responsive.
    """
    return {"status": "API is running"}

# --- Debugging Endpoints ---
# These endpoints are intended for development and debugging purposes only.

@router.get("/debug/headers")
async def debug_headers(request: Request):
    """
    Returns the headers of the incoming request.
    Useful for debugging issues related to CORS, cookies, or other headers.
    """
    return {
        "origin": request.headers.get("origin"),
        "host": request.headers.get("host"),
        "headers": dict(request.headers)
    }

@router.get("/debug/origin")
async def debug_origin(request: Request):
    """
    Returns the request's origin and cookies.
    Helpful for diagnosing cookie and cross-origin request problems.
    """
    return {
        "origin": request.headers.get("origin"),
        "cookies": request.cookies
    }
