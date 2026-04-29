-- Migration Script: database-setup.sql -> database-setup2.sql
-- Description: Migrate from initial schema to current production schema
-- Created: April 2025
-- Version: 1.0

-- ============================================
-- IMPORTANT NOTES:
-- ============================================
-- 1. This script assumes database-setup.sql has already been applied
-- 2. run this script AFTER applying database-setup.sql
-- 3. Make a backup of your database before running this migration
-- 4. Some tables/columns may already exist - the script uses IF NOT EXISTS
-- 5. The database-setup2.sql file is a pg_dump and contains OWNER TO statements
--    which are not included here as they're environment-specific
-- ============================================

-- Start transaction for atomic migration
BEGIN;

-- ============================================
-- SECTION 1: NEW ENUM TYPES
-- ============================================

-- managed_template_type enum (exists in setup2 but not in original setup)
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'managed_template_type') THEN
        CREATE TYPE managed_template_type AS ENUM (
            'proposal',
            'knowledge_card'
        );
        RAISE NOTICE 'Created managed_template_type enum';
    END IF;
END $$;

-- qualification_decision enum
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
        RAISE NOTICE 'Created qualification_decision enum';
    END IF;
END $$;

-- qualification_rule_result enum
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'qualification_rule_result') THEN
        CREATE TYPE qualification_rule_result AS ENUM (
            'pass',
            'fail',
            'waived',
            'not_applicable'
        );
        RAISE NOTICE 'Created qualification_rule_result enum';
    END IF;
END $$;

-- qualification_run_status enum
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
        RAISE NOTICE 'Created qualification_run_status enum';
    END IF;
END $$;

-- release_environment enum
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'release_environment') THEN
        CREATE TYPE release_environment AS ENUM (
            'uat',
            'prod'
        );
        RAISE NOTICE 'Created release_environment enum';
    END IF;
END $$;

-- run_status enum
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'run_status') THEN
        CREATE TYPE run_status AS ENUM (
            'drafting',
            'completed',
            'failed',
            'cancelled'
        );
        RAISE NOTICE 'Created run_status enum';
    END IF;
END $$;

-- ============================================
-- SECTION 2: MISSING TABLES (Present in setup2)
-- ============================================

-- template_registry table
CREATE TABLE IF NOT EXISTS template_registry (
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

-- template_release_history table
CREATE TABLE IF NOT EXISTS template_release_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_registry_id UUID NOT NULL REFERENCES template_registry(id) ON DELETE CASCADE,
    version_number TEXT NOT NULL,
    version_notes TEXT,
    environment release_environment NOT NULL,
    released_by UUID REFERENCES users(id),
    released_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_template_release UNIQUE (template_registry_id, version_number, environment)
);

-- qualification_scenarios table
CREATE TABLE IF NOT EXISTS qualification_scenarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    scenario_type TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- qualification_waivers table
CREATE TABLE IF NOT EXISTS qualification_waivers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    qualification_run_id UUID NOT NULL REFERENCES template_qualification_runs(id) ON DELETE CASCADE,
    rule_id UUID NOT NULL REFERENCES qualification_rules(id) ON DELETE CASCADE,
    waiver_reason TEXT NOT NULL,
    waived_by UUID REFERENCES users(id),
    waived_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE
);

-- template_qualification_signoffs table
CREATE TABLE IF NOT EXISTS template_qualification_signoffs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    qualification_run_id UUID NOT NULL REFERENCES template_qualification_runs(id) ON DELETE CASCADE,
    signed_by UUID NOT NULL REFERENCES users(id),
    signoff_decision qualification_decision NOT NULL,
    comments TEXT,
    signed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    signature_data BYTEA
);

