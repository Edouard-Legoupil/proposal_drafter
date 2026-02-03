# 🤖 AGENTS.md - Guide for AI Agents

Welcome, Agent! This document is designed to help you navigate and contribute effectively to the **Proposal Drafter** project.

---

## 🏗 Project Overview

The **Proposal Drafter** is an agentic AI system built to automate the creation of high-quality project proposals for UN agencies and NGOs. It uses a multi-agent workflow to simulate a professional proposal development team.

### Stack
- **Frontend**: React + Vite + Material UI (MUI)
- **Backend**: FastAPI (Python)
- **Orchestration**: [CrewAI](https://docs.crewai.com/)
- **Database**: PostgreSQL (with `pgvector` for similarity search)
- **Cache**: Redis (for session management)
- **AI Models**: Azure OpenAI (GPT-4) or Vertex AI

### Core Logic
The system uses a **Two-Level Knowledge Management** system:
1. **Knowledge Cards**: Curated, human-in-the-loop verified information snippets.
2. **Grounded Generation**: Injecting relevant Knowledge Cards into the LLM context to minimize hallucinations and ensure compliance.

---

## 🛠 Build and Test Commands

### Local Development (No Docker)
1. **Database Setup**:
   ```bash
   psql postgresql://postgres:postgres@localhost:5432/proposalgen -f db/database-setup.sql
   psql postgresql://postgres:postgres@localhost:5432/proposalgen -f db/seed.sql
   ```
2. **Backend**:
   ```bash
   cd backend
   python -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   uvicorn main:app --host 0.0.0.0 --port 8502 --reload
   ```
3. **Frontend**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

### Running with Docker
```bash
docker-compose -f docker-compose-local.yml up --build
```

---

## 📏 Code Style Guidelines

- **Backend (Python)**:
  - We use **Ruff** for linting and formatting. 
  - Follow FastAPI best practices: type hints, Pydantic models for validation, and dependency injection.
- **Frontend (JavaScript/React)**:
  - We use **ESLint** and **Prettier**.
  - Run linting with: `npm run lint` from the `frontend` directory.
  - Prefer functional components and hooks.

---

## 🧪 Testing Instructions

### End-to-End (Playwright)
The main verification path is through Playwright tests (Python-based).
1. Ensure the app is running (`./start.sh`).
2. Run tests:
   ```bash
   pytest playwright/tests/
   ```

### Frontend (Vitest)
Run component tests:
```bash
cd frontend
npm run test
```

### Backend (Pytest)
Run unit/integration tests:
```bash
cd backend
pytest tests/
```

---

## 🔒 Security Considerations

- **Data Privacy**: The project primarily uses public data sources. However, always treat user data with care.
- **Secrets Management**: **NEVER** hardcode keys. Use `.env` files and Environment Variables.
- **LLM Security**: Be aware of **Prompt Injection** risks. Ensure agent instructions are robust and inputs are sanitized.
- **Secure Coding**: Validate all inputs at the API layer using Pydantic schemas.

---

## 🚀 Agent Workflow & Best Practices

### Commit Messages
Follow the conventional commits pattern:
- `feat: ...` for new features.
- `fix: ...` for bug fixes.
- `docs: ...` for documentation changes.
- Ensure messages describe *why* a change was made, not just *what*.

### Pull Requests
- Provide a clear summary of changes.
- Include evidence of verification (e.g., "Playwright tests passed").
- Reference relevant issue IDs if applicable.

### Large Datasets
- For database changes, update `db/seed.sql` and `db/database-setup.sql`.
- Use the **Knowledge Cards** system (`backend/scripts/`) for managing large-scale AI context instead of cramming it into raw strings.

### Deployment
- **Azure**: Uses Bicep and GitHub Actions. See `infra/README.md`.
- **GCP**: Uses Cloud Run and Cloud SQL. See `doc_cloud-deployment.md`.

---

> [!TIP]
> When implementing new AI features, check `backend/config/agents.yaml` and `backend/config/tasks.yaml` first, as most of the agentic logic resides there.
