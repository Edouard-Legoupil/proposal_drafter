# Template Management System

## Overview

The Proposal Drafter now includes a comprehensive template management system that stores templates in the database instead of JSON files. This provides several key benefits:

- **Version Control**: Track changes to templates over time with full audit trails
- **Access Control**: Manage who can create, edit, and publish templates
- **Easier Updates**: Non-technical users can update templates through the admin interface
- **Audit Trails**: Complete history of all template changes for compliance
- **Donor Mapping**: Flexible association of templates with multiple donors
- **Backward Compatibility**: Existing code continues to work with minimal changes

## Database Schema

### Tables

#### `templates`
Main template metadata table:

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `name` | TEXT | Template display name |
| `filename` | TEXT | Original filename (for backward compatibility) |
| `template_type` | template_type | Type of template (proposal, concept_note, knowledge_card) |
| `description` | TEXT | Template description |
| `status` | template_status | Current status (draft, active, deprecated, archived) |
| `is_default` | BOOLEAN | Whether this is the default template for its type |
| `created_by` | UUID | User who created the template |
| `created_at` | TIMESTAMPTZ | Creation timestamp |
| `updated_by` | UUID | User who last updated the template |
| `updated_at` | TIMESTAMPTZ | Last update timestamp |

#### `template_versions`
Template version history:

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `template_id` | UUID | Foreign key to templates table |
| `version_number` | TEXT | Version identifier (e.g., "1.0", "1.1") |
| `version_notes` | TEXT | Description of changes in this version |
| `template_data` | JSONB | Complete template JSON data |
| `status` | template_status | Version status |
| `created_by` | UUID | User who created this version |
| `created_at` | TIMESTAMPTZ | Creation timestamp |
| `updated_by` | UUID | User who last updated this version |
| `updated_at` | TIMESTAMPTZ | Last update timestamp |

#### `template_donors`
Mapping between templates and donors:

| Column | Type | Description |
|--------|------|-------------|
| `template_id` | UUID | Foreign key to templates table |
| `donor_id` | UUID | Foreign key to donors table |
| `created_by` | UUID | User who created the mapping |
| `created_at` | TIMESTAMPTZ | Creation timestamp |

#### `template_audit_log`
Complete audit trail of all template changes:

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `template_id` | UUID | Foreign key to templates table (nullable) |
| `template_version_id` | UUID | Foreign key to template_versions table (nullable) |
| `action` | TEXT | Action performed (e.g., "template_created", "version_created") |
| `action_details` | JSONB | Additional details about the action |
| `performed_by` | UUID | User who performed the action |
| `performed_at` | TIMESTAMPTZ | Timestamp of the action |

### Enums

#### `template_type`
```sql
('proposal', 'concept_note', 'knowledge_card')
```

#### `template_status`
```sql
('draft', 'active', 'deprecated', 'archived')
```

## API Endpoints

### Template Management

#### GET `/api/admin/templates`
Get all templates with summary information

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "string",
    "filename": "string",
    "template_type": "string",
    "description": "string",
    "status": "string",
    "is_default": boolean,
    "created_by": "uuid",
    "created_at": "datetime",
    "updated_by": "uuid",
    "updated_at": "datetime",
    "latest_version": "string",
    "latest_version_status": "string",
    "donor_count": number
  }
]
```

#### GET `/api/admin/templates/{template_id}`
Get template by ID with full details

**Response:**
```json
{
  "template": {
    "id": "uuid",
    "name": "string",
    "filename": "string",
    "template_type": "string",
    "description": "string",
    "status": "string",
    "is_default": boolean,
    "created_by": "uuid",
    "created_at": "datetime",
    "updated_by": "uuid",
    "updated_at": "datetime"
  },
  "version": {
    "id": "uuid",
    "template_id": "uuid",
    "version_number": "string",
    "version_notes": "string",
    "status": "string",
    "created_by": "uuid",
    "created_at": "datetime",
    "updated_by": "uuid",
    "updated_at": "datetime"
  },
  "template_data": {},
  "donors": [
    {
      "id": "uuid",
      "name": "string",
      "account_id": "string",
      "donor_group": "string"
    }
  ]
}
```

#### GET `/api/admin/templates/by-filename/{filename}`
Get template by filename (for backward compatibility)

**Response:** Same as GET by ID

#### POST `/api/admin/templates`
Create a new template

**Request:**
```json
{
  "name": "string",
  "filename": "string",
  "template_type": "string",
  "description": "string",
  "template_data": {},
  "version_notes": "string",
  "donor_ids": ["uuid"]
}
```

**Response:**
```json
{
  "message": "string",
  "template": {},
  "version": {}
}
```

#### PUT `/api/admin/templates/{template_id}`
Update template metadata

**Request:**
```json
{
  "name": "string",
  "description": "string",
  "status": "string",
  "is_default": boolean
}
```

**Response:** Template object

#### POST `/api/admin/templates/{template_id}/versions`
Create a new version of a template

**Request:**
```json
{
  "version_notes": "string",
  "template_data": {}
}
```

**Response:** Version object

## Migration from File System

### Import Script

Run the import script to migrate existing JSON templates to the database:

```bash
python backend/scripts/import_templates_to_db.py
```

### How It Works

1. **Scans template directories**: Looks in `backend/templates/proposal_template/`, `backend/templates/concept_note_template/`, and `backend/templates/`

2. **Reads JSON files**: Parses each template JSON file

3. **Creates database records**: 
   - Creates a record in the `templates` table
   - Creates version 1.0 in the `template_versions` table
   - Creates donor mappings in `template_donors` table if donors are specified

4. **Preserves compatibility**: Maintains original filenames for backward compatibility

### Important Notes

- The script will **not** overwrite existing templates in the database
- It creates a system user (UUID `00000000-0000-0000-0000-000000000001`) as the creator
- All imported templates are marked as `active` status
- Templates without specific donors are marked as `is_default = true`

## Backward Compatibility

### Template Loading

The `load_proposal_template()` function in `backend/core/config.py` has been updated to:

1. **First try database**: Attempts to load template from database
2. **Fallback to files**: If database loading fails or template not found, falls back to file system
3. **Maintains same interface**: Returns the same data structure as before

### Existing Code

All existing code that uses `load_proposal_template()` will continue to work without modification. The function signature and return value are unchanged.

### Configuration

The `use_db_first` parameter (default `True`) controls the behavior:

```python
# Use database first, then fallback to files (default)
template = load_proposal_template("template.json")

