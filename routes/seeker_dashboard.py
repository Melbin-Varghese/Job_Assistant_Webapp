"""
routes/seeker_dashboard.py
The job seeker's dashboard page and the job-search bar on it.

Split out from seeker_auth.py so that file stays focused on
auth/account pages (register, login, logout, profile, settings) while
this one owns the dashboard + search behavior, which is likely to
grow (pagination, saved searches, filters, etc.).

IMPORTANT -- registration: this blueprint must be registered in your
app factory / app.py alongside seeker_auth_bp, e.g.:

    from seeker_dashboard import seeker_dashboard_bp
    app.register_blueprint(seeker_dashboard_bp)

IMPORTANT -- url_for references: the dashboard route used to live at
seeker_auth.seeker_dashboard. It's now seeker_dashboard.dashboard.
Anywhere that referenced the old endpoint needs updating:
  - seeker_auth.py's login route (redirects here after login)
  - user.html's sidebar "Dashboard" link
Both are already updated to match in this project; if you have other
templates/routes pointing at seeker_auth.seeker_dashboard, update
those too.
"""

import os
import uuid

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from crud import (
    search_jobs,
    create_application,
    list_applied_job_ids,
    list_applications_by_seeker,
    list_notifications_by_seeker,
    count_unread_notifications,
    count_unread_messages_for_seeker,
    mark_all_notifications_read,
    recommend_jobs_for_seeker,
)

seeker_dashboard_bp = Blueprint("seeker_dashboard", __name__)

# Per-application resumes live outside static/ (like message attachments)
# so they aren't publicly reachable by URL guessing -- only the employer
# who owns the job (checked in employer_pages.py's download route) or
# the seeker who applied can fetch one.
APPLICATION_RESUME_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads", "application_resumes"
)
os.makedirs(APPLICATION_RESUME_DIR, exist_ok=True)

ALLOWED_RESUME_EXTENSIONS = {"pdf", "doc", "docx"}
MAX_RESUME_BYTES = 10 * 1024 * 1024  # 10MB


def _allowed_resume_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_RESUME_EXTENSIONS


def _save_application_resume(file_storage):
    """Saves the resume attached to a single job application under a
    random on-disk name (avoids collisions/path traversal from a
    hostile original filename) and returns (stored_filename,
    original_filename), or raises ValueError if validation fails."""
    original_filename = secure_filename(file_storage.filename or "")
    if not original_filename or not _allowed_resume_file(original_filename):
        raise ValueError("Only PDF and DOC/DOCX resumes are supported.")

    file_storage.seek(0, os.SEEK_END)
    size = file_storage.tell()
    file_storage.seek(0)
    if size > MAX_RESUME_BYTES:
        raise ValueError("Resume file is too large (10MB max).")

    ext = original_filename.rsplit(".", 1)[1].lower()
    stored_filename = f"{uuid.uuid4().hex}.{ext}"
    file_storage.save(os.path.join(APPLICATION_RESUME_DIR, stored_filename))

    return stored_filename, original_filename


@seeker_dashboard_bp.route("/seeker/dashboard")
@login_required
def dashboard():
    job_type = request.args.get("job_type", "").strip()
    keyword = request.args.get("keyword", "").strip()
    location = request.args.get("location", "").strip()

    # Only run a search (and show the results panel) once the seeker has
    # actually used the search bar -- otherwise the dashboard renders
    # its normal default content with no results section.
    search_active = bool(job_type or keyword or location)
    jobs = search_jobs(keyword=keyword or None, location=location or None,
                        job_type=job_type or None) if search_active else []

    # Shown under the search bar when the seeker ISN'T actively
    # searching -- jobs matched against the skills on their profile
    # (from their uploaded resume), so they see relevant openings
    # without having to search manually.
    recommended_jobs = [] if search_active else recommend_jobs_for_seeker(current_user.id)

    return render_template(
        "user.html",
        jobs=jobs,
        search_active=search_active,
        search_job_type=job_type,
        search_keyword=keyword,
        search_location=location,
        recommended_jobs=recommended_jobs,
        applied_job_ids=list_applied_job_ids(current_user.id),
        notifications=list_notifications_by_seeker(current_user.id),
        unread_notification_count=count_unread_notifications(current_user.id),
        unread_message_count=count_unread_messages_for_seeker(current_user.id),
    )


@seeker_dashboard_bp.route("/seeker/applications")
@login_required
def my_applications():
    """The 'Track Manual Application' page -- shows every job this
    seeker has applied to (via the in-app Apply button) and the
    recruiter's current decision on each one, newest first."""
    applications = list_applications_by_seeker(current_user.id)
    return render_template("seeker_applications.html", applications=applications)


@seeker_dashboard_bp.route("/seeker/notifications/read-all", methods=["POST"])
@login_required
def mark_notifications_read():
    """Called via fetch() when the seeker opens the notification bell."""
    mark_all_notifications_read(current_user.id)
    return jsonify({"ok": True})


@seeker_dashboard_bp.route("/seeker/jobs/apply", methods=["POST"])
@login_required
def apply_to_job():
    """Called via fetch() from the job details modal / job browse page's
    Apply button. The frontend sends the job id AND a resume file --
    that resume gets saved here and attached to the Application row so
    the employer can view/download exactly what this seeker submitted
    for this specific job."""
    job_id = request.form.get("job_id", type=int)
    if not job_id:
        return jsonify({"ok": False, "error": "Missing job id."}), 400

    resume_file = request.files.get("resume")
    resume_stored_filename = resume_original_filename = None

    if resume_file and resume_file.filename:
        try:
            resume_stored_filename, resume_original_filename = _save_application_resume(resume_file)
        except ValueError as e:
            return jsonify({"ok": False, "error": str(e)}), 400

    try:
        create_application(
            job_id=job_id,
            seeker_id=current_user.id,
            resume_stored_filename=resume_stored_filename,
            resume_original_filename=resume_original_filename,
        )
    except ValueError as e:
        # Already applied, or the job was removed -- not a server error,
        # just tell the frontend why it didn't go through.
        return jsonify({"ok": False, "error": str(e)}), 400

    return jsonify({"ok": True, "message": "Application submitted."})