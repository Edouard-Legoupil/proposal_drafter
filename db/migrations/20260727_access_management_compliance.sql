-- Normalize legacy access control into team-scoped component roles.
-- Safe to re-run: DDL is conditional and data writes use stable conflicts.
BEGIN;

ALTER TABLE teams ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE teams ADD COLUMN IF NOT EXISTS created_by UUID;
ALTER TABLE teams ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE teams ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE roles ADD COLUMN IF NOT EXISTS role_key TEXT;
ALTER TABLE roles ADD COLUMN IF NOT EXISTS component TEXT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'roles_role_key_key'
          AND conrelid = 'roles'::regclass
          AND contype = 'u'
    ) THEN
        ALTER TABLE roles ADD CONSTRAINT roles_role_key_key UNIQUE (role_key);
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'roles_id_role_key_key'
          AND conrelid = 'roles'::regclass
          AND contype = 'u'
    ) THEN
        ALTER TABLE roles ADD CONSTRAINT roles_id_role_key_key UNIQUE (id, role_key);
    END IF;
END$$;

INSERT INTO roles (name, role_key, component) VALUES
    ('proposal writer', 'proposal writer', 'ProposalWorkspace'),
    ('project reviewer', 'project reviewer', 'ReviewWorkspace'),
    ('knowledge manager donors', 'knowledge manager donors', 'DonorKnowledgeCards'),
    ('knowledge manager outcome', 'knowledge manager outcome', 'OutcomeKnowledgeCards'),
    ('knowledge manager field context', 'knowledge manager field context', 'FieldContextKnowledgeCards'),
    ('access_template', 'access_template', 'TemplateLibrary'),
    ('access_metrics', 'access_metrics', 'MetricsDashboard'),
    ('access_incident', 'access_incident', 'IncidentDashboard'),
    ('access_quality_gate', 'access_quality_gate', 'QualityGate'),
    ('ui_analysis', 'ui_analysis', 'InteractionAnalytics'),
    ('system admin', 'system admin', NULL),
    ('TEAM_LEADER', 'TEAM_LEADER', NULL)
ON CONFLICT (name) DO UPDATE
SET role_key = EXCLUDED.role_key,
    component = EXCLUDED.component;

ALTER TABLE team_members ADD COLUMN IF NOT EXISTS status TEXT;
ALTER TABLE team_members ADD COLUMN IF NOT EXISTS joined_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP;

-- Preserve the legacy single-team relationship as an active membership. The
-- normalized table becomes authoritative after this one-way compatibility
-- backfill.
INSERT INTO team_members (team_id, user_id, status)
SELECT team_id, id, 'ACTIVE'
FROM users
WHERE team_id IS NOT NULL
ON CONFLICT (team_id, user_id) DO NOTHING;

UPDATE team_members SET status = UPPER(COALESCE(status, 'ACTIVE'));
UPDATE team_members SET status = 'REJECTED' WHERE status NOT IN ('PENDING', 'ACTIVE', 'REJECTED');
ALTER TABLE team_members ALTER COLUMN status SET DEFAULT 'ACTIVE';
ALTER TABLE team_members ALTER COLUMN status SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'team_members_status_check'
          AND conrelid = 'team_members'::regclass
          AND contype = 'c'
    ) THEN
        ALTER TABLE team_members
            ADD CONSTRAINT team_members_status_check
            CHECK (status IN ('PENDING', 'ACTIVE', 'REJECTED'));
    END IF;
END$$;

ALTER TABLE team_roles ADD COLUMN IF NOT EXISTS role_key TEXT;
UPDATE team_roles tr SET role_key = r.role_key FROM roles r
WHERE tr.role_id = r.id AND tr.role_key IS DISTINCT FROM r.role_key;

CREATE TABLE IF NOT EXISTS legacy_team_role_ambiguities (
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    reason TEXT NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (team_id, role_id)
);

INSERT INTO legacy_team_role_ambiguities (team_id, role_id, reason)
SELECT team_id, role_id, 'special role cannot be inherited by every team member'
FROM team_roles
WHERE role_key IN ('system admin', 'TEAM_LEADER')
ON CONFLICT (team_id, role_id) DO UPDATE SET reason = EXCLUDED.reason;

