# Proposal Drafter Constitution

**Version:** 2.0  
**Last Updated:** April 2025  
**Status:** Active Implementation  

---

## 1. Project Vision

The Proposal Drafter is an **extensible agentic AI system** that automates and enhances the creation of high-quality, structured project proposals for UN agencies, NGOs, and mission-driven organizations. It ensures strategic alignment, compliance, and efficiency while turning complex requirements into compelling, submission-ready drafts.

---

## 2. Project Principles

### 2.1 Core Values

- **Open by default:** Open-source (MIT License) and community-driven development
- **Strategic precision:** All proposals must align with organizational priorities and donor guidelines
- **Security by design:** Secure coding practices, dependency management, and LLM prompt robustness
- **Human-in-the-loop:** AI agents assist and accelerate, but final approval and judgment remain human
- **Reusability and scalability:** Modular architecture for easy adaptation across sectors and organizations

### 2.2 Quality Standards

- **Test-driven development:** All features developed with comprehensive test coverage
- **Production-ready:** Comprehensive error handling, logging, and validation
- **User-centric:** Intuitive interfaces with clear feedback and guidance
- **Transparent:** All AI-generated content is traceable and reviewable
- **Compliant:** Adheres to UN and donor compliance requirements

---

## 3. Technical Stack

### 3.1 Backend

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Framework | FastAPI | Latest | REST API with automatic docs |
| Language | Python | 3.10+ | Primary backend language |
| Async | AnyIO | Latest | Async task support |
| ORM | SQLAlchemy | 2.0+ | Database interactions |
| Database | PostgreSQL | 15+ | Primary data store |
| Vector Search | pgvector | Latest | Embedding similarity search |
| Cache | Redis | 7+ | Session management, caching |

### 3.2 AI & ML

| Component | Technology | Purpose |
|-----------|------------|---------|
| Orchestration | CrewAI | Multi-agent workflow management |
| LLM | Azure OpenAI | GPT-4 for text generation |
| Embeddings | Azure OpenAI | text-embedding-ada-002 (1536-dim) |
| Alternative | Google Vertex AI | Backup LLM provider |
| Alternative | Google Gemini | Experimental support |

### 3.3 Document Processing

| Component | Technology | Purpose |
|-----------|------------|---------|
| PDF Parsing | PyPDF2 | PDF text extraction |
| PDF Parsing | pdfplumber | Advanced PDF extraction |
| Word Gen | python-docx | Word document generation |
| PDF Gen | ReportLab | PDF document generation |
| Excel Gen | openpyxl | Excel spreadsheet generation |
| Markdown | MarkdownIt | Markdown parsing |

### 3.4 Frontend

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Framework | React | 18+ | UI framework |
| Build | Vite | Latest | Fast builds and HMR |
| UI Library | Material UI (MUI) | 5+ | Component library |
| State | React Context | Native | Global state management |
| Testing | Vitest | Latest | Component testing |
| HTTP | Axios | Latest | API communication |
| SSE | Native | - | Real-time updates |

### 3.5 Testing

| Type | Technology | Purpose |
|------|------------|---------|
| Backend Unit | pytest | API and service testing |
| Backend Integration | pytest | Multi-component testing |
| Frontend Unit | Vitest | Component testing |
| E2E | Playwright | Cross-browser testing |
| Mock Server | MSW | API mocking |

### 3.6 Infrastructure

| Component | Technology | Purpose |
|-----------|------------|---------|
| Containerization | Docker | Application packaging |
| Web Server | Gunicorn | Production WSGI server |
| Reverse Proxy | Nginx | Static files, SSL termination |
| Container Orchestration | Docker Compose | Local development |
| CI/CD (GCP) | Cloud Build | Automated deployments |
| Cloud (GCP) | Cloud Run + Cloud SQL | Production hosting |
| Cloud (Azure) | Container Apps | Alternative deployment |

---

## 4. Workflow

### 4.1 High-Level Process

```
User Input → Session Creation → Form Data Collection → 
Template Selection → Section Generation (Background) → 
Review & refinement → Validation & Quality Checks → 
Export (Word/PDF/Excel) → Submission
```

### 4.2 Agentic Workflow

1. **Proposal Generation** (ProposalCrew)
   - Content Generator creates structured sections
   - Evaluator validates quality and compliance
   - Regenerator refines based on feedback

2. **Knowledge Card Generation** (ContentGenerationCrew)
   - Researcher finds relevant information
   - Writer composes knowledge card content

3. **Reference Identification** (ReferenceIdentificationCrew)
   - Identifies and classifies reference materials
   - Extracts and embeds content

