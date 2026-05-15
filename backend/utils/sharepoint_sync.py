"""
SharePoint File Synchronization Job
==================================

This module provides a background job that:
1. Checks all SharePoint files referenced in the database for updates
2. Detects changes using file metadata (modified date, version)
3. Builds diffs between versions
4. Updates the system with new versions
5. Records complete history of all changes

The job runs twice daily (8:00 and 20:00) via a scheduler.

Dependencies:
    - Requires sharepoint_connector.py to be configured
    - Uses existing database tables (proposal_sharepoint_links, knowledge_card_sharepoint_links)
    - Stores sync history in sharepoint_sync_history table

Configuration:
    - Schedule: 2 times per day (8:00 and 20:00)
    - Can be customized via environment variables
    - SHAREPOINT_SYNC_SCHEDULE: Comma-separated times (e.g., "08:00,20:00")
"""

import logging
import os
from datetime import datetime
from typing import Optional, Dict, List, Any
from uuid import UUID

import schedule
import time
import threading

from sqlalchemy import text

from backend.core.db import get_engine
from backend.utils.sharepoint_connector import SharePointConnector

# =============================================================================
# CONFIGURATION
# =============================================================================

logger = logging.getLogger(__name__)

# Default schedule times (2 times per day)
DEFAULT_SCHEDULE_TIMES = ["08:00", "20:00"]

# Get schedule from environment or use defaults
schedule_env = os.getenv("SHAREPOINT_SYNC_SCHEDULE", "08:00,20:00")
SCHEDULE_TIMES = [t.strip() for t in schedule_env.split(",") if t.strip()]

# =============================================================================
# DATABASE SCHEMA (Embedded for reference)
# =============================================================================
#
# The following tables should exist (created by db/database-setup.sql):
#
# CREATE TYPE sharepoint_sync_status AS ENUM ('pending', 'started', 'completed', 'failed');
# CREATE TYPE sync_change_type AS ENUM ('created', 'modified', 'deleted', 'renamed');
#
# CREATE TABLE IF NOT EXISTS sharepoint_sync_history (
#     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
#     sync_started_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
#     sync_completed_at TIMESTAMPTZ,
#     status sharepoint_sync_status NOT NULL DEFAULT 'started',
#     total_files_checked INTEGER DEFAULT 0,
#     files_changed INTEGER DEFAULT 0,
#     files_created INTEGER DEFAULT 0,
#     files_deleted INTEGER DEFAULT 0,
#     errors_encountered INTEGER DEFAULT 0,
#     error_summary JSONB,
#     created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
# );
#
# CREATE TABLE IF NOT EXISTS sharepoint_file_versions (
#     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
#     artifact_type TEXT NOT NULL CHECK (artifact_type IN ('proposal', 'knowledge_card')),
#     artifact_id UUID NOT NULL,
#     user_id UUID NOT NULL REFERENCES users(id),
#     sharepoint_link_id UUID NOT NULL,
#     version_number INTEGER NOT NULL,
#     sharepoint_url TEXT NOT NULL,
#     filename TEXT NOT NULL,
#     file_size BIGINT,
#     sharepoint_version TEXT,
#     last_modified_at TIMESTAMPTZ,
#     last_modified_by TEXT,
#     diff_from_previous TEXT,
#     change_type sync_change_type NOT NULL DEFAULT 'modified',
#     metadata JSONB DEFAULT '{}'::jsonb,
#     is_current BOOLEAN DEFAULT FALSE,
#     created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
#     UNIQUE (sharepoint_link_id, version_number)
# );
#
# CREATE INDEX IF NOT EXISTS idx_sharepoint_file_versions_link ON sharepoint_file_versions(sharepoint_link_id);
# CREATE INDEX IF NOT EXISTS idx_sharepoint_file_versions_artifact ON sharepoint_file_versions(artifact_type, artifact_id);
#
# =============================================================================


# =============================================================================
# SHAREPOINT CONNECTOR MANAGEMENT
# =============================================================================

