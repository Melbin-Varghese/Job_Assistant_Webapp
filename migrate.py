"""
super_admin_api.py
JSON API endpoints the super admin pages call via fetch() to persist
job approvals and employer/seeker status changes. Kept separate from
your main routes file -- just register the blueprint once:

    from super_admin_api import super_admin_api
    app.register_blueprint(super_admin_api)

NOTE: There's no server-side check here confirming the caller is a
super admin, because the current login (super_admin_auth.js) is a
client-side-only demo with sessionStorage and no real backend
session/token. Before this goes anywhere near production, these
routes need a real @login_required-style guard tied to an actual
super admin session -- right now anyone who can reach these URLs
(not just people who passed the login screen) can call them.
"""

from flask import Blueprint, jsonify

import crud

super_admin_api = Blueprint("super_admin_api", __name__, url_prefix="/api/super-admin")


# ==========================================================================
# Jobs — approve / reject
# ==========================================================================
@super_admin_api.route("/jobs/<int:job_id>/approve", methods=["POST"])
def approve_job(job_id):
    job = crud.approve_job(job_id)
    if not job:
        return jsonify({"ok": False, "error": "Job not found."}), 404
    return jsonify({"ok": True, "job_id": job.id, "status": job.status})


@super_admin_api.route("/jobs/<int:job_id>/reject", methods=["POST"])
def reject_job(job_id):
    job = crud.reject_job(job_id)
    if not job:
        return jsonify({"ok": False, "error": "Job not found."}), 404
    return jsonify({"ok": True, "job_id": job.id, "status": job.status})


# ==========================================================================
# Employers (recruiters) — suspend / unsuspend / block / unblock
# ==========================================================================
@super_admin_api.route("/employers/<int:employer_id>/suspend", methods=["POST"])
def suspend_employer(employer_id):
    employer = crud.suspend_employer(employer_id)
    if not employer:
        return jsonify({"ok": False, "error": "Recruiter not found."}), 404
    return jsonify({"ok": True, "employer_id": employer.id, "status": employer.status})


@super_admin_api.route("/employers/<int:employer_id>/unsuspend", methods=["POST"])
def unsuspend_employer(employer_id):
    employer = crud.unsuspend_employer(employer_id)
    if not employer:
        return jsonify({"ok": False, "error": "Recruiter not found."}), 404
    return jsonify({"ok": True, "employer_id": employer.id, "status": employer.status})


@super_admin_api.route("/employers/<int:employer_id>/block", methods=["POST"])
def block_employer(employer_id):
    employer = crud.block_employer(employer_id)
    if not employer:
        return jsonify({"ok": False, "error": "Recruiter not found."}), 404
    return jsonify({"ok": True, "employer_id": employer.id, "status": employer.status})


@super_admin_api.route("/employers/<int:employer_id>/unblock", methods=["POST"])
def unblock_employer(employer_id):
    employer = crud.unblock_employer(employer_id)
    if not employer:
        return jsonify({"ok": False, "error": "Recruiter not found."}), 404
    return jsonify({"ok": True, "employer_id": employer.id, "status": employer.status})


# ==========================================================================
# Seekers (users) — block / unblock
# ==========================================================================
@super_admin_api.route("/seekers/<int:seeker_id>/block", methods=["POST"])
def block_seeker(seeker_id):
    seeker = crud.block_seeker(seeker_id)
    if not seeker:
        return jsonify({"ok": False, "error": "User not found."}), 404
    return jsonify({"ok": True, "seeker_id": seeker.id, "status": seeker.status})


@super_admin_api.route("/seekers/<int:seeker_id>/unblock", methods=["POST"])
def unblock_seeker(seeker_id):
    seeker = crud.unblock_seeker(seeker_id)
    if not seeker:
        return jsonify({"ok": False, "error": "User not found."}), 404
    return jsonify({"ok": True, "seeker_id": seeker.id, "status": seeker.status})