"""
crud.py
All database read/write operations live here, in one place, separate
from routing logic. Routes call these functions instead of touching
`db.session` directly -- keeps the database logic testable and
reusable (e.g. an admin panel and a public API could both call
`list_seekers()` without duplicating query code).

Every function does ONE thing and returns plain Python objects
(model instances, lists, or None/bool) -- no request/response logic
belongs in this file.
"""

import json

from extensions import db
from models import Employer, Seeker, Job, SeekerProfile, Application, Notification, Follow, Message


# ==========================================================================
# EMPLOYER — Create
# ==========================================================================
def create_employer(company_name, employer_name, company_email, mobile_number, password):
    """Creates and saves a new Employer. Returns the new Employer object.
    Raises ValueError if the email is already registered."""

    if get_employer_by_email(company_email):
        raise ValueError("An employer account with this email already exists.")

    employer = Employer(
        company_name=company_name,
        employer_name=employer_name,
        company_email=company_email,
        mobile_number=mobile_number,
    )
    employer.set_password(password)

    db.session.add(employer)
    db.session.commit()
    return employer


# ==========================================================================
# EMPLOYER — Read
# ==========================================================================
def get_employer_by_id(employer_id):
    return Employer.query.get(employer_id)


def get_employer_by_email(company_email):
    return Employer.query.filter_by(company_email=company_email).first()


def list_employers():
    return Employer.query.order_by(Employer.created_at.desc()).all()


# ==========================================================================
# EMPLOYER — Update
# ==========================================================================
def update_employer(employer_id, **fields):
    """
    Updates only the fields passed in. Example:
        update_employer(3, company_name="New Name", mobile_number="9999999999")
    Password updates should go through set_employer_password() instead,
    so the password always gets hashed.
    Returns the updated Employer, or None if no employer with that id exists.
    """
    employer = get_employer_by_id(employer_id)
    if not employer:
        return None

    allowed_fields = {"company_name", "employer_name", "company_email", "mobile_number"}
    for key, value in fields.items():
        if key in allowed_fields:
            setattr(employer, key, value)

    db.session.commit()
    return employer


def set_employer_password(employer_id, new_password):
    employer = get_employer_by_id(employer_id)
    if not employer:
        return None
    employer.set_password(new_password)
    db.session.commit()
    return employer


# ==========================================================================
# EMPLOYER — Status (super admin: suspend / unsuspend / block / unblock)
# ==========================================================================
def suspend_employer(employer_id):
    employer = get_employer_by_id(employer_id)
    if not employer:
        return None
    employer.status = "Suspended"
    db.session.commit()
    return employer


def unsuspend_employer(employer_id):
    """Restores a suspended employer to Active. Does nothing if the
    employer is Blocked -- unblock_employer() should be used instead."""
    employer = get_employer_by_id(employer_id)
    if not employer:
        return None
    if employer.status == "Suspended":
        employer.status = "Active"
        db.session.commit()
    return employer


def block_employer(employer_id):
    employer = get_employer_by_id(employer_id)
    if not employer:
        return None
    employer.status = "Blocked"
    db.session.commit()
    return employer


def unblock_employer(employer_id):
    employer = get_employer_by_id(employer_id)
    if not employer:
        return None
    employer.status = "Active"
    db.session.commit()
    return employer


# ==========================================================================
# EMPLOYER — Delete
# ==========================================================================
def delete_employer(employer_id):
    """Returns True if deleted, False if no employer with that id existed."""
    employer = get_employer_by_id(employer_id)
    if not employer:
        return False

    db.session.delete(employer)
    db.session.commit()
    return True


# ==========================================================================
# SEEKER — Create
# ==========================================================================
def create_seeker(full_name, email, mobile_number, work_status, password):
    """Creates and saves a new Seeker. Returns the new Seeker object.
    Raises ValueError if the email is already registered."""

    if get_seeker_by_email(email):
        raise ValueError("An account with this email already exists.")

    seeker = Seeker(
        full_name=full_name,
        email=email,
        mobile_number=mobile_number,
        work_status=work_status,
    )
    seeker.set_password(password)

    db.session.add(seeker)
    db.session.commit()
    return seeker


# ==========================================================================
# SEEKER — Read
# ==========================================================================
def get_seeker_by_id(seeker_id):
    return Seeker.query.get(seeker_id)


