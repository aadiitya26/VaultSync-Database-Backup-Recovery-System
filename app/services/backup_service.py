
import os
import gzip
import shutil
import subprocess
import logging
from datetime import datetime

from app.config import Config
from app.services.database_service import get_database_by_name
from app.services.integrity_service import calculate_sha256
from app.services.metadata_service import save_backup_metadata
from app.services.audit_service import log_action

logger = logging.getLogger(__name__)


def create_backup(database_name):
    """Create a compressed MySQL backup, save metadata, and apply retention."""

    sql_path = None
    compressed_path = None

    try:
        # 1. Find the managed database.
        database = get_database_by_name(database_name)

        if not database:
            raise ValueError(
                f"Managed database '{database_name}' not found."
            )

        # 2. Create the backup directory.
        os.makedirs(Config.BACKUP_DIR, exist_ok=True)

        # 3. Generate timestamped filenames.
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sql_filename = f"{database_name}_{timestamp}.sql"
        compressed_filename = f"{database_name}_{timestamp}.sql.gz"

        sql_path = os.path.join(Config.BACKUP_DIR, sql_filename)
        compressed_path = os.path.join(
            Config.BACKUP_DIR, compressed_filename
        )

        # 4. Prepare the mysqldump command.
        command = [
            "mysqldump",
            "--set-gtid-purged=OFF",
            "-h", database["host"],
            "-P", str(database["port"]),
            "-u", database["username"],
            database["name"],
        ]

        # Keep the database password out of the command arguments.
        env = os.environ.copy()
        env["MYSQL_PWD"] = Config.MYSQL_PASSWORD

        # 5. Create the temporary SQL dump.
        with open(sql_path, "w", encoding="utf-8") as sql_file:
            result = subprocess.run(
                command,
                stdout=sql_file,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
            )

        if result.returncode != 0:
            raise RuntimeError(
                f"Backup failed: {result.stderr.strip()}"
            )

        # 6. Compress the SQL dump.
        with open(sql_path, "rb") as sql_file:
            with gzip.open(compressed_path, "wb") as compressed_file:
                shutil.copyfileobj(sql_file, compressed_file)

        # 7. Remove the temporary SQL dump.
        os.remove(sql_path)
        sql_path = None

        # 8. Calculate size and SHA-256 hash.
        file_size = os.path.getsize(compressed_path)
        sha256_hash = calculate_sha256(compressed_path)

        # 9. Save backup metadata.
        backup_id = save_backup_metadata(
            database_id=database["id"],
            filename=compressed_filename,
            file_path=compressed_path,
            file_size=file_size,
            sha256_hash=sha256_hash,
            status="CREATED",
        )

        # 10. Record successful backup creation.
        log_action(
            action="BACKUP_CREATED",
            description=(
                f"Backup created successfully: {compressed_filename}"
            ),
            status="SUCCESS",
        )

        backup_result = {
            "id": backup_id,
            "database": database_name,
            "filename": compressed_filename,
            "file_path": compressed_path,
            "file_size": file_size,
            "sha256_hash": sha256_hash,
            "status": "CREATED",
        }

        # 11. Apply retention after saving the new backup.
        # A retention error must not invalidate the successful backup.
        try:
            from app.services.retention_service import apply_retention

            retention_result = apply_retention(
                database["id"],
                keep_count=Config.RETENTION_COUNT,
            )

            if retention_result["errors"]:
                logger.error(
                    "Retention completed with errors for %s: %s",
                    database_name,
                    retention_result["errors"],
                )
            else:
                logger.info(
                    "Retention completed for %s. Deleted IDs: %s",
                    database_name,
                    retention_result["deleted_ids"],
                )

            # Report retention details to the caller as well.
            backup_result["retention"] = retention_result

        except Exception as retention_error:
            logger.exception(
                "Backup %s succeeded, but retention failed for %s.",
                backup_id,
                database_name,
            )
            backup_result["retention"] = {
                "status": "FAILED",
                "error": str(retention_error),
            }

        return backup_result

    except Exception as e:
        # Clean up incomplete files if backup creation itself fails.
        if sql_path and os.path.exists(sql_path):
            os.remove(sql_path)

        if compressed_path and os.path.exists(compressed_path):
            os.remove(compressed_path)

        try:
            log_action(
                action="BACKUP_FAILED",
                description=(
                    f"Backup failed for database "
                    f"'{database_name}': {str(e)}"
                ),
                status="FAILED",
            )
        except Exception:
            logger.exception("Could not record backup failure.")

        raise
