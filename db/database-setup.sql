-- Database setup for Proposal Drafter application
-- IMORTANT ! REPLACE <DB_USERNAME> with ACTUAL DB_USERNAME

-- Grant necessary privileges to the application user
GRANT CONNECT ON DATABASE postgres TO <DB_USERNAME>;
GRANT USAGE ON SCHEMA public TO <DB_USERNAME>;

-- Enable vector extension
CREATE EXTENSION IF NOT EXISTS vector;

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
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);


-- Create Donors table 
CREATE TABLE IF NOT EXISTS donors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id TEXT NOT NULL UNIQUE,
    name TEXT UNIQUE NOT NULL,
    country TEXT NOT NULL,
    donor_group TEXT NOT NULL,
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
    name TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL,
    geographic_coverage TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Create Proposal Status Enum Type
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'proposal_status') THEN
        CREATE TYPE proposal_status AS ENUM ('draft', 'in_review', 'submission', 'submitted', 'approved');
    END IF;
END$$;
-- Add 'deleted' to the proposal_status enum if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumtypid = 'proposal_status'::regtype AND enumlabel = 'deleted') THEN
        ALTER TYPE proposal_status ADD VALUE 'deleted';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumtypid = 'proposal_status'::regtype AND enumlabel = 'generating_sections') THEN
        ALTER TYPE proposal_status ADD VALUE 'generating_sections';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumtypid = 'proposal_status'::regtype AND enumlabel = 'failed') THEN
        ALTER TYPE proposal_status ADD VALUE 'failed';
    END IF;
END$$;

-- Create Proposals table
CREATE TABLE IF NOT EXISTS proposals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    template_name VARCHAR(255) DEFAULT 'unhcr_proposal_template.json',
    form_data JSONB NOT NULL,
    project_description TEXT NOT NULL,
    generated_sections JSONB,
    reviews JSONB,
    is_accepted BOOLEAN DEFAULT FALSE,
    status proposal_status DEFAULT 'draft', 
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
    status VARCHAR(50) DEFAULT 'pending',
    deadline TIMESTAMPTZ,
    review_text TEXT,
    author_response TEXT,
    type_of_comment TEXT,
    severity TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (proposal_id, reviewer_id, section_name)
);

-- Create Knowledge Cards table
CREATE TABLE IF NOT EXISTS knowledge_cards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_name TEXT,
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

-- Create index for faster user lookup
CREATE INDEX IF NOT EXISTS idx_proposals_user_id ON proposals(user_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_knowledge_cards_donor_id ON knowledge_cards(donor_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_cards_outcome_id ON knowledge_cards(outcome_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_cards_field_context_id ON knowledge_cards(field_context_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_card_references_knowledge_card_id ON knowledge_card_references(knowledge_card_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_card_history_knowledge_card_id ON knowledge_card_references(knowledge_card_id);
CREATE INDEX IF NOT EXISTS idx_proposal_peer_reviews_proposal_id ON proposal_peer_reviews(proposal_id);
CREATE INDEX IF NOT EXISTS idx_proposal_peer_reviews_reviewer_id ON proposal_peer_reviews(reviewer_id);
CREATE INDEX IF NOT EXISTS idx_proposal_status_history_proposal_id ON proposal_status_history(proposal_id);

 
 

-- Grant table permissions to application user
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO <DB_USERNAME>;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO <DB_USERNAME>;
