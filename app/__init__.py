from flask import Flask

def create_app():
    app = Flask(__name__)

    app.config.from_object("app.config.Config")

    @app.route("/")
    def home():
        return "VaultSync is running!"

    return app