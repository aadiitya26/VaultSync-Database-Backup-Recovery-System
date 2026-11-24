
import os
import shutil
from datetime import datetime
import logging

from app.config import Config
from app.models.database import get_connection

logger = logging.getLogger(__name__)


def collect_system_health():
    checks = []
    database_checks = []

    backup_dir = Config.BACKUP_DIR
    os.makedirs(backup_dir, exist_ok=True)

    # --------------------------------------------------
    # Backup folder usage
    # --------------------------------------------------
    total_backup_bytes = 0
    backup_files = 0

    for root, _, files in os.walk(backup_dir):
        for filename in files:
            path = os.path.join(root, filename)

            try:
                total_backup_bytes += os.path.getsize(path)
                backup_files += 1
            except OSError:
                logger.warning(
                    "Unable to read backup file size: %s", path
                )

    # --------------------------------------------------
    # Disk usage and backup folder checks
    # --------------------------------------------------
    disk = shutil.disk_usage(backup_dir)

    checks.append({
        "name": "Backup storage folder",
        "status": "OK" if os.path.isdir(backup_dir) else "ERROR",
        "detail": "Backup directory is available.",
    })

    checks.append({
        "name": "Disk space",
        "status": "WARNING" if disk.free < disk.total * 0.10 else "OK",
        "detail": (
            f"{disk.free / (1024 ** 3):.2f} GB free of "
            f"{disk.total / (1024 ** 3):.2f} GB"
        ),
    })

    # --------------------------------------------------
    # Scheduler health check
    # --------------------------------------------------
    scheduler_running = False
    next_run = None

    try:
        from app.services import scheduler_service

        scheduler = scheduler_service._scheduler
        scheduler_running = bool(scheduler and scheduler.running)

        if scheduler_running:
            job = scheduler.get_job("daily_database_backups")

            if job and job.next_run_time:
                next_run = job.next_run_time.strftime(
                    "%Y-%m-%d %H:%M:%S %Z"
                )

    except Exception:
        logger.exception("Scheduler health check failed.")

    checks.append({
        "name": "Daily backup scheduler",
        "status": "OK" if scheduler_running else "WARNING",
        "detail": (
            f"Running. Next run: {next_run}"
            if scheduler_running and next_run
            else (
                "Scheduler is running."
                if scheduler_running
                else "Scheduler is not running in this application process."
            )
        ),
    })

    # --------------------------------------------------
    # Metadata database and registered database checks
    # --------------------------------------------------
    connection = None
    cursor = None

    databases = []
    latest_backup = None
    failed_backups = 0
    verification_pending = 0

    db_status = "ERROR"

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        # Fetch registered databases
        cursor.execute(
            "SELECT name, host, port FROM managed_databases ORDER BY name"
        )
        databases = cursor.fetchall()

        # --------------------------------------------------
        # Individual database connection checks
        # --------------------------------------------------
        try:
            import mysql.connector

            for db in databases:
                try:
                    ping_conn = mysql.connector.connect(
                        host=db["host"],
                        port=int(db["port"]),
                        user=Config.MYSQL_USER,
                        password=Config.MYSQL_PASSWORD,
                        database=db["name"],
                        connection_timeout=3,
                    )

                    ping_conn.close()

                    database_checks.append({
                        "name": db["name"],
                        "status": "OK",
                        "detail": "Connection succeeded.",
                    })

                except Exception as ping_error:
                    database_checks.append({
                        "name": db["name"],
                        "status": "ERROR",
                        "detail": f"Connection failed: {ping_error}",
                    })

        except ImportError:
            database_checks.append({
                "name": "Database connectivity",
                "status": "WARNING",
                "detail": (
                    "mysql.connector is unavailable; "
                    "connection checks skipped."
                ),
            })

        # --------------------------------------------------
        # Latest backup timestamp
        # --------------------------------------------------
        cursor.execute(
            "SELECT created_at FROM backups "
            "ORDER BY created_at DESC, id DESC LIMIT 1"
        )

        latest = cursor.fetchone()
        latest_backup = latest["created_at"] if latest else None

        # --------------------------------------------------
        # Backup record counts
        # Retained for compatibility with existing templates
        # --------------------------------------------------
        cursor.execute(
            "SELECT COUNT(*) AS total FROM backups "
            "WHERE status IN ('FAILED', 'ERROR', 'CORRUPTED')"
        )

        failed_backups = cursor.fetchone()["total"]

        cursor.execute(
            "SELECT COUNT(*) AS total FROM backups "
            "WHERE status NOT IN "
            "('VERIFIED', 'FAILED', 'ERROR', 'CORRUPTED')"
        )

        verification_pending = cursor.fetchone()["total"]

        db_status = "OK"

    except Exception:
        logger.exception("Health monitor database query failed.")

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()

    # --------------------------------------------------
    # Metadata database check
    # --------------------------------------------------
    checks.append({
        "name": "VaultSync metadata database",
        "status": db_status,
        "detail": (
            "Metadata database query succeeded."
            if db_status == "OK"
            else "Could not query VaultSync metadata database."
        ),
    })

    # --------------------------------------------------
    # Overall health status
    # --------------------------------------------------
    all_checks = checks + database_checks

    overall = "HEALTHY"

    if any(check["status"] == "ERROR" for check in all_checks):
        overall = "CRITICAL"

    elif any(check["status"] == "WARNING" for check in all_checks):
        overall = "WARNING"

    # --------------------------------------------------
    # Size formatting
    # --------------------------------------------------
    def format_size(size):
        units = ["B", "KB", "MB", "GB", "TB"]
        value = float(size)

        for unit in units:
            if value < 1024 or unit == units[-1]:
                return f"{value:.2f} {unit}"

            value /= 1024

        return f"{value:.2f} TB"

    # --------------------------------------------------
    # Return health information to the dashboard
    # --------------------------------------------------
    return {
        "overall": overall,
        "checks": checks,
        "database_checks": database_checks,
        "backup_size": format_size(total_backup_bytes),
        "backup_files": backup_files,
        "disk_free": format_size(disk.free),
        "disk_total": format_size(disk.total),
        "databases": databases,
        "latest_backup": latest_backup,
        "failed_backups": failed_backups,
        "verification_pending": verification_pending,
        "generated_at": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
    }
