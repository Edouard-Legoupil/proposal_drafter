# Proposal Drafter: Full Specification

**Spec ID:** 001-proposal-drafter  
---

## 1. Executive Summary

The Proposal Drafter is an **extensible agentic AI system** designed to automate and enhance the creation of high-quality, structured project proposals for UN agencies, NGOs, and mission-driven organizations. It ensures strategic alignment, compliance, and efficiency, turning complex requirements into compelling, submission-ready drafts.

**Core Objectives:**

- **AI-Powered Collaboration:** Simulate a real proposal team with specialized agents.
- **Strategic Precision:** Align proposals with organizational priorities and donor guidelines.
- **Adaptable & Open-Source:** Customizable for diverse sectors and editable by the community.
- **Seamless Export:** Generate, refine, and export proposals in Word/PDF with validation tracking.

---

## 2. Requirements

### 2.1 Functional Requirements


| ID     | Requirement                            | Priority | Notes                                                       |
| ------ | -------------------------------------- | -------- | ----------------------------------------------------------- |
| FR-001 | Agentic workflow for proposal drafting | High     | CrewAI-based agents for research, budgeting, drafting       |
| FR-002 | Document parsing and ingestion         | High     | Docling/MinerU for PDF/Word parsing                         |
| FR-003 | Contextual adaptation                  | High     | Accept user input for countries, populations, sectors       |
| FR-004 | Thematic and donor alignment           | High     | Integrate with organizational priorities and guidelines     |
| FR-005 | Validation and compliance checks       | High     | Ensure proposals meet completeness and compliance standards |
| FR-006 | Word/PDF export                        | High     | Generate and export proposals in Word/PDF format            |
| FR-007 | AI-Powered Budget Builder              | Medium   | Calibrated costing tool for realistic budgeting             |
| FR-008 | AI-Supported Reporting Toolkit         | Medium   | Tailored reporting templates and form generators            |


---

### 2.2 Non-Functional Requirements


| ID      | Requirement                 | Priority | Notes                                                   |
| ------- | --------------------------- | -------- | ------------------------------------------------------- |
| NFR-001 | Open by default             | High     | Open-source and community-driven                        |
| NFR-002 | Security by design          | High     | Secure coding, dependency management, prompt robustness |
| NFR-003 | Human-in-the-loop           | High     | AI agents assist, but final approval is human           |
| NFR-004 | Reusability and scalability | High     | Modular architecture for adaptation and integration     |
| NFR-005 | Test-driven development     | High     | Tests written before code for maintainability           |


---

## 3. User Stories

### 3.1 Proposal Writer

- **US-PROP-001:** As a proposal writer, I want to input project context so that the system generates a structured draft proposal.
  - **Acceptance Criteria:**
    - Proposal is aligned with thematic priorities and donor guidelines.
    - Draft is generated in <5 minutes.
- **US-PROP-002:** As a proposal writer, I want to export the proposal to Word/PDF so that I can submit it.
  - **Acceptance Criteria:**
    - Export includes validation tracking.
    - Format matches donor requirements.

---

### 3.2 Administrator

- **US-ADMIN-001:** As an admin, I want to configure agents and prompts so that the system adapts to new sectors or guidelines.
  - **Acceptance Criteria:**
    - Agents can be updated via configuration files.
    - Prompts are editable without code changes.

---

### 3.3 Donor Focal Point

- **US-REP-001:** As a donor focal point, I want to validate the proposal draft so that I can ensure compliance and quality.
  - **Acceptance Criteria:**
    - Validation checks cover completeness, alignment, and donor requirements.
    - Results are logged and time-stamped.

---

## 4. System Architecture

### 4.1 High-Level Overview

```
User Input → Agentic Workflow (CrewAI) → Proposal Structuring → Validation → Export (Word/PDF)
```

### 4.2 Components


| Component        | Technology                  | Responsibility                           |
| ---------------- | --------------------------- | ---------------------------------------- |
| Agent Framework  | CrewAI                      | Orchestrates specialized agents          |
| Document Parsing | Docling/MinerU              | Ingests and parses documents             |
| Agents           | Google Jules, Mistral, etc. | Research, budgeting, drafting            |
| Validation       | Custom scripts              | Ensures proposal completeness/compliance |
| Export           | Python-docx, ReportLab      | Generates Word/PDF proposals             |


---

## 5. Agent Roles and Prompts

### 5.1 Research Agent

- **Role:** Analyzes thematic priorities and donor guidelines.
- **Prompt:** "Research and summarize relevant policies, past evaluations, and thematic frameworks for the proposed intervention."

### 5.2 Drafting Agent

- **Role:** Composes the final proposal document.
- **Prompt:** "Draft a structured project proposal aligned with the research and budgeting results."

---

## 6. Data Model

- **Agents:** Roles, prompts, tools.
- **Tasks:** Proposal components (context, objectives, budget, M&E).
- **Outputs:** Proposal documents, validation logs, export files.

---

## 7. Workflow and Phases


| Phase                 | Description                               | Output                 |
| --------------------- | ----------------------------------------- | ---------------------- |
| Context Analysis      | Agents analyze priorities and guidelines  | Research summary       |
| Proposal Structuring  | Drafts proposal components                | Structured proposal    |
| Contextual Adaptation | Adapts to user input (countries, sectors) | Context-aware proposal |
| Validation & Export   | Validates and exports to Word/PDF         | Final proposal file    |


---

## 8. Security and Compliance

- **Data Privacy:** Only public data sources are used.
- **Secure Coding:** Input validation, dependency scanning, prompt injection prevention.
- **Access Control:** Role-based access for agents and users.
- **Audit Trail:** Log every change to agents, tasks, or proposals.

---

## 9. Testing Strategy

- **Unit Tests:** Validate agent initialization, parsing, and proposal structuring.
- **Integration Tests:** Ensure agentic workflows and export functionality work as expected.
- **Acceptance Tests:** Verify proposal completeness, alignment, and donor compliance.
- **Regression Tests:** Maintainability across future evolutions.

---

## 10. Deployment Plan

- **Phase 1:** Initialize CrewAI and set up agent framework.
- **Phase 2:** Implement core proposal generation workflow.
- **Phase 3:** Add contextual adaptation and export features.
- **Phase 4:** Deploy future enhancements (budget builder, reporting toolkit).

---

## 11. Risks and Mitigations


| Risk                               | Mitigation                                 |
| ---------------------------------- | ------------------------------------------ |
| Misalignment with donor guidelines | Regular validation and user feedback loops |
| Security vulnerabilities           | Dependency scanning, prompt robustness     |
| Over-reliance on AI                | Human-in-the-loop for final approval       |
| Community adoption                 | Comprehensive documentation and outreach   |


---

## 12. Glossary

- **Agentic Workflow:** Multi-agent system where agents collaborate to solve complex tasks.
- **CrewAI:** Framework for orchestrating AI agents.
- **Thematic Alignment:** Ensuring proposals match organizational priorities.
- **Validation Tracking:** Logs of proposal checks and compliance status.

---

## 13. Next Steps

1. Validate and refine this spec with stakeholders.
2. Initialize the `.specify/` directory in the repository.
3. Use `/specify`, `/plan`, and `/tasks` to generate the corresponding files.
4. Begin implementation with test-driven development.

---

**Reviewers:**

- Project Lead
- Technical Lead
- Donor Focal Point