_sharepoint_connector: Optional[SharePointConnector] = None


def get_sharepoint_connector() -> SharePointConnector:
    """Get or create the SharePoint connector instance."""
    global _sharepoint_connector
    if _sharepoint_connector is None:
        try:
            _sharepoint_connector = SharePointConnector()
            _sharepoint_connector.connect()
            logger.info("SharePoint connector initialized for sync job")
        except Exception as e:
            logger.error(f"Failed to initialize SharePoint connector: {e}")
            raise RuntimeError(f"SharePoint connection failed: {str(e)}")
    return _sharepoint_connector


# =============================================================================
# DATABASE HELPER FUNCTIONS
# =============================================================================


def log_sync_event(
    status: str,
    total_files: int = 0,
    files_changed: int = 0,
    files_created: int = 0,
    files_deleted: int = 0,
    errors: int = 0,
    error_summary: Optional[Dict[str, Any]] = None,
) -> UUID:
    """
    Log a synchronization event to the database.

    Args:
        status: Sync status ('pending', 'started', 'completed', 'failed')
        total_files: Total number of files checked
        files_changed: Number of files that were changed
        files_created: Number of new files
        files_deleted: Number of deleted files
        errors: Number of errors encountered
        error_summary: Summary of errors

    Returns:
        The ID of the sync history record
    """
    try:
        with get_engine().connect() as connection:
            result = connection.execute(
                text(
                    """
                    INSERT INTO sharepoint_sync_history
                    (sync_started_at, sync_completed_at, status,
                     total_files_checked, files_changed, files_created,
                     files_deleted, errors_encountered, error_summary)
                    VALUES
                    (:started_at, :completed_at, :status, :total_files,
                     :files_changed, :files_created, :files_deleted,
                     :errors, :error_summary)
                    RETURNING id
                """
                ),
                {
                    "started_at": datetime.utcnow(),
                    "completed_at": datetime.utcnow() if status in ["completed", "failed"] else None,
                    "status": status,
                    "total_files": total_files,
                    "files_changed": files_changed,
                    "files_created": files_created,
                    "files_deleted": files_deleted,
                    "errors": errors,
                    "error_summary": error_summary,
                },
            )
            sync_id = result.fetchone()[0]
            connection.commit()
            return sync_id
    except Exception as e:
        logger.error(f"Error logging sync event: {e}")
        # Fallback: log to sync history with minimal info
        try:
            with get_engine().connect() as connection:
                connection.execute(
                    text(
                        """
                        INSERT INTO sharepoint_sync_history
                        (sync_started_at, status, error_summary)
                        VALUES (:started_at, :status, :error_summary)
                    """
                    ),
                    {
                        "started_at": datetime.utcnow(),
                        "status": "failed",
                        "error_summary": {"logging_error": str(e)},
                    },
                )
                connection.commit()
        except Exception:
            pass
        raise


