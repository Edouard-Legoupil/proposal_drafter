# The Proposal Lifecycle 
 
 * __Draft:__ The initial stage after a proposal is generated.
 * __In Review:__ The proposal is with colleagues for feedback.
 * __Pre-submission:__ Addressing feedback before finalizing.
 * __Submitted:__ The proposal is finalized and submitted.
 * __Proposal Transfer:__ You can transfer the proposal to another user for submission.
 * __Deleted:__ The proposal is removed.

# User Roles & Access Control (RBAC)

The system uses a Role-Based Access Control system to ensure data security and appropriate collaborative workflows.

## Core Roles
* **System Admin:** Full access to user management, template configuration, and system-wide settings.
* **Knowledge Manager:** Responsible for maintaining the "ground truth" data used by the AI.
    * *Knowledge Manager (Donors):* Can create and edit donor-specific knowledge cards.
    * *Knowledge Manager (Outcomes):* Can create and edit outcome-linked knowledge cards.
    * *Knowledge Manager (Field Context):* Can create and edit field-context cards (restricted to own creations).
* **Project Reviewer:** Can access any proposal in the "In Review" stage to provide expert feedback.

## Access Rules
* **Ownership:** By default, you can edit any proposal or knowledge card you created.
* **Sharing:** Proposals can be transferred to new owners for final submission or continued drafting.
* **Reviewing:** Reviewers have read-access to proposals assigned to them or those marked for open review.

# Core Features


# The Dashboard
Your central hub for managing proposals and knowledge cards.

* **Pipeline Management:** View counts of proposals at different life-cycle stages.
* **Collaboration Metrics:** Track reviewer activity and edit frequency.
* **Knowledge Management:** Monitor the coverage and health of your knowledge card library.

# Proposal Generation
 
1. **Initiation:** Select a donor, outcome, and field context from the dashboard.
2. **Drafting:** Provide a concise project description. The AI dynamically selects the appropriate template (e.g., UNHCR Proposal vs. CERF Concept Note).
3. **AI Generation:** The system orchestrates multiple AI agents to draft sections based on relevant knowledge cards and references.
4. **Refinement:** Review the generated text, request regenerations with specific feedback, or manually update content.

# Peer Review

* **Assignment:** Invite colleagues to review specific sections of your proposal.
* **Feedback Loop:** Reviewers provide ratings and comments. Authors can respond to feedback directly within the tool.
* **Audit Trail:** All reviews and status changes are tracked in the proposal history.

# Knowledge Cards
Knowledge Cards are the foundation of the AI's understanding. They represent reusable snippets of validated information.

## Strategic Association
Knowledge cards are automatically retrieved based on your proposal's metadata (Donor, Outcome, Field Context) to ground the AI's generation in organizational knowledge.

## Versioning & Flexibility
* **Multi-versioning:** You can maintain multiple versions of a card for different contexts or grounding documents.
* **Reference Management:** Each card is backed by specific references (PDFs, URLs). You can audit or update these sources at any time.
* **RAG Integration:** The AI uses "Retrieval-Augmented Generation" to cite specific chunks of text from your references, ensuring accuracy and reducing hallucinations.