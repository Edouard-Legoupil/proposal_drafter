# Proposal Drafter Database Schema


## Overview

The Proposal Drafter application is designed to streamline the process of creating, reviewing, and managing project proposals for humanitarian and development organizations. This database schema supports a comprehensive workflow from proposal creation through peer review and knowledge management.


```mermaid

erDiagram
    teams {
        UUID id PK
        string name UK
    }

    users {
        UUID id PK
        string email UK
        string password
        string name
        UUID team_id FK
        JSONB security_questions
        boolean session_active
        timestamptz created_at
        timestamptz updated_at
    }

    donors {
        UUID id PK
        string account_id UK
        string name UK
        string country
        string donor_group
        UUID created_by FK
        timestamptz created_at
        timestamptz last_updated
    }

    outcomes {
        UUID id PK
        string name UK
        UUID created_by FK
        timestamptz created_at
        timestamptz last_updated
    }

    field_contexts {
        UUID id PK
        string title
        string name UK
        string category
        string geographic_coverage
        UUID created_by FK
        timestamptz created_at
        timestamptz last_updated
    }

    proposals {
        UUID id PK
        UUID user_id FK
        string template_name
        JSONB form_data
        text project_description
        JSONB generated_sections
        JSONB reviews
        boolean is_accepted
        proposal_status status
        UUID created_by FK
        timestamptz created_at
        UUID updated_by FK
        timestamptz updated_at
    }

    proposal_status_history {
        UUID id PK
        UUID proposal_id FK
        proposal_status status
        JSONB generated_sections_snapshot
        timestamptz created_at
    }

    proposal_peer_reviews {
        UUID id PK
        UUID proposal_id FK
        UUID reviewer_id FK
        UUID proposal_status_history_id FK
        string section_name
        string status
        timestamptz deadline
        text review_text
        text author_response
        string type_of_comment
        string severity
        timestamptz created_at
        timestamptz updated_at
    }

    knowledge_cards {
        UUID id PK
        string template_name
        text summary
        JSONB generated_sections
        boolean is_accepted
        proposal_status status
        UUID donor_id FK
        UUID outcome_id FK
        UUID field_context_id FK
        UUID created_by FK
        timestamptz created_at
        UUID updated_by FK
        timestamptz updated_at
    }

    knowledge_card_history {
        UUID id PK
        UUID knowledge_card_id FK
        JSONB generated_sections_snapshot
        UUID created_by FK
        timestamptz created_at
    }

    knowledge_card_references {
        UUID id PK
        UUID knowledge_card_id FK
        string url
        string reference_type
        text summary
        UUID created_by FK
        timestamptz created_at
        UUID updated_by FK
        timestamptz updated_at
        timestamptz scraped_at
        boolean scraping_error
    }

    knowledge_card_reference_vectors {
        UUID id PK
        UUID reference_id FK
        text text_chunk
        vector embedding
    }

    incident_analysis_results {
        UUID id PK
        string artifact_type
        string source_review_id FK
        UUID proposal_id FK
        UUID knowledge_card_id FK
        UUID template_request_id FK
        string incident_type
        string severity
        string status
        JSONB analysis_payload
        timestamptz created_at
        timestamptz updated_at
    }

    rag_evaluation_logs {
        UUID id PK
        UUID knowledge_card_id FK
        text query
        JSONB retrieved_context
        text generated_answer
        timestamptz created_at
    }

    donor_template_comments {
        UUID id PK
        UUID template_request_id FK
        string template_name
        UUID user_id FK
        text comment_text
        string section_name
        string rating
        string severity
        string type_of_comment
        timestamptz created_at
    }

    donor_template_requests {
        UUID id PK
        string name
        string donor_id FK
        JSONB donor_ids
        string template_type
        JSONB configuration
        JSONB initial_file_content
        string status
        timestamptz created_at
        timestamptz updated_at
    }

    proposal_donors {
        UUID proposal_id FK
        UUID donor_id FK
    }

    proposal_outcomes {
        UUID proposal_id FK
        UUID outcome_id FK
    }

    proposal_field_contexts {
        UUID proposal_id FK
        UUID field_context_id FK
    }

    users ||--o{ teams : belongs_to
    users ||--o{ donors : creates
    users ||--o{ outcomes : creates
    users ||--o{ field_contexts : creates
    users ||--o{ proposals : creates
    users ||--o{ proposals : updates
    users ||--o{ knowledge_cards : creates
    users ||--o{ knowledge_cards : updates
    users ||--o{ knowledge_card_history : creates
    users ||--o{ knowledge_card_references : creates
    users ||--o{ knowledge_card_references : updates
    users ||--o{ proposal_peer_reviews : reviews

    proposals ||--o{ proposal_status_history : has
    proposals ||--o{ proposal_peer_reviews : has
    proposals }o--o{ donors : "has many through proposal_donors"
    proposals }o--o{ outcomes : "has many through proposal_outcomes"
    proposals }o--o{ field_contexts : "has many through proposal_field_contexts"

    knowledge_cards ||--o{ knowledge_card_history : has
    knowledge_cards ||--o{ knowledge_card_references : has
    knowledge_card_references ||--o{ knowledge_card_reference_vectors : has

    knowledge_cards }|--|| donors : "optional link to"
    knowledge_cards }|--|| outcomes : "optional link to"
    knowledge_cards }|--|| field_contexts : "optional link to"

    proposal_status_history ||--o{ proposal_peer_reviews : references

    incident_analysis_results }|--|| proposals : "optional link to"
    incident_analysis_results }|--|| knowledge_cards : "optional link to"
    incident_analysis_results }|--|| donor_template_requests : "optional link to"

    knowledge_cards ||--o{ rag_evaluation_logs : has

    donor_template_requests ||--o{ donor_template_comments : has
    users ||--o{ donor_template_comments : creates

    proposals ||--o{ proposal_donors : "has many"
    donors ||--o{ proposal_donors : "has many"
    proposal_donors }|--|| proposals : "belongs to"
    proposal_donors }|--|| donors : "belongs to"

    proposals ||--o{ proposal_outcomes : "has many"
    outcomes ||--o{ proposal_outcomes : "has many"
    proposal_outcomes }|--|| proposals : "belongs to"
    proposal_outcomes }|--|| outcomes : "belongs to"

    proposals ||--o{ proposal_field_contexts : "has many"
    field_contexts ||--o{ proposal_field_contexts : "has many"
    proposal_field_contexts }|--|| proposals : "belongs to"
    proposal_field_contexts }|--|| field_contexts : "belongs to"
```