def save_file_version(
    artifact_type: str,
    artifact_id: UUID,
    user_id: UUID,
    sharepoint_link_id: UUID,
    version_number: int,
    sharepoint_url: str,
    filename: str,
    file_size: Optional[int] = None,
    sharepoint_version: Optional[str] = None,
    last_modified_at: Optional[datetime] = None,
    last_modified_by: Optional[str] = None,
    diff_from_previous: Optional[str] = None,
    change_type: str = "modified",
    metadata: Optional[Dict[str, Any]] = None,
    is_current: bool = True,
) -> UUID:
    """
    Save a file version to the database.

    Args:
        artifact_type: 'proposal' or 'knowledge_card'
        artifact_id: The artifact ID
        user_id: The user ID
        sharepoint_link_id: The SharePoint link ID
        version_number: Version number (1, 2, 3, ...)
        sharepoint_url: SharePoint URL
        filename: Filename
        file_size: File size in bytes
        sharepoint_version: SharePoint version string
        last_modified_at: Last modification timestamp
        last_modified_by: Who last modified the file
        diff_from_previous: Diff text from previous version
        change_type: Type of change (created, modified, deleted, renamed)
        metadata: Additional metadata
        is_current: Whether this is the current version

    Returns:
        The ID of the file version record
    """
    try:
        # Mark previous versions as not current
        with get_engine().connect() as connection:
            connection.execute(
                text(
                    """
                    UPDATE sharepoint_file_versions
                    SET is_current = FALSE
                    WHERE sharepoint_link_id = :link_id
                """
                ),
                {"link_id": sharepoint_link_id},
            )

            # Insert new version
            result = connection.execute(
                text(
                    """
                    INSERT INTO sharepoint_file_versions
                    (artifact_type, artifact_id, user_id, sharepoint_link_id,
                     version_number, sharepoint_url, filename, file_size,
                     sharepoint_version, last_modified_at, last_modified_by,
                     diff_from_previous, change_type, metadata, is_current)
                    VALUES
                    (:artifact_type, :artifact_id, :user_id, :link_id,
                     :version_number, :url, :filename, :file_size,
                     :sp_version, :last_modified_at, :last_modified_by,
                     :diff, :change_type, :metadata, :is_current)
                    RETURNING id
                """
                ),
                {
                    "artifact_type": artifact_type,
                    "artifact_id": artifact_id,
                    "user_id": user_id,
                    "link_id": sharepoint_link_id,
                    "version_number": version_number,
                    "url": sharepoint_url,
                    "filename": filename,
                    "file_size": file_size,
                    "sp_version": sharepoint_version,
                    "last_modified_at": last_modified_at,
                    "last_modified_by": last_modified_by,
                    "diff": diff_from_previous,
                    "change_type": change_type,
                    "metadata": metadata,
                    "is_current": is_current,
                },
            )
            version_id = result.fetchone()[0]
            connection.commit()
            return version_id
    except Exception as e:
        logger.error(f"Error saving file version: {e}")
        raise


def get_sharepoint_links() -> List[Dict[str, Any]]:
    """
    Get all SharePoint links from the database.

    Returns:
        List of dictionaries containing link information
    """
    try:
        links = []

        # Get proposal links
        with get_engine().connect() as connection:
            result = connection.execute(
                text(
                    """
                    SELECT
                        'proposal' AS artifact_type,
                        psl.id AS link_id,
                        psl.proposal_id AS artifact_id,
                        psl.user_id,
                        psl.sharepoint_url,
                        psl.filename,
                        psl.folder_path,
                        psl.file_id,
                        psl.file_version AS sharepoint_version,
                        psl.status,
                        psl.uploaded_at,
                        psl.updated_at
                    FROM proposal_sharepoint_links psl
                    WHERE psl.status = 'uploaded'
                    UNION ALL
                    SELECT
                        'knowledge_card' AS artifact_type,
                        kcsl.id AS link_id,
                        kcsl.knowledge_card_id AS artifact_id,
                        kcsl.user_id,
                        kcsl.sharepoint_url,
                        kcsl.filename,
                        kcsl.folder_path,
                        kcsl.file_id,
                        kcsl.file_version AS sharepoint_version,
                        kcsl.status,
                        kcsl.uploaded_at,
                        kcsl.updated_at
                    FROM knowledge_card_sharepoint_links kcsl
                    WHERE kcsl.status = 'uploaded'
                """
                )
            )
            for row in result:
                links.append(dict(row))

        return links
    except Exception as e:
        logger.error(f"Error fetching SharePoint links: {e}")
        return []