def get_seeker_by_email(email):
    return Seeker.query.filter_by(email=email).first()


def list_seekers():
    return Seeker.query.order_by(Seeker.created_at.desc()).all()


# ==========================================================================
# SEEKER — Update
# ==========================================================================
def update_seeker(seeker_id, **fields):
    """
    Updates only the fields passed in. Example:
        update_seeker(7, full_name="New Name", work_status="experienced")
    """
    seeker = get_seeker_by_id(seeker_id)
    if not seeker:
        return None

    allowed_fields = {"full_name", "email", "mobile_number", "work_status"}
    for key, value in fields.items():
        if key in allowed_fields:
            setattr(seeker, key, value)

    db.session.commit()
    return seeker


def set_seeker_password(seeker_id, new_password):
    seeker = get_seeker_by_id(seeker_id)
    if not seeker:
        return None
    seeker.set_password(new_password)
    db.session.commit()
    return seeker


# ==========================================================================
# SEEKER — Status (super admin: block / unblock)
# ==========================================================================
def block_seeker(seeker_id):
    seeker = get_seeker_by_id(seeker_id)
    if not seeker:
        return None
    seeker.status = "Blocked"
    db.session.commit()
    return seeker


def unblock_seeker(seeker_id):
    seeker = get_seeker_by_id(seeker_id)
    if not seeker:
        return None
    seeker.status = "Active"
    db.session.commit()
    return seeker


# ==========================================================================
# SEEKER — Delete
# ==========================================================================
def delete_seeker(seeker_id):
    """Returns True if deleted, False if no seeker with that id existed."""
    seeker = get_seeker_by_id(seeker_id)
    if not seeker:
        return False

    db.session.delete(seeker)
    db.session.commit()
    return True


# ==========================================================================
# JOB — Create
# ==========================================================================
def create_job(employer_id, title, company_name, company_email, description,
                company_website=None, location=None, job_type="Full-time",
                experience_level="Entry", skills=None):
    """Creates and saves a new Job posting. `skills` can be a list of
    strings or an already-comma-joined string. Returns the new Job."""

    if isinstance(skills, (list, tuple)):
        skills = ",".join(s.strip() for s in skills if s.strip())

    job = Job(
        employer_id=employer_id,
        title=title,
        company_name=company_name,
        company_website=company_website,
        company_email=company_email,
        location=location,
        job_type=job_type,
        experience_level=experience_level,
        description=description,
        skills=skills,
    )

    db.session.add(job)
    db.session.commit()
    return job


# ==========================================================================
# JOB — Read
# ==========================================================================
def get_job_by_id(job_id):
    return Job.query.get(job_id)


def list_jobs_by_employer(employer_id):
    return Job.query.filter_by(employer_id=employer_id).order_by(Job.created_at.desc()).all()


def list_all_jobs():
    """Approved jobs across every employer, newest first -- used by the
    seeker-facing job search/explore page. Jobs still Pending or
    Rejected by the super admin are excluded."""
    return (
        Job.query.filter_by(status="Approved")
        .order_by(Job.created_at.desc())
        .all()
    )


def search_jobs(keyword=None, location=None, job_type=None):
    """Simple case-insensitive search over title/company/skills, plus
    optional location and job_type filters. Used by the seeker-facing
    dashboard search bar (job type dropdown + keyword + location)."""
    query = Job.query.filter_by(status="Approved")

    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            db.or_(
                Job.title.ilike(like),
                Job.company_name.ilike(like),
                Job.skills.ilike(like),
            )
        )

    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))

    if job_type:
        query = query.filter(Job.job_type.ilike(f"%{job_type}%"))

    return query.order_by(Job.created_at.desc()).all()


def list_jobs_for_admin(status=None):
    """All jobs regardless of status, newest first -- used by the super
    admin's Total Job Posts page. Pass status="Pending" to get just the
    ones awaiting review (what the dashboard/job page's table shows)."""
    query = Job.query
    if status:
        query = query.filter_by(status=status)
    return query.order_by(Job.created_at.desc()).all()


# ==========================================================================
# JOB — Approve / Reject (super admin)
# ==========================================================================
def approve_job(job_id):
    """Returns the updated Job, or None if no job with that id exists."""
    job = get_job_by_id(job_id)
    if not job:
        return None
    job.status = "Approved"
    db.session.commit()
    return job


