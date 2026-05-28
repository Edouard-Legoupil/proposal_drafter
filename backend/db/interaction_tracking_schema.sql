-- User Interaction Tracking Schema
-- This schema tracks all user interactions for analytics, debugging, and wizard improvement

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- User Sessions Table - Tracks user sessions for context
CREATE TABLE IF NOT EXISTS user_sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP WITH TIME ZONE,
    ip_address VARCHAR(45),
    user_agent TEXT,
    device_type VARCHAR(50),
    browser_name VARCHAR(50),
    browser_version VARCHAR(20),
    os_name VARCHAR(50),
    os_version VARCHAR(20),
    screen_width INTEGER,
    screen_height INTEGER,
    is_mobile BOOLEAN,
    session_duration INTERVAL GENERATED ALWAYS AS (ended_at - started_at) STORED
);

-- Create index for faster session queries
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_started_at ON user_sessions(started_at);

-- Interaction Types Enum
DO $$ BEGIN
    CREATE TYPE interaction_type AS ENUM (
        'page_view',
        'click',
        'form_submission',
        'navigation',
        'search',
        'wizard_interaction',
        'error',
        'api_call',
        'download',
        'upload',
        'copy_to_clipboard',
        'keyboard_shortcut',
        'hover',
        'scroll',
        'resize'
    );
EXCEPTION WHEN duplicate_object THEN
    -- Type already exists, skip creation
    NULL;
END $$;

