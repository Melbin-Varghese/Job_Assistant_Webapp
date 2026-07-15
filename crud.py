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
from models import Employer, Seeker, Job, SeekerProfile, Application, Notification


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
    """All jobs across every employer, newest first -- used by the
    seeker-facing job search/explore page."""
    return Job.query.order_by(Job.created_at.desc()).all()


def search_jobs(keyword=None, location=None, job_type=None):
    """Simple case-insensitive search over title/company/skills, plus
    optional location and job_type filters. Used by the seeker-facing
    dashboard search bar (job type dropdown + keyword + location)."""
    query = Job.query

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