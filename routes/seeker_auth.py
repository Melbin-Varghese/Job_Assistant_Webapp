"""
routes/seeker_auth.py
Job seeker registration, login, logout, and the seeker-facing page
suite (dashboard, profile, resume builder, skill gap, settings).

Everything lives under this one blueprint (rather than splitting
auth vs. pages like the employer side does) because the existing
templates already reference endpoints like seeker_auth.profile,
seeker_auth.resume_builder, etc.

IMPORTANT: the `name="..."` attributes below are a best guess based
on your screenshots (full_name, email, password, mobile_number,
work_status). If your actual user_login_register.html form uses
different `name` attributes, update the request.form.get(...) calls
below to match exactly -- otherwise the form will submit but the
fields will arrive empty.
"""

import json

from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from flask_login import login_user, logout_user, login_required, current_user

from crud import (
    create_seeker,
    get_seeker_by_email,
    update_seeker,
    set_seeker_password,
    get_seeker_profile,
    upsert_seeker_profile,
)
from txt_ext import extract_from_pdf, extract_from_docx
from prompts.seeker_profile_prompts import build_profile_extraction_prompt
from config import client

seeker_auth_bp = Blueprint("seeker_auth", __name__)

TEMPLATE = "user_login_register.html"


# ==========================================================================
# Auth
# ==========================================================================
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


# ==========================================================================
# Pages
# ==========================================================================
@seeker_auth_bp.route("/seeker/dashboard")
@login_required
def seeker_dashboard():
    return render_template("user.html")


@seeker_auth_bp.route("/seeker/resume-builder")
@login_required
def resume_builder():
    return render_template("resume_user.html")


@seeker_auth_bp.route("/seeker/skill-gap")
@login_required
def skill_gap():
    return render_template("skill_gap_user.html")


@seeker_auth_bp.route("/seeker/settings")
@login_required
def settings():
    seeker_profile = get_seeker_profile(current_user.id)
    return render_template(
        "settings_support_user.html",
        profile_location=seeker_profile.location if seeker_profile else "",
    )


@seeker_auth_bp.route("/seeker/settings/account", methods=["POST"])
@login_required
def settings_account():
    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip().lower()
    mobile_number = request.form.get("mobile_number", "").strip()
    location = request.form.get("location", "").strip()

    def fail(message):
        seeker_profile = get_seeker_profile(current_user.id)
        return render_template(
            "settings_support_user.html",
            profile_location=seeker_profile.location if seeker_profile else "",
            account_error=message,
        )

    if not all([full_name, email, mobile_number]):
        return fail("Please fill in your name, email, and phone number.")

    # If the email is changing, make sure it's not already taken by
    # a different seeker account.
    if email != current_user.email:
        existing = get_seeker_by_email(email)
        if existing and existing.id != current_user.id:
            return fail("That email is already in use by another account.")

    update_seeker(
        current_user.id,
        full_name=full_name,
        email=email,
        mobile_number=mobile_number,
    )
    upsert_seeker_profile(current_user.id, location=location)

    return render_template(
        "settings_support_user.html",
        profile_location=location,
        account_success="Account details saved.",
    )


@seeker_auth_bp.route("/seeker/settings/password", methods=["POST"])
@login_required
def settings_password():
    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")

    seeker_profile = get_seeker_profile(current_user.id)

    def fail(message):
        return render_template(
            "settings_support_user.html",
            profile_location=seeker_profile.location if seeker_profile else "",
            password_error=message,
        )

    if not current_user.check_password(current_password):
        return fail("Current password is incorrect.")

    if len(new_password) < 6:
        return fail("New password must be at least 6 characters.")

    set_seeker_password(current_user.id, new_password)

    return render_template(
        "settings_support_user.html",
        profile_location=seeker_profile.location if seeker_profile else "",
        password_success="Password updated.",
    )


# ==========================================================================
# Profile: view page, save (AJAX/JSON), resume upload -> auto-fill
# ==========================================================================
@seeker_auth_bp.route("/seeker/profile")
@login_required
def profile():
    seeker_profile = get_seeker_profile(current_user.id)

    profile_data = {
        "name": current_user.full_name,
        "email": current_user.email,
        "phone": current_user.mobile_number,
        "headline": seeker_profile.headline if seeker_profile else "",
        "location": seeker_profile.location if seeker_profile else "",
        "linkedin": seeker_profile.linkedin if seeker_profile else "",
        "github": seeker_profile.github if seeker_profile else "",
        "summary": seeker_profile.summary if seeker_profile else "",
        "skills": seeker_profile.skills_list() if seeker_profile else [],
        "additionalSkills": seeker_profile.additional_skills_list() if seeker_profile else [],
        "experience": seeker_profile.experience_list() if seeker_profile else [],
        "projects": seeker_profile.projects_list() if seeker_profile else [],
        "education": seeker_profile.education_list() if seeker_profile else [],
    }

    return render_template("profile_user.html", profile=profile_data)


@seeker_auth_bp.route("/seeker/profile/save", methods=["POST"])
@login_required
def profile_save():
    """Called via fetch() from profile_user.html whenever the seeker
    finishes editing (clicking 'Save Profile'). Expects the same
    `profile` object shape the page already builds client-side."""
    data = request.get_json(silent=True) or {}

    # name/email/phone live on the Seeker login row itself
    update_seeker(
        current_user.id,
        full_name=data.get("name", current_user.full_name),
        mobile_number=data.get("phone", current_user.mobile_number),
        # email intentionally not changed here -- changing login email
        # should go through a dedicated, verified flow, not a silent
        # profile-page save.
    )

    upsert_seeker_profile(
        current_user.id,
        headline=data.get("headline", ""),
        location=data.get("location", ""),
        linkedin=data.get("linkedin", ""),
        github=data.get("github", ""),
        summary=data.get("summary", ""),
        skills=data.get("skills", []),
        additional_skills=data.get("additionalSkills", []),
        experience=data.get("experience", []),
        projects=data.get("projects", []),
        education=data.get("education", []),
    )

    return jsonify({"ok": True})


def _extract_resume_text(resume_file):
    filename = resume_file.filename.lower()
    if filename.endswith(".pdf"):
        return extract_from_pdf(resume_file)
    if filename.endswith(".docx"):
        import io
        return extract_from_docx(io.BytesIO(resume_file.read()))
    raise ValueError("Only PDF and DOCX files are supported.")


@seeker_auth_bp.route("/seeker/profile/extract-resume", methods=["POST"])
@login_required
def profile_extract_resume():
    """Called via fetch() from profile_user.html's resume upload box.
    Extracts resume text server-side (supports PDF and DOCX, unlike
    the old client-side pdf.js-only approach) and asks the AI to
    return structured profile fields for the frontend to merge in."""
    resume = request.files.get("resume")
    if not resume or resume.filename == "":
        return jsonify({"error": "Please choose a resume file."}), 400

    try:
        resume_text = _extract_resume_text(resume)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Could not read that file: {str(e)}"}), 400

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": build_profile_extraction_prompt(resume_text)}],
            temperature=0,
        )
        raw = completion.choices[0].message.content.strip()

        if raw.startswith("```"):
            raw = raw.strip("`")
            raw = raw.replace("json", "", 1).strip()

        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return jsonify({"error": "The AI response wasn't valid JSON. Please try again."}), 500
    except Exception as e:
        return jsonify({"error": f"Groq API Error: {str(e)}"}), 500

    return jsonify(parsed)