-- Database setup for Proposal Drafter application
-- IMORTANT ! REPLACE <DB_USERNAME> with ACTUAL DB_USERNAME

-- Grant necessary privileges to the application user
GRANT CONNECT ON DATABASE postgres TO <DB_USERNAME>;
GRANT USAGE ON SCHEMA public TO <DB_USERNAME>;

-- Enable vector extension
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Create Teams table
CREATE TABLE IF NOT EXISTS teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL
);

-- Create Users table
CREATE TABLE IF NOT EXISTS users (
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

-- Create Roles table
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

-- Create User Roles table for many-to-many relationship
CREATE TABLE IF NOT EXISTS user_roles (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

-- Create User Role Requests table for pending roles
CREATE TABLE IF NOT EXISTS user_role_requests (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

-- Create User Donor Groups table
CREATE TABLE IF NOT EXISTS user_donor_groups (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    donor_group TEXT NOT NULL,
    PRIMARY KEY (user_id, donor_group)
);

-- Create User Donors table for specific donor focal points
CREATE TABLE IF NOT EXISTS user_donors (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    donor_id UUID NOT NULL REFERENCES donors(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, donor_id)
);

-- Create User Outcomes table
CREATE TABLE IF NOT EXISTS user_outcomes (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    outcome_id UUID NOT NULL REFERENCES outcomes(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, outcome_id)
);

-- Create User Field Contexts table
CREATE TABLE IF NOT EXISTS user_field_contexts (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    field_context_id UUID NOT NULL REFERENCES field_contexts(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, field_context_id)
);


-- Create Donors table 
CREATE TABLE IF NOT EXISTS donors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id TEXT UNIQUE,
    name TEXT UNIQUE NOT NULL,
    country TEXT,
    donor_group TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Create Outcomes table  
CREATE TABLE IF NOT EXISTS outcomes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Create Field Contexts table  
CREATE TABLE IF NOT EXISTS field_contexts (
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

-- Create Proposal Status Enum Type
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'proposal_status') THEN
        CREATE TYPE proposal_status AS ENUM (
            'draft',
            'in_review',
            'pre_submission',
            'submitted',
            'deleted',
            'generating_sections',
            'failed'
        );
    END IF;
END$$;

-- Create Proposals table
CREATE TABLE IF NOT EXISTS proposals (
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


-- Create Proposal Status History table
CREATE TABLE IF NOT EXISTS proposal_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
    status proposal_status NOT NULL,
    generated_sections_snapshot JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);


-- Create Proposal Peer Reviews table   
CREATE TABLE IF NOT EXISTS proposal_peer_reviews (
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

-- Create Knowledge Cards table
CREATE TABLE IF NOT EXISTS knowledge_cards (
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

-- Create Knowledge Card History table
CREATE TABLE IF NOT EXISTS knowledge_card_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_card_id UUID NOT NULL REFERENCES knowledge_cards(id) ON DELETE CASCADE,
    generated_sections_snapshot JSONB,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS knowledge_card_reviews (
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

-- Create Knowledge Card References table  
CREATE TABLE IF NOT EXISTS knowledge_card_references (
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

-- Create join table for many-to-many relationship between knowledge cards and references
CREATE TABLE IF NOT EXISTS knowledge_card_to_references (
    knowledge_card_id UUID NOT NULL REFERENCES knowledge_cards(id) ON DELETE CASCADE,
    reference_id UUID NOT NULL REFERENCES knowledge_card_references(id) ON DELETE CASCADE,
    PRIMARY KEY (knowledge_card_id, reference_id)
);

-- Create Knowledge Card Reference Vectors table
CREATE TABLE IF NOT EXISTS knowledge_card_reference_vectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reference_id UUID NOT NULL REFERENCES knowledge_card_references(id) ON DELETE CASCADE,
    text_chunk TEXT NOT NULL,
    embedding vector(1536)
);

-- Create RAG Evaluation Logs table
CREATE TABLE IF NOT EXISTS rag_evaluation_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_card_id UUID NOT NULL REFERENCES knowledge_cards(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    retrieved_context TEXT NOT NULL,
    generated_answer TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Create Knowledge Card Usage Tracking table
CREATE TABLE IF NOT EXISTS knowledge_card_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_card_id UUID NOT NULL REFERENCES knowledge_cards(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    action TEXT NOT NULL, -- e.g., 'view', 'citation', 'generation'
    proposal_id UUID REFERENCES proposals(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Create Knowledge Card Reference Errors table
CREATE TABLE IF NOT EXISTS knowledge_card_reference_errors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reference_id UUID NOT NULL REFERENCES knowledge_card_references(id) ON DELETE CASCADE,
    error_type TEXT NOT NULL, -- e.g., 'broken_link', 'timeout', 'parsing_error'
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Create join tables for many-to-many relationships  
CREATE TABLE IF NOT EXISTS proposal_donors (
    proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
    donor_id UUID NOT NULL REFERENCES donors(id) ON DELETE CASCADE,
    PRIMARY KEY (proposal_id, donor_id)
);

CREATE TABLE IF NOT EXISTS proposal_outcomes (
    proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
    outcome_id UUID NOT NULL REFERENCES outcomes(id) ON DELETE CASCADE,
    PRIMARY KEY (proposal_id, outcome_id)
);

CREATE TABLE IF NOT EXISTS proposal_field_contexts (
    proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
    field_context_id UUID NOT NULL REFERENCES field_contexts(id) ON DELETE CASCADE,
    PRIMARY KEY (proposal_id, field_context_id)
);

-- Create Donor Template Requests table
CREATE TABLE IF NOT EXISTS donor_template_requests (
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

-- Create Donor Template Comments table
CREATE TABLE IF NOT EXISTS donor_template_comments (
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

-- Create index for faster user lookup
CREATE INDEX IF NOT EXISTS idx_proposals_user_id ON proposals(user_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email); 
CREATE INDEX IF NOT EXISTS idx_knowledge_cards_donor_id ON knowledge_cards(donor_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_cards_outcome_id ON knowledge_cards(outcome_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_cards_field_context_id ON knowledge_cards(field_context_id); 

CREATE INDEX IF NOT EXISTS idx_knowledge_card_to_references_card_id ON knowledge_card_to_references(knowledge_card_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_card_to_references_reference_id ON knowledge_card_to_references(reference_id);

CREATE INDEX IF NOT EXISTS idx_knowledge_card_history_knowledge_card_id ON knowledge_card_history(knowledge_card_id);
CREATE INDEX IF NOT EXISTS idx_proposal_peer_reviews_proposal_id ON proposal_peer_reviews(proposal_id);
CREATE INDEX IF NOT EXISTS idx_proposal_peer_reviews_reviewer_id ON proposal_peer_reviews(reviewer_id);
CREATE INDEX IF NOT EXISTS idx_proposal_status_history_proposal_id ON proposal_status_history(proposal_id);
CREATE INDEX IF NOT EXISTS idx_user_role_requests_user_id ON user_role_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_user_donors_user_id ON user_donors(user_id);

CREATE INDEX IF NOT EXISTS idx_donor_template_requests_creator ON donor_template_requests(created_by);
CREATE INDEX IF NOT EXISTS idx_donor_template_comments_request ON donor_template_comments(template_request_id);
CREATE INDEX IF NOT EXISTS idx_donor_template_comments_section ON donor_template_comments(template_request_id, section_name);
CREATE INDEX IF NOT EXISTS idx_donor_template_comments_user ON donor_template_comments(user_id);
 
 

-- Grant table permissions to application user
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO <DB_USERNAME>;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO <DB_USERNAME>;


-- ============================================================================
-- - Incident Analysis + Template Qualification 
-- ============================================================================
-- PURPOSE
--   1) Persisting incident-analysis / agentic QA outputs
--   2) Managing canonical template registry and immutable template versions
--   3) Running UAT -> PROD qualification workflows for proposal and knowledge-card templates
--   4) Storing rule sets, rule evaluations, signoffs, waivers, and release history
--   5) Exposing views to simplify qualification metric evaluation
--
-- PREREQUISITES
--   - Requires pgcrypto extension already enabled in the base schema
-- ============================================================================

BEGIN;

-- --------------------------------------------------------------------------
-- 1) INCIDENT ANALYSIS RESULTS
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS incident_analysis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artifact_type TEXT NOT NULL CHECK (artifact_type IN ('proposal', 'knowledge_card', 'template')),
    source_review_id UUID NOT NULL,
    proposal_id UUID NULL REFERENCES proposals(id) ON DELETE SET NULL,
    knowledge_card_id UUID NULL REFERENCES knowledge_cards(id) ON DELETE SET NULL,
    template_request_id UUID NULL REFERENCES donor_template_requests(id) ON DELETE SET NULL,
    incident_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'analyzed',
    analysis_payload JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (artifact_type, source_review_id)
);

CREATE INDEX IF NOT EXISTS idx_incident_analysis_artifact_type
    ON incident_analysis_results(artifact_type);

CREATE INDEX IF NOT EXISTS idx_incident_analysis_source_review_id
    ON incident_analysis_results(source_review_id);

CREATE INDEX IF NOT EXISTS idx_incident_analysis_proposal_id
    ON incident_analysis_results(proposal_id);

CREATE INDEX IF NOT EXISTS idx_incident_analysis_knowledge_card_id
    ON incident_analysis_results(knowledge_card_id);

CREATE INDEX IF NOT EXISTS idx_incident_analysis_template_request_id
    ON incident_analysis_results(template_request_id);

-- --------------------------------------------------------------------------
-- 2) ENUMS FOR TEMPLATE QUALIFICATION / RELEASE GOVERNANCE
-- --------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'release_environment') THEN
        CREATE TYPE release_environment AS ENUM ('uat', 'prod');
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'managed_template_type') THEN
        CREATE TYPE managed_template_type AS ENUM ('proposal', 'knowledge_card');
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'template_version_status') THEN
        CREATE TYPE template_version_status AS ENUM (
            'draft',
            'in_uat',
            'conditionally_qualified',
            'qualified',
            'disqualified',
            'promoted_to_prod',
            'suspended',
            'retired'
        );
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'qualification_run_status') THEN
        CREATE TYPE qualification_run_status AS ENUM (
            'draft',
            'collecting_evidence',
            'evaluating',
            'pending_signoff',
            'approved',
            'rejected',
            'cancelled'
        );
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'qualification_rule_result') THEN
        CREATE TYPE qualification_rule_result AS ENUM (
            'pass',
            'fail',
            'waived',
            'not_applicable'
        );
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'qualification_decision') THEN
        CREATE TYPE qualification_decision AS ENUM (
            'qualified',
            'conditionally_qualified',
            'disqualified',
            'suspended',
            'rolled_back'
        );
    END IF;