def reject_job(job_id):
    """Returns the updated Job, or None if no job with that id exists."""
    job = get_job_by_id(job_id)
    if not job:
        return None
    job.status = "Rejected"
    db.session.commit()
    return job


# ==========================================================================
# JOB — Update
# ==========================================================================
def update_job(job_id, **fields):
    job = get_job_by_id(job_id)
    if not job:
        return None

    allowed_fields = {
        "title", "company_name", "company_website", "company_email",
        "location", "job_type", "experience_level", "description", "skills",
    }
    for key, value in fields.items():
        if key in allowed_fields:
            if key == "skills" and isinstance(value, (list, tuple)):
                value = ",".join(s.strip() for s in value if s.strip())
            setattr(job, key, value)

    db.session.commit()
    return job


# ==========================================================================
# JOB — Delete
# ==========================================================================
def delete_job(job_id):
    """Returns True if deleted, False if no job with that id existed."""
    job = get_job_by_id(job_id)
    if not job:
        return False

    db.session.delete(job)
    db.session.commit()
    return True


# ==========================================================================
# SEEKER PROFILE — Read
# ==========================================================================
def get_seeker_profile(seeker_id):
    return SeekerProfile.query.filter_by(seeker_id=seeker_id).first()


# ==========================================================================
# SEEKER PROFILE — Create / Update (upsert)
# ==========================================================================
def upsert_seeker_profile(seeker_id, **fields):
    """
    Creates the seeker's profile row if it doesn't exist yet, or
    updates it if it does. `experience`, `projects`, and `education`
    should be passed as Python lists of dicts (they get JSON-encoded
    here) -- `skills` and `additional_skills` as lists of strings
    (comma-joined here). Everything else is passed straight through.
    """
    profile = get_seeker_profile(seeker_id)
    if not profile:
        profile = SeekerProfile(seeker_id=seeker_id)
        db.session.add(profile)

    list_as_csv = {"skills", "additional_skills"}
    list_as_json = {"experience", "projects", "education"}

    allowed_fields = {
        "headline", "location", "linkedin", "github", "summary",
        "skills", "additional_skills", "experience", "projects", "education",
    }

    for key, value in fields.items():
        if key not in allowed_fields:
            continue

        if key in list_as_csv and isinstance(value, (list, tuple)):
            value = ",".join(s.strip() for s in value if s.strip())
        elif key in list_as_json and isinstance(value, (list, tuple)):
            value = json.dumps(value)

        setattr(profile, key, value)

    db.session.commit()
    return profile


# ==========================================================================
# APPLICATION — Create
# ==========================================================================
def create_application(job_id, seeker_id):
    """Creates an Application (a seeker applying to a job). Returns the
    new Application. Raises ValueError if this seeker already applied
    to this job, or if the job doesn't exist."""

    if not get_job_by_id(job_id):
        raise ValueError("That job no longer exists.")

    if has_applied(job_id, seeker_id):
        raise ValueError("You've already applied to this job.")

    application = Application(job_id=job_id, seeker_id=seeker_id)
    db.session.add(application)
    db.session.commit()
    return application


# ==========================================================================
# APPLICATION — Read
# ==========================================================================
def get_application_by_id(application_id):
    return Application.query.get(application_id)


def has_applied(job_id, seeker_id):
    return (
        Application.query.filter_by(job_id=job_id, seeker_id=seeker_id).first()
        is not None
    )


def list_applied_job_ids(seeker_id):
    """Set of job ids this seeker has already applied to -- used to
    show 'Applied' instead of an active Apply button."""
    rows = (
        Application.query.with_entities(Application.job_id)
        .filter_by(seeker_id=seeker_id)
        .all()
    )
    return {row[0] for row in rows}


def list_applications_by_seeker(seeker_id):
    return (
        Application.query.filter_by(seeker_id=seeker_id)
        .order_by(Application.applied_at.desc())
        .all()
    )


def list_applications_by_employer(employer_id):
    """Every application to any job posted by this employer, newest
    first -- powers the employer-facing Candidates page."""
    return (
        Application.query.join(Job, Application.job_id == Job.id)
        .filter(Job.employer_id == employer_id)
        .order_by(Application.applied_at.desc())
        .all()
    )


