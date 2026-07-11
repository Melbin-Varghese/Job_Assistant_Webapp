"""
app.py
Application factory / entry point. Wires together config, the shared
extensions (db, login_manager), the models, and every blueprint.

Run with:
    python app.py
or, for development with auto-reload:
    flask --app app run --debug
"""

import os

from flask import Flask, redirect, url_for, render_template

import config
from extensions import db, login_manager

# Import models so SQLAlchemy knows about them before create_all() runs.
import models  # noqa: F401

from routes.seeker_auth import seeker_auth_bp
from routes.employer_auth import employer_auth_bp
from routes.employer_pages import employer_pages_bp
from routes.chatbot import chatbot_bp
from routes.ai_assistant import ai_assistant_bp
from routes.ats_checker import ats_checker_bp
from routes.cover_letter import cover_letter_bp
from routes.recommendation import recommendation_bp

# If you already have other blueprints in routes/ (e.g. a "pages"
# blueprint powering resource.html, about.html, etc.), import
# and register them here the same way:
# from routes.pages import pages_bp


def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = config.SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key-change-me")

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "seeker_auth.seeker_login_register_page"

    app.register_blueprint(seeker_auth_bp)
    app.register_blueprint(employer_auth_bp)
    app.register_blueprint(employer_pages_bp)
    # app.register_blueprint(pages_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(ai_assistant_bp)
    app.register_blueprint(ats_checker_bp)
    app.register_blueprint(cover_letter_bp)
    app.register_blueprint(recommendation_bp)

    @app.route("/")
    def index():
        return render_template("main_explore.html")

    @app.route("/ai-coach")
    def ai_coach():
        return render_template("chatbot.html")

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)