END$$;

-- --------------------------------------------------------------------------
-- 3) CANONICAL TEMPLATE REGISTRY
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS template_registry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_key TEXT NOT NULL UNIQUE,
    template_name TEXT NOT NULL,
    template_type managed_template_type NOT NULL,
    source_template_request_id UUID NULL REFERENCES donor_template_requests(id) ON DELETE SET NULL,
    owner_user_id UUID NOT NULL REFERENCES users(id),
    owning_team_id UUID NULL REFERENCES teams(id),
    description TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_template_registry_template_type
    ON template_registry(template_type);

CREATE INDEX IF NOT EXISTS idx_template_registry_owner_user_id
    ON template_registry(owner_user_id);

CREATE INDEX IF NOT EXISTS idx_template_registry_owning_team_id
    ON template_registry(owning_team_id);

-- --------------------------------------------------------------------------
-- 4) IMMUTABLE TEMPLATE VERSIONS
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS template_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_registry_id UUID NOT NULL REFERENCES template_registry(id) ON DELETE CASCADE,
    version_label TEXT NOT NULL,
    version_number INTEGER NOT NULL,
    environment release_environment NOT NULL DEFAULT 'uat',
    status template_version_status NOT NULL DEFAULT 'draft',

    configuration JSONB NOT NULL DEFAULT '{}'::jsonb,
    template_content JSONB,
    initial_file_content JSONB,
    release_notes TEXT,

    cloned_from_version_id UUID NULL REFERENCES template_versions(id) ON DELETE SET NULL,

    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID NOT NULL REFERENCES users(id),
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    promoted_at TIMESTAMPTZ,
    promoted_by UUID NULL REFERENCES users(id),
    suspended_at TIMESTAMPTZ,
    suspended_by UUID NULL REFERENCES users(id),

    UNIQUE (template_registry_id, version_number),
    UNIQUE (template_registry_id, version_label)
);

