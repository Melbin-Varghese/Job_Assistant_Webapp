"""
routes/pages.py
All the simple pages that just render a template with no extra logic.
Grouped together using a Flask Blueprint so app.py doesn't need to
know about every single page individually.
"""

from flask import Blueprint, render_template

pages_bp = Blueprint("pages", __name__)


# ---------- Home / Explore page ----------
# Both "/" and "/main_explore.html" show the same page, so it doesn't
# matter which link style you use in your HTML files.
@pages_bp.route("/")
@pages_bp.route("/main_explore.html")
def explore():
    return render_template("main_explore.html")


# ---------- Resources page ----------
@pages_bp.route("/resource.html")
def resource():
    return render_template("resource.html")


# ---------- Seekers pages ----------
@pages_bp.route("/user_login_register.html")
def seekers():
    return render_template("user_login_register.html")


@pages_bp.route("/automation.html")
def automation():
    return render_template("automation.html")


# ---------- Employer page ----------
@pages_bp.route("/empolyer_login_register.html")
def employer():
    return render_template("empolyer_login_register.html")


# ---------- Footer pages ----------
@pages_bp.route("/about.html")
def about():
    return render_template("about.html")


@pages_bp.route("/contact.html")
def contact():
    return render_template("contact.html")


@pages_bp.route("/privacy_policy.html")
def privacy_policy():
    return render_template("privacy_policy.html")


@pages_bp.route("/terms_of_services.html")
def terms_of_services():
    return render_template("terms_of_services.html")


@pages_bp.route("/super_admin_login.html")
def super_admin_login():
    return render_template("super_admin_login.html")

@pages_bp.route("/super_admin_dashboard.html")
def super_admin_dashboard():
    return render_template("super_admin_dashboard.html")


@pages_bp.route("/super_admin_user.html")
def super_admin_user():
    return render_template("super_admin_user.html")

@pages_bp.route("/super_admin_job.html")
def super_admin_job():
    return render_template("super_admin_job.html")

@pages_bp.route("/super_admin_profile.html")
def super_admin_profile():
    return render_template("super_admin_profile.html")

@pages_bp.route("/super_admin_recruiters.html")
def super_admin_recruiters():
    return render_template("super_admin_recruiters.html")

@pages_bp.route("/super_admin_setting.html")
def super_admin_setting():
    return render_template("super_admin_setting.html")

# ----------settings_support_user page ----------


@pages_bp.route("/settings_support_user.html")
def settings_support_user():
    return render_template("settings_support_user.html")
