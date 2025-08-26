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

## Running the Application

For detailed instructions on running the application locally, please refer to the main `CICD-SETUP.md` file in the root of the project.

## Environment Variables

The application uses environment variables for configuration. The primary variable is `VITE_BACKEND_URL`, which should point to the URL of the running backend API. Refer to `.env.example` for details.
