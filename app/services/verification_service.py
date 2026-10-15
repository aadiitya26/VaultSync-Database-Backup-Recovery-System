import os

from app.models.database import get_connection
from app.services.integrity_service import calculate_sha256
from app.services.audit_service import log_action


def verify_backup(backup_id):
    """
    Verify the integrity of a backup using its stored SHA-256 hash.
    """

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

    # 2. Check whether backup exists in database
    if not backup:
        raise ValueError(
            f"Backup with ID {backup_id} not found."
        )

    # 3. Check whether backup file exists
    if not os.path.exists(backup["file_path"]):

        log_action(
            action="BACKUP_MISSING",
            description=f"Backup file is missing: {backup['filename']}",
            status="FAILED"
        )

        return {
            "backup_id": backup_id,
            "filename": backup["filename"],
            "status": "MISSING",
            "message": "Backup file does not exist."
        }

    # 4. Calculate current SHA-256 hash
    current_hash = calculate_sha256(
        backup["file_path"]
    )

    # 5. Compare stored hash with current hash
    if current_hash == backup["sha256_hash"]:

        verification_status = "VERIFIED"
        message = "Backup integrity verified successfully."

        log_action(
            action="BACKUP_VERIFIED",
            description=f"Backup integrity verified: {backup['filename']}",
            status="SUCCESS"
        )

    else:

        verification_status = "CORRUPTED"
        message = "Backup integrity verification failed."

        log_action(
            action="BACKUP_CORRUPTED",
            description=f"Backup integrity check failed: {backup['filename']}",
            status="FAILED"
        )

    # 6. Return verification result
    return {
        "backup_id": backup_id,
        "filename": backup["filename"],
        "stored_hash": backup["sha256_hash"],
        "current_hash": current_hash,
        "status": verification_status,
        "message": message
    }