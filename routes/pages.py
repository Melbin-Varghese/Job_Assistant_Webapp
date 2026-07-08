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


# ---------- Auth pages ----------
@pages_bp.route("/login.html")
def login():
    return render_template("login.html")


@pages_bp.route("/register.html")
def register():
    return render_template("register.html")


# ---------- Employer page ----------
@pages_bp.route("/Employer.html")
def employer():
    return render_template("Employer.html")


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


# ---------- Job Recommendation page ----------
@pages_bp.route("/recom.html")
def recom():
    return render_template("recom.html")