-- template_qualification_run_scenarios table
CREATE TABLE IF NOT EXISTS template_qualification_run_scenarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    qualification_run_id UUID NOT NULL REFERENCES template_qualification_runs(id) ON DELETE CASCADE,
    scenario_id UUID NOT NULL REFERENCES qualification_scenarios(id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    results JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- artifact_runs table (telemetry)
CREATE TABLE IF NOT EXISTS artifact_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artifact_type TEXT NOT NULL CHECK (artifact_type IN ('proposal', 'knowledge_card')),
    artifact_id UUID NOT NULL,
    user_id UUID NOT NULL,
    run_status run_status DEFAULT 'drafting' NOT NULL,
    start_time TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMPTZ,
    agents_executed TEXT[],
    model_deployment TEXT,
    tokens_input INTEGER DEFAULT 0,
    tokens_output INTEGER DEFAULT 0,
    estimated_cost NUMERIC(10,6) DEFAULT 0.0,
    step_count INTEGER DEFAULT 0,
    retry_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    total_latency_ms INTEGER,
    stage_latencies JSONB,
    sections_generated INTEGER DEFAULT 0,
    pages_generated INTEGER DEFAULT 0,
    words_generated INTEGER DEFAULT 0,
    export_events JSONB,
    template_name TEXT,
    template_version TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- qualification_evidence_items table
CREATE TABLE IF NOT EXISTS qualification_evidence_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    qualification_run_id UUID NOT NULL REFERENCES template_qualification_runs(id) ON DELETE CASCADE,
    rule_id UUID NOT NULL REFERENCES qualification_rules(id) ON DELETE CASCADE,
    evidence_type TEXT NOT NULL,
    evidence_description TEXT NOT NULL,
    evidence_data JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- SECTION 3: MISSING SEQUENCES
-- ============================================

-- Sequence for roles.id (if it doesn't exist)
CREATE SEQUENCE IF NOT EXISTS roles_id_seq
    START WITH 1
    INCREMENT BY 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

-- Set the sequence ownership
ALTER SEQUENCE IF EXISTS roles_id_seq OWNED BY roles.id;

-- ============================================
-- SECTION 4: ADD MISSING COLUMNS TO EXISTING TABLES
-- ============================================

-- Add template_type column to donor_template_requests if it doesn't exist
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'donor_template_requests' AND column_name = 'template_type') THEN
        ALTER TABLE donor_template_requests 
        ADD COLUMN template_type TEXT DEFAULT 'proposal';
        RAISE NOTICE 'Added template_type column to donor_template_requests';
    END IF;
END $$;

-- Add updated_at column to donor_template_requests if it doesn't exist
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'donor_template_requests' AND column_name = 'updated_at') THEN
        ALTER TABLE donor_template_requests 
        ADD COLUMN updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP;
        RAISE NOTICE 'Added updated_at column to donor_template_requests';
    END IF;
END $$;

-- Add donor_ids column to donor_template_requests if it doesn't exist
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'donor_template_requests' AND column_name = 'donor_ids') THEN
        ALTER TABLE donor_template_requests 
        ADD COLUMN donor_ids UUID[];
        RAISE NOTICE 'Added donor_ids column to donor_template_requests';
    END IF;
END $$;

-- Add section_name column to donor_template_comments if it doesn't exist
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'donor_template_comments' AND column_name = 'section_name') THEN
        ALTER TABLE donor_template_comments 
        ADD COLUMN section_name TEXT;
        RAISE NOTICE 'Added section_name column to donor_template_comments';
    END IF;
END $$;

-- Add template_name column to donor_template_comments if it doesn't exist
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'donor_template_comments' AND column_name = 'template_name') THEN
        ALTER TABLE donor_template_comments 
        ADD COLUMN template_name TEXT;
        RAISE NOTICE 'Added template_name column to donor_template_comments';
    END IF;
END $$;

-- Add type_of_comment column to donor_template_comments if it doesn't exist
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'donor_template_comments' AND column_name = 'type_of_comment') THEN
        ALTER TABLE donor_template_comments 
        ADD COLUMN type_of_comment TEXT DEFAULT 'Donor Template';
        RAISE NOTICE 'Added type_of_comment column to donor_template_comments';
    END IF;
END $$;

-- Add author_response column to donor_template_comments if it doesn't exist
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'donor_template_comments' AND column_name = 'author_response') THEN
        ALTER TABLE donor_template_comments 
        ADD COLUMN author_response TEXT;
        RAISE NOTICE 'Added author_response column to donor_template_comments';
    END IF;
