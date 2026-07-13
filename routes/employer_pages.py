"""
routes/employer_pages.py
The recruiter-facing dashboard suite: overview, job postings,
candidates, settings, and the employer's own profile page.

All routes here require a logged-in Employer (flask_login's
current_user). Job posting is the one page with real persistence so
far -- it reads/writes the Job table via crud.py. Candidates/settings
still use demo data; wire those up the same way once you have real
models for them.
"""

from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user

from crud import create_job, list_jobs_by_employer

employer_pages_bp = Blueprint("employer_pages", __name__)


@employer_pages_bp.route("/employer/dashboard-home")
@login_required
def dashboard():
    return render_template("empo_dashboard.html")


@employer_pages_bp.route("/employer/jobs", methods=["GET", "POST"])
@login_required
def jobs():
    if request.method == "POST":
        title = request.form.get("jobTitle", "").strip()
        company_name = request.form.get("companyName", "").strip()
        company_website = request.form.get("companyWebsite", "").strip()
        company_email = request.form.get("companyEmail", "").strip()
        location = request.form.get("location", "").strip()
        job_type = request.form.get("jobType", "Full-time").strip()
        experience_level = request.form.get("experience", "Entry").strip()
        description = request.form.get("jobDescription", "").strip()
        skills_raw = request.form.get("keySkills", "").strip()

        if not all([title, company_name, company_email, description]):
            # Required fields missing -- re-render with what they typed
            # still in the form isn't wired up here (the fields would
            # reset), so at minimum we don't silently drop the request.
            return render_template(
                "empo_job_posting_page.html",
                jobs=list_jobs_by_employer(current_user.id),
                error="Please fill in all required fields (Job Title, Company Name, Company Email, Job Description).",
            )

        create_job(
            employer_id=current_user.id,
            title=title,
            company_name=company_name,
            company_website=company_website or None,
            company_email=company_email,
            location=location or None,
            job_type=job_type or "Full-time",
            experience_level=experience_level or "Entry",
            description=description,
            skills=skills_raw,
        )

        # Redirect (POST/redirect/GET) so refreshing the page doesn't
        # re-submit the form, and so the new job shows up in the list.
        return redirect(url_for("employer_pages.jobs", posted=1))

    return render_template(
        "empo_job_posting_page.html",
        jobs=list_jobs_by_employer(current_user.id),
    )


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