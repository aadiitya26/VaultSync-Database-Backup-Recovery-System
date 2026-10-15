
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import Config
from app.models.database import get_connection
from app.services.backup_service import create_backup

logger = logging.getLogger(__name__)

_scheduler = None


def run_scheduled_backup(database_name):
    """Run a backup and record scheduler failures in the application audit log."""
    from app.services.audit_service import log_action

    try:
        result = create_backup(database_name)
        logger.info(
            "Scheduled backup completed for %s: %s",
            database_name,
            result["filename"],
        )
        return result

    except Exception as exc:
        logger.exception(
            "Scheduled backup failed for %s",
            database_name,
        )

        try:
            log_action(
                action="SCHEDULED_BACKUP_FAILED",
                description=(
                    f"Scheduled backup failed for "
                    f"'{database_name}': {exc}"
                ),
                status="FAILED",
            )
        except Exception:
            logger.exception("Could not record scheduler failure")

        return None


def _run_backups_for_all_managed_databases():
    """Create a backup for each database registered in VaultSync."""
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT name FROM managed_databases ORDER BY id"
        )
        databases = cursor.fetchall()
    finally:
        cursor.close()
        connection.close()

    for database in databases:
        run_scheduled_backup(database["name"])


def start_scheduler():
    """Start the daily backup scheduler once per application process."""
    global _scheduler

    if _scheduler is not None and _scheduler.running:
        return _scheduler

    _scheduler = BackgroundScheduler(
        timezone="Asia/Kolkata"
    )

    _scheduler.add_job(
        _run_backups_for_all_managed_databases,
        trigger="cron",
        hour=Config.BACKUP_SCHEDULE_HOUR,
        minute=Config.BACKUP_SCHEDULE_MINUTE,
        id="daily_database_backups",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    _scheduler.start()
    logger.info(
        "VaultSync scheduler started. Daily backups scheduled for %02d:%02d IST.",
        Config.BACKUP_SCHEDULE_HOUR,
        Config.BACKUP_SCHEDULE_MINUTE,
    )

    return _scheduler


def stop_scheduler():
    """Stop the scheduler if it is running."""
    global _scheduler

    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)

    _scheduler = None
