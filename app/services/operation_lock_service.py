import hashlib
import logging
from contextlib import contextmanager

from app.models.database import get_connection

logger = logging.getLogger(__name__)


def _get_lock_name(database_name):
    """Generate a short, consistent MySQL advisory lock name."""
    database_hash = hashlib.sha256(
        database_name.encode("utf-8")
    ).hexdigest()[:32]

    return f"vaultsync_{database_hash}"


@contextmanager
def database_operation_lock(database_name):
    """
    Acquire a MySQL advisory lock for a database.

    The lock is non-blocking. If another operation already
    holds it, raise an error immediately.
    """
    connection = None
    cursor = None
    lock_acquired = False
    lock_name = _get_lock_name(database_name)

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT GET_LOCK(%s, 0)",
            (lock_name,),
        )

        result = cursor.fetchone()

        if result is None or result[0] != 1:
            raise RuntimeError(
                f"Database '{database_name}' is busy. "
                "Another backup or restore operation "
                "is already in progress."
            )

        lock_acquired = True

        logger.info(
            "Operation lock acquired for database '%s'.",
            database_name,
        )

        yield

    finally:
        if cursor is not None:
            try:
                if lock_acquired:
                    cursor.execute(
                        "SELECT RELEASE_LOCK(%s)",
                        (lock_name,),
                    )

                    # Consume the RELEASE_LOCK result.
                    cursor.fetchone()

                    logger.info(
                        "Operation lock released for database '%s'.",
                        database_name,
                    )

            except Exception:
                logger.exception(
                    "Failed to release operation lock for '%s'.",
                    database_name,
                )

            finally:
                try:
                    cursor.close()
                except Exception:
                    logger.exception(
                        "Failed to close lock cursor for '%s'.",
                        database_name,
                    )

        if connection is not None:
            try:
                connection.close()
            except Exception:
                logger.exception(
                    "Failed to close lock connection for '%s'.",
                    database_name,
                )
