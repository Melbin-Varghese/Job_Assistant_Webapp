"""
routes/seeker_auth.py
Job seeker registration, login, and logout.

IMPORTANT: the `name="..."` attributes below are a best guess based
on your screenshots (full_name, email, password, mobile_number,
work_status). If your actual user_login_register.html form uses
different `name` attributes, update the request.form.get(...) calls
below to match exactly -- otherwise the form will submit but the
fields will arrive empty.
"""

from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_user, logout_user, login_required

from crud import create_seeker, get_seeker_by_email

seeker_auth_bp = Blueprint("seeker_auth", __name__)

TEMPLATE = "user_login_register.html"


@seeker_auth_bp.route("/user_login_register.html", methods=["GET"])
def seeker_login_register_page():
    return render_template(TEMPLATE, active_tab="login")


@seeker_auth_bp.route("/seeker/register", methods=["POST"])
def seeker_register():
    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    mobile_number = request.form.get("mobile_number", "").strip()
    work_status = request.form.get("work_status", "fresher").strip().lower()

    def fail(message):
        return render_template(TEMPLATE, active_tab="register", error=message)

    if not all([full_name, email, password, mobile_number]):
        return fail("Please fill in all required fields.")

    if len(password) < 6:
        return fail("Password must be at least 6 characters.")

    if work_status not in ("experienced", "fresher"):
        work_status = "fresher"

    try:
        create_seeker(
            full_name=full_name,
            email=email,
            mobile_number=mobile_number,
            work_status=work_status,
            password=password,
        )
    except ValueError as e:
        return fail(str(e))

    # Registration succeeded -- send them to the login tab to sign in,
    # rather than auto-logging them in.
    return render_template(
        TEMPLATE,
        active_tab="login",
        success="Registration successful! Please log in.",
    )


@seeker_auth_bp.route("/seeker/login", methods=["POST"])
def seeker_login():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    seeker = get_seeker_by_email(email)

    if not seeker or not seeker.check_password(password):
        return render_template(TEMPLATE, active_tab="login", error="Invalid email or password.")

    login_user(seeker)
    return redirect(url_for("seeker_auth.seeker_dashboard"))


@seeker_auth_bp.route("/seeker/logout")
@login_required
def seeker_logout():
    logout_user()
    return redirect(url_for("seeker_auth.seeker_login_register_page"))


@seeker_auth_bp.route("/seeker/dashboard")
@login_required
def seeker_dashboard():
    # return render_template("seeker_dashboard.html")
    return render_template("ai_assistant.html")