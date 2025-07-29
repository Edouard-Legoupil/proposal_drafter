#  Third-Party Libraries
from fastapi import FastAPI, HTTPException
import uvicorn

#  Internal Modules
from backend.api import auth, proposals, session, documents, health
from backend.core.middleware import (
    setup_cors_middleware,
    custom_http_exception_handler,
    setup_scheduler
)

# This is the main application file. It brings together all the different
# parts of the application: API routers, middleware, and event handlers.

# --- FastAPI Application Initialization ---
app = FastAPI(
    title="Proposal Drafting API",
    description="An API for generating, managing, and exporting project proposals.",
    version="1.0.0"
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
@app.on_event("startup")
def on_startup():
    """
    Performs application startup tasks, such as initializing the background scheduler.
    """
    print("Application is starting up...")
    setup_scheduler()
    print("Background scheduler has been started.")


# --- Main Execution Block ---
# This block allows the application to be run directly using `python main.py`.
# It's useful for development and testing.
if __name__ == "__main__":
    # Uvicorn is an ASGI server that runs the FastAPI application.
    uvicorn.run(app, host="0.0.0.0", port=8080)