CREATE INDEX IF NOT EXISTS idx_template_versions_registry
    ON template_versions(template_registry_id);

CREATE INDEX IF NOT EXISTS idx_template_versions_status
    ON template_versions(status);

CREATE INDEX IF NOT EXISTS idx_template_versions_environment
    ON template_versions(environment);

CREATE UNIQUE INDEX IF NOT EXISTS uq_template_versions_single_prod_per_registry
    ON template_versions(template_registry_id)
    WHERE environment = 'prod' AND status = 'promoted_to_prod';

-- --------------------------------------------------------------------------
-- 5) LINK GENERATED OUTPUTS TO EXACT TEMPLATE REGISTRY / VERSION
-- --------------------------------------------------------------------------
ALTER TABLE proposals
    ADD COLUMN IF NOT EXISTS template_registry_id UUID NULL REFERENCES template_registry(id) ON DELETE SET NULL;

ALTER TABLE proposals
    ADD COLUMN IF NOT EXISTS template_version_id UUID NULL REFERENCES template_versions(id) ON DELETE SET NULL;

ALTER TABLE knowledge_cards
    ADD COLUMN IF NOT EXISTS template_registry_id UUID NULL REFERENCES template_registry(id) ON DELETE SET NULL;

ALTER TABLE knowledge_cards
    ADD COLUMN IF NOT EXISTS template_version_id UUID NULL REFERENCES template_versions(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_proposals_template_registry_id
    ON proposals(template_registry_id);

CREATE INDEX IF NOT EXISTS idx_proposals_template_version_id
    ON proposals(template_version_id);

CREATE INDEX IF NOT EXISTS idx_knowledge_cards_template_registry_id
    ON knowledge_cards(template_registry_id);

CREATE INDEX IF NOT EXISTS idx_knowledge_cards_template_version_id
    ON knowledge_cards(template_version_id);

-- --------------------------------------------------------------------------
-- 6) QUALIFICATION RULE SETS
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS qualification_rule_sets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    template_type managed_template_type NOT NULL,
    version_label TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    description TEXT,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID NOT NULL REFERENCES users(id),
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_qualification_rule_sets_template_type
    ON qualification_rule_sets(template_type);

