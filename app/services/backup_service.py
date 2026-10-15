import os
import gzip
import shutil
import subprocess
from datetime import datetime

from app.config import Config
from app.services.database_service import get_database_by_name
from app.services.integrity_service import calculate_sha256
from app.services.metadata_service import save_backup_metadata
from app.services.audit_service import log_action


def create_backup(database_name):
    """
    Create a compressed MySQL backup and store its metadata.
    """

    sql_path = None
    compressed_path = None

    try:
        # 1. Find managed database
        database = get_database_by_name(database_name)

        if not database:
            raise ValueError(
                f"Managed database '{database_name}' not found."
            )

        # 2. Create backup directory
        os.makedirs(Config.BACKUP_DIR, exist_ok=True)

        # 3. Generate timestamped filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        sql_filename = f"{database_name}_{timestamp}.sql"
        compressed_filename = f"{database_name}_{timestamp}.sql.gz"

        sql_path = os.path.join(
            Config.BACKUP_DIR,
            sql_filename
        )

        compressed_path = os.path.join(
            Config.BACKUP_DIR,
            compressed_filename
        )

        # 4. mysqldump command
        command = [
            "mysqldump",
            "--set-gtid-purged=OFF",
            "-h", database["host"],
            "-P", str(database["port"]),
            "-u", database["username"],
            database["name"]
        ]

        # Keep password outside the command
        env = os.environ.copy()
        env["MYSQL_PWD"] = Config.MYSQL_PASSWORD

        # 5. Create temporary SQL backup
        with open(
            sql_path,
            "w",
            encoding="utf-8"
        ) as sql_file:

            result = subprocess.run(
                command,
                stdout=sql_file,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )

        # 6. Handle mysqldump failure
        if result.returncode != 0:
            raise RuntimeError(
                f"Backup failed: {result.stderr.strip()}"
            )

        # 7. Compress SQL backup
        with open(
            sql_path,
            "rb"
        ) as sql_file:

            with gzip.open(
                compressed_path,
                "wb"
            ) as compressed_file:

                shutil.copyfileobj(
                    sql_file,
                    compressed_file
                )

        # 8. Remove temporary uncompressed SQL file
        os.remove(sql_path)
        sql_path = None

        # 9. Get compressed file size
        file_size = os.path.getsize(
            compressed_path
        )

        # 10. Calculate SHA-256
        sha256_hash = calculate_sha256(
            compressed_path
        )

        # 11. Store backup metadata
        backup_id = save_backup_metadata(
            database_id=database["id"],
            filename=compressed_filename,
            file_path=compressed_path,
            file_size=file_size,
            sha256_hash=sha256_hash,
            status="CREATED"
        )

        # 12. Log successful backup
        log_action(
            action="BACKUP_CREATED",
            description=(
                f"Backup created successfully: "
                f"{compressed_filename}"
            ),
            status="SUCCESS"
        )

        # 13. Return backup information
        return {
            "id": backup_id,
            "database": database_name,
            "filename": compressed_filename,
            "file_path": compressed_path,
            "file_size": file_size,
            "sha256_hash": sha256_hash,
            "status": "CREATED"
        }

    except Exception as e:

        # Remove temporary SQL file if it exists
        if sql_path and os.path.exists(sql_path):
            os.remove(sql_path)

        # Remove incomplete compressed file if it exists
        if compressed_path and os.path.exists(compressed_path):
            os.remove(compressed_path)

        # Record failed backup attempt
        try:
            log_action(
                action="BACKUP_FAILED",
                description=(
                    f"Backup failed for database "
                    f"'{database_name}': {str(e)}"
                ),
                status="FAILED"
            )
        except Exception:
            # Do not hide the original backup error
            pass

        # Re-raise the original error
        raise
