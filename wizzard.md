# Wizzard Feature Plan

This document outlines the plan to implement the "Wizzard" feature, a new tool to assist users in creating successful proposals.

## 1. Feature Overview

The Wizzard will be a user-facing tool, accessible from the main chat interface, that provides guidance on selecting proposal parameters (donor, outcome, field context). It will leverage a knowledge base of past successful proposals to offer insights and suggestions, aiming to increase the user's success rate. The same knowledge base will also serve as a foundation for user skill-building in proposal writing and application navigation.

## 2. Knowledge Base for Successful Proposals

A new, distinct knowledge base will be created to power the Wizzard.

### 2.1. Database Schema

A new table, `successful_proposals_insights`, will be added to the database with the following schema:

```sql
CREATE TABLE successful_proposals_insights (
    id UUID PRIMARY KEY,
    donor_id UUID REFERENCES donors(id),
    outcome_id UUID REFERENCES outcomes(id),
    field_context_id UUID REFERENCES field_contexts(id),
    budget_range VARCHAR(255),
    success_rate FLOAT,
    key_themes TEXT,
    common_keywords TEXT,
    dos_and_donts TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### 2.2. Data Population

A Python script, `backend/scripts/populate_wizard_kb.py`, will be created to populate the `successful_proposals_insights` table. The script will:

1.  Connect to the database and query the `proposals` table for all proposals with `status = 'approved'` or `is_accepted = TRUE`.
2.  For each successful proposal, it will extract the `donor_id`, `outcome_id`, `field_context_id`, and `form_data['Budget Range']`.
3.  It will then use a new `InsightExtractionCrew` (details in section 4) to analyze the `generated_sections` of the proposal to identify key themes, common keywords, and generate "do's and don'ts".
4.  The extracted and generated insights will be aggregated and inserted into the `successful_proposals_insights` table.

## 3. Frontend Implementation

### 3.1. `Chat.jsx` Modifications

-   A new "Wizzard" button will be added to the main chat interface in `frontend/src/screens/Chat/Chat.jsx`.
-   Clicking the button will open a modal (`WizzardModal.jsx`) that will contain the Wizzard's user interface.

### 3.2. `WizzardModal.jsx`

This new component will:

-   Display the user's currently selected proposal parameters.
-   Have a button to trigger the Wizzard's analysis.
-   Display the insights and suggestions returned by the backend in a clear and user-friendly format.

## 4. Backend Implementation

### 4.1. New API Endpoint

A new router will be created in `backend/api/wizzard.py`. It will have a single endpoint: `/api/wizzard/get-insights`.

This endpoint will:

-   Accept a POST request with the user's current `donor_id`, `outcome_id`, and `field_context_id`.
-   Query the `successful_proposals_insights` table to find relevant insights.
-   Use a new `WizzardCrew` to synthesize the retrieved insights and provide actionable suggestions to the user.

### 4.2. New AI Crews

Two new CrewAI crews will be created in `backend/utils/crew_wizzard.py`:

-   **`InsightExtractionCrew`**: This crew will be used by the data population script. It will have agents designed to read proposal text and extract themes, keywords, and best practices.
-   **`WizzardCrew`**: This crew will power the API endpoint. It will have agents that take the structured insights from the database and formulate helpful, user-facing advice.

## 5. Skill Building and App Navigation

The `successful_proposals_insights` table will be designed to be extensible. In the future, we can add more columns to store information related to:

-   **Proposal Writing Skills**: Tips on how to structure a proposal, write compelling narratives, etc.
-   **App Navigation**: Contextual help on how to use different features of the application.

This will be a separate, future phase of the project.

## 6. Implementation Plan

1.  ***Milestone 1: Backend Foundation***
    -   [ ] Create the `successful_proposals_insights` table in the database.
    -   [ ] Implement the `InsightExtractionCrew` in `backend/utils/crew_wizzard.py`.
    -   [ ] Implement the `populate_wizard_kb.py` script.

2.  ***Milestone 2: Backend API***
    -   [ ] Implement the `WizzardCrew` in `backend/utils/crew_wizzard.py`.
    -   [ ] Create the `/api/wizzard/get-insights` endpoint in `backend/api/wizzard.py`.

3.  ***Milestone 3: Frontend Integration***
    -   [ ] Create the `WizzardModal.jsx` component.
    -   [ ] Add the "Wizzard" button to `Chat.jsx` and integrate the modal.
    -   [ ] Connect the frontend to the backend API and display the results.

4.  ***Milestone 4: Pre-commit and Submission***
    -   [ ] Complete pre-commit steps to make sure proper testing, verifications, reviews and reflections are done.
    -   [ ] Submit the change.