CREATE INDEX IF NOT EXISTS idx_qualification_rule_sets_is_active
    ON qualification_rule_sets(is_active);

-- --------------------------------------------------------------------------
-- 7) INDIVIDUAL QUALIFICATION RULES
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS qualification_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_set_id UUID NOT NULL REFERENCES qualification_rule_sets(id) ON DELETE CASCADE,

    rule_code TEXT NOT NULL,
    rule_name TEXT NOT NULL,
    category TEXT NOT NULL,
    severity TEXT NOT NULL,
    applies_to managed_template_type NOT NULL,

    evaluation_mode TEXT NOT NULL,
    metric_name TEXT,
    comparator TEXT,
    threshold_numeric NUMERIC,
    threshold_json JSONB,
    weight NUMERIC,
    required BOOLEAN DEFAULT TRUE,

    description TEXT,
    remediation_guidance TEXT,

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (rule_set_id, rule_code)
);

CREATE INDEX IF NOT EXISTS idx_qualification_rules_rule_set_id
    ON qualification_rules(rule_set_id);

CREATE INDEX IF NOT EXISTS idx_qualification_rules_applies_to
    ON qualification_rules(applies_to);

CREATE INDEX IF NOT EXISTS idx_qualification_rules_is_active
    ON qualification_rules(is_active);

-- --------------------------------------------------------------------------
-- 8) QUALIFICATION SCENARIOS
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS qualification_scenarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_code TEXT NOT NULL UNIQUE,
    template_type managed_template_type NOT NULL,
    name TEXT NOT NULL,
    description TEXT,

    donor_id UUID NULL REFERENCES donors(id) ON DELETE SET NULL,
    outcome_id UUID NULL REFERENCES outcomes(id) ON DELETE SET NULL,
    field_context_id UUID NULL REFERENCES field_contexts(id) ON DELETE SET NULL,

    geography JSONB,
    metadata JSONB DEFAULT '{}'::jsonb,

    active BOOLEAN DEFAULT TRUE,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_qualification_scenarios_template_type
    ON qualification_scenarios(template_type);

CREATE INDEX IF NOT EXISTS idx_qualification_scenarios_active
    ON qualification_scenarios(active);

-- --------------------------------------------------------------------------
-- 9) QUALIFICATION RUNS
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS template_qualification_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_version_id UUID NOT NULL REFERENCES template_versions(id) ON DELETE CASCADE,
    rule_set_id UUID NOT NULL REFERENCES qualification_rule_sets(id) ON DELETE RESTRICT,

    run_name TEXT NOT NULL,
    environment release_environment NOT NULL DEFAULT 'uat',
    status qualification_run_status NOT NULL DEFAULT 'draft',

    target_sample_size INTEGER,
    actual_sample_size INTEGER DEFAULT 0,
    required_reviewer_count INTEGER DEFAULT 1,

    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    overall_score NUMERIC,
    decision qualification_decision,
    decision_reason TEXT,

    initiated_by UUID NOT NULL REFERENCES users(id),
    approved_by UUID NULL REFERENCES users(id),

    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_template_qualification_runs_version
    ON template_qualification_runs(template_version_id);

