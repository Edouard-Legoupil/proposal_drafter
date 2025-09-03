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

## API Endpoints

This section provides a detailed, non-technical overview of the API endpoints available in the backend.

### Authentication (`/api/auth.py`)

These endpoints handle user authentication and profile management.

-   **`POST /signup`**: Creates a new user account.
    -   **What it needs**: The user's name, email, password, team, a security question, and the answer to the security question.
    -   **What it returns**: A confirmation message.

-   **`POST /login`**: Logs a user in.
    -   **What it needs**: The user's email and password.
    -   **What it returns**: A confirmation message and sets a secure cookie to manage the user's session.

-   **`GET /profile`**: Fetches the profile of the currently logged-in user.
    -   **What it needs**: A valid session cookie.
    -   **What it returns**: The user's name and email.

-   **`POST /logout`**: Logs a user out.
    -   **What it needs**: A valid session cookie.
    -   **What it returns**: A confirmation message and clears the session cookie.

-   **`POST /get-security-question`**: Retrieves the security question for a user.
    -   **What it needs**: The user's email address.
    -   **What it returns**: The user's security question.

-   **`POST /verify-security-answer`**: Verifies the answer to a security question.
    -   **What it needs**: The user's email, the security question, and the answer.
    -   **What it returns**: A confirmation message if the answer is correct.

-   **`POST /update-password`**: Updates a user's password.
    -   **What it needs**: The user's email, the new password, the security question, and the correct answer.
    -   **What it returns**: A confirmation message.

### Documents (`/api/documents.py`)

This endpoint handles the generation and downloading of proposal documents.

-   **`GET /generate-document/{proposal_id}`**: Generates and downloads a proposal document.
    -   **What it needs**: The ID of the proposal and the desired format (`docx` or `pdf`).
    -   **What it returns**: The generated document as a file download.

### Health (`/api/health.py`)

This endpoint provides health check information for the application.

-   **`GET /health`**: Checks the health of the API.
    -   **What it needs**: Nothing.
    -   **What it returns**: A status message indicating that the API is running, along with the current timestamp and memory usage.

### Knowledge Cards (`/api/knowledge.py`)

These endpoints handle the creation and management of knowledge cards.

-   **`POST /knowledge-cards`**: Creates a new knowledge card.
    -   **What it needs**: A title, an optional summary, and optionally a link to a donor, outcome, or field context.
    -   **What it returns**: A confirmation message and the ID of the new knowledge card.

-   **`GET /knowledge-cards`**: Fetches all knowledge cards.
    -   **What it needs**: Nothing.
    -   **What it returns**: A list of all knowledge cards.

-   **`GET /knowledge-cards/{card_id}`**: Fetches a single knowledge card by its ID.
    -   **What it needs**: The ID of the knowledge card.
    -   **What it returns**: The details of the specified knowledge card.

-   **`PUT /knowledge-cards/{card_id}`**: Updates an existing knowledge card.
    -   **What it needs**: The ID of the knowledge card and the updated information.
    -   **What it returns**: A confirmation message.

-   **`POST /knowledge-cards/{card_id}/generate`**: Generates content for a knowledge card.
    -   **What it needs**: The ID of the knowledge card.
    -   **What it returns**: The AI-generated content for the knowledge card.

### Metrics (`/api/metrics.py`)

These endpoints provide metrics and analytics about the proposals.

-   **`GET /metrics/development-time`**: Calculates the average time proposals spend in each status.
    -   **What it needs**: An optional filter (`user`, `team`, or `all`).
    -   **What it returns**: The average duration for each proposal status.

-   **`GET /metrics/funding-by-category`**: Calculates the number of proposals per status, donor, and outcome.
    -   **What it needs**: An optional filter (`user`, `team`, or `all`).
    -   **What it returns**: The number of proposals for each combination of status, donor, and outcome.

-   **`GET /metrics/donor-interest`**: Calculates the number of projects per donor, outcome, and field context.
    -   **What it needs**: An optional filter (`user`, `team`, or `all`).
    -   **What it returns**: The number of projects for each combination of donor, outcome, and field context.

### Proposals (`/api/proposals.py`)

