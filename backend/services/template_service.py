#  Standard Library
import uuid
import json
from typing import Dict, Optional, Any, List

#  Third-Party Libraries
from fastapi import HTTPException
import logging

#  Local Application/Library Specific Imports
from backend.models.template_models import (
    TemplateCreate,
    TemplateUpdate,
    TemplateVersionCreate,
)

# Configure logging
logger = logging.getLogger(__name__)


class TemplateService:
    """Service for managing templates in the database"""

    def __init__(self, db_pool):
        self.db_pool = db_pool

    async def get_template_by_filename(self, filename: str) -> Optional[Dict[str, Any]]:
        """Get template by filename (for backward compatibility)"""
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT t.id, t.name, t.filename, t.template_type, t.description,
                       t.status, t.is_default, t.created_by, t.created_at,
                       t.updated_by, t.updated_at,
                       tv.version_number, tv.template_data, tv.status as version_status
                FROM templates t
                LEFT JOIN template_versions tv ON t.id = tv.template_id
                    AND tv.status = 'active'
                WHERE t.filename = $1
                ORDER BY tv.created_at DESC
                LIMIT 1
            """
            row = await conn.fetchrow(query, filename)
            if row:
                return dict(row)
            return None

    async def get_template_by_id(self, template_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """Get template by ID"""
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT t.id, t.name, t.filename, t.template_type, t.description,
                       t.status, t.is_default, t.created_by, t.created_at,
                       t.updated_by, t.updated_at,
                       tv.version_number, tv.template_data, tv.status as version_status
                FROM templates t
                LEFT JOIN template_versions tv ON t.id = tv.template_id
                    AND tv.status = 'active'
                WHERE t.id = $1
                ORDER BY tv.created_at DESC
                LIMIT 1
            """
            row = await conn.fetchrow(query, template_id)
            if row:
                return dict(row)
            return None

    async def get_active_template_version(self, template_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """Get the active version of a template"""
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT id, template_id, version_number, version_notes,
                       template_data, status, created_by, created_at,
                       updated_by, updated_at
                FROM template_versions
                WHERE template_id = $1 AND status = 'active'
                ORDER BY created_at DESC
                LIMIT 1
            """
            row = await conn.fetchrow(query, template_id)
            if row:
                return dict(row)
            return None

    async def get_template_donors(self, template_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Get donors associated with a template"""
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT d.id, d.name, d.account_id, d.donor_group
                FROM template_donors td
                JOIN donors d ON td.donor_id = d.id
                WHERE td.template_id = $1
                ORDER BY d.name
            """
            rows = await conn.fetch(query, template_id)
            return [dict(row) for row in rows]

    async def create_template(self, template_data: TemplateCreate, user_id: uuid.UUID) -> Dict[str, Any]:
        """Create a new template"""
        async with self.db_pool.acquire() as conn:
            try:
                async with conn.transaction():
                    # Create the template record
                    template_query = """
                        INSERT INTO templates
                        (name, filename, template_type, description, status, is_default,
                         created_by, updated_by)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $7)
                        RETURNING id, name, filename, template_type, description,
                                  status, is_default, created_by, created_at,
                                  updated_by, updated_at
                    """
                    template_row = await conn.fetchrow(
                        template_query,
                        template_data.name,
                        template_data.filename,
                        template_data.template_type,
                        template_data.description,
                        template_data.status or "draft",
                        template_data.is_default or False,
                        user_id,
                    )

                    if not template_row:
                        raise HTTPException(status_code=500, detail="Failed to create template")

                    template_id = template_row["id"]

                    # Create the first version
                    version_query = """
                        INSERT INTO template_versions
                        (template_id, version_number, version_notes, template_data,
                         status, created_by, updated_by)
                        VALUES ($1, $2, $3, $4, $5, $6, $6)
                        RETURNING id, template_id, version_number, version_notes,
                                  status, created_by, created_at, updated_by, updated_at
                    """
                    version_row = await conn.fetchrow(
                        version_query,
                        template_id,
                        "1.0",
                        template_data.version_notes,
                        json.dumps(template_data.template_data),
                        "active",
                        user_id,
                    )

                    if not version_row:
                        raise HTTPException(status_code=500, detail="Failed to create template version")

                    # Associate with donors if provided
                    if template_data.donor_ids:
                        for donor_id in template_data.donor_ids:
                            donor_query = """
                                INSERT INTO template_donors
                                (template_id, donor_id, created_by)
                                VALUES ($1, $2, $3)
                                ON CONFLICT (template_id, donor_id) DO NOTHING
                            """
                            await conn.execute(donor_query, template_id, donor_id, user_id)

                    # Log the creation
                    await self._log_template_action(
                        conn,
                        template_id,
                        version_row["id"],
                        "template_created",
                        {"initial_version": "1.0"},
                        user_id,
                    )

                    return {
                        "template": dict(template_row),
                        "version": dict(version_row),
                        "template_data": template_data.template_data,
                    }

            except Exception as e:
                logger.error(f"Error creating template: {e}")
                raise HTTPException(status_code=500, detail=f"Error creating template: {e}")

    async def update_template_metadata(
        self, template_id: uuid.UUID, update_data: TemplateUpdate, user_id: uuid.UUID
    ) -> Dict[str, Any] | None:
        """Update template metadata"""
        async with self.db_pool.acquire() as conn:
            try:
                async with conn.transaction():
                    # Build update query dynamically
                    set_clauses = []
                    values = []
                    param_index = 1

                    if update_data.name is not None:
                        set_clauses.append(f"name = ${param_index}")
                        values.append(update_data.name)
                        param_index += 1

                    if update_data.description is not None:
                        set_clauses.append(f"description = ${param_index}")
                        values.append(update_data.description)
                        param_index += 1

                    if update_data.status is not None:
                        set_clauses.append(f"status = ${param_index}")
                        values.append(update_data.status)
                        param_index += 1

                    if update_data.is_default is not None:
                        set_clauses.append(f"is_default = ${param_index}")
                        values.append(str(update_data.is_default))
                        param_index += 1

                    if not set_clauses:
                        return await self.get_template_by_id(template_id)

                    # Add updated_by
                    set_clauses.append(f"updated_by = ${param_index}")
                    values.append(str(user_id))
                    param_index += 1

                    query = f"""
                        UPDATE templates
                        SET {', '.join(set_clauses)}
                        WHERE id = ${param_index}
                        RETURNING id, name, filename, template_type, description,
                                  status, is_default, created_by, created_at,
                                  updated_by, updated_at
                    """
                    values.append(str(template_id))

                    row = await conn.fetchrow(query, *values)
                    if not row:
                        raise HTTPException(status_code=404, detail="Template not found")

                    # Log the update
                    await self._log_template_action(
                        conn,
                        template_id,
                        None,
                        "template_updated",
                        dict(update_data),
                        user_id,
                    )

                    return dict(row)

            except Exception as e:
                logger.error(f"Error updating template metadata: {e}")
                raise HTTPException(status_code=500, detail=f"Error updating template: {e}")

    async def create_template_version(
        self,
        template_id: uuid.UUID,
        version_data: TemplateVersionCreate,
        user_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """Create a new version of a template"""
        async with self.db_pool.acquire() as conn:
            try:
                async with conn.transaction():
                    # Get the latest version number
                    latest_version = await self._get_latest_version_number(conn, template_id)
                    if latest_version:
                        # Increment version number
                        parts = latest_version.split(".")
                        if len(parts) == 2:
                            new_version = f"{parts[0]}.{int(parts[1]) + 1}"
                        else:
                            new_version = f"{latest_version}.1"
                    else:
                        new_version = "1.0"

                    # Create the new version
                    query = """
                        INSERT INTO template_versions
                        (template_id, version_number, version_notes, template_data,
                         status, created_by, updated_by)
                        VALUES ($1, $2, $3, $4, $5, $6, $6)
                        RETURNING id, template_id, version_number, version_notes,
                                  status, created_by, created_at, updated_by, updated_at
                    """
                    row = await conn.fetchrow(
                        query,
                        template_id,
                        new_version,
                        version_data.version_notes,
                        json.dumps(version_data.template_data),
                        version_data.status or "draft",
                        user_id,
                    )

                    if not row:
                        raise HTTPException(status_code=500, detail="Failed to create template version")

                    # If this is an active version, deactivate previous active versions
                    if row["status"] == "active":
                        deactivate_query = """
                            UPDATE template_versions
                            SET status = 'archived', updated_by = $1
                            WHERE template_id = $2 AND id != $3 AND status = 'active'
                        """
                        await conn.execute(deactivate_query, user_id, template_id, row["id"])

                    # Log the version creation
                    await self._log_template_action(
                        conn,
                        template_id,
                        row["id"],
                        "version_created",
                        {"version_number": new_version},
                        user_id,
                    )

                    return dict(row)

            except Exception as e:
                logger.error(f"Error creating template version: {e}")
                raise HTTPException(status_code=500, detail=f"Error creating template version: {e}")

    async def get_all_templates(self) -> List[Dict[str, Any]]:
        """Get all templates with summary information"""
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT t.id, t.name, t.filename, t.template_type, t.description,
                       t.status, t.is_default, t.created_by, t.created_at,
                       t.updated_by, t.updated_at,
                       tv.version_number as latest_version,
                       tv.status as latest_version_status,
                       COUNT(d.id) as donor_count
                FROM templates t
                LEFT JOIN template_versions tv ON t.id = tv.template_id
                    AND tv.status = 'active'
                LEFT JOIN template_donors td ON t.id = td.template_id
                LEFT JOIN donors d ON td.donor_id = d.id
                GROUP BY t.id, tv.version_number, tv.status
                ORDER BY t.name
            """
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]

    async def _get_latest_version_number(self, conn, template_id: uuid.UUID) -> Optional[str]:
        """Get the latest version number for a template"""
        query = """
            SELECT version_number
            FROM template_versions
            WHERE template_id = $1
            ORDER BY
                CAST(SPLIT_PART(version_number, '.', 1) AS INTEGER) DESC,
                CAST(SPLIT_PART(version_number, '.', 2) AS INTEGER) DESC,
                created_at DESC
            LIMIT 1
        """
        row = await conn.fetchrow(query, template_id)
        return row["version_number"] if row else None

    async def _log_template_action(
        self,
        conn,
        template_id: uuid.UUID,
        version_id: Optional[uuid.UUID],
        action: str,
        action_details: Dict[str, Any],
        user_id: uuid.UUID,
    ) -> None:
        """Log a template action in the audit log"""
        query = """
            INSERT INTO template_audit_log
            (template_id, template_version_id, action, action_details, performed_by)
            VALUES ($1, $2, $3, $4, $5)
        """
        await conn.execute(query, template_id, version_id, action, json.dumps(action_details), user_id)
