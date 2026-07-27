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
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'roles_role_key_key') THEN
        ALTER TABLE roles ADD CONSTRAINT roles_role_key_key UNIQUE (role_key);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'roles_id_role_key_key') THEN
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
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'team_members_status_check') THEN
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
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'team_roles_team_id_role_key_key') THEN
        ALTER TABLE team_roles ADD CONSTRAINT team_roles_team_id_role_key_key UNIQUE (team_id, role_key);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'team_roles_role_identity_fkey') THEN
        ALTER TABLE team_roles ADD CONSTRAINT team_roles_role_identity_fkey
            FOREIGN KEY (role_id, role_key) REFERENCES roles(id, role_key) ON DELETE CASCADE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'team_roles_component_role_check') THEN
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
