-- Migration: Add SharePoint integration tables
-- Created: 2026-05-04
-- Description: Add tables for SharePoint file upload tracking

-- Check if we're in a transaction block and commit if needed
-- This is safe to run even if not in a transaction

-- ============================================================================
-- SHAREPOINT ENUMS
-- ============================================================================

-- Create sharepoint_status enum for tracking upload states
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sharepoint_status') THEN
        CREATE TYPE sharepoint_status AS ENUM (
            'pending',
            'uploading',
            'uploaded',
            'failed',
            'expired'
        );
        RAISE NOTICE 'Created sharepoint_status enum';
    ELSE
        RAISE NOTICE 'sharepoint_status enum already exists';
    END IF;
END$$;

-- Create error_type enum for SharePoint errors
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sharepoint_error_type') THEN
        CREATE TYPE sharepoint_error_type AS ENUM (
            'authentication_error',
            'connection_error',
            'upload_error',
            'metadata_error',
            'quota_exceeded',
            'permission_error',
            'file_exists',
            'unknown_error'
        );
        RAISE NOTICE 'Created sharepoint_error_type enum';
    ELSE
        RAISE NOTICE 'sharepoint_error_type enum already exists';
    END IF;
END$$;


-- ============================================================================
-- SHAREPOINT LINK TABLES
-- ============================================================================

-- Table for storing SharePoint document links for proposals
CREATE TABLE IF NOT EXISTS proposal_sharepoint_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    sharepoint_url TEXT NOT NULL,
    filename TEXT NOT NULL,
    folder_path TEXT,
    file_id TEXT,
    file_version TEXT,
    status sharepoint_status NOT NULL DEFAULT 'uploading',
    error_type sharepoint_error_type,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    last_attempt_at TIMESTAMPTZ,
    uploaded_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (proposal_id, user_id)
);

-- Table for storing SharePoint document links for knowledge cards
CREATE TABLE IF NOT EXISTS knowledge_card_sharepoint_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_card_id UUID NOT NULL REFERENCES knowledge_cards(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    sharepoint_url TEXT NOT NULL,
    filename TEXT NOT NULL,
    folder_path TEXT,
    file_id TEXT,
    file_version TEXT,
    status sharepoint_status NOT NULL DEFAULT 'uploading',
    error_type sharepoint_error_type,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    last_attempt_at TIMESTAMPTZ,
    uploaded_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (knowledge_card_id, user_id)
);

-- Table for SharePoint upload events and logs
CREATE TABLE IF NOT EXISTS sharepoint_upload_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type TEXT NOT NULL CHECK (event_type IN ('upload_started', 'upload_success', 'upload_failed', 'retry_attempt', 'url_retrieved', 'access_error')),
    artifact_type TEXT NOT NULL CHECK (artifact_type IN ('proposal', 'knowledge_card')),
    artifact_id UUID NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id),
    sharepoint_link_id UUID,
    status sharepoint_status,
    error_type sharepoint_error_type,
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================================
-- INDEXES FOR SHAREPOINT TABLES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_proposal_sharepoint_links_proposal_id ON proposal_sharepoint_links(proposal_id);
CREATE INDEX IF NOT EXISTS idx_proposal_sharepoint_links_user_id ON proposal_sharepoint_links(user_id);
CREATE INDEX IF NOT EXISTS idx_proposal_sharepoint_links_status ON proposal_sharepoint_links(status);

CREATE INDEX IF NOT EXISTS idx_knowledge_card_sharepoint_links_card_id ON knowledge_card_sharepoint_links(knowledge_card_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_card_sharepoint_links_user_id ON knowledge_card_sharepoint_links(user_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_card_sharepoint_links_status ON knowledge_card_sharepoint_links(status);

CREATE INDEX IF NOT EXISTS idx_sharepoint_upload_events_artifact ON sharepoint_upload_events(artifact_type, artifact_id);
CREATE INDEX IF NOT EXISTS idx_sharepoint_upload_events_user ON sharepoint_upload_events(user_id);
CREATE INDEX IF NOT EXISTS idx_sharepoint_upload_events_created ON sharepoint_upload_events(created_at);


-- ============================================================================
-- TRIGGERS FOR SHAREPOINT TABLES
-- ============================================================================

-- Trigger to update updated_at for proposal_sharepoint_links
CREATE OR REPLACE FUNCTION update_proposal_sharepoint_link_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_proposal_sharepoint_links_updated_at ON proposal_sharepoint_links;
CREATE TRIGGER trg_proposal_sharepoint_links_updated_at
    BEFORE UPDATE ON proposal_sharepoint_links
    FOR EACH ROW
    EXECUTE FUNCTION update_proposal_sharepoint_link_timestamp();

-- Trigger to update updated_at for knowledge_card_sharepoint_links
CREATE OR REPLACE FUNCTION update_knowledge_card_sharepoint_link_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_knowledge_card_sharepoint_links_updated_at ON knowledge_card_sharepoint_links;
CREATE TRIGGER trg_knowledge_card_sharepoint_links_updated_at
    BEFORE UPDATE ON knowledge_card_sharepoint_links
    FOR EACH ROW
    EXECUTE FUNCTION update_knowledge_card_sharepoint_link_timestamp();


-- ============================================================================
-- GRANT PERMISSIONS
-- ============================================================================

-- Grant permissions on SharePoint tables to the application user
-- Note: Replace <DB_USERNAME> with your actual database username
DO $$
DECLARE
    app_user TEXT;
BEGIN
    -- Try to get the user from environment or common defaults
    SELECT usename INTO app_user 
    FROM pg_user 
    WHERE usename IN ('proposalgen', 'postgres', current_user) 
    LIMIT 1;
    
    IF app_user IS NOT NULL THEN
        EXECUTE format('GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO %I', app_user);
        EXECUTE format('GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO %I', app_user);
        RAISE NOTICE 'Granted permissions to user: %', app_user;
    ELSE
        RAISE WARNING 'Could not determine application user to grant permissions';
    END IF;
END$$;


-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE proposal_sharepoint_links IS 'Stores SharePoint document links for proposals with user-specific access';
COMMENT ON TABLE knowledge_card_sharepoint_links IS 'Stores SharePoint document links for knowledge cards with user-specific access';
COMMENT ON TABLE sharepoint_upload_events IS 'Logs all SharePoint upload events for auditing and debugging';

COMMENT ON TYPE sharepoint_status IS 'Status of SharePoint file upload: pending, uploading, uploaded, failed, expired';
COMMENT ON TYPE sharepoint_error_type IS 'Type of error that occurred during SharePoint upload';

RAISE NOTICE 'SharePoint integration tables migration completed successfully!';
