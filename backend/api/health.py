#  Third-Party Libraries
from fastapi import APIRouter, Request
from datetime import datetime 
import psutil  

#  Internal Modules
from backend.core.db import test_connection
from backend.core.redis import redis_client

# This module provides health check and debugging endpoints.
# These are useful for monitoring the application's status and for troubleshooting.

# Create a new router for health-related endpoints.
router = APIRouter()

@router.get("/health")
def health():
    """
    A simple endpoint to confirm that the API is running and responsive.
    """
    return {
        "status": "لْحَمْدُ لِلَّٰهِ -- API is running", 
        "timestamp": datetime.now().isoformat(),
        "memory_usage": psutil.Process().memory_info().rss / 1024 / 1024
        }

# very cheap health endpoint
@router.get("/healthz")
async def kubernetes_health():
    """Health check for Kubernetes/Azure"""
    return {"status": "ok"}   

# /robots933456.txt (the platform’s classic warm‑up path): 
@router.get("/robots933456.txt")
def warmup():
    return "ok"
       

# --- Debugging Endpoints ---
# These endpoints are intended for development and debugging purposes only.

# @router.get("/debug/headers")
# async def debug_headers(request: Request):
#     """
#     Returns the headers of the incoming request.
#     Useful for debugging issues related to CORS, cookies, or other headers.
#     """
#     return {
#         "origin": request.headers.get("origin"),
#         "host": request.headers.get("host"),
#         "headers": dict(request.headers)
#     }

# @router.get("/debug/origin")
# async def debug_origin(request: Request):
#     """
#     Returns the request's origin and cookies.
#     Helpful for diagnosing cookie and cross-origin request problems.
#     """
#     return {
#         "origin": request.headers.get("origin"),
#         "cookies": request.cookies
#     }
