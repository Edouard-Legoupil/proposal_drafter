# Backend Application

This directory contains the backend of the proposal drafting application, built with FastAPI.

## Code Structure

The backend code is organized into the following modules:

-   **`main.py`**: The main entry point of the application. It initializes the FastAPI app, includes the API routers, and sets up middleware.

-   **`api/`**: This module contains the API endpoints, with each file representing a different domain.
    -   `auth.py`: User authentication endpoints (signup, login, logout, etc.).
    -   `proposals.py`: Endpoints for managing proposals (creation, editing, listing, etc.).
    -   `session.py`: Endpoints for managing temporary user session data in Redis.
    -   `documents.py`: Endpoints for generating and downloading proposal documents.
    -   `health.py`: Health check and debugging endpoints.

-   **`core/`**: This module contains the core components of the application.
    -   `config.py`: Application configuration, including environment variable loading and CORS settings.
    -   `db.py`: Database connection logic, including the SQLAlchemy engine.
    -   `llm.py`: Language model initialization and configuration.
    -   `middleware.py`: Custom middleware, such as CORS and exception handlers.
    -   `redis.py`: Redis client initialization with a fallback to in-memory storage.
    -   `security.py`: Security-related functions, such as authentication and password management.

-   **`models/`**: This module contains the Pydantic models for data validation.
    -   `schemas.py`: Pydantic models for request and response data.

-   **`utils/`**: This module contains utility functions.
    -   `crew.py`: Defines the CrewAI agents and tasks for proposal generation.
    -   `doc_export.py`: Helper functions for creating and exporting documents.
    -   `markdown.py`: Helper functions for handling Markdown conversions.
    -   `proposal_logic.py`: Core logic for generating and regenerating proposal sections.

-   **`tests/`**: This directory contains the tests for the backend application.

## Running the Application

To run the application locally, you will need to have Docker and Docker Compose installed. From the root of the project, run:

```bash
docker-compose up --build
```

The application will be available at `http://localhost:8080`.

## Environment Variables

The application uses environment variables for configuration. You can find a list of the required variables in `.env.example`. Create a `.env` file in this directory with your own values.
