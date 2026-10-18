
import logging
import mysql.connector

from app.config import Config
from app.models.database import get_connection
from app.services.audit_service import log_action


logger = logging.getLogger(__name__)


def get_database_by_name(name):
    """Retrieve a registered database by its name."""
    connection = get_connection()
    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, name, host, port, username, created_at
            FROM managed_databases
            WHERE name = %s
            """,
            (name,),
        )
        return cursor.fetchone()

    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


def validate_database_exists(name, host, port):
    """
    Check whether the target MySQL server is reachable and
    the requested database exists using VaultSync credentials.
    """
    connection = None
    cursor = None

    try:
        connection = mysql.connector.connect(
            host=host,
            port=port,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            connection_timeout=5,
        )

        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT SCHEMA_NAME
            FROM INFORMATION_SCHEMA.SCHEMATA
            WHERE SCHEMA_NAME = %s
            """,
            (name,),
        )

        if cursor.fetchone() is None:
            raise ValueError(
                f"Database '{name}' does not exist on {host}:{port}."
            )

        return True

    except ValueError:
        raise

    except mysql.connector.Error as exc:
        raise ValueError(
            f"Could not validate database '{name}' on {host}:{port}. "
            "Check the server, port, credentials, and database permissions."
        ) from exc

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()


def add_managed_database(name, host, port, username):
    """Validate and register an existing MySQL database."""

    name = name.strip() if isinstance(name, str) else ""
    host = host.strip() if isinstance(host, str) else ""
    username = username.strip() if isinstance(username, str) else ""

    if not name or not host or not username:
        raise ValueError("Name, host, and username are required.")

    if isinstance(port, bool):
        raise ValueError(
            "Port must be an integer between 1 and 65535."
        )

    try:
        port = int(port)
    except (TypeError, ValueError):
        raise ValueError(
            "Port must be an integer between 1 and 65535."
        )

    if not 1 <= port <= 65535:
        raise ValueError(
            "Port must be an integer between 1 and 65535."
        )

    # Reject duplicate registrations.
    if get_database_by_name(name):
        raise ValueError(
            f"Database '{name}' is already registered."
        )

    # Verify the target exists before inserting a registry record.
    validate_database_exists(name, host, port)

    connection = get_connection()
    cursor = None

    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO managed_databases (name, host, port, username)
            VALUES (%s, %s, %s, %s)
            """,
            (name, host, port, username),
        )

        database_id = cursor.lastrowid
        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        if cursor is not None:
            cursor.close()
        connection.close()

    # Audit logging should not undo a successful registration.
    try:
        log_action(
            action="MANAGED_DATABASE_ADDED",
            description=(
                f"Managed database '{name}' registered "
                f"at {host}:{port}."
            ),
            status="SUCCESS",
        )
    except Exception:
        logger.exception(
            "Database was registered, but audit logging failed."
        )

    return {
        "id": database_id,
        "name": name,
        "host": host,
        "port": port,
        "username": username,
    }
