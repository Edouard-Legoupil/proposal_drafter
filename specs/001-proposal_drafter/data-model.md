# Data Model: Proposal Drafter

**Version:** 1.0  
**Date:** 2025-05-13  
**Input:** Feature specification from `/specs/001-proposal_drafter/spec.md`  
**Purpose:** Phase 1 - Data Model Design

---

## Executive Summary

This document defines the comprehensive data model for the Proposal Drafter system, including database schema (PostgreSQL with pgvector), Pydantic models for request/response validation, and entity relationships. The data model supports the full proposal generation workflow, knowledge management, template management, and quality assurance processes.

**Source:** The detailed database schema is defined in [specs/001-proposal_drafter/spec.md - Section 8](specs/001-proposal_drafter/spec.md#8-database-schema). This document provides a consolidated overview and design rationale.

---

## Entity Overview

### 1. Core Entities

#### 1.1 Users and Authentication

| Entity | Type | Purpose | Relationships |
|--------|------|---------|---------------|
| Team | Core | Organizational group | One-to-many with Users |
| User | Core | User account with authentication | Belongs to Team, has many Roles, Donor Groups, Outcomes, Field Contexts |
| Role | Core | Permission level (6 types) | Many-to-many with Users |
| UserDonorGroup | Association | User-donor group mapping | Many-to-many |
| UserOutcome | Association | User-outcome association | Many-to-many |
| UserFieldContext | Association | User-field context association | Many-to-many |
| UserSettings | Extended | Geographic coverage and preferences | Belongs to User |

**Design Rationale:**
- Users are the primary actors in the system, creating proposals, knowledge cards, and reviews
- RBAC (Role-Based Access Control) with 6 role types enables fine-grained permissions
- Association tables enable many-to-many relationships between users and organizational entities
- Geographic coverage and preferences support contextual adaptation

#### 1.2 Organizational Context

| Entity | Type | Purpose | Relationships |
|--------|------|---------|---------------|
| Donor | Core | Funding organization/agency | Has many Knowledge Cards, Templates |
| Outcome | Core | Strategic outcome/result | Linked to Proposals, Knowledge Cards |
| FieldContext | Core | Geographic/operational context | Linked to Proposals, Knowledge Cards |

**Design Rationale:**
- Donors, Outcomes, and Field Contexts provide the organizational framework for proposals
- These entities enable contextual adaptation of proposals to specific funding sources and operational contexts
- Each entity can be linked to knowledge cards for grounding AI generation in relevant context

#### 1.3 Proposals

| Entity | Type | Purpose | Relationships |
|--------|------|---------|---------------|
| Proposal | Core | Project proposal document | Belongs to User, has many Status History, Peer Reviews |
| ProposalStatusHistory | Audit | Track status changes over time | Belongs to Proposal |
| ProposalPeerReview | Quality | Peer review workflow | Belongs to Proposal, Reviewer |

**Status Enum:**
```sql
CREATE TYPE proposal_status AS ENUM (
    'draft',
    'in_review',
    'pre_submission',
    'submitted',
    'deleted',
    'generating_sections',
    'failed'
);
```

**Design Rationale:**
- Proposals are the primary artifact of the system
- Status history enables full audit trail of proposal evolution
- Peer review workflow supports quality assurance and collaboration
- JSONB fields (form_data, generated_sections) enable flexible, evolving proposal structures

#### 1.4 Knowledge Management

| Entity | Type | Purpose | Relationships |
|--------|------|---------|---------------|
| KnowledgeCard | Core | Curated information snippet | Belongs to User, linked to Donor/Outcome/FieldContext, has many History, Reviews |
| KnowledgeCardHistory | Audit | Track knowledge card changes | Belongs to KnowledgeCard |
| KnowledgeCardReview | Quality | Review workflow for knowledge cards | Belongs to KnowledgeCard, Reviewer |
| KnowledgeCardReference | Source | External reference/document | Has many KnowledgeCards |
| KnowledgeCardReferenceVector | Vector | Embedding for similarity search | Belongs to Reference |
| KnowledgeCardToReferences | Association | Many-to-many between Cards and References | Association |

**Design Rationale:**
- Knowledge cards are the foundation of the grounded generation approach
- Each knowledge card can be linked to exactly one of: Donor, Outcome, or FieldContext (constraint: one_link_only)
- References are scraped from URLs and chunked for vector embedding
- Vector embeddings (1536-dimensional) enable similarity search via pgvector
- Reviews ensure quality and relevance of knowledge cards

#### 1.5 Templates

| Entity | Type | Purpose | Relationships |
|--------|------|---------|---------------|
| Template | Core | Structured document format | Has many Versions, linked to Donor |
| TemplateVersion | Version | Versioned template content | Belongs to Template |
| TemplateRegistry | Registry | Template metadata registry | Standalone |
| DonorTemplateRequest | Request | Template customization request | Belongs to User, linked to Donor |
| DonorTemplateComment | Feedback | Comments on template requests | Belongs to Request, User |

**Type Enums:**
```sql
CREATE TYPE template_type AS ENUM (
    'proposal',
    'concept_note',
    'knowledge_card'
);

CREATE TYPE template_status AS ENUM (
    'draft',
    'active',
    'deprecated',
    'archived'
);
```

**Design Rationale:**
- Templates define the structure and instructions for proposal generation
- Versioning enables evolution of templates while maintaining compatibility
- Donor-specific templates support alignment with donor guidelines
- Template requests enable collaborative template development workflow

#### 1.6 Quality Assurance

| Entity | Type | Purpose | Relationships |
|--------|------|---------|---------------|
| Incident | Analysis | AI-powered review and root cause | Belongs to User, linked to Artifact |
| Qualification | Validation | Rule-based artifact validation | Belongs to User, linked to Artifact |
| Review | Collaboration | Peer review workflow | Polymorphic (Proposal, KnowledgeCard, Template) |
| AuditLog | Compliance | Change tracking | System-wide |

**Artifact Type Enum:**
```sql
CREATE TYPE artifact_type AS ENUM (
    'proposal',
    'knowledge_card',
    'template'
);
```

**Severity Enum:**
```sql
CREATE TYPE severity AS ENUM (
    'P0',  -- Critical
    'P1',  -- High
    'P2',  -- Medium
    'P3'   -- Low
);
```

**Design Rationale:**
- Incident analysis provides AI-powered quality assurance
- Qualification system enables rule-based validation before submission
- Review workflow supports human-in-the-loop quality control
- Audit logs ensure full traceability of all changes

---

## Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                           USERS & AUTHENTICATION                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────┐       ┌──────────┐       ┌──────────┐               │
│  │   Team   │       │   User   │       │   Role   │               │
│  └────┬─────┘       └────┬─────┘       └────┬─────┘               │
│       │                │                   │                       │
│       │ 1:N            │ N:M                │                       │
│       ▼                ▼                   ▼                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                             │
│  │UserRoles │  │UserDonor │  │UserOutcome│                             │
│  │          │  │ Groups   │  │          │                             │
│  └──────────┘  └──────────┘  └──────────┘                             │
│                                                     ┌──────────┐    │
│                                                     │UserField │    │
│                                                     │Contexts │    │
│                                                     └──────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         ORGANIZATIONAL CONTEXT                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │    Donor     │  │   Outcome     │  │ Field Context │           │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘           │
│         │                 │                  │                  │
│         │ 1:N             │ 1:N              │ 1:N               │
│         ▼                 ▼                  ▼                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   Knowledge Cards                         │   │
│  │  (Each card linked to exactly one: Donor OR Outcome OR FC) │   │
│  └──────────────────────┬───────────────────────────────────┘   │
│                          │                                          │
│        ┌─────────────────┼─────────────────┐                     │
│        ▼                 ▼                 ▼                     │
│  ┌─────────┐       ┌─────────┐       ┌─────────┐              │
│  │ History │       │ Reviews │       │References│              │
│  └─────────┘       └─────────┘       └────┬────┘              │
│                                              │                   │
│                       ┌──────────────────────┼───────────────┐   │
│                       ▼                      ▼                 │   │
│                ┌──────────────┐      ┌──────────────┐           │   │
│                │  Reference    │      │   Vectors     │           │   │
│                │   Metadata    │      │  (pgvector)   │           │   │
│                └──────────────┘      └──────────────┘           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                           PROPOSALS                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐       ┌──────────────┐                           │
│  │   Proposal   │◄──────│    User      │                           │
│  └──────┬───────┘       └──────────────┘                           │
│         │                                                          │
│         │ 1:N                                                       │
│         ▼                                                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                Proposal Status History                       │   │
│  └──────────────┬───────────────────────────────────────────┘   │
│                 │                                               │
│                 ▼                                               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                Proposal Peer Reviews                        │   │
│  └───────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                          TEMPLATES                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐       ┌──────────────┐                           │
│  │   Template   │◄──────│    User      │                           │
│  └──────┬───────┘       └──────────────┘                           │
│         │                                                          │
│         │ 1:N                                                       │
│         ▼                                                          │
│  ┌──────────────┐                                                   │
│  │TemplateVersions│                                                   │
│  └──────────────┘                                                   │
│                                                                      │
│  ┌──────────────┐       ┌──────────────┐                           │
│  │ DonorTemplate │       │  Comments    │                           │
│  │   Requests    │◄──────│              │                           │
│  └──────────────┘       └──────────────┘                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        QUALITY ASSURANCE                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐       ┌──────────────┐                           │
│  │  Incidents    │       │ Qualifications│                           │
│  └──────────────┘       └──────────────┘                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Validation Rules

### User Input Validation

All API inputs are validated using Pydantic models. Key validation rules:

1. **Email:** Valid email format, unique
2. **Password:** Minimum 12 characters (recommended), complexity requirements
3. **JSONB Fields:** Valid JSON structure, size limits (10MB max)
4. **UUID Fields:** Valid UUID format
5. **Enum Fields:** Must match defined enum values
6. **Text Fields:** Length limits based on database column definitions

### Business Logic Validation

1. **Proposal Validation:**
   - Required fields must be present in form_data
   - Project description must not be empty
   - Template must exist and be active
   - User must have permission to create proposals

2. **Knowledge Card Validation:**
   - Summary must not be empty
   - Must be linked to exactly one context (Donor, Outcome, or FieldContext)
   - References must have valid URLs

3. **Template Validation:**
   - Template data must be valid JSON
   - Version numbers must be unique per template
   - Only one default template per type

4. **Review Validation:**
   - Reviewer must not be the author
   - Rating must be within valid range
   - Deadline must be in the future

### State Transitions

**Proposal Status Flow:**
```
draft → in_review → pre_submission → submitted
         ↓
   generating_sections → draft (on completion)
         ↓
       failed (on error)
```

**Knowledge Card Status Flow:**
```
draft → in_review → accepted
         ↓
       failed
```

**Template Request Status Flow:**
```
pending → approved → active
         ↓
       rejected
```

---

## Database Design Decisions

### 1. PostgreSQL with pgvector

**Decision:** Use PostgreSQL with pgvector extension  
**Rationale:**
- ACID compliance for transactional data
- pgvector provides efficient vector similarity search
- No need for separate vector database
- Native JSONB support for flexible schemas
- Strong community support and reliability

### 2. UUID Primary Keys

**Decision:** Use UUID v4 for most primary keys  
**Rationale:**
- Avoids ID collisions in distributed systems
- No sequential information leakage
- Easier for replication and sharding
- Compatible with PostgreSQL's gen_random_uuid()

**Exceptions:**
- Roles: SERIAL (small, fixed set)
- Some association tables use composite primary keys

### 3. JSONB for Flexible Data

**Decision:** Use JSONB for form_data, generated_sections, etc.  
**Rationale:**
- Proposal structures evolve over time
- Avoids frequent schema migrations
- Enables dynamic form fields
- Supports nested data structures
- Indexable in PostgreSQL

**Trade-offs:**
- Less type safety at database level
- Harder to query specific fields
- Larger storage footprint

### 4. Association Tables for Many-to-Many

**Decision:** Explicit association tables for M:N relationships  
**Rationale:**
- Clear schema structure
- Can include additional metadata in associations
- Consistent with relational database best practices
- Easier to query and maintain

### 5. Audit Tables for History Tracking

**Decision:** Separate history tables for mutable entities  
**Rationale:**
- Complete audit trail
- No data loss on updates
- Efficient for compliance and debugging
- Can be archived or pruned separately

### 6. pgvector Configuration

**Decision:** HNSW index with m=16, ef_construction=64  
**Rationale:**
- Good balance between accuracy and performance
- m=16: 16 bidirectional links per node
- ef_construction=64: 64 neighbors considered during construction
- ef_search: Typically 40-100 for search queries

---

## Indexing Strategy

### Primary Indexes

1. **Primary Keys:** All tables have primary key indexes (UUID or composite)
2. **Foreign Keys:** All foreign keys are indexed for join performance
3. **Unique Constraints:** All UNIQUE columns have indexes

### Performance Indexes

1. **User Lookup:**
   - users.email (UNIQUE)
   - users.team_id

2. **Proposal Lookup:**
   - proposals.user_id
   - proposals.status
   - proposals.template_name
   - proposals.created_at

3. **Knowledge Card Lookup:**
   - knowledge_cards.donor_id
   - knowledge_cards.outcome_id
   - knowledge_cards.field_context_id
   - knowledge_cards.status
   - knowledge_cards.created_at

4. **Vector Search:**
   - knowledge_card_reference_vectors.embedding (HNSW)

5. **Full-Text Search:**
   - Proposals: form_data (JSONB) - consider GIN index
   - Knowledge Cards: summary, generated_sections

---

## Storage Estimates

### Per-Record Sizes

| Entity | Average Size | Notes |
|--------|--------------|-------|
| User | ~1KB | Basic profile info |
| Proposal | ~10-100KB | Includes form_data and generated_sections JSONB |
| Knowledge Card | ~5-50KB | Includes generated_sections JSONB |
| Knowledge Card Reference | ~1-10KB | Text content and metadata |
| Knowledge Card Reference Vector | ~6KB | 1536 float32 values = 6144 bytes |
| Template | ~1-10KB | Template metadata |
| Template Version | ~5-50KB | Full template data |

### Database Growth Projections

| Deployment Scale | Proposals | Knowledge Cards | Storage |
|----------------|-----------|----------------|---------|
| Small (1 year) | 1,000 | 5,000 | ~500MB |
| Medium (1 year) | 10,000 | 50,000 | ~5GB |
| Large (1 year) | 100,000 | 500,000 | ~50GB |

---

## Data Retention Policy

| Data Type | Retention Period | Notes |
|-----------|-----------------|-------|
| Proposals | Forever | User-created content |
| Knowledge Cards | Forever | Reusable content |
| Templates | Forever | Reusable templates |
| Sessions | 8 hours | Active sessions only |
| Audit Logs | 1 year | Compliance requirement |
| Incident Analysis | 1 year | Quality assurance |
| Reviews | Forever | Part of proposal history |

---

## Backup Strategy

1. **Database Backups:**
   - Daily full backups
   - Hourly WAL archiving
   - Retention: 30 days on-site, 90 days off-site

2. **Document Storage:**
   - Generated documents stored in S3-compatible storage
   - Versioned with proposal versions
   - Retention: Same as proposal

3. **Configuration:**
   - Infrastructure as code (Terraform/Bicep)
   - Version controlled in Git

---

## Integration with Constitution

The data model supports all constitution principles:

| Constitution Principle | Data Model Support |
|------------------------|---------------------|
| Open by default | Schema is documented and open |
| Strategic precision | Donor/Outcome/FieldContext linking |
| Security by design | Encryption, access control, audit logs |
| Human-in-the-loop | Review workflows, manual overrides |
| Reusability and scalability | Modular design, flexible schemas |
| Test-driven development | Test data support, validation |
| Production-ready | Comprehensive error handling, constraints |
| User-centric | User preferences, geographic coverage |
| Transparent | Full audit trail, history tracking |
| Compliant | Validation, qualification, compliance checks |

---

*Generated by `/speckit.architecture-guard.governed-plan` workflow - Phase 1 Data Model*