## Core Entities

### Users & Teams

 * Users represent individual team members with authentication credentials and security questions

 * Teams group users together for organizational purposes

 * Each user belongs to one team, supporting collaborative work environments


## Proposal Management

### Proposals

The central entity representing project proposals with:

 * Form data stored as JSON for flexible field structures

 * Generated sections containing AI-generated content

 * Status tracking through an enum type (draft, in_review, submission, submitted, approved, deleted, generating_sections, failed)

 * Review system with peer feedback mechanisms

 * Version control through status history snapshots

## Proposal Relationships

Proposals can be linked to multiple:

 * Donors - funding organizations

 * Outcomes - desired results or impact areas

 * Field Contexts - geographical and thematic focus areas

These many-to-many relationships are managed through join tables (proposal_donors, proposal_outcomes, proposal_field_contexts).

## Knowledge Management

### Knowledge Cards

Reusable content components that serve as a knowledge base:

 * Can be linked to one of: Donor, Outcome, or Field Context (enforced by constraint)

 * Store generated content sections for reuse across proposals

 * Maintain version history through snapshots

 * Support reference management with web scraping capabilities

### Knowledge Card References

 * Store external references and resources

 * Support vector embeddings for semantic search (knowledge_card_reference_vectors)

 * Include scraping status and error tracking

 * Enable AI-powered content recommendations

## Workflow Support

### Peer Review System

 * Proposal Peer Reviews allow multiple reviewers to provide feedback

 * Section-specific comments with severity ratings

 * Author response tracking

 * Deadline management for review cycles

### Status Tracking

 * Proposal Status History maintains complete audit trails

 * Snapshots of generated sections at each status change

 * Supports rollback and version comparison

## Technical Features

