#  Third-Party Libraries
import logging
from fastapi import FastAPI, HTTPException
import uvicorn
from dotenv import load_dotenv

load_dotenv()

# --- Logging Configuration ---
import sys
# Configure logging to stream to stdout
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     stream=sys.stdout
# )

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = logging.FileHandler("log/app.log")
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(handler)

import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

#  Internal Modules
from backend.api import auth, proposals, session, documents, health
from backend.core.middleware import (
    setup_cors_middleware,
    custom_http_exception_handler,
    setup_scheduler
)

from backend.core.db import test_connection

# This is the main application file. It brings together all the different
# parts of the application: API routers, middleware, and event handlers.

# --- FastAPI Application Initialization ---
app = FastAPI(
    title="Proposal Drafting API",
    description="An API for generating, managing, and exporting project proposals.", 
    version="0.0.1", 
   # root_path="/api",
    terms_of_service="http://www.unhcr.org",
    contact={
        "name": "Edouard Legoupil",
        "url": "http://edouard-legoupil.github.io",
        "email": "legoupil@unhcr.org",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    }
)



# --- Middleware Configuration ---
# Middleware functions run for every request, before it's processed by a specific endpoint.
# They are used here for handling CORS and custom exceptions.
setup_cors_middleware(app)
app.add_exception_handler(HTTPException, custom_http_exception_handler)


# --- API Router Inclusion ---
# The API is split into logical sections using routers. Each router handles a
# specific domain (e.g., authentication, proposals). They are included here
# with a common prefix.
app.include_router(auth.router, prefix="/api", tags=["Authentication"])
app.include_router(session.router, prefix="/api", tags=["Session Management"])
app.include_router(proposals.router, prefix="/api", tags=["Proposals"])
app.include_router(documents.router, prefix="/api", tags=["Documents"])
app.include_router(health.router, tags=["Health & Debugging"])


# --- Application Startup Events ---
# Code in this block is executed when the application starts up.
# Instead of connecting at import, do it in your startup event for lazy loading
# If DB is unavailable, Cloud Run can retry health checks instead of killing container instantly.
@app.on_event("startup")
async def startup_event():
    """
    Performs application startup tasks, such as initializing the background scheduler.
    """
    if not test_connection():
        # Optional: fail fast or just log
        raise RuntimeError("Database connection failed at startup")
    print("Application is starting up...")
    setup_scheduler()
    print("Background scheduler has been started.")


# --- Main Execution Block ---
# This block allows the application to be run directly using `python main.py`.
# It's useful for development and testing.
if __name__ == "__main__":
    # Uvicorn is an ASGI server that runs the FastAPI application.
    uvicorn.run(app, host="0.0.0.0", port=8502)
