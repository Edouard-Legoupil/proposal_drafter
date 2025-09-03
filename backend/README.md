# Backend Application

This directory contains the backend of the proposal drafting application, built with FastAPI. It handles user authentication, proposal data management, and AI-powered content generation.

## Code Structure

The backend code is organized into the following modules:

-   **`main.py`**: The main entry point of the application. It initializes the FastAPI app, includes the API routers, and sets up middleware.

-   **`api/`**: This module contains the API endpoints, with each file representing a different domain.
    -   `auth.py`: User authentication endpoints (signup, login, logout, etc.).
    -   `proposals.py`: Endpoints for managing the entire proposal lifecycle.
    -   `documents.py`: Endpoints for generating and downloading proposal documents.
    -   `health.py`: Health check and debugging endpoints.

-   **`core/`**: This module contains the core components of the application.
    -   `config.py`: Application configuration, environment variable loading, and template discovery.
    -   `db.py`: Database connection logic using SQLAlchemy.
    -   `redis.py`: Redis client initialization for session management.
    -   `security.py`: Security-related functions for authentication and authorization.

-   **`models/`**: This module contains the Pydantic models for data validation.
    -   `schemas.py`: Pydantic models for all API request and response data.

-   **`utils/`**: This module contains utility functions.
    -   `crew.py`: Defines the CrewAI agents and tasks for proposal generation.
    -   `doc_export.py`: Helper functions for creating and exporting `.docx` and `.pdf` documents.
    -   `markdown.py`: Helper functions for handling Markdown conversions.
    -   `proposal_logic.py`: Core logic for regenerating proposal sections.

-   **`templates/`**: Contains the JSON proposal templates that define the structure and sections for different donors.

-   **`tests/`**: This directory contains the tests for the backend application.

## Testing

The backend API is tested using a suite of end-to-end tests written with Playwright. These tests are located in the `frontend/tests` directory and cover the main user journeys of the application, ensuring that the API endpoints are functioning correctly.

For more details on how to run these tests, please refer to the "Testing with Playwright" section in the `frontend/README.md` file.

## Proposal Generation Workflow

The backend follows a specific workflow for creating and generating a new proposal, designed to be robust and ensure data consistency.

1.  **Template Discovery (`GET /templates`)**: The frontend first requests the list of available proposal templates. The backend scans the `templates/` directory, reads each JSON file, and returns a map of donor names to template filenames.

2.  **Session Creation (`POST /create-session`)**: When a user fills out the initial form and clicks "Generate", the frontend sends the form data and project description to this endpoint. The backend then:
    a. Determines the correct template based on the "Targeted Donor" in the form data.
    b. Creates a new proposal record in the PostgreSQL database.
    c. Creates a new session in Redis containing all the necessary context (form data, project description, and the full proposal template).
    d. Returns the `proposal_id` and `session_id` to the frontend.

3.  **Section Processing (`POST /process_section/{session_id}`)**: The frontend iterates through the sections defined in the template and calls this endpoint for each one. To ensure the AI has the latest information, the frontend sends the **current form data and project description** with every request. The backend updates the Redis session with this fresh data before kicking off the CrewAI generation process.

4.  **Manual Edits (`POST /update-section-content`)**: If a user manually edits a section, the frontend calls this dedicated endpoint. It directly updates the content for that section in the PostgreSQL database, bypassing the AI for a fast and reliable save.

5.  **Document Generation (`GET /generate-document/{proposal_id}`)**: When a user requests to download the document, the backend fetches the proposal from the database, loads the appropriate template to ensure correct section ordering, and generates the requested file (`.docx` or `.pdf`).

## Proposal Template Format

Each proposal template is a `.json` file located in the `templates/` directory. To be discovered correctly by the backend, each template file must be a JSON object (not a list) and contain a `donors` key.

-   **`donors`**: A list of strings, where each string is a donor name that can use this template. This allows a single template to be associated with multiple donors.

Example:
```json
{
  "donors": ["UNHCR", "IOM"],
  "project_info": { ... },
  "sections": [ ... ]
}
```

## Running the Application

For detailed instructions on running the application locally (with and without Docker) and deploying to Azure, please refer to the main `CICD-SETUP.md` file in the root of the project.

## Environment Variables

The application uses environment variables for configuration. You can find a list of the required variables in `.env.example`. Create a `.env` file in this directory with your own values when running locally.
