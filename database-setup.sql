-- Database setup for Proposal Drafter application

-- Create application user (if it doesn't exist)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'iom_uc1_user') THEN
        CREATE USER iom_uc1_user WITH PASSWORD 'IomUC1@20250605$';
    END IF;
END $$;

-- Grant necessary privileges to the application user
GRANT CONNECT ON DATABASE postgres TO iom_uc1_user;
GRANT USAGE ON SCHEMA public TO iom_uc1_user;

-- Create Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    name TEXT,
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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster user lookup
CREATE INDEX IF NOT EXISTS idx_proposals_user_id ON proposals(user_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Grant table permissions to application user
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO iom_uc1_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO iom_uc1_user;

-- Create sample user for testing (password: password123)
INSERT INTO users (id, email, name, password) 
VALUES (
    '550e8400-e29b-41d4-a716-446655440000', 
    'test@example.com', 
    'Test User', 
    'pbkdf2:sha256:150000$KkCqT4Mj$7ca33681db68f809b46e9ac6187248f9f20b8895b15dfd29522c51b884306250'
) ON CONFLICT (email) DO NOTHING;