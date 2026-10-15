from app.models.database import get_connection


def save_backup_metadata(
    database_id,
    filename,
    file_path,
    file_size,
    sha256_hash,
    status="CREATED"
):
    """
    Store backup metadata in the backups table.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        query = """
            INSERT INTO backups
            (
                database_id,
                filename,
                file_path,
                file_size,
                sha256_hash,
                status
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """

        values = (
            database_id,
            filename,
            file_path,
            file_size,
            sha256_hash,
            status
        )

        cursor.execute(query, values)
        connection.commit()

        return cursor.lastrowid

    finally:
        cursor.close()
        connection.close()