These endpoints handle the lifecycle of a proposal.

-   **`GET /templates`**: Returns a list of available proposal templates.
    -   **What it needs**: Nothing.
    -   **What it returns**: A mapping of donor names to template filenames.

-   **`POST /create-session`**: Creates a new proposal session and a corresponding draft.
    -   **What it needs**: The project description and form data.
    -   **What it returns**: A new session ID and proposal ID.

-   **`POST /process_section/{session_id}`**: Processes a single section of a proposal.
    -   **What it needs**: The session ID, the section to process, the proposal ID, form data, and project description.
    -   **What it returns**: The AI-generated content for the section.

-   **`POST /regenerate_section/{session_id}`**: Manually regenerates a section.
    -   **What it needs**: The session ID, the section to regenerate, a concise input, the proposal ID, form data, and project description.
    -   **What it returns**: The regenerated content for the section.

-   **`POST /update-section-content`**: Updates the content of a section.
    -   **What it needs**: The proposal ID, the section to update, and the new content.
    -   **What it returns**: A confirmation message.

-   **`POST /save-draft`**: Saves a new draft or updates an existing one.
    -   **What it needs**: The proposal data, including form data, project description, and generated sections.
    -   **What it returns**: A confirmation message and the proposal ID.

-   **`GET /list-drafts`**: Lists all drafts for the current user.
    -   **What it needs**: A valid session cookie.
    -   **What it returns**: A list of all the user's drafts.

-   **`GET /load-draft/{proposal_id}`**: Loads a specific draft.
    -   **What it needs**: The ID of the proposal to load.
    -   **What it returns**: The data for the specified draft.

-   **`POST /finalize-proposal`**: Marks a proposal as "accepted".
    -   **What it needs**: The ID of the proposal to finalize.
    -   **What it returns**: A confirmation message.

-   **`POST /proposals/{proposal_id}/submit-for-review`**: Submits a proposal for peer review.
    -   **What it needs**: The ID of the proposal and a list of reviewers.
    -   **What it returns**: A confirmation message.

-   **`POST /proposals/{proposal_id}/review`**: Submits a peer review for a proposal.
    -   **What it needs**: The ID of the proposal and the review data.
    -   **What it returns**: A confirmation message.

### Session (`/api/session.py`)

These endpoints manage temporary user session data.

-   **`POST /store_base_data`**: Stores the initial proposal data in a temporary session.
    -   **What it needs**: The form data and project description.
    -   **What it returns**: A new session ID.

-   **`GET /get_base_data/{session_id}`**: Retrieves the base proposal data from a session.
    -   **What it needs**: The session ID.
    -   **What it returns**: The base proposal data.

### Users (`/api/users.py`)

These endpoints handle user and team management.

-   **`GET /teams`**: Returns a list of all teams.
    -   **What it needs**: Nothing.
    -   **What it returns**: A list of all teams in the system.

-   **`GET /users`**: Returns a list of all users.
    -   **What it needs**: Nothing.
    -   **What it returns**: A list of all users in the system, excluding the current user.

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

## Knowledge Card Management

The application supports the creation and management of "Knowledge Cards". These are reusable pieces of information that can be linked to donors, outcomes, or field contexts. Knowledge cards can be populated with AI-generated content based on a title and summary.

The workflow for knowledge cards is as follows:
1.  **Create a Knowledge Card**: A user can create a new knowledge card by providing a title, a summary, and linking it to a donor, outcome, or field context.
2.  **Populate Content**: After a knowledge card is created, its content can be populated by an AI agent.
3.  **Use in Proposals**: The information from knowledge cards can be used to enrich the content of proposals.

## Peer Review Workflow

The application includes a peer review workflow for proposals. This allows users to get feedback on their proposals from other users before submitting them.

The peer review workflow is as follows:
1.  **Submit for Review**: A user can submit a proposal for peer review to one or more other users.
2.  **Review**: The selected reviewers can view the proposal and provide comments on each section.
3.  **Complete Review**: Once a reviewer has finished providing feedback, they can mark the review as complete.
4.  **View Feedback**: The original author of the proposal can view the feedback provided by the reviewers.

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
