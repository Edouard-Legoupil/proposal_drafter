# Database Migration 007: database-setup.sql → database-setup2.sql

**Migration ID:** 007  
**Created:** April 2025  
**Status:** Ready for Deployment  
**Author:** Mistral Vibe (with Edouard Legoupil)  

---

## Overview

This migration upgrades the database schema from the initial `database-setup.sql` to the current production schema found in `database-setup2.sql`. The `database-setup2.sql` file is a pg_dump output from a live production database that has evolved with additional features.

---

## Migration Files

- **Migration Script:** `db/migrations/007_migrate_to_database_setup2.sql`
- **Current Schema:** `db/database-setup2.sql` (pg_dump from production)
- **Previous Schema:** `db/database-setup.sql` (initial schema)

---

## Changes Summary

### 1. New Enum Types (6)

| Enum Name | Values | Purpose |
|-----------|--------|---------|
| `managed_template_type` | proposal, knowledge_card | Template type classification |
| `qualification_decision` | qualified, conditionally_qualified, disqualified, suspended, rolled_back | Qualification outcome |
| `qualification_rule_result` | pass, fail, waived, not_applicable | Rule evaluation result |
| `qualification_run_status` | draft, collecting_evidence, evaluating, pending_signoff, approved, rejected, cancelled | Qualification workflow status |
| `release_environment` | uat, prod | Deployment environment |
| `run_status` | drafting, completed, failed, cancelled | Artifact generation status |

### 2. New Tables (8)

| Table Name | Purpose | Key Fields |
|------------|---------|------------|
| `artifact_runs` | Telemetry tracking for all artifact generation | artifact_type, artifact_id, run_status, agents_executed, tokens_input/output, latency metrics |
| `template_registry` | Central registry for all templates | template_key, template_type, display_name, description |
| `template_release_history` | Track template releases by environment | template_registry_id, version_number, environment, version_notes |
| `qualification_scenarios` | Define qualification test scenarios | name, description, scenario_type, is_active |
| `qualification_waivers` | Track waived qualification rules | qualification_run_id, rule_id, waiver_reason, expires_at |
| `template_qualification_signoffs` | Approval signoffs for qualification runs | qualification_run_id, signed_by, signoff_decision, comments, signature_data |
| `template_qualification_run_scenarios` | Link scenarios to qualification runs | qualification_run_id, scenario_id, status, results |
| `qualification_evidence_items` | Store evidence for qualification | qualification_run_id, rule_id, evidence_type, evidence_data |

### 3. New Columns in Existing Tables

#### donor_template_requests
- `template_type TEXT DEFAULT 'proposal'`
- `updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP`
- `donor_ids UUID[]` (array of UUIDs for multiple donors)

#### donor_template_comments
- `section_name TEXT`
- `template_name TEXT`
- `type_of_comment TEXT DEFAULT 'Donor Template'`
- `author_response TEXT`
- `author_response_by TEXT`
- `severity TEXT`

#### proposals
- `template_registry_id UUID` (Foreign key to template_registry)
- `template_version_id UUID` (Foreign key to template_versions)

#### knowledge_cards
- `template_registry_id UUID` (Foreign key to template_registry)
- `template_version_id UUID` (Foreign key to template_versions)

Note: Some Foreign Key constraints may be missing in database-setup2.sql as pg_dump doesn't always preserve them. These should be added manually if needed.

### 4. New Sequences

- `roles_id_seq` - Sequence for the roles.id SERIAL field

### 5. New Indexes

- `idx_artifact_runs_artifact_id` - Index on artifact_runs(artifact_id)
- `idx_artifact_runs_artifact_type` - Index on artifact_runs(artifact_type)
- `idx_artifact_runs_user_id` - Index on artifact_runs(user_id)
- `idx_artifact_runs_run_status` - Index on artifact_runs(run_status)
- `idx_template_registry_key_type` - Index on template_registry(template_key, template_type)
- `idx_template_registry_created_at` - Index on template_registry(created_at)
- `idx_template_versions_registry_id` - Index on template_versions(template_registry_id)
- `idx_template_qualification_runs_run_id` - Index on template_qualification_runs(id)
- `idx_qualification_rules_rule_set_id` - Index on qualification_rules(rule_set_id)
- `idx_qualification_rule_sets_template_type` - Index on qualification_rule_sets(template_type)

---

## Differences in Table Definitions

### 1. knowledge_cards

**database-setup.sql:**
```sql
CREATE TABLE IF NOT EXISTS knowledge_cards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_name TEXT,
    type TEXT,  -- <= Has type column
    summary TEXT NOT NULL,
    generated_sections JSONB,
    is_accepted BOOLEAN DEFAULT FALSE,
    status proposal_status DEFAULT 'draft',
    donor_id UUID REFERENCES donors(id) ON DELETE SET NULL,
    outcome_id UUID REFERENCES outcomes(id) ON DELETE SET NULL,
    field_context_id UUID REFERENCES field_contexts(id) ON DELETE SET NULL,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID NOT NULL REFERENCES users(id),
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT one_link_only CHECK (...)
);
```