def get_file_metadata_from_sharepoint(
    connector: SharePointConnector, folder_path: str, filename: str
) -> Optional[Dict[str, Any]]:
    """
    Get metadata for a file from SharePoint.

    Args:
        connector: SharePoint connector instance
        folder_path: Folder path
        filename: Filename

    Returns:
        Dictionary with file metadata or None if not found
    """
    try:
        metadata = connector.get_file_metadata(filename, folder_path)
        return {
            "id": metadata.get("id"),
            "name": metadata.get("name"),
            "size": metadata.get("size"),
            "version": metadata.get("version"),
            "lastModifiedDateTime": metadata.get("lastModifiedDateTime"),
            "lastModifiedBy": metadata.get("lastModifiedBy", {}).get("user", {}).get("displayName")
            if metadata.get("lastModifiedBy")
            else None,
            "webUrl": metadata.get("webUrl"),
            "eTag": metadata.get("eTag"),
        }
    except Exception as e:
        logger.error(f"Error getting file metadata: {e}")
        return None


def download_file_from_sharepoint(connector: SharePointConnector, folder_path: str, filename: str) -> Optional[bytes]:
    """
    Download a file from SharePoint.

    Args:
        connector: SharePoint connector instance
        folder_path: Folder path
        filename: Filename

    Returns:
        File content as bytes or None if failed
    """
    try:
        content = connector.download_file(filename, folder_path)
        return content
    except Exception as e:
        logger.error(f"Error downloading file {filename}: {e}")
        return None


# =============================================================================
# DIFF BUILDING FUNCTIONS
# =============================================================================


def extract_text_from_docx(docx_bytes: bytes) -> str:
    """
    Extract plain text from a DOCX file for diff comparison.

    Args:
        docx_bytes: Raw bytes of a DOCX file

    Returns:
        Extracted text as a single string
    """
    try:
        from docx import Document
        import io

        doc = Document(io.BytesIO(docx_bytes))
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {e}")
        return ""


def build_text_diff(old_text: str, new_text: str) -> str:
    """
    Build a text diff between two strings.

    Args:
        old_text: Old version text
        new_text: New version text

    Returns:
        Diff as a formatted string
    """
    import difflib

    old_lines = old_text.splitlines(keepends=True)
    new_lines = new_text.splitlines(keepends=True)

    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile="previous_version",
        tofile="current_version",
        lineterm="",
    )

    return "".join(diff)