CREATE INDEX IF NOT EXISTS idx_template_qualification_runs_status
    ON template_qualification_runs(status);

CREATE INDEX IF NOT EXISTS idx_template_qualification_runs_decision
    ON template_qualification_runs(decision);

CREATE INDEX IF NOT EXISTS idx_template_qualification_runs_environment
    ON template_qualification_runs(environment);

-- --------------------------------------------------------------------------
-- 10) RUN-TO-SCENARIO MAPPING
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS template_qualification_run_scenarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    qualification_run_id UUID NOT NULL REFERENCES template_qualification_runs(id) ON DELETE CASCADE,
    scenario_id UUID NOT NULL REFERENCES qualification_scenarios(id) ON DELETE CASCADE,
    is_required BOOLEAN DEFAULT TRUE,
    executed BOOLEAN DEFAULT FALSE,
    notes TEXT,
    UNIQUE (qualification_run_id, scenario_id)
);

CREATE INDEX IF NOT EXISTS idx_template_qualification_run_scenarios_run
    ON template_qualification_run_scenarios(qualification_run_id);

CREATE INDEX IF NOT EXISTS idx_template_qualification_run_scenarios_scenario
    ON template_qualification_run_scenarios(scenario_id);

-- --------------------------------------------------------------------------
-- 11) QUALIFICATION EVIDENCE ITEMS
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS qualification_evidence_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    qualification_run_id UUID NOT NULL REFERENCES template_qualification_runs(id) ON DELETE CASCADE,

    source_artifact_type TEXT NOT NULL,
    source_id UUID NOT NULL,
    source_table TEXT NOT NULL,

    proposal_id UUID NULL REFERENCES proposals(id) ON DELETE SET NULL,
    knowledge_card_id UUID NULL REFERENCES knowledge_cards(id) ON DELETE SET NULL,
    template_request_id UUID NULL REFERENCES donor_template_requests(id) ON DELETE SET NULL,

    scenario_id UUID NULL REFERENCES qualification_scenarios(id) ON DELETE SET NULL,
    section_name TEXT,
    severity TEXT,
    incident_type TEXT,
    rating VARCHAR(10),

    evidence_payload JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_qualification_evidence_items_run
    ON qualification_evidence_items(qualification_run_id);

CREATE INDEX IF NOT EXISTS idx_qualification_evidence_items_source
    ON qualification_evidence_items(source_table, source_id);

CREATE INDEX IF NOT EXISTS idx_qualification_evidence_items_proposal_id
    ON qualification_evidence_items(proposal_id);

CREATE INDEX IF NOT EXISTS idx_qualification_evidence_items_knowledge_card_id
    ON qualification_evidence_items(knowledge_card_id);

CREATE INDEX IF NOT EXISTS idx_qualification_evidence_items_scenario_id
    ON qualification_evidence_items(scenario_id);

-- --------------------------------------------------------------------------
-- 12) RULE EVALUATION RESULTS
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS qualification_rule_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    qualification_run_id UUID NOT NULL REFERENCES template_qualification_runs(id) ON DELETE CASCADE,
    rule_id UUID NOT NULL REFERENCES qualification_rules(id) ON DELETE RESTRICT,

    result qualification_rule_result NOT NULL,
    metric_value NUMERIC,
    metric_payload JSONB DEFAULT '{}'::jsonb,
    explanation TEXT,
    waived_by UUID NULL REFERENCES users(id),
    waiver_reason TEXT,

    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (qualification_run_id, rule_id)
);

CREATE INDEX IF NOT EXISTS idx_qualification_rule_evaluations_run
    ON qualification_rule_evaluations(qualification_run_id);

CREATE INDEX IF NOT EXISTS idx_qualification_rule_evaluations_rule
    ON qualification_rule_evaluations(rule_id);

-- --------------------------------------------------------------------------
-- 13) REVIEWER SIGNOFFS
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS template_qualification_signoffs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    qualification_run_id UUID NOT NULL REFERENCES template_qualification_runs(id) ON DELETE CASCADE,
    reviewer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    role_name TEXT,
    decision TEXT NOT NULL,
    comments TEXT,
    signed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (qualification_run_id, reviewer_id, role_name)
);

CREATE INDEX IF NOT EXISTS idx_template_qualification_signoffs_run
    ON template_qualification_signoffs(qualification_run_id);

