
import logging
import os

from app.config import Config
from app.models.database import get_connection
from app.services.audit_service import log_action

logger = logging.getLogger(__name__)


def _is_inside_backup_directory(file_path):
    """Return True only when the resolved file path is inside BACKUP_DIR."""
    backup_root = os.path.realpath(Config.BACKUP_DIR)
    resolved_path = os.path.realpath(file_path)

    try:
        return (
            resolved_path != backup_root
            and os.path.commonpath([backup_root, resolved_path])
            == backup_root
        )
    except ValueError:
        # For example, paths on different Windows drives.
        return False


def _record_retention_audit(action, description, status):
    """Prevent audit logging failures from masking retention results."""
    try:
        log_action(action, description, status)
    except Exception:
        logger.exception("Could not record retention audit event: %s", action)


def apply_retention(database_id, keep_count=None):
    """
    Keep the newest keep_count backups for one managed database.
    Delete older backup files and their metadata.
    Never delete files outside Config.BACKUP_DIR.
    """
    if keep_count is None:
        keep_count = Config.RETENTION_COUNT

    if (
        isinstance(keep_count, bool)
        or not isinstance(keep_count, int)
        or keep_count < 1
    ):
        raise ValueError("Retention count must be a positive integer.")

    connection = None
    cursor = None
    deleted = []
    errors = []

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, filename, file_path, created_at
            FROM backups
            WHERE database_id = %s
            ORDER BY created_at DESC, id DESC
            """,
            (database_id,),
        )
        backups = cursor.fetchall()
        old_backups = backups[keep_count:]

        for backup in old_backups:
            backup_id = backup["id"]
            file_path = backup["file_path"]

            try:
                if not _is_inside_backup_directory(file_path):
                    raise ValueError(
                        "Refusing to delete a backup outside "
                        "the configured backup directory."
                    )

                # Remove the file first. Keep metadata if deletion fails.
                if os.path.exists(file_path):
                    os.remove(file_path)

                cursor.execute(
                    "DELETE FROM backups WHERE id = %s",
                    (backup_id,),
                )
                connection.commit()
                deleted.append(backup_id)

                _record_retention_audit(
                    "BACKUP_RETENTION_DELETED",
                    f"Retention removed backup ID {backup_id} "
                    f"for managed database ID {database_id}.",
                    "SUCCESS",
                )

            except Exception as exc:
                connection.rollback()
                errors.append((backup_id, str(exc)))

                _record_retention_audit(
                    "BACKUP_RETENTION_FAILED",
                    f"Could not remove backup ID {backup_id}: {exc}",
                    "FAILED",
                )

        return {
            "database_id": database_id,
            "keep_count": keep_count,
            "total_backups": len(backups),
            "deleted_ids": deleted,
            "errors": errors,
        }

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()