-- User Interactions Table - Main interaction tracking
CREATE TABLE IF NOT EXISTS user_interactions (
    interaction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES user_sessions(session_id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    interaction_type interaction_type,
    interaction_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    page_url TEXT,
    page_title TEXT,
    component_name VARCHAR(100),
    element_type VARCHAR(50),
    element_selector TEXT,
    element_test_id VARCHAR(100),
    element_text TEXT,
    event_data JSONB,
    metadata JSONB,
    duration_ms INTEGER,
    was_successful BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    error_stack TEXT
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_interactions_session_id ON user_interactions(session_id);
CREATE INDEX IF NOT EXISTS idx_user_interactions_user_id ON user_interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_interactions_timestamp ON user_interactions(interaction_timestamp);
CREATE INDEX IF NOT EXISTS idx_user_interactions_type ON user_interactions(interaction_type);
CREATE INDEX IF NOT EXISTS idx_user_interactions_page_url ON user_interactions(page_url);
CREATE INDEX IF NOT EXISTS idx_user_interactions_element_test_id ON user_interactions(element_test_id);

-- Wizard-Specific Interactions - For learning and improvement
CREATE TABLE IF NOT EXISTS wizard_interactions (
    wizard_interaction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    interaction_id UUID REFERENCES user_interactions(interaction_id) ON DELETE CASCADE,
    session_id UUID REFERENCES user_sessions(session_id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    interaction_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    action_type VARCHAR(50) NOT NULL,  -- 'search', 'question_view', 'feedback', 'category_select', etc.
    search_query TEXT,
    selected_category_id UUID REFERENCES wizard_categories(category_id) ON DELETE SET NULL,
    viewed_qa_item_id UUID REFERENCES wizard_qa_items(qa_item_id) ON DELETE SET NULL,
    feedback_score INTEGER,
    feedback_comment TEXT,
    time_spent_ms INTEGER,
    was_helpful BOOLEAN,
    related_qa_items JSONB,  -- Other QA items that might be relevant
    context_data JSONB  -- Additional context about the user's state
);

-- Create indexes for wizard interactions
CREATE INDEX IF NOT EXISTS idx_wizard_interactions_session_id ON wizard_interactions(session_id);
CREATE INDEX IF NOT EXISTS idx_wizard_interactions_user_id ON wizard_interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_wizard_interactions_timestamp ON wizard_interactions(interaction_timestamp);
CREATE INDEX IF NOT EXISTS idx_wizard_interactions_category ON wizard_interactions(selected_category_id);
CREATE INDEX IF NOT EXISTS idx_wizard_interactions_qa_item ON wizard_interactions(viewed_qa_item_id);

-- User Journey Patterns - Aggregated patterns for analysis
CREATE TABLE IF NOT EXISTS user_journey_patterns (
    pattern_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pattern_name VARCHAR(100) NOT NULL,
    pattern_description TEXT,
    interaction_sequence JSONB NOT NULL,  -- Sequence of interaction types
    frequency_count INTEGER DEFAULT 0,
    last_observed TIMESTAMP WITH TIME ZONE,
    first_observed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    typical_duration INTERVAL,
    common_next_steps JSONB,
    related_questions JSONB  -- Questions that often follow this pattern
);

-- Create index for pattern lookup
CREATE INDEX IF NOT EXISTS idx_user_journey_patterns_name ON user_journey_patterns(pattern_name);

-- User Interaction Analytics - Pre-aggregated data for dashboard
CREATE TABLE IF NOT EXISTS interaction_analytics (
    analytics_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    date DATE NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    total_interactions INTEGER DEFAULT 0,
    total_sessions INTEGER DEFAULT 0,
    total_session_duration INTERVAL,
    average_session_duration INTERVAL,
    interaction_types JSONB,  -- Count by interaction type
    most_used_features JSONB,  -- Features used most frequently
    error_count INTEGER DEFAULT 0,
    wizard_usage_count INTEGER DEFAULT 0,
    wizard_feedback_score NUMERIC(3,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for analytics
CREATE INDEX IF NOT EXISTS idx_interaction_analytics_date ON interaction_analytics(date);
CREATE INDEX IF NOT EXISTS idx_interaction_analytics_user_id ON interaction_analytics(user_id);

-- Create materialized view for common user journeys
CREATE MATERIALIZED VIEW IF NOT EXISTS common_user_journeys AS
SELECT 
    ui.user_id,
    COUNT(DISTINCT ui.session_id) AS session_count,
    COUNT(ui.interaction_id) AS interaction_count,
    STRING_AGG(DISTINCT ui.interaction_type, ', ' ORDER BY COUNT(ui.interaction_type) DESC) AS common_interactions,
    STRING_AGG(DISTINCT ui.page_url, ', ' ORDER BY COUNT(ui.page_url) DESC) AS common_pages,
    AVG(EXTRACT(EPOCH FROM (us.ended_at - us.started_at))) AS avg_session_duration_seconds
FROM user_interactions ui
JOIN user_sessions us ON ui.session_id = us.session_id
WHERE ui.interaction_timestamp > CURRENT_TIMESTAMP - INTERVAL '30 days'
GROUP BY ui.user_id
WITH DATA;

-- Refresh the materialized view daily
CREATE OR REPLACE FUNCTION refresh_common_user_journeys() 
RETURNS TRIGGER AS $$ 
BEGIN 
    REFRESH MATERIALIZED VIEW common_user_journeys; 
    RETURN NULL; 
END; 
$$ LANGUAGE plpgsql;

-- Create a trigger to refresh the view periodically
CREATE OR REPLACE PROCEDURE refresh_journey_analytics() 
LANGUAGE SQL 
AS $$ 
    REFRESH MATERIALIZED VIEW common_user_journeys; 
$$;

-- Create a function to end user sessions
CREATE OR REPLACE FUNCTION end_user_session(session_id UUID) 
RETURNS VOID AS $$ 
BEGIN 
    UPDATE user_sessions 
    SET ended_at = CURRENT_TIMESTAMP 
    WHERE session_id = end_user_session.session_id AND ended_at IS NULL; 
END; 
$$ LANGUAGE plpgsql;

-- Create a function to log user interactions
CREATE OR REPLACE FUNCTION log_user_interaction(
    p_session_id UUID,
    p_user_id UUID,
    p_interaction_type interaction_type,
    p_page_url TEXT,
    p_page_title TEXT,
    p_component_name VARCHAR(100),
    p_element_type VARCHAR(50),
    p_element_selector TEXT,
    p_element_test_id VARCHAR(100),
    p_element_text TEXT,
    p_event_data JSONB,
    p_metadata JSONB
) RETURNS UUID AS $$ 
DECLARE 
    interaction_id UUID; 
BEGIN 
    -- Insert the interaction
    INSERT INTO user_interactions (
        interaction_id, 
        session_id, 
        user_id, 
        interaction_type, 
        page_url, 
        page_title, 
        component_name, 
        element_type, 
        element_selector, 
        element_test_id, 
        element_text, 
        event_data, 
        metadata
    ) VALUES (
        uuid_generate_v4(), 
        p_session_id, 
        p_user_id, 
        p_interaction_type, 
        p_page_url, 
        p_page_title, 
        p_component_name, 
        p_element_type, 
        p_element_selector, 
        p_element_test_id, 
        p_element_text, 
        p_event_data, 
        p_metadata
    ) RETURNING interaction_id INTO interaction_id;
    
    RETURN interaction_id; 
END; 
$$ LANGUAGE plpgsql;

-- Create a function to log wizard interactions
CREATE OR REPLACE FUNCTION log_wizard_interaction(
    p_interaction_id UUID,
    p_session_id UUID,
    p_user_id UUID,
    p_action_type VARCHAR(50),
    p_search_query TEXT,
    p_selected_category_id UUID,
    p_viewed_qa_item_id UUID,
    p_feedback_score INTEGER,
    p_feedback_comment TEXT,
    p_time_spent_ms INTEGER,
    p_was_helpful BOOLEAN,
    p_context_data JSONB
) RETURNS UUID AS $$ 
DECLARE 
    wizard_interaction_id UUID; 
BEGIN 
    -- Insert the wizard interaction
    INSERT INTO wizard_interactions (
        wizard_interaction_id, 
        interaction_id, 
        session_id, 
        user_id, 
        action_type, 
        search_query, 
        selected_category_id, 
        viewed_qa_item_id, 
        feedback_score, 
        feedback_comment, 
        time_spent_ms, 
        was_helpful, 
        context_data
    ) VALUES (
        uuid_generate_v4(), 
        p_interaction_id, 
        p_session_id, 
        p_user_id, 
        p_action_type, 
        p_search_query, 
        p_selected_category_id, 
        p_viewed_qa_item_id, 
        p_feedback_score, 
        p_feedback_comment, 
        p_time_spent_ms, 
        p_was_helpful, 
        p_context_data
    ) RETURNING wizard_interaction_id INTO wizard_interaction_id;
    
    RETURN wizard_interaction_id; 
END; 
$$ LANGUAGE plpgsql;