CREATE INDEX IF NOT EXISTS idx_template_qualification_signoffs_reviewer
    ON template_qualification_signoffs(reviewer_id);

-- --------------------------------------------------------------------------
-- 14) PROMOTION / RELEASE HISTORY
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS template_release_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_version_id UUID NOT NULL REFERENCES template_versions(id) ON DELETE CASCADE,
    qualification_run_id UUID NULL REFERENCES template_qualification_runs(id) ON DELETE SET NULL,

    action TEXT NOT NULL,
    from_environment release_environment,
    to_environment release_environment,
    previous_status template_version_status,
    new_status template_version_status,

    reason TEXT,
    actioned_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_template_release_history_version
    ON template_release_history(template_version_id);

CREATE INDEX IF NOT EXISTS idx_template_release_history_qualification_run
    ON template_release_history(qualification_run_id);

-- --------------------------------------------------------------------------
-- 15) OPTIONAL WAIVERS / EXCEPTIONS
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS qualification_waivers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    qualification_run_id UUID NOT NULL REFERENCES template_qualification_runs(id) ON DELETE CASCADE,
    rule_id UUID NOT NULL REFERENCES qualification_rules(id) ON DELETE RESTRICT,

    approved_by UUID NOT NULL REFERENCES users(id),
    reason TEXT NOT NULL,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_qualification_waivers_run
    ON qualification_waivers(qualification_run_id);

CREATE INDEX IF NOT EXISTS idx_qualification_waivers_rule
    ON qualification_waivers(rule_id);

-- --------------------------------------------------------------------------
-- 16) OPTIONAL AUTOMATED TIMESTAMP TRIGGER
-- --------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION set_updated_at_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_incident_analysis_results_updated_at ON incident_analysis_results;
CREATE TRIGGER trg_incident_analysis_results_updated_at
BEFORE UPDATE ON incident_analysis_results
FOR EACH ROW
EXECUTE FUNCTION set_updated_at_timestamp();

DROP TRIGGER IF EXISTS trg_template_registry_updated_at ON template_registry;
CREATE TRIGGER trg_template_registry_updated_at
BEFORE UPDATE ON template_registry
FOR EACH ROW
EXECUTE FUNCTION set_updated_at_timestamp();

DROP TRIGGER IF EXISTS trg_template_versions_updated_at ON template_versions;
CREATE TRIGGER trg_template_versions_updated_at
BEFORE UPDATE ON template_versions
FOR EACH ROW
EXECUTE FUNCTION set_updated_at_timestamp();

DROP TRIGGER IF EXISTS trg_qualification_rule_sets_updated_at ON qualification_rule_sets;
CREATE TRIGGER trg_qualification_rule_sets_updated_at
BEFORE UPDATE ON qualification_rule_sets
FOR EACH ROW
EXECUTE FUNCTION set_updated_at_timestamp();

DROP TRIGGER IF EXISTS trg_template_qualification_runs_updated_at ON template_qualification_runs;
CREATE TRIGGER trg_template_qualification_runs_updated_at
BEFORE UPDATE ON template_qualification_runs
FOR EACH ROW
EXECUTE FUNCTION set_updated_at_timestamp();

-- --------------------------------------------------------------------------
-- 17) QUALIFICATION METRIC VIEWS
-- --------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_proposal_template_quality_metrics AS
SELECT
    p.template_version_id,
    COUNT(DISTINCT p.id) AS proposal_count,
    COUNT(ppr.id) AS total_reviews,

    COUNT(*) FILTER (WHERE ppr.severity = 'P0') AS p0_count,
    COUNT(*) FILTER (WHERE ppr.severity = 'P1') AS p1_count,
    COUNT(*) FILTER (WHERE ppr.severity = 'P2') AS p2_count,
    COUNT(*) FILTER (WHERE ppr.severity = 'P3') AS p3_count,

    COUNT(*) FILTER (
        WHERE ppr.severity = 'P0'
          AND COALESCE(ppr.status, 'pending') <> 'resolved'
    ) AS unresolved_p0_count,

    AVG(
        CASE
            WHEN ppr.rating ~ '^[0-9]+(\.[0-9]+)?$' THEN ppr.rating::numeric
            ELSE NULL
        END
    ) AS avg_numeric_rating
FROM proposals p
LEFT JOIN proposal_peer_reviews ppr
    ON ppr.proposal_id = p.id
WHERE p.template_version_id IS NOT NULL
GROUP BY p.template_version_id;

