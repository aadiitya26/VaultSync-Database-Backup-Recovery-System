
import logging

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
)

from app.config import Config
from app.models.database import get_connection
from app.routes.auth import login_required
from app.services.database_service import (
    add_managed_database,
    get_database_by_name,
)
from app.services.backup_service import create_backup
from app.services.restore_service import restore_backup
from app.services.database_service import validate_database_exists


logger = logging.getLogger(__name__)

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    connection = get_connection()
    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT COUNT(*) AS total FROM managed_databases"
        )
        total_databases = cursor.fetchone()["total"]

        cursor.execute(
            "SELECT COUNT(*) AS total FROM backups"
        )
        total_backups = cursor.fetchone()["total"]

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM backups
            WHERE status = 'VERIFIED'
            """
        )
        verified_backups = cursor.fetchone()["total"]

        cursor.execute(
            """
            SELECT id, name, host, port, username, created_at
            FROM managed_databases
            ORDER BY id DESC
            """
        )
        databases = cursor.fetchall()

        cursor.execute(
            """
            SELECT
                b.id,
                b.database_id,
                d.name AS database_name,
                b.filename,
                b.file_path,
                b.file_size,
                b.status,
                b.created_at
            FROM backups AS b
            LEFT JOIN managed_databases AS d
                ON b.database_id = d.id
            ORDER BY b.created_at DESC, b.id DESC
            LIMIT 10
            """
        )
        backups = cursor.fetchall()

        cursor.execute(
            """
            SELECT action, description, status, created_at
            FROM audit_logs
            ORDER BY created_at DESC, id DESC
            LIMIT 10
            """
        )
        audit_logs = cursor.fetchall()

    finally:
        if cursor is not None:
            cursor.close()
        connection.close()

    return render_template(
        "dashboard.html",
        total_databases=total_databases,
        total_backups=total_backups,
        verified_backups=verified_backups,
        databases=databases,
        backups=backups,
        audit_logs=audit_logs,
        restore_host=Config.MYSQL_HOST,
        restore_port=Config.MYSQL_PORT,
    )


@dashboard_bp.route("/databases/register", methods=["POST"])
@login_required
def register_database():
    name = request.form.get("name", "").strip()
    host = request.form.get("host", "").strip()
    port = request.form.get("port", "3306").strip()

    try:
        result = add_managed_database(
            name=name,
            host=host,
            port=port,
            username=Config.MYSQL_USER,
        )
        flash(
            f"Database '{result['name']}' registered successfully.",
            "success",
        )

    except ValueError as exc:
        flash(str(exc), "error")

    except Exception:
        logger.exception("Database registration failed.")
        flash(
            "Registration failed because of an unexpected error. "
            "Check the application logs.",
            "error",
        )

    return redirect(url_for("dashboard.dashboard"))


@dashboard_bp.route("/backups/create", methods=["POST"])
@login_required
def create_database_backup():
    database_name = request.form.get("database_name", "").strip()

    if not database_name:
        flash("Select a database to back up.", "error")
        return redirect(url_for("dashboard.dashboard"))

    try:
        database = get_database_by_name(database_name)

        if not database:
            raise ValueError(
                f"Database '{database_name}' is not registered."
            )

        result = create_backup(database_name)

        flash(
            f"Backup created successfully: {result['filename']}",
            "success",
        )

        retention = result.get("retention", {})
        if retention.get("errors"):
            flash(
                "The backup succeeded, but retention reported errors. "
                "Check the application logs.",
                "error",
            )
        elif retention.get("status") == "FAILED":
            flash(
                "The backup succeeded, but retention could not complete.",
                "error",
            )

    except ValueError as exc:
        flash(str(exc), "error")

    except Exception:
        logger.exception(
            "Manual backup failed for database '%s'.",
            database_name,
        )
        flash(
            f"Backup failed for '{database_name}'. "
            "Check the application logs.",
            "error",
        )

    return redirect(url_for("dashboard.dashboard"))


@dashboard_bp.route(
    "/backups/<int:backup_id>/restore",
    methods=["POST"],
)
@login_required
def restore_database_backup(backup_id):
    target_database = request.form.get("target_database", "").strip()
    confirmation = request.form.get("confirm_restore")

    if confirmation != "yes":
        flash("Restore was not confirmed.", "error")
        return redirect(url_for("dashboard.dashboard"))

    if not target_database:
        flash("Select a target database for restoration.", "error")
        return redirect(url_for("dashboard.dashboard"))

    try:
        # The restore service currently uses Config's MySQL server.
        # Only allow registered targets on that same configured server.
        target = get_database_by_name(target_database)

        if not target:
            raise ValueError(
                f"Target database '{target_database}' is not registered."
            )

        if (
            target["host"].lower() != Config.MYSQL_HOST.lower()
            or int(target["port"]) != int(Config.MYSQL_PORT)
        ):
            raise ValueError(
                "This restore service supports targets on the configured "
                "MySQL server only. The selected database's host or port "
                "does not match the application's configured server."
            )

        validate_database_exists(
            target_database,
            Config.MYSQL_HOST,
            Config.MYSQL_PORT,
        )

        result = restore_backup(
            backup_id=backup_id,
            target_database=target_database,
        )

        flash(
            f"Backup '{result['filename']}' restored successfully "
            f"to '{result['target_database']}'.",
            "success",
        )

    except (ValueError, FileNotFoundError) as exc:
        flash(str(exc), "error")

    except Exception:
        logger.exception(
            "Restore failed for backup ID %s to database '%s'.",
            backup_id,
            target_database,
        )
        flash(
            "Restore failed. Check the application logs and audit activity.",
            "error",
        )

    return redirect(url_for("dashboard.dashboard"))
