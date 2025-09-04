# Frontend Application

This directory contains the frontend of the proposal drafting application, built with React and Vite.

## Code Structure

The frontend code is organized into the following directories:

-   **`public/`**: Contains static assets that are publicly accessible.
-   **`src/`**: The main directory for the application's source code.
    -   **`assets/`**: Contains static assets imported into the application, such as images and fonts.
    -   **`components/`**: Contains reusable React components used throughout the application.
    -   **`screens/`**: Contains the main screens or pages of the application.
    -   **`mocks/`**: Contains mock data and server handlers for testing.
    -   **`App.jsx`**: The main application component, which sets up routing.
    -   **`main.jsx`**: The entry point of the application.
    -   **`index.css`**: The main stylesheet for the application.

## Key Components and Logic

The core of the user experience is handled by two main screen components:

### `screens/Dashboard/Dashboard.jsx`

-   **Responsibility**: This component serves as the user's home page after logging in. It displays a list of all existing proposal drafts and sample proposals.
-   **API Interaction**: On load, it makes a `GET` request to the `/api/list-drafts` endpoint to fetch the list of proposals.
-   **User Flow**:
    -   A user can click "Generate New Proposal" to navigate to the `/chat` screen to start a new proposal.
    -   A user can click on an existing draft, which stores the `proposal_id` in `sessionStorage` and navigates to the `/chat` screen to load it for editing.
-   **New Features**:
    -   **Project Options**: Each project card now has a popover menu with options to "View", "Delete", or "Transfer Ownership".
    -   **Soft Delete**: The "Delete" option performs a soft delete by updating the proposal's status to "deleted" in the backend.
    -   **Transfer Ownership**: The "Transfer Ownership" option opens a modal to select a new owner for the proposal.

### `screens/Chat/Chat.jsx`

-   **Responsibility**: This is the main workspace for creating, viewing, and editing a proposal. It handles the proposal form, the generation of sections, and the display of results.
-   **State Management**: It uses React's `useState` and `useEffect` hooks to manage the form data, the project description, the proposal sections, and the overall UI state (e.g., loading indicators).
-   **API Interaction and Workflow**:
    1.  **Template Loading**: On component mount, it fetches the available donor-to-template mappings from the `/api/templates` endpoint and populates the "Targeted Donor" dropdown.
    2.  **Creating a New Proposal**:
        - When the user clicks "Generate", it calls the `POST /api/create-session` endpoint, sending the form data and project description.
        - It receives a `session_id` and `proposal_id` from the backend, storing them in `sessionStorage`.
        - It then triggers the `getSections` function to start generating content.
    3.  **Loading an Existing Proposal**:
        - If a `proposal_id` is found in `sessionStorage`, it calls `GET /api/load-draft/{proposal_id}` to fetch the existing proposal data and populate the form and results.
    4.  **Generating Sections**:
        - The `getSections` function iterates through the list of sections for the proposal and calls `POST /api/process_section/{session_id}` for each one.
        - Crucially, it sends the **latest form data** with each call to ensure the backend is always working with fresh information.
    5.  **Saving Manual Edits**:
        - When a user manually edits a section and clicks "Save", the component calls the `POST /api/update-section-content` endpoint.
        - This provides a direct, fast way to save content without involving the AI generation process.
-   **New Features**:
    -   **Workflow Badges**: The status badges have been updated to be more sequential and are now grouped in a "Workflow Stage" box. "Submission" has been renamed to "Pre-Submission", and each badge has a descriptive tooltip.
    -   **Version Switching**: Users can revert a proposal to a previous status by clicking the "Revert" button next to an inactive status badge.
    -   **Restricted Editing**: The proposal form and generation buttons are disabled if the proposal's status is not "Drafting".
    -   **Pre-Submission View**: When a proposal is in the "Pre-Submission" stage, peer review comments are displayed under each section, along with a form for the author to respond.
    -   **Approved View**: When a proposal is "Approved", an "Upload approved document version" button is displayed.

### `screens/KnowledgeCard/KnowledgeCard.jsx`

-   **Responsibility**: This screen allows users to create and manage "Knowledge Cards". These are reusable pieces of information that can be linked to donors, outcomes, or field contexts.
-   **User Flow**:
    -   A user can create a new knowledge card by providing a title, a summary, and linking it to a donor, outcome, or field context.
    -   After a knowledge card is created, its content can be populated by an AI agent.
    -   The information from knowledge cards can be used to enrich the content of proposals.
-   **New Features**:
    -   **Updated Form**: The "Reference Type" field is now a compulsory dropdown at the top of the form. When "Field Context" is selected as the link type, a "Geographic Coverage" dropdown appears to filter the items.
    -   **Restyled Buttons**: The buttons have been restyled and realigned as per the user's request.
    -   **Save and Navigate**: The "Save Card" button now saves the card and navigates the user back to the "Knowledge Card" tab on the dashboard.

### `screens/Review/Review.jsx`

-   **Responsibility**: This screen is used for the peer review process. It allows a user to review a proposal that has been submitted to them for feedback.
-   **User Flow**:
    -   A user navigates to this screen by clicking on a proposal that has been assigned to them for review on their dashboard.
    -   The user can view the proposal content section by section and provide comments in a dedicated text area for each section.
    -   Once the review is complete, the user can submit their feedback by clicking the "Review Completed" button.
-   **New Features**:
    -   **Scrollable View**: The review screen is now scrollable to accommodate long proposals.
    -   **Enhanced Comments**: The review form for each section now includes dropdowns for "Type of Comment" and "Severity".

## Running the Application

For detailed instructions on running the application locally, please refer to the main `CICD-SETUP.md` file in the root of the project.

## Environment Variables

The application uses environment variables for configuration. The primary variable is `VITE_BACKEND_URL`, which should point to the URL of the running backend API. Refer to `.env.example` for details.

## Testing with Playwright

This project uses [Playwright](https://playwright.dev/) for end-to-end testing. The tests are located in the `frontend/tests` directory.

### Prerequisites

-   [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
-   [Node.js](https://nodejs.org/) and [npm](https://www.npmjs.com/)
-   `psql` client (you can install it with `sudo apt-get update && sudo apt-get install -y postgresql-client`)

### Setting up the Environment

1.  **Create a `.env` file** in the root of the project by copying the `.env.example` file:
    ```bash
    cp .env.example .env
    ```
    Make sure to fill in the required environment variables in the `.env` file.

2.  **Start the application** using the local Docker Compose file from the root of the project:
    ```bash
    sudo docker compose -f docker-compose-local.yml up --build -d
    ```

3.  **Set up the database** by running the following commands from the root of the project:
    ```bash
    # Wait for the database to be ready
    sleep 20

    # Set up the database schema
    psql postgresql://postgres:postgres@localhost:5432/proposalgen -f database-setup.sql

    # Load the test data
    psql postgresql://postgres:postgres@localhost:5432/proposalgen -f frontend/tests/test-data.sql
    ```

