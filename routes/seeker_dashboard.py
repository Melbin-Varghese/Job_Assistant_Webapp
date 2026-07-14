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

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user

from crud import search_jobs, create_application, list_applied_job_ids

seeker_dashboard_bp = Blueprint("seeker_dashboard", __name__)


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

    return render_template(
        "user.html",
        jobs=jobs,
        search_active=search_active,
        search_job_type=job_type,
        search_keyword=keyword,
        search_location=location,
        applied_job_ids=list_applied_job_ids(current_user.id),
    )


@seeker_dashboard_bp.route("/seeker/jobs/apply", methods=["POST"])
@login_required
def apply_to_job():
    """Called via fetch() from the job details modal's Apply button."""
    job_id = request.form.get("job_id", type=int)
    if not job_id:
        return jsonify({"ok": False, "error": "Missing job id."}), 400

    try:
        create_application(job_id=job_id, seeker_id=current_user.id)
    except ValueError as e:
        # Already applied, or the job was removed -- not a server error,
        # just tell the frontend why it didn't go through.
        return jsonify({"ok": False, "error": str(e)}), 400

    return jsonify({"ok": True, "message": "Application submitted."})