# ==========================================================================
# APPLICATION — Update
# ==========================================================================
def update_application_status(application_id, status):
    """Returns the updated Application, or None if no application with
    that id exists."""
    application = get_application_by_id(application_id)
    if not application:
        return None

    allowed_statuses = {"Applied", "Shortlisted", "Interview", "Offer", "Rejected"}
    if status in allowed_statuses:
        application.status = status
        db.session.commit()

    return application


# ==========================================================================
# NOTIFICATION — Create
# ==========================================================================
def create_notification(seeker_id, message, job_id=None):
    notification = Notification(seeker_id=seeker_id, message=message, job_id=job_id)
    db.session.add(notification)
    db.session.commit()
    return notification


# ==========================================================================
# NOTIFICATION — Read
# ==========================================================================
def list_notifications_by_seeker(seeker_id, limit=20):
    return (
        Notification.query.filter_by(seeker_id=seeker_id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .all()
    )


def count_unread_notifications(seeker_id):
    return Notification.query.filter_by(seeker_id=seeker_id, is_read=False).count()


# ==========================================================================
# NOTIFICATION — Update
# ==========================================================================
def mark_notification_read(notification_id, seeker_id):
    """Only marks it read if it actually belongs to this seeker --
    otherwise one seeker could mark another seeker's notification as
    read just by guessing an id. Returns True if it updated a row."""
    notification = Notification.query.filter_by(
        id=notification_id, seeker_id=seeker_id
    ).first()
    if not notification:
        return False

    notification.is_read = True
    db.session.commit()
    return True


def mark_all_notifications_read(seeker_id):
    Notification.query.filter_by(seeker_id=seeker_id, is_read=False).update(
        {"is_read": True}
    )
    db.session.commit()

# ==========================================================================
# CANDIDATE SEARCH (employer searching seekers)
# ==========================================================================
def search_seekers(query):
    """Searches Active seekers by their profile headline and summary
    (case-insensitive substring match), e.g. an employer searching
    "AI Engineer" matches a seeker whose headline says "AI/ML Engineer".
    Seekers with no profile yet (no headline/summary filled in) won't
    match anything -- that's expected, there's nothing to search.
    Returns a list of (Seeker, SeekerProfile) tuples, newest profile
    updates first."""
    query = (query or "").strip()
    if not query:
        return []

    like = f"%{query}%"
    return (
        db.session.query(Seeker, SeekerProfile)
        .join(SeekerProfile, SeekerProfile.seeker_id == Seeker.id)
        .filter(Seeker.status == "Active")
        .filter(
            db.or_(
                SeekerProfile.headline.ilike(like),
                SeekerProfile.summary.ilike(like),
            )
        )
        .order_by(SeekerProfile.updated_at.desc())
        .all()
    )


def get_seeker_with_profile(seeker_id):
    """Returns (Seeker, SeekerProfile) for the given id, or (None, None)
    if the seeker doesn't exist. SeekerProfile may itself be None if
    the seeker hasn't filled in their profile yet."""
    seeker = Seeker.query.get(seeker_id)
    if not seeker:
        return None, None
    return seeker, seeker.profile


# ==========================================================================
# FOLLOW — employer following a seeker's profile
# ==========================================================================
def follow_seeker(employer_id, seeker_id):
    """Idempotent -- following someone you already follow is a no-op,
    not an error, so the UI doesn't need to special-case it."""
    existing = Follow.query.filter_by(employer_id=employer_id, seeker_id=seeker_id).first()
    if existing:
        return existing

    follow = Follow(employer_id=employer_id, seeker_id=seeker_id)
    db.session.add(follow)
    db.session.commit()
    return follow


def unfollow_seeker(employer_id, seeker_id):
    Follow.query.filter_by(employer_id=employer_id, seeker_id=seeker_id).delete()
    db.session.commit()


def is_following(employer_id, seeker_id):
    return (
        Follow.query.filter_by(employer_id=employer_id, seeker_id=seeker_id).first()
        is not None
    )


def list_followed_seekers(employer_id):
    """Returns (Seeker, SeekerProfile) tuples for everyone this
    employer follows, newest follow first."""
    return (
        db.session.query(Seeker, SeekerProfile)
        .join(Follow, Follow.seeker_id == Seeker.id)
        .outerjoin(SeekerProfile, SeekerProfile.seeker_id == Seeker.id)
        .filter(Follow.employer_id == employer_id)
        .order_by(Follow.created_at.desc())
        .all()
    )


# ==========================================================================
# MESSAGES — employer <-> seeker chat
# ==========================================================================
def send_message(employer_id, seeker_id, sender_role, body=None,
                  attachment_stored_filename=None, attachment_original_filename=None,
                  attachment_content_type=None):
    """sender_role is "employer" or "seeker" -- whichever side is
    sending this particular message. Raises ValueError if there's
    neither text nor an attachment (an empty message)."""
    body = (body or "").strip() or None

    if not body and not attachment_stored_filename:
        raise ValueError("Message can't be empty.")

    if sender_role not in ("employer", "seeker"):
        raise ValueError("Invalid sender role.")

    message = Message(
        employer_id=employer_id,
        seeker_id=seeker_id,
        sender_role=sender_role,
        body=body,
        attachment_stored_filename=attachment_stored_filename,
        attachment_original_filename=attachment_original_filename,
        attachment_content_type=attachment_content_type,
    )
    db.session.add(message)
    db.session.commit()
    return message


def list_messages(employer_id, seeker_id):
    """Full thread between one employer and one seeker, oldest first
    (chat reading order)."""
    return (
        Message.query.filter_by(employer_id=employer_id, seeker_id=seeker_id)
        .order_by(Message.created_at.asc())
        .all()
    )


def get_message_by_id(message_id):
    return Message.query.get(message_id)


def mark_thread_read(employer_id, seeker_id, reader_role):
    """Marks every message in this thread sent by the OTHER side as
    read -- e.g. when the seeker opens the thread, their unread count
    should only drop for messages the employer sent."""
    other_role = "seeker" if reader_role == "employer" else "employer"
    Message.query.filter_by(
        employer_id=employer_id, seeker_id=seeker_id, sender_role=other_role, is_read=False
    ).update({"is_read": True})
    db.session.commit()


def list_conversations_for_employer(employer_id):
    """One row per seeker this employer has ever messaged (or been
    messaged by), each with the latest message and unread count from
    that seeker, newest activity first."""
    seeker_ids = [
        row[0] for row in
        db.session.query(Message.seeker_id)
        .filter(Message.employer_id == employer_id)
        .distinct()
        .all()
    ]

    conversations = []
    for seeker_id in seeker_ids:
        seeker = Seeker.query.get(seeker_id)
        if not seeker:
            continue
        last_message = (
            Message.query.filter_by(employer_id=employer_id, seeker_id=seeker_id)
            .order_by(Message.created_at.desc())
            .first()
        )
        unread_count = Message.query.filter_by(
            employer_id=employer_id, seeker_id=seeker_id, sender_role="seeker", is_read=False
        ).count()
        conversations.append({
            "seeker": seeker,
            "last_message": last_message,
            "unread_count": unread_count,
        })

    conversations.sort(
        key=lambda c: c["last_message"].created_at if c["last_message"] else 0,
        reverse=True,
    )
    return conversations


def list_conversations_for_seeker(seeker_id):
    """Same as list_conversations_for_employer, mirrored for the
    seeker's inbox -- one row per employer they've exchanged messages
    with."""
    employer_ids = [
        row[0] for row in
        db.session.query(Message.employer_id)
        .filter(Message.seeker_id == seeker_id)
        .distinct()
        .all()
    ]

    conversations = []
    for employer_id in employer_ids:
        employer = Employer.query.get(employer_id)
        if not employer:
            continue
        last_message = (
            Message.query.filter_by(employer_id=employer_id, seeker_id=seeker_id)
            .order_by(Message.created_at.desc())
            .first()
        )
        unread_count = Message.query.filter_by(
            employer_id=employer_id, seeker_id=seeker_id, sender_role="employer", is_read=False
        ).count()
        conversations.append({
            "employer": employer,
            "last_message": last_message,
            "unread_count": unread_count,
        })

    conversations.sort(
        key=lambda c: c["last_message"].created_at if c["last_message"] else 0,
        reverse=True,
    )
    return conversations


def count_unread_messages_for_seeker(seeker_id):
    return Message.query.filter_by(seeker_id=seeker_id, sender_role="employer", is_read=False).count()


def count_unread_messages_for_employer(employer_id):
    return Message.query.filter_by(employer_id=employer_id, sender_role="seeker", is_read=False).count()