4. **Incident Analysis** (IncidentAnalysisCrew)
   - Triage categorizes incidents
   - Root Cause Analysis identifies underlying issues
   - Remediation suggests fixes
   - Consistency validates outputs

### 4.3 Generation Lifecycle

```
┌──────────┐    ┌──────────┐    ┌──────────┐
│  Draft   │───▶│Generating│───▶│  Draft   │
└──────────┘    └──────────┘    └──────────┘
                      │
                      ▼
┌──────────┐    ┌──────────┐    ┌──────────┐
│  Review  │◀───│ In Review│◀───│Submitted │
└──────────┘    └──────────┘    └──────────┘
                      │
                 ┌────────┴────────┐
                 ▼                  ▼
            ┌──────────┐       ┌──────────┐
            │ Approved │       │ Rejected │
            └──────────┘       └──────────┘
```

---

## 5. Data Model

### 5.1 Core Entities

- **Users**: User accounts with roles, teams, and permissions
- **Teams**: Organizational groups
- **Roles**: Permission levels (admin, knowledge manager, proposal writer, reviewer)
- **Donors**: Funding organizations and agencies
- **Outcomes**: Strategic outcomes and results
- **Field Contexts**: Geographic and operational contexts

### 5.2 Artifacts

- **Proposals**: Project proposal documents
- **Knowledge Cards**: Curated information snippets (donor/outcome/field-context linked)
- **Templates**: Structured document formats with sections and instructions
- **references**: Source documents and materials

### 5.3 Quality & Compliance

- **Incident Analysis**: AI-powered review and root cause analysis
- **Qualification**: Rule-based validation of artifacts
- **Reviews**: Peer review workflows and feedback
- **Audit Logs**: Change tracking for all artifacts

---

## 6. Security & Compliance

### 6.1 Authentication

- **JWT Tokens**: Primary authentication mechanism (HS256)
- **EntraID**: Microsoft Azure AD OAuth 2.0 integration
- **Session Cookies**: Secure HTTP-only cookies
- **Password Hashing**: Werkzeug security (PBKDF2)

### 6.2 Authorization

- **RBAC**: Role-Based Access Control with 6 role types
- **Group Access**: Donor/Outcome/Field Context level permissions
- **Ownership**: Object-level permission checks

### 6.3 Data Protection

- **Input Validation**: Pydantic models for all API requests
- **Sanitization**: User input cleaning before processing
- **Secrets Management**: Environment variables (NO hardcoded secrets)
- **Encryption**: HTTPS/TLS for all communications

### 6.4 LLM Security

- **Prompt Injection Prevention**: Structured prompts with boundaries
- **Output Validation**: JSON parsing, schema validation, repair
- **Grounding**: Similarity search with pgvector
- **Rate Limiting**: Per-user request throttling

### 6.5 Audit & Compliance

- **Audit Trail**: All changes logged with timestamps and user IDs
- **Proposal History**: Complete version history
- **Incident Tracking**: All issues and resolutions logged
- **Compliance Checks**: Automated validation against standards

---

## 7. Quality Assurance

### 7.1 Automated Quality Checks

- **Incident Analysis**: AI-powered review of all feedback
- **Root Cause Analysis**: Identifies underlying issues (12 categories)
- **Severity Classification**: P0 (Critical) to P3 (Low)
- **System Fix Suggestions**: Remediation recommendations

### 7.2 Manual Quality Gates

- **Peer Review**: Structured review workflow with ratings
- **Quality Gate**: Pre-submission validation checklist
- **Template Validation**: Donor-specific compliance checks
- **Knowledge Card Review**: Content curation and approval

### 7.3 Qualification System

- **Rule Sets**: Organized by artifact type (proposal, knowledge_card, template)
- **Rule Evaluation**: Automated pass/fail assessment
- **Status Tracking**: Qualification status for all artifacts

---

## 8. Open Source Commitments

### 8.1 Licensing

- **License**: MIT License
- **Repository**: Public GitHub repository
- **Contribution**: Open to community contributions
- **Attribution**: Proper credit for all contributors

### 8.2 Community

- **Documentation**: Comprehensive and up-to-date
- **Issues**: Transparent issue tracking
- **Roadmap**: Public development roadmap
- **Support**: Community support channels

### 8.3 Standards

- **Code Quality**: PEP 8, Ruff linting
- **Testing**: TDD approach with 75-90% coverage
- **Documentation**: Markdown with examples
- **Contribution**: Clear contribution guidelines

---

*This constitution defines the principles, standards, and commitments that guide the Proposal Drafter project.*

**Reviewers:**
- Project Lead: Edouard Legoupil (legoupil@unhcr.org)
- Technical Lead: [TBD]
- Donor Focal Point: [TBD]
- QA Lead: [TBD]
