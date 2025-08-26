#  Third-Party Libraries
import logging
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.responses import FileResponse
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
log_dir = Path(__file__).parent / "log"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "app.log"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = logging.FileHandler(log_file)
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

# --- Serve React Frontend ---
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
#frontend_path = os.path.join(os.path.dirname(__file__), "..", "/frontend/dist")
if os.path.isdir(frontend_path):
    # Serve static assets first
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_path, "assets")), name="assets")
    
    # Serve other static files that might exist in the build
    static_dirs = ['static', 'public']  # common React build directories
    for static_dir in static_dirs:
        static_path = os.path.join(frontend_path, static_dir)
        if os.path.isdir(static_path):
            app.mount(f"/{static_dir}", StaticFiles(directory=static_path), name=static_dir)

    # SPA fallback - MUST BE DEFINED AFTER ALL API ROUTES
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """
        SPA fallback for React Router: always return index.html for non-API routes.
        This should be the last route defined.
        """
        # Skip API routes explicitly
        if full_path.startswith("api/"):
            return {"detail": "API route not found"}
        
        # Check if the request is for a static file that exists
        possible_file = os.path.join(frontend_path, full_path)
        if os.path.isfile(possible_file):
            return FileResponse(possible_file)
        
        # Check for common static file extensions
        if '.' in full_path:
            file_ext = full_path.split('.')[-1]
            if file_ext in ['js', 'css', 'png', 'jpg', 'jpeg', 'gif', 'ico', 'svg', 'woff', 'woff2', 'ttf', 'eot']:
                return {"detail": "Static file not found"}
        
        # Otherwise serve index.html for SPA routing
        index_file = os.path.join(frontend_path, "index.html")
        if os.path.isfile(index_file):
            return FileResponse(index_file)
        
        return {"detail": "Frontend not built"}


# --- Application Startup Events ---
# Code in this block is executed when the application starts up.
# Instead of connecting at import, do it in your startup event for lazy loading
# If DB is unavailable, Cloud Run can retry health checks instead of killing container instantly.
@app.on_event("startup")
async def startup_event():
    """
    Performs application startup tasks, such as initializing the background scheduler.
    """
    logging.info("Application is starting up...")
    
    # Debug: Check database configuration
   # logging.info(f"Database config - on_gcp: {on_gcp}, host: {db_host}, db: {db_name}")
   # logging.info(f"DB username: {db_username}, password set: {bool(db_password)}")
    
    # Test connection
    #if test_connection():
    #    logging.info("✅ Database connection test passed")
    #else:
    #    logging.error("❌ Database connection test failed")
        # Don't raise error immediately, let health checks handle it
    setup_scheduler()
    logging.info("Background scheduler has been started.")


# --- Main Execution Block ---
# This block allows the application to be run directly using `python main.py`.
# It's useful for development and testing.
if __name__ == "__main__":
    # Uvicorn is an ASGI server that runs the FastAPI application.
    uvicorn.run(app, host="0.0.0.0", port=8502)