# Force file system only
template = load_proposal_template("template.json", use_db_first=False)
```

## Usage Examples

### Creating a New Template

```python
from backend.services.template_service import TemplateService
from backend.models.template_models import TemplateCreate

service = TemplateService(db_pool)

template_data = {
    "template_name": "New Proposal Template",
    "template_type": "proposal",
    "description": "A new template for modern proposals",
    "donors": ["New Donor Inc"],
    "sections": [
        {
            "section_name": "Executive Summary",
            "instructions": "Write a compelling executive summary",
            "word_limit": 300
        }
    ]
}

create_request = TemplateCreate(
    name="New Proposal Template",
    filename="new_proposal_template.json",
    template_type="proposal",
    description="A new template for modern proposals",
    template_data=template_data,
    version_notes="Initial version with modern sections",
    donor_ids=[donor_id]  # UUID of donor
)

result = await service.create_template(create_request, current_user_id)
```

### Updating Template Metadata

```python
from backend.models.template_models import TemplateUpdate

update_request = TemplateUpdate(
    name="Updated Template Name",
    description="Updated description with more details",
    status="active"
)

updated_template = await service.update_template_metadata(
    template_id, 
    update_request, 
    current_user_id
)
```

### Creating a New Version

```python
from backend.models.template_models import TemplateVersionCreate

# Load existing template
existing_template = await service.get_template_by_id(template_id)

# Modify the template data
updated_data = existing_template["template_data"]
updated_data["sections"].append({
    "section_name": "New Section",
    "instructions": "New section instructions",
    "word_limit": 500
})

# Create new version
version_request = TemplateVersionCreate(
    version_notes="Added new section for enhanced proposals",
    template_data=updated_data
)

new_version = await service.create_template_version(
    template_id, 
    version_request, 
    current_user_id
)
```

## Security Considerations

### Access Control

- All template management endpoints require authentication
- Use the existing role-based access control system
- Consider adding specific permissions for template management

### Data Validation

- All template data is validated using Pydantic models
- JSON schema validation is performed on template_data
- Input sanitization is applied to prevent injection attacks

### Audit Logging

- All template changes are logged in `template_audit_log`
- Includes who made the change and when
- Stores before/after states for critical changes

## Performance Considerations

### Caching

Consider implementing caching for frequently accessed templates:

```python
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache

@cache(expire=3600)  # Cache for 1 hour
async def get_template_by_filename(filename: str):
    # ... existing implementation
```

### Database Indexes

The migration creates appropriate indexes for performance:

- `idx_templates_name`: For template name searches
- `idx_templates_type`: For filtering by template type
- `idx_template_versions_template_id`: For version history queries
- `idx_template_donors_template_id`: For donor-template mapping queries

## Troubleshooting

### Template Not Found

1. **Check database**: Verify the template exists in the `templates` table
2. **Check filename**: Ensure the filename matches exactly
3. **Check status**: Template must have `status = 'active'` to be returned
4. **Check fallback**: If using `use_db_first=True`, verify file system fallback works

### Version Conflicts

1. **Check active versions**: Only one version per template can be `active`
2. **Review audit log**: Check `template_audit_log` for recent changes
3. **Manual resolution**: Update version statuses if needed

### Performance Issues

1. **Check indexes**: Ensure all indexes are created
2. **Review queries**: Optimize complex queries with EXPLAIN ANALYZE
3. **Consider caching**: Implement caching for frequently accessed templates

## Future Enhancements

### Template Validation

- Add JSON schema validation for template structure
- Implement pre-submit validation hooks
- Add template linting tools

### Advanced Versioning

- Support semantic versioning
- Add version comparison tools
- Implement version diffing

### Template Sharing

- Add template export/import functionality
- Implement template marketplace
- Add template cloning

### Enhanced Editor

- Build visual template editor
- Add preview functionality
- Implement collaborative editing

## Database Maintenance

### Regular Backups

Ensure templates are included in regular database backups:

```bash
pg_dump -U username -d database_name -t templates -t template_versions -t template_donors -t template_audit_log > template_backup.sql
```

### Monitoring

Add monitoring for template usage:

```sql
-- Templates by usage
SELECT t.id, t.name, COUNT(*) as usage_count
FROM templates t
JOIN proposals p ON t.filename = p.template_name
GROUP BY t.id, t.name
ORDER BY usage_count DESC;

-- Recent template changes
SELECT t.name, a.action, a.performed_at, u.name as user_name
FROM template_audit_log a
JOIN templates t ON a.template_id = t.id
JOIN users u ON a.performed_by = u.id
ORDER BY a.performed_at DESC
LIMIT 50;
```

### Cleanup

Periodically archive old template versions:

```sql
-- Archive old draft versions
UPDATE template_versions
SET status = 'archived'
WHERE status = 'draft'
AND created_at < CURRENT_TIMESTAMP - INTERVAL '6 months';

-- Remove very old archived versions
DELETE FROM template_versions
WHERE status = 'archived'
AND created_at < CURRENT_TIMESTAMP - INTERVAL '2 years';
```