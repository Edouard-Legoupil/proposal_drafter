BEGIN;

CREATE TABLE IF NOT EXISTS resource_access_grants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_type TEXT NOT NULL CHECK (resource_type IN ('proposals', 'knowledge-cards', 'templates')),
    resource_id UUID NOT NULL,
    subject_type TEXT NOT NULL CHECK (subject_type IN ('user', 'team')),
    subject_id UUID NOT NULL,
    permissions JSONB NOT NULL,
    data_scope TEXT NOT NULL DEFAULT 'self'
        CHECK (data_scope IN ('self', 'team', 'organization', 'global')),
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (resource_type, resource_id, subject_type, subject_id)
);

CREATE INDEX IF NOT EXISTS idx_resource_access_grants_lookup
ON resource_access_grants(resource_type, resource_id);

CREATE TABLE IF NOT EXISTS resource_access_settings (
    resource_type TEXT NOT NULL CHECK (resource_type = 'templates'),
    resource_id UUID NOT NULL,
    visibility TEXT NOT NULL DEFAULT 'private'
        CHECK (visibility IN ('private', 'organization', 'restricted')),
    updated_by UUID NOT NULL REFERENCES users(id),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (resource_type, resource_id)
);

CREATE TABLE IF NOT EXISTS resource_access_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_type TEXT NOT NULL,
    resource_id UUID NOT NULL,
    action TEXT NOT NULL,
    actor_id UUID NOT NULL REFERENCES users(id),
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_resource_access_audit_lookup
ON resource_access_audit(resource_type, resource_id, created_at DESC);

COMMIT;
