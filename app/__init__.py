
from flask import Flask, redirect, url_for


def create_app():
    app = Flask(__name__)
    app.config.from_object("app.config.Config")

    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)

    @app.route("/")
    def home():
        return redirect(url_for("dashboard.dashboard"))

    return app
