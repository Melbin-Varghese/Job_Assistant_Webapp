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
from datetime import datetime

from flask import Flask, redirect, url_for, render_template

import config
from extensions import db, login_manager
import crud

# Import models so SQLAlchemy knows about them before create_all() runs.
import models  # noqa: F401

from routes.seeker_auth import seeker_auth_bp
from routes.seeker_dashboard import seeker_dashboard_bp
from routes.employer_auth import employer_auth_bp
from routes.employer_pages import employer_pages_bp
from routes.chatbot import chatbot_bp
from routes.ai_assistant import ai_assistant_bp
from routes.ats_checker import ats_checker_bp
from routes.cover_letter import cover_letter_bp
from routes.automation import automation_bp
from routes.recommendation import recommendation_bp
from routes.job_browse import job_browse_bp
from super_admin_api import super_admin_api

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
    app.register_blueprint(seeker_dashboard_bp)
    app.register_blueprint(employer_auth_bp)
    app.register_blueprint(employer_pages_bp)
    # app.register_blueprint(pages_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(ai_assistant_bp)
    app.register_blueprint(ats_checker_bp)
    app.register_blueprint(cover_letter_bp)
    app.register_blueprint(automation_bp)
    app.register_blueprint(recommendation_bp)
    app.register_blueprint(job_browse_bp)
    app.register_blueprint(super_admin_api)

    @app.route("/")
    def index():
        featured_jobs = crud.list_all_jobs()[:4]
        return render_template("main_explore.html", featured_jobs=featured_jobs)

    @app.route("/ai-coach")
    def ai_coach():
        return render_template("chatbot.html")
    
    @app.route("/resources")
    def resources():
        return render_template("resource.html")
    @app.route("/coming_soon")
    def coming_soon():
        return render_template("coming_soon.html")
    

    @app.route("/about")
    def about():
        return render_template("about.html")
    

    @app.route("/terms_of_services")
    def terms_of_services():
        return render_template("terms_of_services.html")
    
    @app.route("/privacy_policy")
    def privacy_policy():
        return render_template("privacy_policy.html")
    
    @app.route("/contact")
    def contact():
        return render_template("contact.html")
    
    @app.route("/super_admin_login")
    def super_admin_login():
        return render_template("super_admin_login.html")
    

    @app.route("/super_admin_dashboard")
    def super_admin_dashboard():
        employers = crud.list_employers()
        seekers = crud.list_seekers()
        all_jobs = crud.list_jobs_for_admin()

        stats = {
            "total_employers": len(employers),
            "active_employers": sum(1 for e in employers if e.status == "Active"),
            "suspended_employers": sum(
                1 for e in employers if e.status in ("Suspended", "Blocked")
            ),
            "total_seekers": len(seekers),
            "active_seekers": sum(1 for s in seekers if s.status == "Active"),
            "flagged_seekers": sum(1 for s in seekers if s.status == "Blocked"),
            "total_jobs": len(all_jobs),
            "pending_jobs": sum(1 for j in all_jobs if j.status == "Pending"),
            "approved_jobs": sum(1 for j in all_jobs if j.status == "Approved"),
        }

        pending_jobs = [j for j in all_jobs if j.status == "Pending"][:5]

        # Recruiters and job seekers merged into one "recent registrations"
        # feed, newest first. Employer.status can be "Verifying" -- the
        # template's status pill only branches on Active/Suspended/else
        # Blocked, so a Verifying recruiter will currently render as
        # "Blocked" here. Worth adding a Verifying branch to the template
        # if that distinction matters on this page.
        recent_employers = [
            {
                "name": e.employer_name,
                "email": e.company_email,
                "role": "Recruiter",
                "status": e.status,
                "created_at": e.created_at,
            }
            for e in employers
        ]
        recent_seekers = [
            {
                "name": s.full_name,
                "email": s.email,
                "role": "Job Seeker",
                "status": s.status,
                "created_at": s.created_at,
            }
            for s in seekers
        ]
        recent_users = sorted(
            recent_employers + recent_seekers,
            key=lambda u: u["created_at"] or datetime.min,
            reverse=True,
        )[:5]

        return render_template(
            "super_admin_dashboard.html",
            stats=stats,
            pending_jobs=pending_jobs,
            recent_users=recent_users,
        )
    
    @app.route("/super_admin_user")
    def super_admin_user():
        seekers = crud.list_seekers()
        return render_template(
            "super_admin_user.html",
            seekers=seekers,
            total_seekers_count=len(seekers),
            active_seekers_count=sum(1 for s in seekers if s.status == "Active"),
            blocked_seekers_count=sum(1 for s in seekers if s.status == "Blocked"),
        )
    
    @app.route("/super_admin_job")
    def super_admin_job():
        all_jobs = crud.list_jobs_for_admin()
        pending_jobs = [j for j in all_jobs if j.status == "Pending"]
        approved_jobs_count = sum(1 for j in all_jobs if j.status == "Approved")
        rejected_jobs_count = sum(1 for j in all_jobs if j.status == "Rejected")
        return render_template(
            "super_admin_job.html",
            pending_jobs=pending_jobs,
            total_jobs_count=len(all_jobs),
            approved_jobs_count=approved_jobs_count,
            rejected_jobs_count=rejected_jobs_count,
        )
    
    @app.route("/super_admin_profile")
    def super_admin_profile():
        return render_template("super_admin_profile.html")

    @app.route("/super_admin_recruiters")
    def super_admin_recruiters():
        employers = crud.list_employers()
        return render_template(
            "super_admin_recruiters.html",
            employers=employers,
            total_employers_count=len(employers),
            active_employers_count=sum(1 for e in employers if e.status == "Active"),
            verifying_employers_count=sum(1 for e in employers if e.status == "Verifying"),
            suspended_or_blocked_employers_count=sum(
                1 for e in employers if e.status in ("Suspended", "Blocked")
            ),
        )
    

    @app.route("/super_admin_setting")
    def super_admin_setting():
        return render_template("super_admin_setting.html")

    @app.route("/support_user")
    def support_user():
        return render_template("settings_support_user.html")
    @app.route("/empo_job_posting_page")
    def empo_job_posting_page():
        return render_template("empo_job_posting_page.html")
    
    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)