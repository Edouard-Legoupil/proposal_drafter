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

-- Create Donors, Outcomes, and Knowledge Cards tables
CREATE TABLE IF NOT EXISTS donors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS outcomes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS knowledge_cards (
    id SERIAL PRIMARY KEY,
    category VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    summary TEXT,
    last_updated TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
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


-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_proposals_user_id ON proposals(user_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_proposal_donors_proposal_id ON proposal_donors(proposal_id);
CREATE INDEX IF NOT EXISTS idx_proposal_donors_donor_id ON proposal_donors(donor_id);
CREATE INDEX IF NOT EXISTS idx_proposal_outcomes_proposal_id ON proposal_outcomes(proposal_id);
CREATE INDEX IF NOT EXISTS idx_proposal_outcomes_outcome_id ON proposal_outcomes(outcome_id);


-- Grant table permissions to application user
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO <DB_USERNAME>;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO <DB_USERNAME>;

-- Seed data for new tables
INSERT INTO donors (name) VALUES ('ECHO'), ('SIDA'), ('PRM'), ('CERF') ON CONFLICT (name) DO NOTHING;
INSERT INTO outcomes (name) VALUES ('WASH'), ('Shelter'), ('Livelihoods'), ('Community'), ('Education'), ('Child protection'), ('Status'), ('Data') ON CONFLICT (name) DO NOTHING;

INSERT INTO knowledge_cards (category, title, summary) VALUES
('Donor Insights', 'ECHO', 'Key compliance and funding priorities for ECHO.'),
('Donor Insights', 'CERF', 'Key compliance and funding priorities for CERF.'),
('Field Context', 'Country A', 'Recent situational updates for Country A.'),
('Field Context', 'Route Based Approach - West Africa', 'Recent situational updates for the West Africa route.'),
('Outcome Lessons', 'Shelter', 'Extracted insights from Policies, Guidance and related Past Evaluation Recommendation for Shelter.')
ON CONFLICT DO NOTHING;
