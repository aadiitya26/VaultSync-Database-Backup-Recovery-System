
from functools import wraps

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)
from werkzeug.security import check_password_hash

from app.models.database import get_connection
from app.services.audit_service import log_action

auth_bp = Blueprint("auth", __name__)


def login_required(view_function):
    @wraps(view_function)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))

        return view_function(*args, **kwargs)

    return wrapped_view


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Enter both username and password.", "error")
            return render_template("login.html")

        connection = None
        cursor = None

        try:
            connection = get_connection()
            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT id, username, password_hash
                FROM users
                WHERE username = %s
                """,
                (username,),
            )
            user = cursor.fetchone()

        except Exception:
            app_logger = __import__("logging").getLogger(__name__)
            app_logger.exception("Login database lookup failed")
            flash("Login is temporarily unavailable.", "error")
            return render_template("login.html")

        finally:
            if cursor is not None:
                cursor.close()
            if connection is not None:
                connection.close()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]

            try:
                log_action(
                    action="LOGIN_SUCCESS",
                    description=f"Administrator '{username}' logged in.",
                    status="SUCCESS",
                )
            except Exception:
                __import__("logging").getLogger(__name__).exception(
                    "Could not record successful login"
                )

            return redirect(url_for("dashboard.dashboard"))

        try:
            log_action(
                action="LOGIN_FAILED",
                description="A login attempt failed.",
                status="FAILED",
            )
        except Exception:
            __import__("logging").getLogger(__name__).exception(
                "Could not record failed login"
            )

        flash("Invalid username or password.", "error")

    return render_template("login.html")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    username = session.get("username", "administrator")
    session.clear()

    try:
        log_action(
            action="LOGOUT",
            description=f"Administrator '{username}' logged out.",
            status="SUCCESS",
        )
    except Exception:
        __import__("logging").getLogger(__name__).exception(
            "Could not record logout"
        )

    return redirect(url_for("auth.login"))