DELETE FROM team_roles WHERE role_key IN ('system admin', 'TEAM_LEADER');

-- A legacy role without a stable key or component cannot participate in the
-- normalized component-role identity. Preserve a report before removing it.
INSERT INTO legacy_team_role_ambiguities (team_id, role_id, reason)
SELECT tr.team_id, tr.role_id,
    CASE
        WHEN r.role_key IS NULL THEN 'role has no normalized role_key'
        ELSE 'role is not a static component role'
    END
FROM team_roles tr
LEFT JOIN roles r ON r.id = tr.role_id
WHERE r.role_key IS NULL OR r.component IS NULL
ON CONFLICT (team_id, role_id) DO UPDATE SET reason = EXCLUDED.reason;

DELETE FROM team_roles tr
USING roles r
WHERE tr.role_id = r.id AND (r.role_key IS NULL OR r.component IS NULL);

ALTER TABLE team_roles ALTER COLUMN role_key SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'team_roles_team_id_role_key_key'
          AND conrelid = 'team_roles'::regclass
          AND contype = 'u'
    ) THEN
        ALTER TABLE team_roles ADD CONSTRAINT team_roles_team_id_role_key_key UNIQUE (team_id, role_key);
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'team_roles_role_identity_fkey'
          AND conrelid = 'team_roles'::regclass
          AND contype = 'f'
    ) THEN
        ALTER TABLE team_roles ADD CONSTRAINT team_roles_role_identity_fkey
            FOREIGN KEY (role_id, role_key) REFERENCES roles(id, role_key) ON DELETE CASCADE;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'team_roles_component_role_check'
          AND conrelid = 'team_roles'::regclass
          AND contype = 'c'
    ) THEN
        ALTER TABLE team_roles ADD CONSTRAINT team_roles_component_role_check
            CHECK (role_key NOT IN ('system admin', 'TEAM_LEADER'));
    END IF;
END$$;

CREATE TABLE IF NOT EXISTS team_member_roles (
    team_id UUID NOT NULL,
    user_id UUID NOT NULL,
    role_key TEXT NOT NULL CHECK (role_key = 'TEAM_LEADER'),
    assigned_by UUID NOT NULL,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (team_id, user_id, role_key),
    FOREIGN KEY (team_id, user_id) REFERENCES team_members(team_id, user_id) ON DELETE CASCADE,
    FOREIGN KEY (role_key) REFERENCES roles(role_key),
    FOREIGN KEY (assigned_by) REFERENCES users(id)
);

-- Remove any invalid rows left by a partial or earlier migration before the
-- active-membership trigger is installed.
DELETE FROM team_member_roles tmr
WHERE NOT EXISTS (
    SELECT 1 FROM team_members tm
    WHERE tm.team_id = tmr.team_id
      AND tm.user_id = tmr.user_id
      AND tm.status = 'ACTIVE'
);

CREATE OR REPLACE FUNCTION enforce_active_team_leader_membership()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    membership_status TEXT;
BEGIN
    SELECT tm.status INTO membership_status
    FROM team_members tm
    WHERE tm.team_id = NEW.team_id
      AND tm.user_id = NEW.user_id
    FOR UPDATE;

    IF membership_status IS DISTINCT FROM 'ACTIVE' THEN
        RAISE EXCEPTION 'TEAM_LEADER requires an active membership';
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS enforce_active_team_leader_membership ON team_member_roles;
CREATE TRIGGER enforce_active_team_leader_membership
BEFORE INSERT OR UPDATE ON team_member_roles
FOR EACH ROW EXECUTE FUNCTION enforce_active_team_leader_membership();

CREATE OR REPLACE FUNCTION remove_inactive_team_leader_assignment()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.status IS DISTINCT FROM 'ACTIVE' THEN
        DELETE FROM team_member_roles
        WHERE team_id = NEW.team_id AND user_id = NEW.user_id;
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS remove_inactive_team_leader_assignment ON team_members;
CREATE TRIGGER remove_inactive_team_leader_assignment
AFTER UPDATE OF status ON team_members
FOR EACH ROW EXECUTE FUNCTION remove_inactive_team_leader_assignment();

