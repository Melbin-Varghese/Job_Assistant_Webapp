"""
routes/employer_auth.py
Employer registration, login, and logout. Uses the same toggle-tab
template pattern as before (one HTML file, two forms).

IMPORTANT: the `name="..."` attributes below match your original
Employer.html form (company_name, employer_name, company_email,
mobile_number, password, confirm_password). If your current
empolyer_login_register.html uses different `name` attributes,
update the request.form.get(...) calls below to match.
"""

from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_user, logout_user, login_required

from crud import create_employer, get_employer_by_email

employer_auth_bp = Blueprint("employer_auth", __name__)

TEMPLATE = "empolyer_login_register.html"


@employer_auth_bp.route("/empolyer_login_register.html", methods=["GET"])
def employer_login_register_page():
    return render_template(TEMPLATE, active_tab="login")


@employer_auth_bp.route("/employer/register", methods=["POST"])
def employer_register():
    company_name = request.form.get("company_name", "").strip()
    employer_name = request.form.get("employer_name", "").strip()
    company_email = request.form.get("company_email", "").strip().lower()
    mobile_number = request.form.get("mobile_number", "").strip()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    def fail(message):
        return render_template(TEMPLATE, active_tab="register", error=message)

    if not all([company_name, employer_name, company_email, mobile_number, password]):
        return fail("Please fill in all fields.")

    if password != confirm_password:
        return fail("Passwords do not match.")

    if len(password) < 8:
        return fail("Password must be at least 8 characters.")

    try:
        create_employer(
            company_name=company_name,
            employer_name=employer_name,
            company_email=company_email,
            mobile_number=mobile_number,
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


@employer_auth_bp.route("/employer/login", methods=["POST"])
def employer_login():
    company_email = request.form.get("company_email", "").strip().lower()
    password = request.form.get("password", "")

    employer = get_employer_by_email(company_email)

    if not employer or not employer.check_password(password):
        return render_template(TEMPLATE, active_tab="login", error="Invalid email or password.")

    login_user(employer)
    return redirect(url_for("employer_pages.dashboard"))


@employer_auth_bp.route("/employer/logout")
@login_required
def employer_logout():
    logout_user()
    return redirect(url_for("employer_auth.employer_login_register_page"))


@employer_auth_bp.route("/employer/dashboard")
@login_required
def employer_dashboard():
    # Kept for backward compatibility with anything still linking here;
    # the real dashboard now lives in routes/employer_pages.py.
    return redirect(url_for("employer_pages.dashboard"))