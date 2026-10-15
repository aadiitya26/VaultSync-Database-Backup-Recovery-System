
import os

from app.config import Config
from app.models.database import get_connection
from app.services.audit_service import log_action


def apply_retention(database_id, keep_count=None):
    """
    Keep the newest keep_count backups for one managed database.
    Delete older backup files and their metadata.
    """

    if keep_count is None:
        keep_count = Config.RETENTION_COUNT

    if keep_count < 1:
        raise ValueError("Retention count must be at least 1.")

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    deleted = []
    errors = []

    try:
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
                # Remove the file first. If this fails, keep its metadata.
                if os.path.exists(file_path):
                    os.remove(file_path)

                cursor.execute(
                    "DELETE FROM backups WHERE id = %s",
                    (backup_id,),
                )
                connection.commit()

                deleted.append(backup_id)

                log_action(
                    "BACKUP_RETENTION_DELETED",
                    f"Retention removed backup ID {backup_id} "
                    f"for managed database ID {database_id}.",
                    "SUCCESS",
                )

            except Exception as exc:
                connection.rollback()
                errors.append((backup_id, str(exc)))

                log_action(
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
        cursor.close()
        connection.close()
