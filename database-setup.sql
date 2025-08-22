-- Database setup for Proposal Drafter application
-- IMPORTANT! REPLACE <DB_USERNAME> with ACTUAL DB_USERNAME

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

-- Create Proposals table
CREATE TABLE IF NOT EXISTS proposals (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    form_data JSONB NOT NULL,
    project_description TEXT NOT NULL,
    generated_sections JSONB,
    is_accepted BOOLEAN DEFAULT FALSE,
    status VARCHAR(255) DEFAULT 'draft',
    field_contexts TEXT[],
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Create Donors table
CREATE TABLE IF NOT EXISTS donors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE
);

-- Create Outcomes table
CREATE TABLE IF NOT EXISTS outcomes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE
);

-- Create Field Contexts table
CREATE TABLE IF NOT EXISTS field_contexts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE
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
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_card_id UUID NOT NULL REFERENCES knowledge_cards(id) ON DELETE CASCADE,
    url TEXT NOT NULL
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_proposals_user_id ON proposals(user_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_knowledge_cards_donor_id ON knowledge_cards(donor_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_cards_outcome_id ON knowledge_cards(outcome_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_cards_field_context_id ON knowledge_cards(field_context_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_card_references_knowledge_card_id ON knowledge_card_references(knowledge_card_id);

-- Grant table permissions to application user
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO <DB_USERNAME>;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO <DB_USERNAME>;

-- Seed data for new tables
INSERT INTO donors (name) VALUES ('ECHO'), ('SIDA'), ('PRM'), ('CERF') ON CONFLICT (name) DO NOTHING;
INSERT INTO outcomes (name) VALUES ('WASH'), ('Shelter'), ('Livelihoods'), ('Community'), ('Education'), ('Child protection'), ('Status'), ('Data') ON CONFLICT (name) DO NOTHING;
INSERT INTO field_contexts (name) VALUES ('Country A'), ('Country B'), ('Route based Approach - West Africa') ON CONFLICT (name) DO NOTHING;
