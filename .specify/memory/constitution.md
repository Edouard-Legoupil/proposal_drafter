# Proposal Drafter Constitution  


---

## 1. Project Principles

- **Open by default:** The tool is open-source and community-driven.
- **Strategic precision:** Proposals must align with organizational priorities and donor guidelines.
- **Security by design:** Secure coding, dependency management, and LLM prompt robustness.
- **Human-in-the-loop:** AI agents assist, but final approval and judgment are human.
- **Reusability and scalability:** Modular architecture for easy adaptation and integration.

---

## 2. Technical Stack


| Component        | Technology                  | Notes                                   |
| ---------------- | --------------------------- | --------------------------------------- |
| Agent Framework  | CrewAI                      | Modular AI agents for proposal drafting |
| Document Parsing | Docling, MinerU             | Standard and complex document layouts   |
| API              | FastAPI/GraphQL             | For downstream use                      |
| LLM              | Google Jules, Mistral, etc. | Multi-model support                     |
| Testing          | pytest, custom              | Test-driven development                 |
| Export           | Python-docx, ReportLab      | Word/PDF export for proposals           |


---

## 3. Workflow

1. **Context Analysis:** Agents analyze thematic priorities and compliance requirements.
2. **Proposal Structuring:** Outputs fully-structured, ready-to-submit project proposals.
3. **Contextual Adaptation:** Accepts input on target countries, population groups, and sectors.
4. **Validation & Export:** Projects are refined, validated, then exported to Word/PDF.

---

## 4. Data Model

- **Agents:** Specialized roles (research, budgeting, drafting).
- **Tasks:** Structured proposal components (context, objectives, budget, M&E).
- **Outputs:** Proposal documents (Word/PDF), validation tracking, export logs.

---

## 5. Security & Compliance

- **Data Privacy:** Only public data sources are used.
- **Secure Coding:** Input validation, dependency scanning, and LLM prompt injection prevention.
- **Access Control:** Role-based access for agents and users.
- **Audit Trail:** Log every change to agents, tasks, or proposals.

---