CREATE OR REPLACE VIEW vw_proposal_template_repeated_p1_sections AS
SELECT
    p.template_version_id,
    ppr.section_name,
    COUNT(*) AS p1_count
FROM proposals p
JOIN proposal_peer_reviews ppr
    ON ppr.proposal_id = p.id
WHERE p.template_version_id IS NOT NULL
  AND ppr.severity = 'P1'
GROUP BY p.template_version_id, ppr.section_name;

CREATE OR REPLACE VIEW vw_knowledge_card_template_quality_metrics AS
SELECT
    kc.template_version_id,
    COUNT(DISTINCT kc.id) AS knowledge_card_count,
    COUNT(kcr.id) AS total_reviews,

    COUNT(*) FILTER (WHERE kcr.severity = 'P0') AS p0_count,
    COUNT(*) FILTER (WHERE kcr.severity = 'P1') AS p1_count,
    COUNT(*) FILTER (WHERE kcr.severity = 'P2') AS p2_count,
    COUNT(*) FILTER (WHERE kcr.severity = 'P3') AS p3_count,

    COUNT(*) FILTER (
        WHERE kcr.severity = 'P0'
          AND COALESCE(kcr.status, 'pending') <> 'resolved'
    ) AS unresolved_p0_count,

    COUNT(*) FILTER (WHERE kcr.type_of_comment = 'Outdated Information') AS outdated_information_count,
    COUNT(*) FILTER (WHERE kcr.type_of_comment = 'Duplicate Content') AS duplicate_content_count,
    COUNT(*) FILTER (WHERE kcr.type_of_comment = 'Generic Content') AS generic_content_count,

    AVG(
        CASE
            WHEN kcr.rating ~ '^[0-9]+(\.[0-9]+)?$' THEN kcr.rating::numeric
            ELSE NULL
        END
    ) AS avg_numeric_rating
FROM knowledge_cards kc
LEFT JOIN knowledge_card_reviews kcr
    ON kcr.knowledge_card_id = kc.id
WHERE kc.template_version_id IS NOT NULL
GROUP BY kc.template_version_id;

CREATE OR REPLACE VIEW vw_knowledge_card_template_traceability AS
SELECT
    kc.template_version_id,
    COUNT(DISTINCT kc.id) AS knowledge_card_count,
    COUNT(DISTINCT kctr.reference_id) AS total_linked_references,
    COUNT(DISTINCT rel.id) AS total_rag_logs,
    COUNT(DISTINCT kc.id) FILTER (
        WHERE EXISTS (
            SELECT 1
            FROM knowledge_card_to_references x
            WHERE x.knowledge_card_id = kc.id
        )
    ) AS cards_with_references
FROM knowledge_cards kc
LEFT JOIN knowledge_card_to_references kctr
    ON kctr.knowledge_card_id = kc.id
LEFT JOIN rag_evaluation_logs rel
    ON rel.knowledge_card_id = kc.id
WHERE kc.template_version_id IS NOT NULL
GROUP BY kc.template_version_id;


COMMIT;


-- automatically maintains template registry and version

