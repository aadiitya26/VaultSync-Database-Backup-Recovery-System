import gzip
import os
import subprocess
import tempfile

from app.config import Config
from app.models.database import get_connection
from app.services.integrity_service import calculate_sha256
from app.services.audit_service import log_action


def restore_backup(backup_id, target_database):
    """
    Restore a compressed MySQL backup into the specified database.

    The backup is verified using SHA-256 before restoration.
    All restore failures are recorded in the audit log.
    """

    backup = None
    temporary_sql_path = None

    try:
        # 1. Get backup metadata
        connection = get_connection()

        try:
            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT
                    id,
                    filename,
                    file_path,
                    sha256_hash,
                    status
                FROM backups
                WHERE id = %s
            """

            cursor.execute(query, (backup_id,))

            backup = cursor.fetchone()

        finally:
            cursor.close()
            connection.close()

        # 2. Check whether backup exists
        if not backup:
            raise ValueError(
                f"Backup with ID {backup_id} not found."
            )

        # 3. Check whether backup file exists
        if not os.path.exists(backup["file_path"]):
            raise FileNotFoundError(
                f"Backup file not found: {backup['file_path']}"
            )

        # 4. Verify backup integrity before restore
        current_hash = calculate_sha256(
            backup["file_path"]
        )

        if current_hash != backup["sha256_hash"]:
            raise ValueError(
                "Backup integrity verification failed. "
                "Restore aborted."
            )

        # 5. Create temporary SQL file
        temporary_sql = tempfile.NamedTemporaryFile(
            suffix=".sql",
            delete=False
        )

        temporary_sql_path = temporary_sql.name
        temporary_sql.close()

        # 6. Decompress the .sql.gz backup
        with gzip.open(
            backup["file_path"],
            "rt",
            encoding="utf-8"
        ) as compressed_file:

            sql_content = compressed_file.read()

        # 7. Remove GTID_PURGED statements
        #    to avoid GTID conflicts during restore.
        lines = sql_content.splitlines()

        filtered_lines = [
            line
            for line in lines
            if "GTID_PURGED" not in line
        ]

        # 8. Write cleaned SQL to temporary file
        with open(
            temporary_sql_path,
            "w",
            encoding="utf-8"
        ) as sql_file:

            sql_file.write(
                "\n".join(filtered_lines)
            )

        # 9. Restore using MySQL client
        command = [
            "mysql",
            "-h", Config.MYSQL_HOST,
            "-P", str(Config.MYSQL_PORT),
            "-u", Config.MYSQL_USER,
            target_database
        ]

        # Keep password outside the command
        env = os.environ.copy()
        env["MYSQL_PWD"] = Config.MYSQL_PASSWORD

        with open(
            temporary_sql_path,
            "r",
            encoding="utf-8"
        ) as sql_file:

            result = subprocess.run(
                command,
                stdin=sql_file,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )

        # 10. Check restore result
        if result.returncode != 0:
            raise RuntimeError(
                f"Restore failed: {result.stderr.strip()}"
            )

        # 11. Log successful restore
        log_action(
            action="BACKUP_RESTORED",
            description=(
                f"Backup restored successfully: "
                f"{backup['filename']} "
                f"to database '{target_database}'"
            ),
            status="SUCCESS"
        )

        # 12. Return restore information
        return {
            "backup_id": backup_id,
            "filename": backup["filename"],
            "target_database": target_database,
            "status": "RESTORED"
        }

    except Exception as e:

        # Determine a useful description
        if backup:
            description = (
                f"Restore failed for backup "
                f"'{backup['filename']}' "
                f"to database '{target_database}': {str(e)}"
            )
        else:
            description = (
                f"Restore failed for backup ID "
                f"{backup_id} "
                f"to database '{target_database}': {str(e)}"
            )

        # Record failed restore attempt
        try:
            log_action(
                action="BACKUP_RESTORE_FAILED",
                description=description,
                status="FAILED"
            )
        except Exception:
            # Do not hide the original restore error
            pass

        # Re-raise the original error
        raise

    finally:

        # Remove temporary SQL file
        if (
            temporary_sql_path
            and os.path.exists(temporary_sql_path)
        ):
            os.remove(temporary_sql_path)