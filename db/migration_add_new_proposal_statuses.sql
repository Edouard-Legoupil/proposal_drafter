BEGIN;

-- This script migrates the database schema to use the new 'proposal_status_new' enum,
-- which includes 'generating_sections' and 'failed' statuses.
-- It is designed to be idempotent and can be safely run on a database that has
-- already been migrated.

-- Step 1: Create the new enum type if it doesn't exist.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'proposal_status_new') THEN
        CREATE TYPE proposal_status_new AS ENUM (
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

-- Step 2: Conditionally migrate tables and drop the old enum.
-- This entire block is skipped if the old 'proposal_status' enum does not exist,
-- which indicates the migration has already been performed.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'proposal_status') THEN
        -- Update 'proposals' table to use the new enum.
        -- We temporarily drop the default, change the type by casting, and then restore the default.
        ALTER TABLE proposals ALTER COLUMN status DROP DEFAULT;
        ALTER TABLE proposals ALTER COLUMN status TYPE proposal_status_new USING status::text::proposal_status_new;
        ALTER TABLE proposals ALTER COLUMN status SET DEFAULT 'draft';

        -- Update 'proposal_status_history' table.
        ALTER TABLE proposal_status_history ALTER COLUMN status TYPE proposal_status_new USING status::text::proposal_status_new;

        -- Update 'knowledge_cards' table.
        ALTER TABLE knowledge_cards ALTER COLUMN status DROP DEFAULT;
        ALTER TABLE knowledge_cards ALTER COLUMN status TYPE proposal_status_new USING status::text::proposal_status_new;
        ALTER TABLE knowledge_cards ALTER COLUMN status SET DEFAULT 'draft';

        -- Drop the old enum type, which is now no longer referenced by any table.
        DROP TYPE proposal_status;
    END IF;
END$$;

COMMIT;
