"""
routes/employer_pages.py
The recruiter-facing dashboard suite: overview, job postings,
candidates, settings, and the employer's own profile page.

All routes here require a logged-in Employer (flask_login's
current_user). The templates read current_user.employer_name,
current_user.company_name, current_user.company_email, and
current_user.mobile_number directly -- no data is passed in from
these view functions yet, since the pages are still using demo
data for jobs/candidates/stats. Wire those up via crud.py once you
have real Job/Candidate models.
"""

from flask import Blueprint, render_template
from flask_login import login_required

employer_pages_bp = Blueprint("employer_pages", __name__)


@employer_pages_bp.route("/employer/dashboard-home")
@login_required
def dashboard():
    return render_template("empo_dashboard.html")


@employer_pages_bp.route("/employer/jobs")
@login_required
def jobs():
    return render_template("empo_job_posting_page.html")


@employer_pages_bp.route("/employer/candidates")
@login_required
def candidates():
    return render_template("empo_can_page.html")


@employer_pages_bp.route("/employer/settings")
@login_required
def settings():
    return render_template("empo_setting_support_profile.html")


@employer_pages_bp.route("/employer/profile")
@login_required
def profile():
    return render_template("empo_profile.html")
