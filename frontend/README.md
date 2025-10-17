# Frontend Application

This directory contains the frontend of the proposal drafting application, built with React and Vite.

## High-Level Design Philosophy

This application is designed around a two-level knowledge management system to enhance proposal generation, minimize hallucinations, and ensure human accountability throughout the process.

### Two-Level Knowledge Management

1.  **Knowledge Card Creation**: The first level focuses on building a curated knowledge base.
    *   **Reference Identification**: The system identifies and ingests relevant information from web sources to serve as references.
    *   **RAG-Based Content**: It then uses a Retrieval-Augmented Generation (RAG) model to create structured "Knowledge Cards" from these references.
    *   **Human in the Loop**: Crucially, these cards are not final. They can be reviewed and edited by users, ensuring that the knowledge is accurate, well-curated, and fit for purpose.

2.  **Grounded Proposal Generation**: The second level leverages this curated knowledge.
    *   **Consistent Knowledge Injection**: When generating proposals, users can associate specific Knowledge Cards with the generation process. This ensures that precise, pre-approved information is consistently used across multiple proposals.
    *   **Optimal Context Management**: This approach helps to manage the context window of the language model effectively, feeding it only the most relevant information and reducing the risk of content mismatch or deviation from the core message.

### Continuous Learning

The application is built for continuous improvement. The peer review workflow for proposals allows the system to learn from fully reviewed and approved documents over time. This creates a feedback loop where the quality of generated content improves with each successful proposal cycle.

### Core Benefits

This design ensures:
-   **Better Proposals**: Grounded in curated, specific knowledge.
-   **Minimized Hallucination**: By relying on RAG and human-verified knowledge cards.
-   **Human Accountability**: Users are in control of the knowledge base and the final output, maintaining clear accountability.

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
    -   **Grounded Generation**: Users can click "Associate Knowledge" to open a modal and select one or more Knowledge Cards. This links the curated information to the proposal, grounding the AI's output in verified data and optimizing the context window.
    -   **Workflow Badges**: The status badges have been updated to be more sequential and are now grouped in a "Workflow Stage" box. "Submission" has been renamed to "Pre-Submission", and each badge has a descriptive tooltip.
    -   **Version Switching**: Users can revert a proposal to a previous status by clicking the "Revert" button next to an inactive status badge.
    -   **Restricted Editing**: The proposal form and generation buttons are disabled if the proposal's status is not "Drafting".
    -   **Pre-Submission View**: When a proposal is in the "Pre-Submission" stage, peer review comments are displayed under each section, along with a form for the author to respond.
    -   **Approved View**: When a proposal is "Approved", an "Upload approved document version" button is displayed.

### `screens/KnowledgeCard/KnowledgeCard.jsx`

-   **Responsibility**: This screen allows users to create and manage "Knowledge Cards." It is central to the application's two-level knowledge management system.
-   **User Flow**:
    -   **Reference Ingestion**: A user starts by providing a URL to a reference document. The system's AI ingests the content.
    -   **AI-Powered Creation**: Based on the ingested reference, the AI generates a structured Knowledge Card with content organized according to a predefined template.
    -   **Human-in-the-Loop Editing**: The user can then review, edit, and refine the AI-generated content to ensure its accuracy and quality.
    -   **Association**: The curated Knowledge Card can then be associated with proposals to ground the generation process in reliable information.
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

