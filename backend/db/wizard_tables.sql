-- Wizard utility tables for Q&A system
-- This file contains the database schema for the wizard utility

CREATE TABLE IF NOT EXISTS qa_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT qa_categories_name_unique UNIQUE (name)
);

CREATE TABLE IF NOT EXISTS qa_items (
    id SERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category_id INTEGER REFERENCES qa_categories(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    CONSTRAINT qa_items_question_unique UNIQUE (question)
);

CREATE TABLE IF NOT EXISTS user_interactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    qa_item_id INTEGER REFERENCES qa_items(id),
    interaction_type VARCHAR(50) NOT NULL CHECK (interaction_type IN ('view', 'search', 'feedback')),
    feedback_score INTEGER CHECK (feedback_score BETWEEN 1 AND 5),
    feedback_comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_qa_items_category ON qa_items(category_id);
CREATE INDEX IF NOT EXISTS idx_qa_items_active ON qa_items(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_user_interactions_user ON user_interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_interactions_qa ON user_interactions(qa_item_id);
CREATE INDEX IF NOT EXISTS idx_user_interactions_type ON user_interactions(interaction_type);
CREATE INDEX IF NOT EXISTS idx_user_interactions_created ON user_interactions(created_at);