from app.models.database import get_connection


def get_database_by_name(name):
    """
    Retrieve a managed database by its name.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT
                id,
                name,
                host,
                port,
                username,
                created_at
            FROM managed_databases
            WHERE name = %s
        """

        cursor.execute(query, (name,))

        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()