### Data Types & Extensions

 * Vector extension for AI-powered semantic search (1536-dimensional embeddings)

 * JSONB for flexible schema-less data storage

 * UUID primary keys for distributed system compatibility

 * Enum types for controlled status values

### Constraints & Validation

 * Unique constraints prevent duplicate entities

 * Check constraints ensure data integrity (e.g., knowledge card linking rules)

 * Foreign key constraints maintain referential integrity

 * Timestamp tracking for audit purposes

## Key Relationships

### One-to-Many

 * Team → Users

 * User → Created entities (proposals, knowledge cards, etc.)

 * Proposal → Status History entries

 * Knowledge Card → Reference entries

### Many-to-Many

 * Proposals ↔ Donors (through proposal_donors)

 * Proposals ↔ Outcomes (through proposal_outcomes)

 * Proposals ↔ Field Contexts (through proposal_field_contexts)

### Optional Links

 * Knowledge Cards can optionally link to one related entity (donor, outcome, or field context)

## Indexing Strategy

The schema includes strategic indexes on:

 * User email for authentication

 * Foreign key columns for join performance

 * Proposal and knowledge card relationships

 * Review and status tracking tables

## Incident Management System

### Incident Analysis Results

The `incident_analysis_results` table stores comprehensive analysis of quality issues and incidents:

 * **Artifact Types**: proposal, knowledge_card, template
 * **Severity Levels**: P0 (Critical), P1 (High), P2 (Medium), P3 (Low)
 * **Incident Types**: Taxonomy-based classification (Factual Error, Compliance Violation, etc.)
 * **Analysis Payload**: Complete JSON analysis including root cause, suggestions, and remediation
 * **Status Tracking**: Analysis lifecycle management

### RAG Evaluation Logs

The `rag_evaluation_logs` table captures retrieval-augmented generation interactions:

 * **Query Tracking**: Original user queries
 * **Retrieved Context**: Source documents and references used
 * **Generated Answers**: AI-produced responses
 * **Knowledge Card Link**: Association with specific knowledge cards

### Template Management

The `donor_template_requests` and `donor_template_comments` tables support template-based workflows:

 * **Template Requests**: Donor-specific template configurations
 * **Template Comments**: Review and feedback on templates
 * **Version Control**: Template evolution tracking
 * **Configuration Management**: Flexible template structures

## Incident Analysis Workflow

```mermaid
flowchart TD
    A[Incident Reported] --> B[Validate Taxonomy]
    B -->|Valid| C[Build Evidence Pack]
    C --> D[Fetch Related Data]
    D --> E[Run Multi-Agent Analysis]
    E --> F[Triage Agent]
    E --> G[Correction Agent]
    E --> H[RCA Agent]
    E --> I[Remediation Agent]
    E --> J[Consistency Agent]
    J --> K{Needs Human Review?}
    K -->|Yes| L[Flag for Review]
    K -->|No| M[Store Results]
    L --> M
    M --> N[incident_analysis_results]
    N --> O[Return Response to User]
```

### Key Relationships

 * **Incident Analysis → Proposals**: Links analysis to specific proposals
 * **Incident Analysis → Knowledge Cards**: Links analysis to knowledge cards
 * **Incident Analysis → Template Requests**: Links analysis to templates
 * **Knowledge Cards → RAG Logs**: Tracks retrieval operations
 * **Template Requests → Comments**: Manages template feedback

## Security Considerations

 * User authentication with password hashing

 * Security questions for account recovery

 * Session management tracking

 * Audit trails for all major operations

## Incident Management Features

### Quality Assurance
 * Automated incident detection and classification
 * Multi-agent AI analysis with specialized roles
 * Root cause analysis with confidence scoring
 * Evidence-based recommendations

### Continuous Improvement
 * Incident trend tracking
 * Systemic issue identification
 * Remediation task management
 * Performance metrics and KPIs

### Integration Points
 * Proposal peer review system
 * Knowledge card validation
 * Template quality control
 * User feedback mechanisms

This schema supports a collaborative, AI-enhanced proposal drafting workflow while maintaining data integrity, audit capabilities, and performance optimization for enterprise-scale operations.