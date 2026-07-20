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

import os

from flask import Blueprint, render_template, request, redirect, url_for, jsonify, send_from_directory, abort
from flask_login import login_required, current_user

from crud import (
    create_job,
    get_job_by_id,
    update_job,
    delete_job,
    list_jobs_by_employer,
    list_applications_by_employer,
    get_application_by_id,
    update_application_status,
    create_notification,
    count_unread_messages_for_employer,
)

employer_pages_bp = Blueprint("employer_pages", __name__)

# Must match seeker_dashboard.py's APPLICATION_RESUME_DIR -- that's
# where per-application resumes get saved when a seeker applies.
APPLICATION_RESUME_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads", "application_resumes"
)


@employer_pages_bp.route("/employer/dashboard-home")
@login_required
def dashboard():
    jobs = list_jobs_by_employer(current_user.id)
    applications = list_applications_by_employer(current_user.id)

    job_count = len(jobs)
    candidate_count = len({app.seeker_id for app in applications})  # unique applicants
    new_application_count = sum(1 for app in applications if app.status == "Applied")

    return render_template(
        "empo_dashboard.html",
        job_count=job_count,
        candidate_count=candidate_count,
        new_application_count=new_application_count,
        unread_message_count=count_unread_messages_for_employer(current_user.id),
    )


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
                unread_message_count=count_unread_messages_for_employer(current_user.id),
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
        unread_message_count=count_unread_messages_for_employer(current_user.id),
    )


@employer_pages_bp.route("/employer/jobs/<int:job_id>/edit", methods=["GET", "POST"])
@login_required
def edit_job(job_id):
    job = get_job_by_id(job_id)

    # Only the employer who posted it can edit it -- otherwise any
    # logged-in employer could edit another company's job by guessing
    # an id in the URL.
    if not job or job.employer_id != current_user.id:
        return redirect(url_for("employer_pages.jobs"))

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
            return render_template(
                "empo_job_edit.html",
                job=job,
                error="Please fill in all required fields (Job Title, Company Name, Company Email, Job Description).",
                unread_message_count=count_unread_messages_for_employer(current_user.id),
            )

        update_job(
            job_id,
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

        return redirect(url_for("employer_pages.jobs", updated=1))

    return render_template(
        "empo_job_edit.html",
        job=job,
        unread_message_count=count_unread_messages_for_employer(current_user.id),
    )


@employer_pages_bp.route("/employer/jobs/<int:job_id>/delete", methods=["POST"])
@login_required
def delete_job_route(job_id):
    job = get_job_by_id(job_id)

    # Same ownership check as edit -- silently no-ops instead of
    # erroring if the job isn't found or belongs to someone else, so
    # a stale/tampered form post can't delete another employer's job.
    if job and job.employer_id == current_user.id:
        delete_job(job_id)

    return redirect(url_for("employer_pages.jobs", deleted=1))


@employer_pages_bp.route("/employer/candidates")
@login_required
def candidates():
    applications = list_applications_by_employer(current_user.id)
    has_jobs = len(list_jobs_by_employer(current_user.id)) > 0
    return render_template(
        "empo_can_page.html",
        applications=applications,
        has_jobs=has_jobs,
        unread_message_count=count_unread_messages_for_employer(current_user.id),
    )


@employer_pages_bp.route("/employer/candidates/<int:application_id>/status", methods=["POST"])
@login_required
def update_candidate_status(application_id):
    """Called via fetch() from the Candidates page's Shortlist/Reject
    buttons. Returns JSON so the row can update without a full reload."""
    application = get_application_by_id(application_id)

    # Make sure this application actually belongs to one of THIS
    # employer's jobs -- otherwise any logged-in employer could edit
    # any other employer's applications by guessing an id.
    if not application or application.job.employer_id != current_user.id:
        return jsonify({"ok": False, "error": "Application not found."}), 404

    status = request.form.get("status", "").strip()
    updated = update_application_status(application_id, status)
    if not updated:
        return jsonify({"ok": False, "error": "Could not update status."}), 400

    # Let the seeker know -- only for the two decisions that actually
    # mean something to them; "Interview"/"Offer" can be added the
    # same way later if those get their own UI actions.
    if updated.status == "Shortlisted":
        create_notification(
            seeker_id=updated.seeker_id,
            message=f"You've been shortlisted for {updated.job.title} at {updated.job.company_name}!",
            job_id=updated.job_id,
        )
    elif updated.status == "Rejected":
        create_notification(
            seeker_id=updated.seeker_id,
            message=f"Your application for {updated.job.title} at {updated.job.company_name} was not selected this time.",
            job_id=updated.job_id,
        )

    return jsonify({"ok": True, "status": updated.status})


@employer_pages_bp.route("/employer/candidates/<int:application_id>/resume")
@login_required
def download_candidate_resume(application_id):
    """Lets the employer view/download the resume the candidate
    attached to THIS specific application. Only the employer who owns
    the job this application is for can fetch it -- matches the same
    ownership pattern as update_candidate_status()."""
    application = get_application_by_id(application_id)

    if not application or application.job.employer_id != current_user.id:
        abort(404)

    if not application.resume_stored_filename:
        abort(404)

    return send_from_directory(
        APPLICATION_RESUME_DIR,
        application.resume_stored_filename,
        as_attachment=False,
        download_name=application.resume_original_filename,
    )


@employer_pages_bp.route("/employer/settings")
@login_required
def settings():
    return render_template(
        "empo_setting_support_profile.html",
        unread_message_count=count_unread_messages_for_employer(current_user.id),
    )


@employer_pages_bp.route("/employer/profile")
@login_required
def profile():
    jobs = list_jobs_by_employer(current_user.id)
    applications = list_applications_by_employer(current_user.id)

    # "Reviewed" = employer has made some decision on it, i.e. it's
    # moved past the initial "Applied" state. Interview/Offer aren't
    # reachable from the current Candidates page UI (only
    # Shortlist/Reject buttons exist there yet), so those two will
    # read 0 until that's wired up -- that's accurate, not a bug.
    reviewed_statuses = {"Shortlisted", "Interview", "Offer", "Rejected"}
    profile_stats = {
        "jobs_posted": len(jobs),
        "candidates_reviewed": sum(1 for a in applications if a.status in reviewed_statuses),
        "interviews_scheduled": sum(1 for a in applications if a.status == "Interview"),
        "offers_extended": sum(1 for a in applications if a.status == "Offer"),
    }

    return render_template(
        "empo_profile.html",
        profile_stats=profile_stats,
        recent_jobs=jobs[:3],
        unread_message_count=count_unread_messages_for_employer(current_user.id),
    )