-- Migration: Add team settings table and inheritance functions
-- This migration adds the team_settings table and PostgreSQL functions
-- to handle automatic inheritance of team settings to team members

BEGIN;

-- Create team_settings table
CREATE TABLE IF NOT EXISTS team_settings (
    id SERIAL PRIMARY KEY,
    team_id UUID NOT NULL,
    setting_type VARCHAR(50) NOT NULL,
    setting_value VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
    UNIQUE (team_id, setting_type, setting_value)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_team_settings_team_id ON team_settings(team_id);
CREATE INDEX IF NOT EXISTS idx_team_settings_type ON team_settings(setting_type);

-- Create function to get inherited settings for a user
CREATE OR REPLACE FUNCTION get_inherited_settings_for_user(user_id VARCHAR(36))
RETURNS TABLE(
    setting_type VARCHAR(50),
    setting_value VARCHAR(255),
    source_type VARCHAR(20),
    source_id VARCHAR(36)
) AS $$
BEGIN
    RETURN QUERY
    -- First get the user's teams
    WITH user_teams AS (
        SELECT team_id FROM team_members WHERE user_id = get_inherited_settings_for_user.user_id
    )
    -- Get team settings for those teams
    SELECT
        ts.setting_type,
        ts.setting_value,
        'team' AS source_type,
        ts.team_id AS source_id
    FROM team_settings ts
    JOIN user_teams ut ON ts.team_id = ut.team_id

    UNION ALL

    -- Also include user's direct settings for completeness
    SELECT
        setting_type,
        setting_value,
        'user' AS source_type,
        user_id AS source_id
    FROM user_settings_requests
    WHERE user_id = get_inherited_settings_for_user.user_id
    AND status = 'approved';
END;
$$ LANGUAGE plpgsql;

-- Create function to apply inherited settings to a user
CREATE OR REPLACE FUNCTION apply_inherited_settings_to_user(user_id VARCHAR(36))
RETURNS VOID AS $$
DECLARE
    team_setting RECORD;
BEGIN
    -- Get all inherited team settings for the user
    FOR team_setting IN
        SELECT setting_type, setting_value
        FROM team_settings ts
        WHERE ts.team_id IN (
            SELECT team_id FROM team_members WHERE user_id = apply_inherited_settings_to_user.user_id
        )
    LOOP
        -- Check if user already has this setting
        PERFORM 1 FROM user_settings_requests
        WHERE user_id = apply_inherited_settings_to_user.user_id
        AND setting_type = team_setting.setting_type
        AND setting_value = team_setting.setting_value
        AND status = 'approved'
        LIMIT 1;

        IF NOT FOUND THEN
            -- User doesn't have this setting, so grant it
            INSERT INTO user_settings_requests (
                user_id, setting_type, setting_value, status, approved_at, approved_by
            ) VALUES (
                apply_inherited_settings_to_user.user_id,
                team_setting.setting_type,
                team_setting.setting_value,
                'approved',
                CURRENT_TIMESTAMP,
                NULL -- NULL provenance marks system-materialized inheritance
            ) ON CONFLICT (user_id, setting_type, setting_value) DO NOTHING;
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for automatic inheritance
CREATE OR REPLACE FUNCTION handle_team_settings_inheritance()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        -- When a team setting is added or updated, apply to all team members
        PERFORM apply_inherited_settings_to_user(user_id)
        FROM team_members
        WHERE team_id = NEW.team_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create the trigger
CREATE TRIGGER team_settings_inheritance_trigger
AFTER INSERT OR UPDATE ON team_settings
FOR EACH ROW
EXECUTE FUNCTION handle_team_settings_inheritance();

-- Create view for comprehensive user settings
CREATE OR REPLACE VIEW user_effective_settings AS
SELECT
    usr.user_id,
    usr.setting_type,
    usr.setting_value,
    usr.status,
    usr.requested_at,
    usr.approved_at,
    'direct' AS source
FROM user_settings_requests usr
WHERE usr.status = 'approved'

UNION ALL

SELECT
    tm.user_id,
    ts.setting_type,
    ts.setting_value,
    'approved' AS status,
    NULL AS requested_at,
    CURRENT_TIMESTAMP AS approved_at,
    'inherited' AS source
FROM team_settings ts
JOIN team_members tm ON ts.team_id = tm.team_id
WHERE NOT EXISTS (
    SELECT 1 FROM user_settings_requests usr
    WHERE usr.user_id = tm.user_id
    AND usr.setting_type = ts.setting_type
    AND usr.setting_value = ts.setting_value
    AND usr.status = 'approved'
);

COMMIT;

-- Migration completed successfully