**database-setup2.sql:**
```sql
CREATE TABLE public.knowledge_cards (
    id uuid NOT NULL,
    template_name text,
    -- No type column
    summary text NOT NULL,
    generated_sections jsonb,
    is_accepted boolean DEFAULT false,
    status public.proposal_status DEFAULT 'draft',
    donor_id uuid,
    outcome_id uuid,
    field_context_id uuid,
    created_by uuid NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_by uuid NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    template_registry_id uuid,  -- <= NEW
    template_version_id uuid,   -- <= NEW
    CONSTRAINT knowledge_cards_pkey PRIMARY KEY (id)
);
```

**Migration Note:** The `type TEXT` column is missing in database-setup2.sql. This may be intentional (obsolete) or an oversight. The migration script does NOT remove this column to preserve backward compatibility.

### 2. proposals

**database-setup.sql:**
```sql
CREATE TABLE IF NOT EXISTS proposals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    template_name VARCHAR(255) DEFAULT 'proposal_template_unhcr.json',
    ...
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID NOT NULL REFERENCES users(id),
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

**database-setup2.sql:**
```sql
CREATE TABLE public.proposals (
    ...
    template_registry_id uuid,  -- <= NEW
    template_version_id uuid,   -- <= NEW
    -- Also has slightly different default: 'unhcr_proposal_template.json'
);
```

---

## Known Issues

### 1. Case Sensitivity in Table Names
- database-setup.sql uses lowercase table names without schema prefix
- database-setup2.sql uses "public." schema prefix and lowercase
- This is a cosmetic difference and doesn't affect functionality

### 2. Missing ON DELETE CASCADE Constraints
- database-setup2.sql (from pg_dump) doesn't always include CASCADE clauses
- The migration script preserves the original constraints from database-setup.sql

### 3. Type Column in knowledge_cards
- database-setup.sql has a `type TEXT` column
- database-setup2.sql doesn't have this column
- The migration script does NOT alter this to preserve backward compatibility

### 4. Template References
- database-setup.sql: template_versions references templates(id)
- database-setup2.sql: template_versions should reference template_registry(id)
- The migration script notes this but doesn't change it automatically (requires data migration)

---

## Migration Steps

### Step 1: Backup Current Database
```bash
# Create a backup dump before migration
pg_dump -U postgres -h localhost -p 5432 -Fc -f backup_before_migration.dump proposalgen
```

### Step 2: Apply Initial Schema (if not already applied)
```bash
psql -U postgres -h localhost -p 5432 -d proposalgen -f db/database-setup.sql
```

### Step 3: Apply Migration Script
```bash
psql -U postgres -h localhost -p 5432 -d proposalgen -f db/migrations/007_migrate_to_database_setup2.sql
```

### Step 4: Verify Migration
```bash
# Check new tables exist
psql -U postgres -h localhost -p 5432 -d proposalgen -c "\dt"

# Check new enums exist
psql -U postgres -h localhost -p 5432 -d proposalgen -c "\dT"

# Check new columns exist
psql -U postgres -h localhost -p 5432 -d proposalgen -c "\d artifact_runs"
```

---

## Rollback Procedure

If the migration fails or causes issues, restore from the backup:

```bash
# Drop and recreate database (or use --clean with pg_restore)
createdb -U postgres proposalgen_rolled_back
pg_restore -U postgres -h localhost -p 5432 -d proposalgen_rolled_back backup_before_migration.dump
```

---

## Testing

The migration script has been designed to be idempotent (can be run multiple times safely). Test with:

```bash
# Run migration once
psql -f db/migrations/007_migrate_to_database_setup2.sql proposalgen

# Run migration again (should succeed with no errors)
psql -f db/migrations/007_migrate_to_database_setup2.sql proposalgen
```

---

## Dependent Files

- **db/database-setup.sql** - Original schema (required before migration)
- **db/migrations/007_migrate_to_database_setup2.sql** - This migration script
- **db/database-setup2.sql** - Target schema (for reference)

---

## Future Migrations

After this migration, use the numbered migration files in the `db/migrations/` directory:
- 001_*.sql
- 002_*.sql
- ...
- 007_migrate_to_database_setup2.sql (this file)
- 008_*.sql (next migration)

---

## Contact

For questions about this migration:
- **Author:** Edouard Legoupil (legoupil@unhcr.org)
- **Technical Support:** Mistral Vibe (vibe@mistral.ai)

---

*Document Version: 1.0*  
*Last Updated: April 2025*  
