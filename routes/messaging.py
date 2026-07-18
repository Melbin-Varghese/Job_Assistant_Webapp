"""
routes/messaging.py
Two related features that share this one file because they're used
together (search a candidate -> view their profile -> follow ->
message them):

1. Employer-side candidate search -- searches Seeker profiles by
   headline/summary (e.g. "AI Engineer") and lets the employer view
   a full profile and follow it.
2. Employer <-> Seeker messaging, including file/photo attachments,
   saved directly on the server's disk (see UPLOAD_DIR below).

Attachments are stored OUTSIDE the static/ folder and served through
attachment_download() below, which checks the requester is actually
one of the two participants in that message's thread before sending
the file -- static/ would make every attachment public to anyone
with the URL, regardless of login.
"""

import os
import uuid

from flask import Blueprint, render_template, request, redirect, url_for, jsonify, send_from_directory, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from crud import (
    search_seekers,
    get_seeker_with_profile,
    follow_seeker,
    unfollow_seeker,
    is_following,
    list_followed_seekers,
    send_message,
    list_messages,
    get_message_by_id,
    mark_thread_read,
    list_conversations_for_employer,
    list_conversations_for_seeker,
)
from models import Employer, Seeker

messaging_bp = Blueprint("messaging", __name__)

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads", "messages")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "pdf", "doc", "docx", "txt"}
MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024  # 10MB


def _allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _save_attachment(file_storage):
    """Saves an uploaded file under a random name (avoids collisions
    and path-traversal from a hostile original filename) and returns
    (stored_filename, original_filename, content_type), or raises
    ValueError if the file fails validation."""
    original_filename = secure_filename(file_storage.filename or "")
    if not original_filename or not _allowed_file(original_filename):
        raise ValueError("That file type isn't supported.")

    file_storage.seek(0, os.SEEK_END)
    size = file_storage.tell()
    file_storage.seek(0)
    if size > MAX_ATTACHMENT_BYTES:
        raise ValueError("File is too large (10MB max).")

    ext = original_filename.rsplit(".", 1)[1].lower()
    stored_filename = f"{uuid.uuid4().hex}.{ext}"
    file_storage.save(os.path.join(UPLOAD_DIR, stored_filename))

    return stored_filename, original_filename, file_storage.content_type


def _require_employer():
    if not (current_user.is_authenticated and isinstance(current_user, Employer)):
        abort(403)


def _require_seeker():
    if not (current_user.is_authenticated and isinstance(current_user, Seeker)):
        abort(403)


# ==========================================================================
# Candidate search (employer side) -- powers the navbar search box
# ==========================================================================
@messaging_bp.route("/employer/search-candidates")
@login_required
def search_candidates():
    _require_employer()

    q = request.args.get("q", "").strip()
    results = search_seekers(q) if q else []
    followed_ids = {seeker.id for seeker, _profile in list_followed_seekers(current_user.id)}

    return render_template(
        "empo_candidate_search.html",
        query=q,
        results=results,
        followed_ids=followed_ids,
    )


@messaging_bp.route("/employer/candidates/<int:seeker_id>/profile")
@login_required
def candidate_profile(seeker_id):
    _require_employer()

    seeker, profile = get_seeker_with_profile(seeker_id)
    if not seeker or seeker.status != "Active":
        return redirect(url_for("messaging.search_candidates"))

    return render_template(
        "empo_candidate_profile.html",
        seeker=seeker,
        profile=profile,
        following=is_following(current_user.id, seeker_id),
    )


@messaging_bp.route("/employer/candidates/<int:seeker_id>/follow", methods=["POST"])
@login_required
def toggle_follow(seeker_id):
    _require_employer()

    seeker, _profile = get_seeker_with_profile(seeker_id)
    if not seeker:
        return jsonify({"ok": False, "error": "Candidate not found."}), 404

    if is_following(current_user.id, seeker_id):
        unfollow_seeker(current_user.id, seeker_id)
        return jsonify({"ok": True, "following": False})

    follow_seeker(current_user.id, seeker_id)
    return jsonify({"ok": True, "following": True})