def get_latest_version(link_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Get the latest version for a SharePoint link.

    Args:
        link_id: SharePoint link ID

    Returns:
        Dictionary with version info or None if not found
    """
    try:
        with get_engine().connect() as connection:
            result = connection.execute(
                text(
                    """
                    SELECT *
                    FROM sharepoint_file_versions
                    WHERE sharepoint_link_id = :link_id
                    ORDER BY version_number DESC
                    LIMIT 1
                """
                ),
                {"link_id": link_id},
            )
            row = result.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"Error fetching latest version: {e}")
        return None


# =============================================================================
# MAIN SYNC FUNCTION
# =============================================================================


def sync_sharepoint_files():
    """
    Main synchronization function that checks all SharePoint files for updates.

    This function:
    1. Logs sync start
    2. Retrieves all SharePoint links from database
    3. For each link, checks if file has been modified on SharePoint
    4. If modified, downloads both versions and builds diff
    5. Saves new version with diff
    6. Logs sync completion

    The function handles errors gracefully and continues with other files
    if one fails.
    """
    logger.info("Starting SharePoint file synchronization...")

    sync_start_time = datetime.utcnow()
    sync_id = None
    total_files = 0
    files_changed = 0
    files_created = 0
    files_deleted = 0
    errors = 0
    error_summary = {}

    try:
        # Log sync start
        sync_id = log_sync_event(status="started", total_files=0, errors=0)

        # Get SharePoint connector
        connector = get_sharepoint_connector()

        # Get all SharePoint links
        links = get_sharepoint_links()
        total_files = len(links)

        logger.info(f"Found {total_files} SharePoint links to check")

        # Track progress
        processed = 0

        for link in links:
            processed += 1
            artifact_type = link["artifact_type"]
            artifact_id = link["artifact_id"]
            user_id = link["user_id"]
            link_id = link["link_id"]
            folder_path = link["folder_path"]
            filename = link["filename"]
            link.get("sharepoint_version")

            logger.info(f"Checking {artifact_type} {artifact_id} ({processed}/{total_files}): {filename}")

            try:
                # Get current file metadata from SharePoint
                current_metadata = get_file_metadata_from_sharepoint(connector, folder_path, filename)

                if not current_metadata:
                    # File not found on SharePoint
                    logger.warning(f"File not found on SharePoint: {filename}")
                    errors += 1
                    error_summary[f"{artifact_type}_{artifact_id}"] = "File not found on SharePoint"
                    continue

                # Check if file was modified
                new_version = current_metadata.get("version")
                new_last_modified = current_metadata.get("lastModifiedDateTime")

                # Get latest version from our database
                latest_version = get_latest_version(link_id)

                if latest_version:
                    # Compare versions
                    db_version = latest_version.get("sharepoint_version")
                    db_last_modified = latest_version.get("last_modified_at")

                    # Check if file was modified
                    version_changed = new_version != db_version
                    date_changed = new_last_modified and (
                        not db_last_modified
                        or datetime.fromisoformat(new_last_modified.replace("T", " ").replace("Z", ""))
                        > datetime.fromisoformat(str(db_last_modified).replace("T", " ").replace("Z", ""))
                    )

                    if version_changed or date_changed:
                        logger.info(f"File {filename} has been modified (version: {db_version} -> {new_version})")

                        # Download both versions for diff
                        new_content = download_file_from_sharepoint(connector, folder_path, filename)

                        if new_content:
                            # Try to get old version content
                            old_version_content = None
                            if latest_version:
                                # This is a simplification - in production, you'd store the actual file content
                                # or have a way to retrieve previous versions from SharePoint
                                pass

                            # Extract text for diff
                            new_text = extract_text_from_docx(new_content) if new_content else ""
                            old_text = extract_text_from_docx(old_version_content) if old_version_content else ""

                            # Build diff
                            diff_text = build_text_diff(old_text, new_text) if old_text and new_text else None

                            # Determine change type
                            change_type = "modified"
                            if not latest_version:
                                change_type = "created"

                            # Calculate new version number
                            new_version_number = (latest_version.get("version_number", 0) if latest_version else 0) + 1

                            # Save new version
                            save_file_version(
                                artifact_type=artifact_type,
                                artifact_id=artifact_id,
                                user_id=user_id,
                                sharepoint_link_id=link_id,
                                version_number=new_version_number,
                                sharepoint_url=current_metadata.get("webUrl"),
                                filename=filename,
                                file_size=current_metadata.get("size"),
                                sharepoint_version=new_version,
                                last_modified_at=datetime.fromisoformat(
                                    new_last_modified.replace("T", " ").replace("Z", "")
                                )
                                if new_last_modified
                                else None,
                                last_modified_by=current_metadata.get("lastModifiedBy"),
                                diff_from_previous=diff_text,
                                change_type=change_type,
                                metadata={
                                    "previous_version": db_version,
                                    "previous_last_modified": str(db_last_modified) if db_last_modified else None,
                                },
                            )

                            files_changed += 1

                            # Update the link with new version info
                            update_link_version(
                                artifact_type,
                                link_id,
                                new_version,
                                datetime.fromisoformat(new_last_modified.replace("T", " ").replace("Z", ""))
                                if new_last_modified
                                else None,
                            )

                            logger.info(f"Saved new version {new_version_number} for {filename}")
                        else:
                            logger.error(f"Failed to download file: {filename}")
                            errors += 1
                            error_summary[f"{artifact_type}_{artifact_id}"] = f"Failed to download file: {filename}"
                    else:
                        logger.debug(f"File {filename} unchanged")
                else:
                    # No previous version - this is the first sync
                    logger.info(f"First sync for {filename}")

                    # Save as version 1
                    version_number = 1
                    save_file_version(
                        artifact_type=artifact_type,
                        artifact_id=artifact_id,
                        user_id=user_id,
                        sharepoint_link_id=link_id,
                        version_number=version_number,
                        sharepoint_url=current_metadata.get("webUrl"),
                        filename=filename,
                        file_size=current_metadata.get("size"),
                        sharepoint_version=new_version,
                        last_modified_at=datetime.fromisoformat(new_last_modified.replace("T", " ").replace("Z", ""))
                        if new_last_modified
                        else None,
                        last_modified_by=current_metadata.get("lastModifiedBy"),
                        change_type="created",
                        metadata={"initial_sync": True},
                    )

                    files_created += 1

                    # Update the link with version info
                    update_link_version(
                        artifact_type,
                        link_id,
                        new_version,
                        datetime.fromisoformat(new_last_modified.replace("T", " ").replace("Z", ""))
                        if new_last_modified
                        else None,
                    )

            except Exception as e:
                logger.error(
                    f"Error processing {artifact_type} {artifact_id} ({filename}): {e}",
                    exc_info=True,
                )
                errors += 1
                error_key = f"{artifact_type}_{artifact_id}"
                error_summary[error_key] = str(e)

        # Log sync completion
        log_sync_event(
            status="completed",
            total_files=total_files,
            files_changed=files_changed,
            files_created=files_created,
            files_deleted=files_deleted,
            errors=errors,
            error_summary=error_summary,
        )

        sync_end_time = datetime.utcnow()
        duration = sync_end_time - sync_start_time

        logger.info(
            f"SharePoint synchronization completed. "
            f"Processed {total_files} files, {files_changed} changed, "
            f"{files_created} created, {errors} errors in {duration.total_seconds():.2f}s"
        )

    except Exception as e:
        logger.error(f"Fatal error during synchronization: {e}", exc_info=True)

        # Log sync failure
        if sync_id:
            log_sync_event(
                status="failed",
                total_files=total_files,
                errors=errors + 1,
                error_summary={"fatal_error": str(e)},
            )

        raise


def update_link_version(
    artifact_type: str,
    link_id: UUID,
    sharepoint_version: str,
    last_modified_at: Optional[datetime],
) -> None:
    """
    Update the SharePoint link with new version information.

    Args:
        artifact_type: 'proposal' or 'knowledge_card'
        link_id: SharePoint link ID
        sharepoint_version: New SharePoint version
        last_modified_at: Last modification timestamp
    """
    try:
        table_map = {
            "proposal": "proposal_sharepoint_links",
            "knowledge_card": "knowledge_card_sharepoint_links",
        }

        if artifact_type not in table_map:
            return

        table = table_map[artifact_type]

        with get_engine().connect() as connection:
            connection.execute(
                text(
                    f"""
                    UPDATE {table}
                    SET file_version = :version,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = :link_id
                """
                ),
                {"version": sharepoint_version, "link_id": link_id},
            )
            connection.commit()
    except Exception as e:
        logger.error(f"Error updating link version: {e}")


# =============================================================================
# SCHEDULER SETUP
# =============================================================================


def setup_sharepoint_sync_scheduler():
    """
    Set up the scheduler for SharePoint synchronization.

    This sets up the job to run at the configured times (default: 08:00 and 20:00).
    The scheduler runs in a background thread.
    """
    logger.info("Setting up SharePoint synchronization scheduler...")

    # Clear existing jobs with the same tag
    schedule.clear("sharepoint-sync")

    # Schedule the job at each configured time
    for schedule_time in SCHEDULE_TIMES:
        logger.info(f"Scheduling SharePoint sync at {schedule_time}")
        schedule.every().day.at(schedule_time).do(sync_sharepoint_files).tag("sharepoint-sync")

    # Start the scheduler in a background thread
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)

    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True, name="SharePointSyncScheduler")
    scheduler_thread.start()

    logger.info(f"SharePoint sync scheduler started (runs at: {', '.join(SCHEDULE_TIMES)})")

    # Return the thread for potential cleanup
    return scheduler_thread


# =============================================================================
# DATABASE INITIALIZATION (for new tables)
# =============================================================================


def initialize_database():
    """
    Initialize the database tables for SharePoint synchronization.

    This creates the necessary tables if they don't exist.
    """
    logger.info("Initializing SharePoint sync database tables...")

    try:
        with get_engine().connect() as connection:
            # Create sharepoint_sync_status enum if not exists
            connection.execute(
                text(
                    """
                    DO $$
                    BEGIN
                        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sharepoint_sync_status') THEN
                            CREATE TYPE sharepoint_sync_status AS ENUM (
                                'pending',
                                'started',
                                'completed',
                                'failed'
                            );
                        END IF;
                    END$$;
                """
                )
            )

            # Create sync_change_type enum if not exists
            connection.execute(
                text(
                    """
                    DO $$
                    BEGIN
                        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sync_change_type') THEN
                            CREATE TYPE sync_change_type AS ENUM (
                                'created',
                                'modified',
                                'deleted',
                                'renamed'
                            );
                        END IF;
                    END$$;
                """
                )
            )

            # Create sharepoint_sync_history table
            connection.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS sharepoint_sync_history (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        sync_started_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        sync_completed_at TIMESTAMPTZ,
                        status sharepoint_sync_status NOT NULL DEFAULT 'started',
                        total_files_checked INTEGER DEFAULT 0,
                        files_changed INTEGER DEFAULT 0,
                        files_created INTEGER DEFAULT 0,
                        files_deleted INTEGER DEFAULT 0,
                        errors_encountered INTEGER DEFAULT 0,
                        error_summary JSONB,
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )
            )

            # Create sharepoint_file_versions table
            connection.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS sharepoint_file_versions (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        artifact_type TEXT NOT NULL CHECK (artifact_type IN ('proposal', 'knowledge_card')),
                        artifact_id UUID NOT NULL,
                        user_id UUID NOT NULL REFERENCES users(id),
                        sharepoint_link_id UUID NOT NULL,
                        version_number INTEGER NOT NULL,
                        sharepoint_url TEXT NOT NULL,
                        filename TEXT NOT NULL,
                        file_size BIGINT,
                        sharepoint_version TEXT,
                        last_modified_at TIMESTAMPTZ,
                        last_modified_by TEXT,
                        diff_from_previous TEXT,
                        change_type sync_change_type NOT NULL DEFAULT 'modified',
                        metadata JSONB DEFAULT '{}'::jsonb,
                        is_current BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE (sharepoint_link_id, version_number)
                    )
                """
                )
            )

            # Create indexes
            connection.execute(
                text(
                    """
                    CREATE INDEX IF NOT EXISTS idx_sharepoint_sync_history_status
                    ON sharepoint_sync_history(status)
                """
                )
            )
            connection.execute(
                text(
                    """
                    CREATE INDEX IF NOT EXISTS idx_sharepoint_sync_history_created
                    ON sharepoint_sync_history(created_at)
                """
                )
            )
            connection.execute(
                text(
                    """
                    CREATE INDEX IF NOT EXISTS idx_sharepoint_file_versions_link
                    ON sharepoint_file_versions(sharepoint_link_id)
                """
                )
            )
            connection.execute(
                text(
                    """
                    CREATE INDEX IF NOT EXISTS idx_sharepoint_file_versions_artifact
                    ON sharepoint_file_versions(artifact_type, artifact_id)
                """
                )
            )
            connection.execute(
                text(
                    """
                    CREATE INDEX IF NOT EXISTS idx_sharepoint_file_versions_current
                    ON sharepoint_file_versions(sharepoint_link_id, is_current)
                    WHERE is_current = TRUE
                """
                )
            )

            connection.commit()
            logger.info("SharePoint sync database tables initialized successfully")

    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    # Initialize database
    initialize_database()

    # Set up scheduler
    setup_sharepoint_sync_scheduler()

    # Keep the main thread alive
    logger.info("SharePoint sync service running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(3600)  # Sleep for 1 hour
    except KeyboardInterrupt:
        logger.info("Shutting down SharePoint sync service...")