CREATE OR REPLACE FUNCTION ensure_template_registry_and_version(
    p_template_name TEXT,
    p_template_type managed_template_type,
    p_user_id UUID
)
RETURNS TABLE (
    template_registry_id UUID,
    template_version_id  UUID
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_template_key TEXT;
    v_registry_id  UUID;
    v_version_id   UUID;
    v_next_version INTEGER;
BEGIN
    IF p_template_name IS NULL OR trim(p_template_name) = '' THEN
        RETURN;
    END IF;

    -- Normalize template key
    v_template_key :=
        lower(regexp_replace(p_template_name, '[^a-zA-Z0-9]+', '_', 'g'));

    -- Ensure template_registry
    SELECT tr.id
    INTO v_registry_id
    FROM template_registry tr
    WHERE tr.template_key = v_template_key
      AND tr.template_type = p_template_type;

    IF v_registry_id IS NULL THEN
        INSERT INTO template_registry (
            template_key,
            template_name,
            template_type,
            owner_user_id,
            description
        )
        VALUES (
            v_template_key,
            p_template_name,
            p_template_type,
            p_user_id,
            'Auto-registered from usage'
        )
        RETURNING id INTO v_registry_id;
    END IF;

    -- Ensure at least one UAT version
    SELECT tv.id
    INTO v_version_id
    FROM template_versions tv
    WHERE tv.template_registry_id = v_registry_id
      AND tv.environment = 'uat'
    ORDER BY tv.version_number DESC
    LIMIT 1;

    IF v_version_id IS NULL THEN
        SELECT COALESCE(MAX(tv.version_number), 0) + 1
        INTO v_next_version
        FROM template_versions tv
        WHERE tv.template_registry_id = v_registry_id;

        INSERT INTO template_versions (
            template_registry_id,
            version_label,
            version_number,
            environment,
            status,
            release_notes,
            created_by,
            updated_by
        )
        VALUES (
            v_registry_id,
            'auto-uat-v' || v_next_version,
            v_next_version,
            'uat'::release_environment,
            'in_uat'::template_version_status,
            'Auto-created from existing usage',
            p_user_id,
            p_user_id
        )
        RETURNING id INTO v_version_id;
    END IF;

    -- ✅ Explicitly assign output variables
    template_registry_id := v_registry_id;
    template_version_id  := v_version_id;

    RETURN NEXT;
END;
$$;
 

-------------

CREATE OR REPLACE FUNCTION trg_proposals_template_autoregister()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_result RECORD;
BEGIN
    IF NEW.template_name IS NULL THEN
        RETURN NEW;
    END IF;

    -- Only act if not already populated or template changed
    IF NEW.template_registry_id IS NULL
       OR NEW.template_version_id IS NULL
       OR NEW.template_name IS DISTINCT FROM OLD.template_name THEN

        SELECT *
        INTO v_result
        FROM ensure_template_registry_and_version(
            NEW.template_name,
            'proposal',
            NEW.created_by
        );

        NEW.template_registry_id := v_result.template_registry_id;
        NEW.template_version_id := v_result.template_version_id;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS proposals_template_autoregister
ON proposals;

CREATE TRIGGER proposals_template_autoregister
BEFORE INSERT OR UPDATE OF template_name
ON proposals
FOR EACH ROW
EXECUTE FUNCTION trg_proposals_template_autoregister();


CREATE OR REPLACE FUNCTION trg_knowledge_cards_template_autoregister()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_result RECORD;
BEGIN
    IF NEW.template_name IS NULL THEN
        RETURN NEW;
    END IF;

    IF NEW.template_registry_id IS NULL
       OR NEW.template_version_id IS NULL
       OR NEW.template_name IS DISTINCT FROM OLD.template_name THEN

        SELECT *
        INTO v_result
        FROM ensure_template_registry_and_version(
            NEW.template_name,
            'knowledge_card',
            NEW.created_by
        );

        NEW.template_registry_id := v_result.template_registry_id;
        NEW.template_version_id := v_result.template_version_id;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS knowledge_cards_template_autoregister
ON knowledge_cards;

CREATE TRIGGER knowledge_cards_template_autoregister
BEFORE INSERT OR UPDATE OF template_name
ON knowledge_cards
FOR EACH ROW
EXECUTE FUNCTION trg_knowledge_cards_template_autoregister();


----------------
-- ## One-time backfill for existing data
UPDATE proposals p
SET
    template_registry_id = src.template_registry_id,
    template_version_id  = src.template_version_id
FROM (
    SELECT
        p2.id AS proposal_id,
        r.template_registry_id,
        r.template_version_id
    FROM proposals p2
    JOIN LATERAL ensure_template_registry_and_version(
        p2.template_name,
        'proposal'::managed_template_type,
        p2.created_by
    ) r ON TRUE
    WHERE p2.template_name IS NOT NULL
      AND (
          p2.template_registry_id IS NULL
          OR p2.template_version_id IS NULL
      )
) src
WHERE p.id = src.proposal_id;





UPDATE knowledge_cards kc
SET
    template_registry_id = src.template_registry_id,
    template_version_id  = src.template_version_id
FROM (
    SELECT
        kc2.id AS knowledge_card_id,
        r.template_registry_id,
        r.template_version_id
    FROM knowledge_cards kc2
    JOIN LATERAL ensure_template_registry_and_version(
        kc2.template_name,
        'knowledge_card'::managed_template_type,
        kc2.created_by
    ) r ON TRUE
    WHERE kc2.template_name IS NOT NULL
      AND (
          kc2.template_registry_id IS NULL
          OR kc2.template_version_id IS NULL
      )
) src
WHERE kc.id = src.knowledge_card_id;


---
 CREATE UNIQUE INDEX IF NOT EXISTS uq_template_registry_key_type
ON template_registry(template_key, template_type);

CREATE UNIQUE INDEX IF NOT EXISTS uq_single_prod_version
ON template_versions(template_registry_id)
WHERE environment = 'prod' AND status = 'promoted_to_prod'; 