CREATE TABLE IF NOT EXISTS access_settings (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    role_key TEXT NOT NULL REFERENCES roles(role_key),
    key TEXT NOT NULL,
    value JSONB NOT NULL,
    created_by UUID NOT NULL REFERENCES users(id),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, team_id, role_key, key)
);

-- Refresh definitions originally installed by 20240818_add_team_settings.sql.
-- Existing deployments must receive the same active-membership and provenance
-- policy as a database created from the current bootstrap.
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
        SELECT team_id FROM team_members
        WHERE user_id = get_inherited_settings_for_user.user_id
          AND status = 'ACTIVE'
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
    FROM user_settings_requests usr
    WHERE usr.user_id = get_inherited_settings_for_user.user_id
      AND usr.status = 'approved'
      AND (
          usr.approved_by IS NOT NULL
          OR EXISTS (
              SELECT 1
              FROM team_members tm
              JOIN team_settings ts ON ts.team_id = tm.team_id
              WHERE tm.user_id = usr.user_id
                AND tm.status = 'ACTIVE'
                AND LOWER(TRIM(ts.setting_type)) = LOWER(TRIM(usr.setting_type))
                AND LOWER(TRIM(CAST(ts.setting_value AS TEXT))) =
                    LOWER(TRIM(CAST(usr.setting_value AS TEXT)))
          )
      );
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
            SELECT team_id FROM team_members
            WHERE user_id = apply_inherited_settings_to_user.user_id
              AND status = 'ACTIVE'
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
        WHERE team_id = NEW.team_id
          AND status = 'ACTIVE';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

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
AND (
    usr.approved_by IS NOT NULL
    OR EXISTS (
        SELECT 1
        FROM team_members tm
        JOIN team_settings matching_ts ON matching_ts.team_id = tm.team_id
        WHERE tm.user_id = usr.user_id
          AND tm.status = 'ACTIVE'
          AND LOWER(TRIM(matching_ts.setting_type)) = LOWER(TRIM(usr.setting_type))
          AND LOWER(TRIM(CAST(matching_ts.setting_value AS TEXT))) =
              LOWER(TRIM(CAST(usr.setting_value AS TEXT)))
    )
)

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
WHERE tm.status = 'ACTIVE'
AND NOT EXISTS (
    SELECT 1 FROM user_settings_requests usr
    WHERE usr.user_id = tm.user_id
    AND LOWER(TRIM(usr.setting_type)) = LOWER(TRIM(ts.setting_type))
    AND LOWER(TRIM(CAST(usr.setting_value AS TEXT))) =
        LOWER(TRIM(CAST(ts.setting_value AS TEXT)))
    AND usr.status = 'approved'
    AND (
        usr.approved_by IS NOT NULL
        OR EXISTS (
            SELECT 1
            FROM team_members matching_tm
            JOIN team_settings matching_ts ON matching_ts.team_id = matching_tm.team_id
            WHERE matching_tm.user_id = usr.user_id
              AND matching_tm.status = 'ACTIVE'
              AND LOWER(TRIM(matching_ts.setting_type)) = LOWER(TRIM(usr.setting_type))
              AND LOWER(TRIM(CAST(matching_ts.setting_value AS TEXT))) =
                  LOWER(TRIM(CAST(usr.setting_value AS TEXT)))
        )
    )
);

-- Assignments that cannot be mapped without granting a role to additional
-- users are quarantined here rather than retained as global authorization.
CREATE TABLE IF NOT EXISTS legacy_access_assignment_ambiguities (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    candidate_team_ids UUID[] NOT NULL DEFAULT '{}',
    reason TEXT NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, role_id)
);