# ==========================================================================
# Messaging -- employer side
# ==========================================================================
@messaging_bp.route("/employer/messages")
@messaging_bp.route("/employer/messages/<int:seeker_id>")
@login_required
def employer_messages(seeker_id=None):
    _require_employer()

    conversations = list_conversations_for_employer(current_user.id)

    active_seeker = None
    thread = []
    if seeker_id:
        active_seeker, _profile = get_seeker_with_profile(seeker_id)
        if active_seeker:
            thread = list_messages(current_user.id, seeker_id)
            mark_thread_read(current_user.id, seeker_id, reader_role="employer")

    return render_template(
        "empo_messages.html",
        conversations=conversations,
        active_seeker=active_seeker,
        active_seeker_id=seeker_id,
        thread=thread,
    )


@messaging_bp.route("/employer/messages/<int:seeker_id>/send", methods=["POST"])
@login_required
def employer_send_message(seeker_id):
    _require_employer()

    body = request.form.get("body", "")
    file = request.files.get("attachment")

    stored_filename = original_filename = content_type = None
    if file and file.filename:
        try:
            stored_filename, original_filename, content_type = _save_attachment(file)
        except ValueError as e:
            conversations = list_conversations_for_employer(current_user.id)
            active_seeker, _profile = get_seeker_with_profile(seeker_id)
            thread = list_messages(current_user.id, seeker_id)
            return render_template(
                "empo_messages.html",
                conversations=conversations,
                active_seeker=active_seeker,
                active_seeker_id=seeker_id,
                thread=thread,
                error=str(e),
            )

    try:
        send_message(
            employer_id=current_user.id,
            seeker_id=seeker_id,
            sender_role="employer",
            body=body,
            attachment_stored_filename=stored_filename,
            attachment_original_filename=original_filename,
            attachment_content_type=content_type,
        )
    except ValueError:
        pass  # empty message with no file -- just no-op, nothing to send

    return redirect(url_for("messaging.employer_messages", seeker_id=seeker_id))


# ==========================================================================
# Messaging -- seeker side
# ==========================================================================
@messaging_bp.route("/seeker/messages")
@messaging_bp.route("/seeker/messages/<int:employer_id>")
@login_required
def seeker_messages(employer_id=None):
    _require_seeker()

    conversations = list_conversations_for_seeker(current_user.id)

    active_employer = None
    thread = []
    if employer_id:
        active_employer = Employer.query.get(employer_id)
        if active_employer:
            thread = list_messages(employer_id, current_user.id)
            mark_thread_read(employer_id, current_user.id, reader_role="seeker")

    return render_template(
        "seeker_messages.html",
        conversations=conversations,
        active_employer=active_employer,
        active_employer_id=employer_id,
        thread=thread,
    )


@messaging_bp.route("/seeker/messages/<int:employer_id>/send", methods=["POST"])
@login_required
def seeker_send_message(employer_id):
    _require_seeker()

    body = request.form.get("body", "")
    file = request.files.get("attachment")

    stored_filename = original_filename = content_type = None
    if file and file.filename:
        try:
            stored_filename, original_filename, content_type = _save_attachment(file)
        except ValueError as e:
            conversations = list_conversations_for_seeker(current_user.id)
            active_employer = Employer.query.get(employer_id)
            thread = list_messages(employer_id, current_user.id)
            return render_template(
                "seeker_messages.html",
                conversations=conversations,
                active_employer=active_employer,
                active_employer_id=employer_id,
                thread=thread,
                error=str(e),
            )

    try:
        send_message(
            employer_id=employer_id,
            seeker_id=current_user.id,
            sender_role="seeker",
            body=body,
            attachment_stored_filename=stored_filename,
            attachment_original_filename=original_filename,
            attachment_content_type=content_type,
        )
    except ValueError:
        pass

    return redirect(url_for("messaging.seeker_messages", employer_id=employer_id))


# ==========================================================================
# Shared attachment download (both employer and seeker use this)
# ==========================================================================
@messaging_bp.route("/messages/attachment/<int:message_id>")
@login_required
def attachment_download(message_id):
    message = get_message_by_id(message_id)
    if not message or not message.attachment_stored_filename:
        abort(404)

    # Only the two people in this thread can fetch the file -- not
    # any logged-in user who happens to guess a message id.
    is_participant = (
        (isinstance(current_user, Employer) and current_user.id == message.employer_id)
        or (isinstance(current_user, Seeker) and current_user.id == message.seeker_id)
    )
    if not is_participant:
        abort(403)

    return send_from_directory(
        UPLOAD_DIR,
        message.attachment_stored_filename,
        as_attachment=not message.is_image(),
        download_name=message.attachment_original_filename,
    )