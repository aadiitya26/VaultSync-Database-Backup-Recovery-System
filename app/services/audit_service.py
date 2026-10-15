from app.models.database import get_connection


def log_action(action, description, status):
    """
    Store an action in the audit_logs table.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        query = """
            INSERT INTO audit_logs
            (
                action,
                description,
                status
            )
            VALUES (%s, %s, %s)
        """

        values = (
            action,
            description,
            status
        )

        cursor.execute(query, values)
        connection.commit()

        return cursor.lastrowid

    finally:
        cursor.close()
        connection.close()