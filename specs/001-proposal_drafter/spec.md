# Proposal Drafter: Complete Technical Specification

**Spec ID:** 001-proposal-drafter  
**Version:** 2.0  
**Last Updated:** April 2025  
**Status:** Active Implementation  
---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Overview](#2-system-overview)
3. [Architecture](#3-architecture)
4. [Core Components](#4-core-components)
5. [API Endpoints](#5-api-endpoints)
6. [Agentic Workflow](#6-agentic-workflow)
7. [Data Model](#7-data-model)
8. [Database Schema](#8-database-schema)
9. [Knowledge Management System](#9-knowledge-management-system)
10. [Template System](#10-template-system)
11. [Incident Analysis & Quality Control](#11-incident-analysis--quality-control)
12. [Qualification System](#12-qualification-system)
13. [Authentication & Security](#13-authentication--security)
14. [Document Export](#14-document-export)
15. [Frontend Architecture](#15-frontend-architecture)
16. [Testing Strategy](#16-testing-strategy)
17. [Deployment](#17-deployment)
18. [Monitoring & Telemetry](#18-monitoring--telemetry)
19. [Requirements Traceability](#19-requirements-traceability)
20. [Glossary](#20-glossary)

---

## 1. Executive Summary

The **Proposal Drafter** is a comprehensive **agentic AI system** designed to automate and enhance the creation of high-quality, structured project proposals for UN agencies, NGOs, and mission-driven organizations. The system leverages **CrewAI** for multi-agent orchestration, **PostgreSQL with pgvector** for knowledge management, and **Redis** for session state management.

### Key Capabilities

| Capability | Description | Status |
|-----------|-------------|--------|
| Agentic Proposal Generation | Multi-agent workflow for drafting proposals | ✅ Implemented |
| Document Parsing & Ingestion | PDF/Word parsing via Docling/MinerU | ✅ Implemented |
| Contextual Adaptation | Dynamic adaptation to countries, populations, sectors | ✅ Implemented |
| Thematic & Donor Alignment | Integration with organizational priorities | ✅ Implemented |
| Validation & Compliance | Automated checks for completeness | ✅ Implemented |
| Word/PDF/Excel Export | Multi-format document generation | ✅ Implemented |
| Knowledge Card System | Curated, human-verified information snippets | ✅ Implemented |
| Template Management | Versioned donor-specific templates | ✅ Implemented |
| Incident Analysis | AI-powered review and root cause analysis | ✅ Implemented |
| Qualification System | Rule-based artifact validation | ✅ Implemented |
| Real-time Collaboration | SSE-based progress streaming | ✅ Implemented |
| Telemetry & Analytics | Comprehensive usage tracking | ✅ Implemented |

### Technology Stack

- **Frontend**: React 18 + Vite + Material UI (MUI)
- **Backend**: FastAPI (Python 3.10+)
- **Orchestration**: CrewAI with Azure OpenAI / Google Vertex AI
- **Database**: PostgreSQL 15+ with pgvector extension
- **Cache/Session**: Redis 7+
- **Search**: Vector embeddings with pgvector
- **LLMs**: Azure OpenAI (GPT-4), Google Vertex AI
- **Document Generation**: python-docx, ReportLab, openpyxl
- **Testing**: Pytest, Playwright, Vitest

---

## 2. System Overview

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                           FRONTEND                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐ │
│  │   React     │  │ Material UI  │  │       Custom Components        │ │
│  │   + Vite    │  │   (MUI)      │  │  (Dashboard, Chat, Reviews...) │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         FASTAPI BACKEND                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐ │
│  │  API        │  │  Core       │  │       Services                │ │
│  │  Routers   │  │  (Config, DB)│  │  (Template, Knowledge, etc.)   │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    CREWAI AGENTS                                │ │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌───────────────────────┐  │ │
│  │  │Proposal │ │Knowledge│ │Reference│ │Incident Analysis│  │ │
│  │  │ Agents │ │ Agents  │ │ Agents  │ │       Agent          │  │ │
│  │  └─────────┘ └─────────┘ └─────────┘ └───────────────────────┘  │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   PostgreSQL    │  │     Redis       │  │  Azure OpenAI   │
│  + pgvector     │  │   (Sessions)    │  │  / Vertex AI    │
│  (Persistent)   │  │   (Cache)       │  │  (LLM Crossing) │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### 2.2 Functional Overview

The Proposal Drafter system provides the following core functionalities:

1. **Proposal Generation**: AI-powered creation of structured proposals based on user inputs
2. **Knowledge Management**: Curated knowledge cards with versioning and referencing
3. **Template Management**: Donor-specific templates with version control
4. **Quality Assurance**: Automated incident analysis and qualification checks
5. **Collaboration**: Peer review workflows and feedback management
6. **Document Export**: Multi-format export (Word, PDF, Excel)
7. **Telemetry**: Comprehensive logging and analytics

---

## 3. Architecture

### 3.1 Backend Architecture

The backend follows a **layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────────┐
│                         API Layer (FastAPI)                          │
│  api/*.py - Route definitions and request handlers                 │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      Service Layer                                  │
│  services/*.py - Business logic and orchestration                 │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      Utility Layer                                   │
│  utils/*.py - Reusable components and helpers                      │
│    - crew_*.py: Agent crews and tasks                              │
│    - doc_export.py: Document generation                            │
│    - embedding_utils.py: Vector embeddings                         │
│    - incident_*.py: Incident analysis                              │
│    - qualification_*.py: Qualification validation                  │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      Core Layer                                      │
│  core/*.py - Infrastructure and configuration                       │
│    - config.py: Application settings                               │
│    - db.py: Database connection management                         │
│    - redis.py: Redis client and session management                 │
│    - security.py: Authentication and authorization                 │
│    - llm.py: LLM configuration                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      Models Layer                                   │
│  models/*.py - Data schemas and Pydantic models                    │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Frontend Architecture

The frontend uses a **component-based architecture** with React and Material UI:

- **Screens**: Page-level components (Dashboard, Chat, Login, etc.)
- **Components**: Reusable UI elements (Modal, Sidebar, Cards, etc.)
- **Utils**: Utility functions and hooks
- **State Management**: React Context and custom hooks

---

## 4. Core Components

### 4.1 API Routers

The backend exposes the following API routers:

| Router | Prefix | Purpose | Status |
|--------|--------|---------|--------|
| auth.py | /api | Authentication (JWT, SSO) | ✅ |
| proposals.py | /api | Proposal CRUD operations | ✅ |
| documents.py | /api | Document generation/export | ✅ |
| knowledge.py | /api | Knowledge card management | ✅ |
| templates.py | /api/templates | Template management | ✅ |
| template_management.py | /api/admin | Admin template operations | ✅ |
| incident.py | /api | Incident analysis | ✅ |
| qualification.py | /api | Qualification validation | ✅ |
| session.py | /api | Session management | ✅ |
| users.py | /api | User management | ✅ |
| admin.py | /api/admin | System administration | ✅ |
| metrics.py | /api | Metrics and analytics | ✅ |
| health.py | / | Health checks | ✅ |

### 4.2 Key Services

| Service | Location | Purpose |
|---------|----------|---------|
| IncidentService | utils/incident_service.py | AI-powered incident analysis |
| QualificationService | utils/qualification_service.py | Rule-based validation |
| TemplateService | services/template_service.py | Template management |
| PersistenceRepository | utils/persistence_repository.py | Database persistence |

---

## 5. API Endpoints

### 5.1 Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | /api/login | User login (JWT) | ❌ |
| POST | /api/logout | User logout | ✅ |
| POST | /api/refresh | Token refresh | ✅ |
| GET | /api/me | Current user info | ✅ |

### 5.2 Proposal Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/proposals | List all proposals |
| POST | /api/create-session | Create new proposal session |
| POST | /api/generate-proposal-sections/{session_id} | Generate all sections |
| POST | /api/process_section/{session_id} | Generate single section |
| POST | /api/regenerate_section/{proposal_id} | Regenerate section |
| POST | /api/update-section-content | Manual section update |
| POST | /api/save-draft | Save proposal draft |
| POST | /api/finalize-proposal | Finalize proposal |
| GET | /api/load-draft/{proposal_id} | Load draft |
| GET | /api/list-drafts | List user drafts |
| GET | /api/list-all-proposals | List all proposals |
| GET | /api/proposals/reviews | List proposals for review |
| GET | /api/templates | Get available templates |
| GET | /api/templates/{template_name} | Get template details |
| GET | /api/sections | Get default sections (deprecated) |

### 5.3 Knowledge Card Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/knowledge-cards | List knowledge cards |
| GET | /api/knowledge-cards/{card_id} | Get knowledge card |
| GET | /api/knowledge-cards/{card_id}/history | Get card history |
| POST | /api/knowledge-cards | Create knowledge card |
| PUT | /api/knowledge-cards/{card_id} | Update knowledge card |
| PUT | /api/knowledge-cards/{card_id}/sections/{section_name} | Update section |
| DELETE | /api/knowledge-cards/{card_id} | Delete knowledge card |
| POST | /api/knowledge-cards/{card_id}/generate | Generate card content |
| POST | /api/knowledge-cards/{card_id}/ingest-references | Ingest references |
| GET | /api/knowledge-cards/{card_id}/status | Generation status (SSE) |
| POST | /api/knowledge-cards/references | Create reference |
| PUT | /api/knowledge-cards/references/{reference_id} | Update reference |
| DELETE | /api/knowledge-cards/references/{reference_id} | Delete reference |
| POST | /api/knowledge-cards/references/{reference_id}/upload | Upload PDF |

### 5.4 Template Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/templates | List all templates |
| GET | /api/templates/request | List template requests |
| POST | /api/templates/request | Create template request |
| GET | /api/templates/request/{request_id} | Get template request |
| PUT | /api/templates/request/{request_id}/status | Update status |
| POST | /api/templates/request/{request_id}/comment | Add comment |
| POST | /api/templates/request/{request_id}/reply | Reply to feedback |
| GET | /api/templates/published/{template_name} | Get published template |
| GET | /api/templates/{template_name}/sections | Get template sections |

### 5.5 Incident Analysis Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/incidents/analyze | Analyze incident |
| POST | /api/incidents/analyze/proposal-review/{review_id} | Analyze proposal review |
| POST | /api/incidents/analyze/knowledge-card-review/{review_id} | Analyze KC review |
| POST | /api/incidents/analyze/template-review/{review_id} | Analyze template review |
| GET | /api/incidents/result/{analysis_id} | Get analysis result |
| GET | /api/reviews/{review_id}/analysis | Get review analysis |

### 5.6 Qualification Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/qualification/run | Run qualification |
| GET | /api/qualification/status | Get qualification status |

### 5.7 Document Export Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/generate-document/{proposal_id} | Generate document |
| GET | /api/export-pdf/{proposal_id} | Export as PDF |
| GET | /api/export-excel/{proposal_id} | Export as Excel |

### 5.8 Admin Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/admin/users | List all users |
| GET | /api/admin/options | Get admin options |
| PUT | /api/admin/users/{user_id}/settings | Update user settings |
| PUT | /api/admin/users/{user_id}/team | Update user team |
| DELETE | /api/admin/users/{user_id} | Delete user |
| POST | /api/admin/teams | Create team |
| GET | /api/admin/template-requests | Get template requests |

### 5.9 Health & Metrics Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | / | Health check / SPA fallback |
| GET | /api/health | System health |
| GET | /api/metrics | System metrics |

---

## 6. Agentic Workflow

### 6.1 Proposal Generation Crew (ProposalCrew)

**Location**: `backend/utils/crew_proposal.py`

**Agents**:
- **content_generator**: Generates structured content for each section
- **evaluator**: Reviews and validates generated content
- **regenerator**: Refines content based on user feedback

**Tasks**:
- **content_generation_task**: Generate section content with word/char limits
- **evaluation_task**: Review content against instructions and limits
- **regeneration_task**: Regenerate with user feedback

**Configuration**: `backend/utils/config/agents_proposal.yaml`

### 6.2 Knowledge Card Crew (ContentGenerationCrew)

**Location**: `backend/utils/crew_knowledge.py`

**Agents**:
- **researcher**: Finds relevant information from knowledge base
- **writer**: Composes knowledge card sections

**Configuration**: `backend/utils/config/agents_knowledge.yaml`

### 6.3 Reference Identification Crew (ReferenceIdentificationCrew)

**Location**: `backend/utils/crew_reference.py`

**Purpose**: Automated reference identification and classification

**Configuration**: `backend/utils/config/agents_reference.yaml`

### 6.4 Incident Analysis Crew (IncidentAnalysisCrew)

**Location**: `backend/utils/crew_incident_analysis.py`

**Agents**:
- **incident_triage_agent**: Categorizes and prioritizes incidents
- **incident_rca_agent**: Performs root cause analysis
- **incident_remediation_agent**: Suggests remediation strategies
- **incident_consistency_agent**: Validates consistency

**Purpose**: Comprehensive incident analysis with root cause identification and system fix recommendations

### 6.5 Agent Configurations

#### Proposal Agents Configuration

```yaml
content_generator:
  role: "Proposal Content Generator"
  goal: "Generate structured content for each section of the project proposal"
  backstory: "You are an AI specialized in drafting well-structured and informative humanitarian project proposals for UNHCR..."

evaluator:
  role: "Proposal Evaluator"
  goal: "Review and validate the generated content for quality, completeness, and adherence to instructions and word limit"
  backstory: "You are an AI trained to critically analyze humanitarian project proposals..."

regenerator:
  role: "Proposal Content Regenerator"
  goal: "Modify and refine existing content based on user feedback while ensuring adherence to project context"
  backstory: "You are an AI trained to refine and regenerate project proposal sections..."
```

#### Knowledge Agents Configuration

```yaml
researcher:
  role: "Expert Researcher"
  goal: "To find the most relevant information for a given section of a knowledge card"
  backstory: "You are an expert at sifting through large amounts of text to find the exact information needed..."

writer:
  role: "Senior Technical Writer"
  goal: "To write a clear, concise, and accurate section for a knowledge card"
  backstory: "You are a senior technical writer working for UNHCR..."
```

---

## 7. Data Model

### 7.1 Pydantic Models (Request/Response Validation)

**Location**: `backend/models/schemas.py`

#### User Models
- **User**: User information with roles, donor groups, outcomes, field contexts
- **UserRole**: User-role association
- **UserDonorGroup**: User-donor group mapping
- **UserOutcome**: User-outcome association
- **UserFieldContext**: User-field context association
- **UserSettings**: Geographic coverage and preferences

#### Proposal Models
- **BaseDataRequest**: Initial proposal data (form_data, project_description)
- **SectionRequest**: Single section generation request
- **RegenerateRequest**: Section regeneration with user feedback
- **SaveDraftRequest**: Draft save/Update request
- **FinalizeProposalRequest**: Proposal finalization
- **CreateSessionRequest**: New session creation
- **UpdateSectionRequest**: Manual section update
- **SubmitPeerReviewRequest**: Peer review submission
- **ReviewComment**: Individual review comment
- **SubmitReviewRequest**: Complete review submission

#### Knowledge Card Models
- **KnowledgeCardIn**: Knowledge card creation
- **KnowledgeCardReferenceIn**: Reference creation
- **IdentifyReferencesIn**: Reference identification
- **UpdateSectionIn**: Section update
- **IngestReferencesIn**: Reference ingestion

#### Template Models
- **DonorTemplateRequestCreate**: Template request creation
- **DonorTemplateCommentCreate**: Template comment
- **DonorTemplateStatusUpdate**: Status update

#### Incident Models
- **IncidentAnalyzeRequest**: Incident analysis request
- **IncidentAnalysisResponse**: Complete analysis response
- **ArtifactType**: Enum (proposal, knowledge_card, template)
- **Severity**: Enum (P0, P1, P2, P3)
- **UserSuggestion**: Suggested user action
- **RootCauseAnalysis**: Root cause with hypotheses
- **SuggestedSystemFix**: System-level fix recommendation
- **BlastRadius**: Impact scope assessment
- **ConsistencyCheck**: Validation results

### 7.2 Database Models

The database uses SQLAlchemy ORM-style models with raw SQL for flexibility. See [Database Schema](#8-database-schema) for complete table definitions.

---

## 8. Database Schema

### 8.1 Core Tables

#### Users and Authentication

```sql
-- Teams
CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL
);

-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    name TEXT,
    team_id UUID REFERENCES teams(id),
    security_questions JSONB,
    session_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    geographic_coverage_type TEXT,
    geographic_coverage_region TEXT,
    geographic_coverage_country TEXT,
    requested_role_id INTEGER REFERENCES roles(id)
);

-- Roles
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

-- User Roles (Many-to-Many)
CREATE TABLE user_roles (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

-- User Donor Groups
CREATE TABLE user_donor_groups (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    donor_group TEXT NOT NULL,
    PRIMARY KEY (user_id, donor_group)
);

-- User Outcomes (Many-to-Many)
CREATE TABLE user_outcomes (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    outcome_id UUID NOT NULL REFERENCES outcomes(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, outcome_id)
);

-- User Field Contexts (Many-to-Many)
CREATE TABLE user_field_contexts (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    field_context_id UUID NOT NULL REFERENCES field_contexts(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, field_context_id)
);
```

#### Donors, Outcomes, and Field Contexts

```sql
-- Donors
CREATE TABLE donors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id TEXT UNIQUE,
    name TEXT UNIQUE NOT NULL,
    country TEXT,
    donor_group TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Outcomes
CREATE TABLE outcomes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Field Contexts
CREATE TABLE field_contexts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT,
    name TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL,
    geographic_coverage TEXT,
    unhcr_region TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

#### Proposals

```sql
-- Proposal Status Enum
CREATE TYPE proposal_status AS ENUM (
    'draft',
    'in_review',
    'pre_submission',
    'submitted',
    'deleted',
    'generating_sections',
    'failed'
);

-- Proposals
CREATE TABLE proposals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    template_name VARCHAR(255) DEFAULT 'proposal_template_unhcr.json',
    form_data JSONB NOT NULL,
    project_description TEXT NOT NULL,
    generated_sections JSONB,
    reviews JSONB,
    is_accepted BOOLEAN DEFAULT FALSE,
    status proposal_status DEFAULT 'draft',
    contribution_id TEXT,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID NOT NULL REFERENCES users(id),
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Proposal Status History
CREATE TABLE proposal_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
    status proposal_status NOT NULL,
    generated_sections_snapshot JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Proposal Peer Reviews
CREATE TABLE proposal_peer_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
    reviewer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    proposal_status_history_id UUID REFERENCES proposal_status_history(id),
    section_name TEXT,
    rating VARCHAR(10),
    status VARCHAR(50) DEFAULT 'pending',
    deadline TIMESTAMPTZ,
    review_text TEXT,
    author_response TEXT,
    author_response_by TEXT,
    type_of_comment TEXT,
    severity TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

#### Knowledge Cards

```sql
-- Knowledge Cards
CREATE TABLE knowledge_cards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_name TEXT,
    type TEXT,
    summary TEXT NOT NULL,
    generated_sections JSONB,
    is_accepted BOOLEAN DEFAULT FALSE,
    status proposal_status DEFAULT 'draft',
    donor_id UUID REFERENCES donors(id) ON DELETE SET NULL,
    outcome_id UUID REFERENCES outcomes(id) ON DELETE SET NULL,
    field_context_id UUID REFERENCES field_contexts(id) ON DELETE SET NULL,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID NOT NULL REFERENCES users(id),
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT one_link_only CHECK (
        (CASE WHEN donor_id IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN outcome_id IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN field_context_id IS NOT NULL THEN 1 ELSE 0 END) <= 1
    )
);

-- Knowledge Card History
CREATE TABLE knowledge_card_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_card_id UUID NOT NULL REFERENCES knowledge_cards(id) ON DELETE CASCADE,
    generated_sections_snapshot JSONB,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Knowledge Card Reviews
CREATE TABLE knowledge_card_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_card_id UUID NOT NULL REFERENCES knowledge_cards(id) ON DELETE CASCADE,
    reviewer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    section_name TEXT,
    rating VARCHAR(10),
    review_text TEXT,
    author_response TEXT,
    author_response_by TEXT,
    type_of_comment TEXT,
    severity TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Knowledge Card References
CREATE TABLE knowledge_card_references (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url TEXT NOT NULL UNIQUE,
    reference_type TEXT NOT NULL,
    summary TEXT NOT NULL,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID NOT NULL REFERENCES users(id),
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    scraped_at TIMESTAMPTZ,
    scraping_error BOOLEAN DEFAULT FALSE
);

-- Knowledge Card to References (Many-to-Many)
CREATE TABLE knowledge_card_to_references (
    knowledge_card_id UUID NOT NULL REFERENCES knowledge_cards(id) ON DELETE CASCADE,
    reference_id UUID NOT NULL REFERENCES knowledge_card_references(id) ON DELETE CASCADE,
    PRIMARY KEY (knowledge_card_id, reference_id)
);

-- Knowledge Card Reference Vectors
CREATE TABLE knowledge_card_reference_vectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reference_id UUID NOT NULL REFERENCES knowledge_card_references(id) ON DELETE CASCADE,
    text_chunk TEXT NOT NULL,
    embedding vector(1536)
);
```

#### Templates and Qualification

```sql
-- Template Type Enum
CREATE TYPE template_type AS ENUM (
    'proposal',
    'concept_note',
    'knowledge_card'
);

-- Template Status Enum
CREATE TYPE template_status AS ENUM (
    'draft',
    'active',
    'deprecated',
    'archived'
);

-- Templates
CREATE TABLE templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    filename TEXT NOT NULL,
    template_type template_type NOT NULL,
    description TEXT,
    status template_status DEFAULT 'draft',
    is_default BOOLEAN DEFAULT FALSE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID REFERENCES users(id),
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_template_filename UNIQUE (filename),
    CONSTRAINT unique_default_template UNIQUE (template_type) DEFERRABLE INITIALLY IMMEDIATE
);

-- Template Versions
CREATE TABLE template_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES templates(id) ON DELETE CASCADE,
    version_number TEXT NOT NULL,
    version_notes TEXT,
    template_data JSONB NOT NULL,
    status template_status DEFAULT 'draft',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID REFERENCES users(id),
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_template_version UNIQUE (template_id, version_number)
);

-- Template Registry
CREATE TABLE template_registry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_key TEXT NOT NULL,
    template_type template_type NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID REFERENCES users(id),
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Donor Template Requests
CREATE TABLE donor_template_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    donor_id UUID REFERENCES donors(id) ON DELETE SET NULL,
    donor_ids UUID[],
    template_type TEXT DEFAULT 'proposal',
    configuration JSONB NOT NULL,
    initial_file_content JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Donor Template Comments
CREATE TABLE donor_template_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_request_id UUID REFERENCES donor_template_requests(id) ON DELETE CASCADE,
    template_name TEXT,
    user_id UUID NOT NULL REFERENCES users(id),
    comment_text TEXT NOT NULL,
    section_name TEXT,
    rating VARCHAR(10),
    severity TEXT,
    type_of_comment TEXT DEFAULT 'Donor Template',
    author_response TEXT,
    author_response_by TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Template Donors
CREATE TABLE template_donors (
    template_id UUID NOT NULL REFERENCES templates(id) ON DELETE CASCADE,
    donor_id UUID NOT NULL REFERENCES donors(id) ON DELETE CASCADE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (template_id, donor_id)
);

-- Template Audit Log
CREATE TABLE template_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID REFERENCES templates(id) ON DELETE SET NULL,
    template_version_id UUID REFERENCES template_versions(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    action_details JSONB,
    performed_by UUID REFERENCES users(id),
    performed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

#### Incident Analysis

```sql
-- Incident Analysis Results
CREATE TABLE incident_analysis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artifact_type TEXT NOT NULL,
    source_review_id TEXT NOT NULL,
    proposal_id UUID REFERENCES proposals(id),
    knowledge_card_id UUID REFERENCES knowledge_cards(id),
    template_request_id UUID REFERENCES donor_template_requests(id),
    incident_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'analyzed',
    analysis_payload JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (artifact_type, source_review_id)
);
```

#### Qualification System

```sql
-- Qualification Rule Sets
CREATE TABLE qualification_rule_sets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    template_type TEXT NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

-- Qualification Rules
CREATE TABLE qualification_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_set_id UUID NOT NULL REFERENCES qualification_rule_sets(id),
    rule_code TEXT NOT NULL,
    rule_name TEXT NOT NULL,
    description TEXT NOT NULL,
    rule_logic TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- Template Qualification Runs
CREATE TABLE template_qualification_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_version_id UUID NOT NULL REFERENCES template_versions(id),
    rule_set_id UUID NOT NULL REFERENCES qualification_rule_sets(id),
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Qualification Rule Evaluations
CREATE TABLE qualification_rule_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    qualification_run_id UUID NOT NULL REFERENCES template_qualification_runs(id),
    rule_id UUID NOT NULL REFERENCES qualification_rules(id),
    result TEXT NOT NULL,
    details TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

---

## 9. Knowledge Management System

### 9.1 Overview

The Knowledge Management System is a **two-level knowledge framework** designed to minimize hallucinations and ensure compliance:

1. **Knowledge Cards**: Curated, human-in-the-loop verified information snippets
2. **Grounded Generation**: Injecting relevant Knowledge Cards into LLM context

### 9.2 Knowledge Card Types

| Type | Template | Purpose | Example |
|------|----------|---------|---------|
| Donor | knowledge_card_donor_template.json | Donor-specific strategies and priorities | UNHCR, USAID |
| Outcome | knowledge_card_outcome_template.json | Strategic outcomes and results | Protection, Health |
| Field Context | knowledge_card_field_context_template.json | Geographic/location-specific context | Syria, Myanmar |

### 9.3 Knowledge Card Workflow

```
1. Create Knowledge Card
   - Link to Donor/Outcome/Field Context
   - Add summary and references
   - Submit for generation

2. AI Generation (Background)
   - ContentGenerationCrew generates sections
   - Researcher finds relevant information
   - Writer composes knowledge card content

3. Reference Ingestion
   - Upload PDF or URL
   - Extract text and create embeddings
   - Store in vector database (pgvector)

4. Versioning
   - Knowledge card history tracked
   - Snapshots stored for audit trail
```

### 9.4 Reference Management

- **URL scraping**: Automated web content extraction
- **PDF upload**: PDF text extraction via PyPDF2
- **Embedding**: 1536-dimensional vectors (text-embedding-ada-002)
- **Chunking**: RecursiveCharacterTextSplitter for optimal retrieval
- **Classification**: Evidence types (RCT, Case Study, Policy, etc.)

---

## 10. Template System

### 10.1 Template Hierarchy

```
File System templates/                      Database
          │                                       │
    ┌─────────┬─────────┐               ┌─────────┐
    │ Concept │ Proposal │               │ templates│
    │ Note    │          │               └─────────┘
    │         │          │                       │
    └─────────┴─────────┘                       ▼
          │                              template_versions
          ▼
    Template Files (.json)
    - proposal_template_unhcr.json
    - proposal_template_wfp.json
    - concept_note_unhcr.json
    - etc.
```

### 10.2 Template Structure

```json
{
  "template_name": "UNHCR Proposal",
  "template_type": "Proposal",
  "donors": ["UNHCR"],
  "description": "Template for UNHCR project proposals",
  "special_requirements": {
    "instructions": [
      "Follow UNHCR branding guidelines",
      "Include budget breakdown in USD"
    ]
  },
  "section_sequence": ["Executive Summary", "Problem Analysis", "..."],
  "sections": [
    {
      "section_name": "Executive Summary",
      "format_type": "text",
      "char_limit": 500,
      "instructions": "Write a concise executive summary...",
      "generation_sequence": 1
    },
    {
      "section_name": "Logical Framework",
      "format_type": "table",
      "instructions": "Create a logical framework table...",
      "columns": [...],
      "rows": [...],
      "generation_sequence": 5
    }
  ]
}
```

### 10.3 Template Management Features

| Feature | Description | Endpoint |
|---------|-------------|----------|
| Template Request | Submit request for new donor template | POST /api/templates/request |
| Status Update | Approve/reject template requests | PUT /api/templates/request/{id}/status |
| Comment/Review | Provide feedback on template requests | POST /api/templates/request/{id}/comment |
| Version Control | Track template versions in database | N/A |
| Donor Mapping | Map templates to donors | template_donors table |
| AuditLogging | Track all template changes | template_audit_log table |

### 10.4 Format Types

| Format | Description | Handler |
|--------|-------------|---------|
| text | Standard text generation | handle_text_format |
| fixed_text | Static text from template | handle_fixed_text_format |
| number | Numeric value generation | handle_number_format |
| table | Markdown table generation | handle_table_format |

---

## 11. Incident Analysis & Quality Control

### 11.1 Incident Analysis Workflow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Incident    │────▶│  Incident    │────▶│  Analysis   │
│  Submission  │     │  Triage     │     │  Result    │
└─────────────┘     └─────────────┘     └─────────────┘
                        │                    │
                        ▼                    ▼
                ┌─────────────┐     ┌─────────────┐
                │  Root Cause  │     │  Corrective  │
                │  Analysis    │     │  Suggestions │
                └─────────────┘     └─────────────┘
                        │                    │
                        └───────────┬───────┘
                                    ▼
                         ┌─────────────┐
                         │ Persistence  │
                         │ (Database)   │
                         └─────────────┘
```

### 11.2 Severity Levels

| Level | Description | Response Time | Examples |
|-------|-------------|---------------|----------|
| P0 | Critical | Immediate | Factual errors, compliance violations |
| P1 | High | < 24 hours | Major content gaps, structural issues |
| P2 | Medium | < 72 hours | Clarity issues, tone mismatches |
| P3 | Low | < 7 days | Formatting, typos, style suggestions |

### 11.3 Incident Types by Artifact

#### Proposal Incidents
- **P0**: Factual Error, Compliance Violation, Security Risk
- **P1**: Major Content Gap, Structural Issue, Quality Concern
- **P2**: Clarity Issue, Tone Mismatch, Minor Gap
- **P3**: Formatting Issue, Typo, Style Suggestion

#### Knowledge Card Incidents
- **P0**: Data Integrity, Source Error, Critical Omission
- **P1**: Metadata Issue, Duplicate Content, Outdated Information
- **P2**: Relevance Issue, Traceability Gap, Generic Content
- **P3**: Formatting Issue, Minor Error, Style Suggestion

#### Template Incidents
- **P0**: Compliance Issue, Structural Problem, Critical Error
- **P1**: Major Quality Issue, Content Gap, Format Problem
- **P2**: Clarity Issue, Tone Mismatch, Minor Improvement
- **P3**: Formatting Issue, Typo, Style Suggestion

### 11.4 Root Cause Taxonomy

| Root Cause | Description | Prevention |
|------------|-------------|------------|
| grounding_failure | AI couldn't ground in sources | Improve retrieval |
| outdated_knowledge | Sources are outdated | Regular updates |
| retrieval_failure | Failed to retrieve relevant info | Better embeddings |
| policy_guardrail_failure | Policy checks failed | Strengthen guardrails |
| template_mapping_failure | Template structure issue | Fix template mapping |
| citation_traceability_failure | Can't trace citations | Improve metadata |
| prompt_instruction_failure | Prompt misunderstanding | Clarify instructions |
| section_planning_failure | Section planning issue | Better planning |
| post_processing_failure | Post-processing error | Improve validation |
| metadata_quality_issue | Poor metadata quality | Better curation |
| missing_source_content | Source content missing | Add sources |

### 11.5 Auto-Analysis

The system provides **automated incident analysis** triggered by:
- Proposal review submissions
- Knowledge card review submissions
- Template feedback

**Process**:
1. Immediate acknowledgment to user
2. 30-second delay (to allow user to navigate away)
3. Background AI analysis via IncidentAnalysisCrew
4. Persist results to database
5. Update with final message

---

## 12. Qualification System

### 12.1 Overview

The Qualification System provides **rule-based validation** for:
- Proposals
- Knowledge Cards
- Templates

### 12.2 Qualification Rules

Rules are organized into **Rule Sets** by artifact type (proposal, knowledge_card, template).

**Example Rules**:
- **COMPLETENESS**: All required sections present
- **WORD_LIMIT**: Sections within specified limits
- **CITATION_QUALITY**: All citations properly formatted
- **TEMPLATE_COMpliance**: Follows template structure
- **DONOR_ALIGNMENT**: Aligned with donor requirements

### 12.3 Qualification Process

1. **Trigger**: Manual request via API or background task
2. **Rule Evaluation**: All active rules for artifact type are executed
3. **Result Collection**: Pass/fail for each rule
4. **Status Update**: Artifact marked as qualified or needs revision

### 12.4 Current Implementation

**Status**: Basic infrastructure in place (Backend API endpoints and database schema exist)
**Next Steps**: Implement rule engine and add comprehensive rule definitions

---

## 13. Authentication & Security

### 13.1 Authentication Methods

| Method | Implementation | Status |
|--------|---------------|--------|
| JWT Tokens | Custom JWT with HS256 | ✅ |
| EntraID (Azure AD) | OAuth 2.0 integration | ✅ |
| Session Cookies | Secure HTTP-only cookies | ✅ |

### 13.2 Security Features

#### Secrets Management
- Environment variables via .env files
- Required variables: SECRET_KEY, DB_*, AZURE_*
- NO hardcoded secrets in source code

#### Input Validation
- Pydantic models for all API requests
- Form data validation at database level
- Sanitization of user inputs

#### Prompt Injection Prevention
- Structured prompts with clear boundaries
- Input sanitization before LLM calls
- Output validation and repair

#### Access Control (RBAC)

**Roles**:
- **system admin**: Full system access
- **knowledge manager donors**: Manage donor-related knowledge cards
- **knowledge manager outcome**: Manage outcome-related knowledge cards
- **knowledge manager field context**: Manage field context knowledge cards
- **proposal writer**: Create and manage proposals
- **project reviewer**: Review and validate proposals

**RBAC Implementation**:
```python
# In security.py
def check_user_group_access(current_user, donor_id, outcome_id, field_context_id, owner_id):
    # Validate user has appropriate role for the artifact type
    if donor_id and "knowledge manager donors" not in current_user.get("roles", []):
        raise HTTPException(403, "Access denied")
    # ...
```

### 13.3 Audit Trail

- **Database**: All changes logged with timestamps and user IDs
- **Proposal History**: proposal_status_history table
- **Template Audit**: template_audit_log table
- **Knowledge Card History**: knowledge_card_history table
- **Incident Analysis**: incident_analysis_results table

---

## 14. Document Export

### 14.1 Supported Formats

| Format | Library | Features |
|--------|---------|----------|
| Word (.docx) | python-docx | Full styling, tables, headers |
| PDF | ReportLab | Print-ready, professional |
| Excel (.xlsx) | openpyxl | Spreadsheet data, tables |

### 14.2 Export Features

#### Word Export
- **Component**: `doc_export.py::create_word_from_sections`
- **Features**:
  - Markdown to Word conversion
  - Table support (Markdown → Word tables)
  - Bold/italic formatting
  - Section headers
  - Custom styles

#### PDF Export
- **Component**: `doc_export.py::create_pdf_from_sections`
- **Features**:
  - Classic PDF styling
  - Page formatting (A4, margins)
  - Content flow with proper spacing
  - Tables with grid styling

#### Excel Export
- **Component**: `doc_export.py::create_excel_from_sections`
- **Features**:
  - Multi-sheet support
  - Styled tables
  - Formula support
  - Conditional formatting

### 14.3 Export Endpoint

```
GET /api/generate-document/{proposal_id}?format={docx|pdf|xlsx}
```

**Process**:
1. Fetch proposal data from database
2. Resolve UUID references to names (donor, outcome, field context)
3. Load template for section ordering
4. Generate document using appropriate library
5. Stream as download

---

## 15. Frontend Architecture

### 15.1 File Structure

```
frontend/
├── src/
│   ├── App.jsx              # Main application router
│   ├── main.jsx             # React entry point
│   │
│   ├── components/          # Reusable UI components
│   │   ├── AlertModal/
│   │   ├── AnalysisModal/
│   │   ├── AssociateKnowledgeModal/
│   │   ├── Base/
│   │   ├── CommonButton/
│   │   ├── ConfirmationModal/
│   │   ├── KnowledgeCardHistory/
│   │   ├── KnowledgeCardReferences/
│   │   ├── LoadingModal/
│   │   ├── Modal/
│   │   ├── MultiSelectModal/
│   │   ├── OSSFooter/
│   │   ├── PdfUploadModal/
│   │   ├── ProgressModal/
│   │   ├── ResponsiveIllustration/
│   │   ├── RoleRequestModal/
│   │   ├── SectionReview/
│   │   ├── Sidebar/
│   │   ├── SingleSelectUserModal/
│   │   ├── UploadReferenceModal/
│   │   ├── UserAdminModal/
│   │   └── UserSettingsModal/
│   │
│   ├── screens/             # Page-level components
│   │   ├── Chat/
│   │   ├── Dashboard/
│   │   ├── DonorTemplateDetail/
│   │   ├── DonorTemplateRequest/
│   │   ├── ForgotPassword/
│   │   ├── KnowledgeCard/
│   │   ├── Login/
│   │   ├── QualityGate/
│   │   ├── Review/
│   │   └── ...
│   │
│   └── utils/
│       └── sse.js           # Server-Sent Events
│
├── public/                 # Static assets
├── Dockerfile
├── nginx.conf
├── package.json
└── vite.config.js
```

### 15.2 Key Screens

| Screen | Purpose | Features |
|--------|---------|----------|
| Dashboard | User homepage | Proposal list, metrics, quick actions |
| Chat | Interactive generation | Real-time AI chat, section generation |
| Knowledge Card | KC management | Create, view, edit knowledge cards |
| Review | Peer review | Rate, comment, reject/approve |
| Quality Gate | Validation | Pre-submission checks, compliance |
| Donor Template Detail | Template viewing | View, comment on templates |
| Donor Template Request | Request templates | Submit new template requests |
| Login | Authentication | JWT, SSO, session management |

### 15.3 Component Library

The frontend uses **Material UI (MUI)** components extented with custom styling and logic:

- **CommonButton**: Custom-styled buttons with consistent behavior
- **Modal**: Custom modal dialogs with consistent styling
- **ProgressModal**: Show async operation progress
- **Sidebar**: Navigation and user info
- **SectionReview**: Review interface for proposal sections
- **UploadReferenceModal**: PDF/URL upload for knowledge cards

### 15.4 State Management

- **React Context**: For global state (user, theme)
- **Custom Hooks**: For reusable state logic
- **Local State**: Component-level state with useState
- **SSE (Server-Sent Events)**: Real-time progress updates

---

## 16. Testing Strategy

### 16.1 Backend Testing (Pytest)

**Location**: `backend/tests/`

#### Unit Tests
- **test_health_check.py**: API health endpoint validation
- **test_knowledge.py**: Knowledge card operations
- **test_templates.py**: Template management
- **test_template_integration.py**: Template integration tests
- **test_template_system.py**: Template system validation

#### Integration Tests
- **test_auth_sso.py**: Authentication flow testing
- **test_generate_document.py**: Document generation
- **test_generation_fallback.py**: Fallback scenarios
- **test_geo_coverage.py**: Geographic coverage
- **test_get_base_data.py**: Base data retrieval
- **test_process_section.py**: Section processing
- **test_proposal_run_telemetry.py**: Telemetry tracking
- **test_regenerate_section.py**: Regeneration logic
- **test_reviews.py**: Review system
- **test_store_base_data.py**: Base data storage

### 16.2 Frontend Testing (Vitest)

**Location**: `frontend/src/screens/*/*.test.jsx`

- **Login.test.jsx**: Authentication form validation
- **ForgotPassword.test.jsx**: Password reset flow
- **Chat.test.jsx**: Chat interface
- **Dashboard.test.jsx**: Dashboard rendering

### 16.3 End-to-End Testing (Playwright)

**Location**: `playwright/tests/`

- **Full user journeys**: Login → Create proposal → Generate → Export
- **Cross-browser testing**: Chrome, Firefox, WebKit
- **Mobile responsiveness**: Viewport testing
- **Error scenarios**: Invalid inputs, network failures

### 16.4 Test Coverage Targets

| Component | Target Coverage |
|-----------|-----------------|
| Backend API | 90%+ |
| Backend Services | 85%+ |
| Frontend Components | 80%+ |
| Frontend Screens | 75%+ |
| Integration | 100% critical paths |

---

## 17. Deployment

### 17.1 Deployment Options

| Environment | Configuration | Status |
|-------------|---------------|--------|
| Local Development | docker-compose-local.yml | ✅ |
| Local (No DB) | docker-compose-local-nodb.yml | ✅ |
| Azure | docker-compose-azure.yml | ✅ |
| GCP Cloud Run | service.yaml, cloudbuild.yaml | ✅ |

### 17.2 Docker Configuration

#### Backend Dockerfile
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend /app/backend
COPY frontend/dist /app/frontend/dist
EXPOSE 8502
CMD ["python", "backend/main.py"]
```

#### Frontend Dockerfile
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm install
COPY frontend .
RUN npm run build
EXPOSE 80
CMD ["npx", "serve", "-s", "build", "-l", "80"]
```

### 17.3 Cloud Deployment (GCP)

**Infrastructure as Code**:
- **service.yaml**: Cloud Run service definition
- **cloudbuild.yaml**: CI/CD pipeline

**Database**: Cloud SQL PostgreSQL with pgvector extension

**Authentication**: 
- OAuth 2.0 for user auth
- IAM-based database auth

### 17.4 Environment Configuration

**Required Variables**:
```bash
# Database
DB_USERNAME=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=proposalgen
CLOUD_PROVIDER=local  # local | gcp | azure

# Azure OpenAI (LLM)
AZURE_OPENAI_ENDPOINT=https://...
AZURE_OPENAI_API_KEY=***
OPENAI_API_VERSION=2024-02-01
AZURE_DEPLOYMENT_NAME=gpt-4

# Azure OpenAI (Embeddings)
AZURE_EMBEDDING_MODEL=text-embedding-ada-002
AZURE_EMBEDDING_DEPLOYMENT_NAME=text-embedding-ada-002
AZURE_OPENAI_API_KEY_EMBED=***
AZURE_OPENAI_ENDPOINT_EMBED=https://...
AZURE_OPENAI_API_VERSION_EMBED=2023-05-15

# JWT
SECRET_KEY=your-secret-key

# EntraID (Microsoft Azure AD)
ENTRA_TENANT_ID=***
ENTRA_CLIENT_ID=***
ENTRA_CLIENT_SECRET=***
ENTRA_REDIRECT_URI=http://localhost:8503/auth/callback

# Redis
REDIS_URL=redis://localhost:6379

# Application
DEBUG=true
PERSIST_ANALYSIS_RESULTS=true
```

---

## 18. Monitoring & Telemetry

### 18.1 Telemetry System

**Component**: `backend/utils/proposal_run_logger.py`

**Tracker**: `artifact_run_logger` (ArtifactRunLogger)

#### Tracked Metrics

| Metric | Type | Purpose |
|--------|------|---------|
| Run Creation | Event | Track proposal generation starts |
| Agent Execution | Event | Track each agent's performance |
| Section Generation | Event | Track per-section timing |
| Output Metrics | Event | Track generated content stats |
| Run Completion | Event | Track overall success/failure |
| Failure Logging | Event | Track errors and exceptions |

#### Captured Data

```python
# Run creation
run_id = artifact_run_logger.create_run_record(
    artifact_type=