-- A component role is deterministic only when the user has exactly one active
-- team and every active member of that team already held the same direct role.
-- This prevents the conversion itself from widening access.
WITH active_memberships AS (
    SELECT user_id, array_agg(team_id ORDER BY team_id::text) AS team_ids
    FROM team_members
    WHERE status = 'ACTIVE'
    GROUP BY user_id
),
safe_team_roles AS (
    SELECT DISTINCT (am.team_ids)[1] AS team_id, ur.role_id, r.role_key
    FROM user_roles ur
    JOIN roles r ON r.id = ur.role_id AND r.component IS NOT NULL
    JOIN active_memberships am ON am.user_id = ur.user_id AND cardinality(am.team_ids) = 1
    WHERE NOT EXISTS (
        SELECT 1
        FROM team_members member
        WHERE member.team_id = (am.team_ids)[1]
          AND member.status = 'ACTIVE'
          AND NOT EXISTS (
              SELECT 1 FROM user_roles peer_role
              WHERE peer_role.user_id = member.user_id AND peer_role.role_id = ur.role_id
          )
    )
)
INSERT INTO team_roles (team_id, role_id, role_key)
SELECT team_id, role_id, role_key FROM safe_team_roles
ON CONFLICT DO NOTHING;

WITH active_memberships AS (
    SELECT user_id, array_agg(team_id ORDER BY team_id::text) AS team_ids
    FROM team_members
    WHERE status = 'ACTIVE'
    GROUP BY user_id
)
INSERT INTO team_member_roles (team_id, user_id, role_key, assigned_by)
SELECT (am.team_ids)[1], ur.user_id, 'TEAM_LEADER', ur.user_id
FROM user_roles ur
JOIN roles r ON r.id = ur.role_id AND r.role_key = 'TEAM_LEADER'
JOIN active_memberships am ON am.user_id = ur.user_id AND cardinality(am.team_ids) = 1
ON CONFLICT DO NOTHING;

WITH active_memberships AS (
    SELECT user_id, array_agg(team_id ORDER BY team_id::text) AS team_ids
    FROM team_members
    WHERE status = 'ACTIVE'
    GROUP BY user_id
),
safe_assignments AS (
    SELECT member.user_id, tr.role_id
    FROM team_roles tr
    JOIN team_members member ON member.team_id = tr.team_id AND member.status = 'ACTIVE'
    JOIN roles r ON r.id = tr.role_id AND r.component IS NOT NULL
),
unmappable AS (
    SELECT ur.user_id, ur.role_id, COALESCE(am.team_ids, '{}') AS team_ids,
        CASE
            WHEN r.role_key = 'TEAM_LEADER' THEN 'TEAM_LEADER has zero or multiple active teams'
            WHEN r.component IS NULL THEN 'role is not a static component role'
            WHEN am.team_ids IS NULL OR cardinality(am.team_ids) <> 1 THEN 'user has zero or multiple active teams'
            ELSE 'team conversion would widen access to another active member'
        END AS reason
    FROM user_roles ur
    JOIN roles r ON r.id = ur.role_id
    LEFT JOIN active_memberships am ON am.user_id = ur.user_id
    LEFT JOIN safe_assignments safe ON safe.user_id = ur.user_id AND safe.role_id = ur.role_id
    WHERE r.role_key IS DISTINCT FROM 'system admin'
      AND (am.team_ids IS NULL OR cardinality(am.team_ids) <> 1 OR safe.user_id IS NULL)
      AND NOT (
          r.role_key = 'TEAM_LEADER'
          AND am.team_ids IS NOT NULL
          AND cardinality(am.team_ids) = 1
      )
)
INSERT INTO legacy_access_assignment_ambiguities (user_id, role_id, candidate_team_ids, reason)
SELECT user_id, role_id, team_ids, reason FROM unmappable
ON CONFLICT (user_id, role_id) DO UPDATE
SET candidate_team_ids = EXCLUDED.candidate_team_ids,
    reason = EXCLUDED.reason;

-- Only system administrators remain global. Component roles are inherited
-- through team_roles and TEAM_LEADER is represented by team_member_roles.
DELETE FROM user_roles ur
USING roles r
WHERE ur.role_id = r.id AND r.role_key IS DISTINCT FROM 'system admin';

COMMIT;