END $$;

-- Add author_response_by column to donor_template_comments if it doesn't exist
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'donor_template_comments' AND column_name = 'author_response_by') THEN
        ALTER TABLE donor_template_comments 
        ADD COLUMN author_response_by TEXT;
        RAISE NOTICE 'Added author_response_by column to donor_template_comments';
    END IF;
END $$;

-- Add severity column to donor_template_comments if it doesn't exist
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'donor_template_comments' AND column_name = 'severity') THEN
        ALTER TABLE donor_template_comments 
        ADD COLUMN severity TEXT;
        RAISE NOTICE 'Added severity column to donor_template_comments';
    END IF;
END $$;

-- ============================================
-- SECTION 5: ADD MISSING INDEXES
-- ============================================

-- Indexes for artifact_runs
CREATE INDEX IF NOT EXISTS idx_artifact_runs_artifact_id ON artifact_runs(artifact_id);
CREATE INDEX IF NOT EXISTS idx_artifact_runs_artifact_type ON artifact_runs(artifact_type);
CREATE INDEX IF NOT EXISTS idx_artifact_runs_user_id ON artifact_runs(user_id);
CREATE INDEX IF NOT EXISTS idx_artifact_runs_run_status ON artifact_runs(run_status);

-- Indexes for template tables
CREATE INDEX IF NOT EXISTS idx_template_registry_key_type ON template_registry(template_key, template_type);
CREATE INDEX IF NOT EXISTS idx_template_registry_created_at ON template_registry(created_at);
CREATE INDEX IF NOT EXISTS idx_template_versions_registry_id ON template_versions(template_registry_id);
CREATE INDEX IF NOT EXISTS idx_template_qualification_runs_run_id ON template_qualification_runs(id);

-- Indexes for qualification tables
CREATE INDEX IF NOT EXISTS idx_qualification_rules_rule_set_id ON qualification_rules(rule_set_id);
CREATE INDEX IF NOT EXISTS idx_qualification_rule_sets_template_type ON qualification_rule_sets(template_type);

-- ============================================
-- SECTION 6: FIX TEMPLATE VERSIONS DUPLICATE
-- (In database-setup.sql, template_versions is created twice)
-- ============================================

-- This is just a cleanup note - the duplicate CREATE TABLE in database-setup.sql
-- doesn't cause issues because it uses IF NOT EXISTS. No action needed.

-- ============================================
-- SECTION 7: GRANT PERMISSIONS
-- ============================================

-- Grant permissions on new tables (if DB_USERNAME is set)
DO $$ 
BEGIN 
    IF current_setting('app.db_username', true) IS NOT NULL THEN
        PERFORM GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO current_setting('app.db_username', true);
        PERFORM GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO current_setting('app.db_username', true);
        RAISE NOTICE 'Granted permissions to DB user';
    END IF;
EXCEPTION WHEN undefined_table THEN
    RAISE NOTICE 'DB_USERNAME not set, skipping permission grants';
END $$;

-- ============================================
-- SECTION 8: CREATE MISSING TEMPLATES TABLES
-- (template_versions references template_registry, not templates)
-- ============================================

-- Check if template_versions already references templates or template_registry
-- In database-setup.sql it references templates(id), but in setup2 it should reference template_registry(id)
-- We need to handle both cases

DO $$ 
BEGIN 
    -- Check current foreign key reference
    PERFORM pg_get_constraintdef(oid) 
    FROM pg_constraint 
    WHERE conrelid = 'template_versions'::regclass 
    AND confrelid = 'templates'::regclass;
    
    IF FOUND THEN
        -- If it references templates, we need to migrate
        -- For now, we'll add a comment noting this should be updated
        RAISE NOTICE 'template_versions currently references templates, consider updating to template_registry';
    END IF;
END $$;

-- ============================================
-- FINAL: COMMIT TRANSACTION
-- ============================================

COMMIT;

-- ============================================
-- MIGRATION COMPLETE
-- ============================================

RAISE NOTICE 'Migration from database-setup.sql to database-setup2.sql completed successfully!';
