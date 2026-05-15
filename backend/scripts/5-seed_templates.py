#!/usr/bin/env python3
"""
Template Synchronization Script
==============================

This script FULLY SYNCHRONIZES template files on disk with the database.
It handles:
- Adding new templates from disk to DB
- Updating existing templates when files change
- Optionally removing templates from DB that no longer exist on disk
- Flushing all template data for a fresh start

Usage:
    python 5-seed_templates.py [--dry-run] [--verbose] [--remove-deprecated] [--flush]

    --dry-run: Show what would be done without making changes
    --verbose: Show detailed information about each template
    --remove-deprecated: Remove templates from DB that don't exist on disk
    --flush: Flush all template data from DB before syncing (fresh start)
"""

import os
import json
import uuid
import hashlib
import sys
from datetime import datetime
import argparse
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import register_uuid

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
register_uuid()

# Load environment variables once at the top level
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))


class TemplateSynchronizer:
    """Handles full two-way synchronization between file system and database"""

    def __init__(
        self,
        dry_run: bool = False,
        verbose: bool = False,
        remove_deprecated: bool = False,
        flush: bool = False,
        system_user_id: str = "00000000-0000-0000-0000-000000000001",
    ):
        self.dry_run = dry_run
        self.verbose = verbose
        self.remove_deprecated = remove_deprecated
        self.flush = flush
        self.system_user_id = system_user_id
        self.templates_added = 0
        self.templates_updated = 0
        self.templates_removed = 0
        self.templates_unchanged = 0
        self.errors = []
        self._conn = None

    def _get_connection(self):
        """Get or create database connection"""
        if self._conn is None or self._conn.closed:
            try:
                db_username = os.getenv("DB_USERNAME", "").strip('"')
                db_password = os.getenv("DB_PASSWORD")
                db_name = os.getenv("DB_NAME")
                db_host = os.getenv("DB_HOST")
                db_port = os.getenv("DB_PORT")

                self._conn = psycopg2.connect(
                    dbname=db_name,
                    user=db_username,
                    password=db_password,
                    host=db_host,
                    port=db_port,
                )
            except Exception as e:
                self.log(f"Failed to connect to database: {e}", "error")
                return None
        return self._conn

    def log(self, message: str, level: str = "info"):
        """Log messages with different levels"""
        if self.verbose or level in ["error", "warning", "success"]:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] [{level.upper()}] {message}")

    def calculate_checksum(self, filepath: str) -> Optional[str]:
        """Calculate MD5 checksum of a file for change detection"""
        try:
            with open(filepath, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            self.log(f"Error calculating checksum for {filepath}: {e}", "error")
            return None

    def find_template_files(self) -> List[Dict[str, Any]]:
        """Find all JSON template files in the templates directory"""
        templates = []

        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        templates_dir = os.path.join(backend_dir, "templates")

        if not os.path.exists(templates_dir):
            self.log(f"Templates directory not found: {templates_dir}", "error")
            return []

        for root, dirs, files in os.walk(templates_dir):
            for file in files:
                if file.endswith(".json"):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            template_data = json.load(f)

                        # Determine template type based on directory
                        if "proposal_template" in root:
                            template_type = "proposal"
                        elif "concept_note_template" in root:
                            template_type = "concept_note"
                        else:
                            template_type = "knowledge_card"

                        checksum = self.calculate_checksum(filepath)

                        templates.append(
                            {
                                "filename": file,
                                "filepath": filepath,
                                "template_type": template_type,
                                "data": template_data,
                                "checksum": checksum,
                            }
                        )

                        if self.verbose:
                            self.log(f"Found template: {file} (type: {template_type})")

                    except json.JSONDecodeError as e:
                        self.log(f"Invalid JSON in {file}: {e}", "warning")
                        self.errors.append(f"JSON error in {file}: {e}")
                    except Exception as e:
                        self.log(f"Error reading {file}: {e}", "error")
                        self.errors.append(f"Read error in {file}: {e}")

        return templates

    def get_template_key(self, filename: str) -> str:
        """Generate a consistent template key from filename"""
        name = os.path.splitext(filename)[0]
        return name.lower().replace(" ", "_").replace("-", "_")

    def get_registry_from_db(self, template_key: str, template_type: str) -> Optional[Dict]:
        """Get template_registry entry by template_key and type"""
        conn = self._get_connection()
        if not conn:
            return None

        try:
            with conn.cursor() as cur:
                query = """
                    SELECT id, template_name, description
                    FROM template_registry
                    WHERE template_key = %s AND template_type = %s
                    LIMIT 1
                """
                cur.execute(query, (template_key, template_type))
                row = cur.fetchone()
                if row:
                    return {
                        "id": str(row[0]),
                        "template_name": row[1],
                        "description": row[2],
                    }
        except Exception as e:
            self.log(f"Error fetching registry entry: {e}", "error")
            self.errors.append(f"DB fetch error: {e}")
        return None

    def get_latest_version(self, registry_id: str) -> Optional[Dict]:
        """Get the latest version for a template registry"""
        conn = self._get_connection()
        if not conn:
            return None

        try:
            with conn.cursor() as cur:
                # Try ordering by integer version_number first
                # But handle both TEXT and INTEGER types
                query = """
                    SELECT id, version_number, template_data
                    FROM template_versions
                    WHERE template_registry_id = %s
                    ORDER BY
                        CASE WHEN version_number ~ '^[0-9]+$'
                             THEN version_number::integer
                             ELSE 0 END DESC,
                        created_at DESC
                    LIMIT 1
                """
                cur.execute(query, (registry_id,))
                row = cur.fetchone()
                if row:
                    return {
                        "id": str(row[0]),
                        "version_number": row[1],
                        "template_data": row[2],
                    }
        except Exception as e:
            self.log(f"Error fetching latest version: {e}", "error")
        return None

    def get_all_registries_from_db(self) -> Dict[str, Dict]:
        """Get all template_registry entries"""
        registries = {}
        conn = self._get_connection()
        if not conn:
            return registries

        try:
            with conn.cursor() as cur:
                query = "SELECT id, template_key, template_name, template_type FROM template_registry"
                cur.execute(query)
                for row in cur.fetchall():
                    registries[row[1]] = {
                        "id": str(row[0]),
                        "template_key": row[1],
                        "template_name": row[2],
                        "template_type": row[3],
                    }
        except Exception as e:
            self.log(f"Error fetching all registries: {e}", "error")
        return registries

    def flush_templates(self) -> bool:
        """Remove all template data from database for a fresh sync"""
        if self.dry_run:
            self.log("[DRY RUN] Would flush all template data from database", "info")
            return True

        if not self.flush:
            return True

        self.log("Flushing all template data from database...", "warning")
        conn = self._get_connection()
        if not conn:
            return False

        try:
            with conn.cursor() as cur:
                # Delete in proper order for foreign key constraints
                # First delete child tables, then parent tables
                cur.execute("DELETE FROM template_versions")
                cur.execute("DELETE FROM template_donors")
                cur.execute("DELETE FROM template_audit_log")
                cur.execute("DELETE FROM template_registry")
                conn.commit()
                self.log("Successfully flushed all template data", "success")
                return True
        except Exception as e:
            if conn:
                conn.rollback()
            self.log(f"Error flushing templates: {e}", "error")
            self.errors.append(f"Flush error: {e}")
            return False

    def get_next_version_number(self, registry_id: str) -> str:
        """Get the next version number for a registry"""
        latest = self.get_latest_version(registry_id)
        if latest and latest["version_number"]:
            try:
                # Handle both integer and version string formats
                if "." in str(latest["version_number"]):
                    version_num = float(latest["version_number"])
                else:
                    version_num = int(latest["version_number"])
                return str(int(version_num) + 1)
            except ValueError:
                return "2"
        return "1"

    def create_registry(
        self,
        template_key: str,
        template_name: str,
        template_type: str,
        description: str = "",
    ) -> Optional[str]:
        """Create a new template_registry entry"""
        if self.dry_run:
            self.log(f"[DRY RUN] Would create registry: {template_key}", "info")
            return str(uuid.uuid4())

        conn = self._get_connection()
        if not conn:
            return None

        try:
            with conn.cursor() as cur:
                registry_id = str(uuid.uuid4())
                query = """
                    INSERT INTO template_registry
                    (id, template_key, template_name, template_type,
                     description, owner_user_id, active, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    RETURNING id
                """
                cur.execute(
                    query,
                    (
                        registry_id,
                        template_key,
                        template_name,
                        template_type,
                        description,
                        self.system_user_id,
                        True,
                    ),
                )
                conn.commit()
                result = cur.fetchone()
                self.log(
                    f"Created registry: {template_key} (type: {template_type})",
                    "success",
                )
                return str(result[0]) if result else registry_id
        except Exception as e:
            if conn:
                conn.rollback()
            self.log(f"Error creating registry {template_key}: {e}", "error")
            self.errors.append(f"Registry creation error: {e}")
            return None

    def create_version(
        self,
        registry_id: str,
        template_data: Dict,
        version_number: str,
        environment: str = "uat",
    ) -> Optional[str]:
        """Create a new template_version entry"""
        if self.dry_run:
            self.log(f"[DRY RUN] Would create version for registry {registry_id}", "info")
            return str(uuid.uuid4())

        conn = self._get_connection()
        if not conn:
            return None

        version_id = str(uuid.uuid4())

        try:
            with conn.cursor() as cur:
                # Use the same UUID for template_id as registry_id as placeholder
                # (template_id is required but templates table has unique constraint issues)
                query = """
                    INSERT INTO template_versions
                    (id, template_registry_id, template_id, version_label, version_number,
                     environment, status, template_content, template_data,
                     release_notes, created_by, updated_by, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, 'active', %s, %s, %s, %s, %s, NOW(), NOW())
                    RETURNING id
                """
                cur.execute(
                    query,
                    (
                        version_id,
                        registry_id,
                        registry_id,  # Use registry_id as placeholder for template_id
                        f"v{version_number}",
                        version_number,
                        environment,
                        json.dumps(template_data),
                        json.dumps(template_data),
                        "Auto synced from filesystem",
                        self.system_user_id,
                        self.system_user_id,
                    ),
                )
                conn.commit()
                self.log(
                    f"Created version {version_number} for registry {registry_id}",
                    "success",
                )
                return version_id
        except Exception as e:
            if conn:
                conn.rollback()
            self.log(f"Error creating version: {e}", "error")
            self.errors.append(f"Version creation error: {e}")
            return None

    def update_version(self, version_id: str, template_data: Dict) -> bool:
        """Update an existing template version with new content"""
        if self.dry_run:
            self.log(f"[DRY RUN] Would update version {version_id}", "info")
            return True

        conn = self._get_connection()
        if not conn:
            return False

        try:
            with conn.cursor() as cur:
                query = """
                    UPDATE template_versions
                    SET template_content = %s,
                        template_data = %s,
                        version_notes = %s,
                        updated_by = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """
                cur.execute(
                    query,
                    (
                        json.dumps(template_data),
                        json.dumps(template_data),
                        f"Auto-synced from filesystem at {datetime.now().isoformat()}",
                        self.system_user_id,
                        version_id,
                    ),
                )
                conn.commit()
                self.log(f"Updated version {version_id}", "success")
                return True
        except Exception as e:
            if conn:
                conn.rollback()
            self.log(f"Error updating version {version_id}: {e}", "error")
            self.errors.append(f"Version update error: {e}")
            return False

    def remove_registry(self, registry_id: str, template_key: str) -> bool:
        """Remove a template registry and all its versions"""
        if self.dry_run:
            self.log(
                f"[DRY RUN] Would remove registry {template_key} ({registry_id})",
                "info",
            )
            return True

        conn = self._get_connection()
        if not conn:
            return False

        try:
            with conn.cursor() as cur:
                # Soft delete
                query = """
                    UPDATE template_registry
                    SET active = FALSE,
                        updated_by = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """
                cur.execute(query, (self.system_user_id, registry_id))
                conn.commit()
                self.log(f"Deactivated registry {template_key} ({registry_id})", "success")
                return True
        except Exception as e:
            if conn:
                conn.rollback()
            self.log(f"Error removing registry {template_key}: {e}", "error")
            self.errors.append(f"Registry removal error: {e}")
            return False

    def synchronize_template(self, file_template: Dict) -> bool:
        """Synchronize a single template file with the database"""
        filename = file_template["filename"]
        template_type = file_template["template_type"]
        template_data = file_template["data"]

        template_key = self.get_template_key(filename)
        template_name = template_data.get("template_name", filename.replace(".json", ""))
        description = template_data.get("description", f"Template from {filename}")

        # Check if registry exists
        registry = self.get_registry_from_db(template_key, template_type)

        if not registry:
            # Create new registry
            self.log(f"Creating new registry for {filename}")
            registry_id = self.create_registry(template_key, template_name, template_type, description)
            if not registry_id:
                return False

            # Create initial version with integer version number
            version_id = self.create_version(registry_id, template_data, "1", "uat")
            if version_id:
                self.templates_added += 1
                return True
            return False
        else:
            # Registry exists, check latest version
            latest_version = self.get_latest_version(registry["id"])

            if not latest_version:
                # No versions exist, create one
                self.log(f"Creating first version for {filename}")
                version_id = self.create_version(registry["id"], template_data, "1", "uat")
                if version_id:
                    self.templates_added += 1
                return version_id is not None

            # For now, always update (we can't compare checksums without storing them)
            self.log(f"Updating template {filename}")
            if self.update_version(latest_version["id"], template_data):
                self.templates_updated += 1
                return True
            return False

    def remove_deprecated_templates(self, current_files: List[Dict]) -> None:
        """Remove templates from DB that don't exist in current files"""
        if not self.remove_deprecated:
            return

        self.log("Checking for deprecated templates...", "info")

        db_registries = self.get_all_registries_from_db()

        # Build set of current template keys
        current_keys = set()
        for tpl in current_files:
            key = self.get_template_key(tpl["filename"])
            current_keys.add(key)

        # Find deprecated
        deprecated = []
        for key, registry in db_registries.items():
            if key not in current_keys:
                deprecated.append(registry)

        if not deprecated:
            self.log("No deprecated templates found", "info")
            return

        self.log(f"Found {len(deprecated)} deprecated templates", "warning")

        for registry in deprecated:
            if self.remove_registry(registry["id"], registry["template_key"]):
                self.templates_removed += 1

    def run(self):
        """Run the full synchronization process"""
        self.log("Starting template synchronization process...")

        if self.dry_run:
            self.log("Running in DRY-RUN mode - no changes will be made to the database")
        if self.remove_deprecated:
            self.log("Will REMOVE deprecated templates from database")
        if self.flush:
            self.log("Will FLUSH all template data before syncing")
            if not self.flush_templates():
                self.log("Flush failed, aborting", "error")
                return False

        # Find all template files
        templates = self.find_template_files()

        if not templates:
            self.log("No template files found to sync", "warning")
            return False

        self.log(f"Found {len(templates)} template files to process")

        # Synchronize each template
        for template in templates:
            if self.dry_run:
                self.log(f"[DRY RUN] Would sync: {template['filename']}")
                self.templates_added += 1
            else:
                self.synchronize_template(template)

        # Check for deprecated templates
        self.remove_deprecated_templates(templates)

        # Summary
        self.log("\n" + "=" * 60)
        self.log("TEMPLATE SYNCHRONIZATION SUMMARY")
        self.log("=" * 60)
        self.log(f"Templates processed: {len(templates)}")
        self.log(f"Templates added: {self.templates_added}")
        self.log(f"Templates updated: {self.templates_updated}")
        self.log(f"Templates removed: {self.templates_removed}")
        self.log(f"Errors encountered: {len(self.errors)}")

        if self.errors:
            self.log("\nErrors:")
            for error in self.errors[:5]:
                self.log(f"  - {error}")
            if len(self.errors) > 5:
                self.log(f"  - ... and {len(self.errors) - 5} more errors")

        self.log("\nSynchronization process completed!")
        return True


def main():
    """Main entry point for the synchronization script"""
    parser = argparse.ArgumentParser(
        description="Synchronize template files with the database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed information about each template",
    )
    parser.add_argument(
        "--remove-deprecated",
        action="store_true",
        help="Remove templates from DB that no longer exist on disk",
    )
    parser.add_argument(
        "--flush",
        action="store_true",
        help="Flush all template data from DB before syncing (fresh start)",
    )
    parser.add_argument(
        "--system-user-id",
        default="00000000-0000-0000-0000-000000000001",
        help="UUID to record as created_by/updated_by (default system user)",
    )

    args = parser.parse_args()

    synchronizer = TemplateSynchronizer(
        dry_run=args.dry_run,
        verbose=args.verbose,
        remove_deprecated=args.remove_deprecated,
        flush=args.flush,
        system_user_id=args.system_user_id,
    )

    try:
        success = synchronizer.run()
        return 0 if success else 1
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
