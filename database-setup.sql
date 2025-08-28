-- Database setup for Proposal Drafter application
-- IMORTANT ! REPLACE <DB_USERNAME> with ACTUAL DB_USERNAME

-- Grant necessary privileges to the application user
GRANT CONNECT ON DATABASE postgres TO <DB_USERNAME>;
GRANT USAGE ON SCHEMA public TO <DB_USERNAME>;

-- Create Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    name TEXT,
    security_questions JSONB,
    session_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Create Proposal Status Enum Type
CREATE TYPE proposal_status AS ENUM ('draft', 'in_review', 'submission', 'submitted', 'approved');

-- Create Proposals table
CREATE TABLE IF NOT EXISTS proposals (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    template_name VARCHAR(255) DEFAULT 'unhcr_proposal_template.json',
    form_data JSONB NOT NULL,
    project_description TEXT NOT NULL,
    generated_sections JSONB,
    is_accepted BOOLEAN DEFAULT FALSE,
    pstatus VARCHAR(255) DEFAULT 'draft',
    donor VARCHAR(255),
    field_contexts TEXT[],
    outcome VARCHAR(255),
    reviews JSONB,
    status proposal_status DEFAULT 'draft',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Create Proposal_Peer table
CREATE TABLE IF NOT EXISTS proposal_peer (
    id SERIAL PRIMARY KEY,
    proposal_id UUID REFERENCES proposals(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);


-- Create Donors table
CREATE TABLE IF NOT EXISTS donors (
    id SERIAL PRIMARY KEY,
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL
    name TEXT NOT NULL UNIQUE
);


-- Create Outcomes table
CREATE TABLE IF NOT EXISTS outcomes (
    id SERIAL PRIMARY KEY,
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL
    name TEXT NOT NULL UNIQUE
);


-- Create Field Contexts table
CREATE TABLE IF NOT EXISTS field_contexts (
    category VARCHAR(255) NOT NULL,
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    name TEXT NOT NULL UNIQUE
    summary TEXT,
    last_updated TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Create Knowledge Cards table
CREATE TABLE IF NOT EXISTS knowledge_cards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    summary TEXT,
    generated_sections JSONB,
    is_accepted BOOLEAN DEFAULT FALSE,
    status VARCHAR(255) DEFAULT 'draft',
    donor_id UUID REFERENCES donors(id) ON DELETE SET NULL,
    outcome_id UUID REFERENCES outcomes(id) ON DELETE SET NULL,
    field_context_id UUID REFERENCES field_contexts(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT one_link_only CHECK (
        (CASE WHEN donor_id IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN outcome_id IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN field_context_id IS NOT NULL THEN 1 ELSE 0 END) = 1
    )
);

-- Create Knowledge Card References table
CREATE TABLE IF NOT EXISTS knowledge_card_references (
    outcome_id INTEGER REFERENCES outcomes(id) ON DELETE CASCADE,
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    PRIMARY KEY (proposal_id, outcome_id)
    knowledge_card_id UUID NOT NULL REFERENCES knowledge_cards(id) ON DELETE CASCADE,
    url TEXT NOT NULL
); 

-- Create join tables for many-to-many relationships
CREATE TABLE IF NOT EXISTS proposal_donors (
    proposal_id UUID REFERENCES proposals(id) ON DELETE CASCADE,
    donor_id INTEGER REFERENCES donors(id) ON DELETE CASCADE,
    PRIMARY KEY (proposal_id, donor_id)
);

CREATE TABLE IF NOT EXISTS proposal_outcomes (
    proposal_id UUID REFERENCES proposals(id) ON DELETE CASCADE,
    outcome_id INTEGER REFERENCES outcomes(id) ON DELETE CASCADE,
    PRIMARY KEY (proposal_id, outcome_id)
);

CREATE TABLE IF NOT EXISTS proposal_field_context (
    proposal_id UUID REFERENCES proposals(id) ON DELETE CASCADE,
    field_context_id INTEGER REFERENCES field_context(id) ON DELETE CASCADE,
    PRIMARY KEY (proposal_id, outcome_id)
);

-- Create index for faster user lookup
CREATE INDEX IF NOT EXISTS idx_proposals_user_id ON proposals(user_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_knowledge_cards_donor_id ON knowledge_cards(donor_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_cards_outcome_id ON knowledge_cards(outcome_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_cards_field_context_id ON knowledge_cards(field_context_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_card_references_knowledge_card_id ON knowledge_card_references(knowledge_card_id);
CREATE INDEX IF NOT EXISTS idx_proposal_peer_proposal_id ON proposal_peer(proposal_id);
CREATE INDEX IF NOT EXISTS idx_proposal_peer_user_id ON proposal_peer(user_id);


-- Grant table permissions to application user
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO <DB_USERNAME>;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO <DB_USERNAME>;
