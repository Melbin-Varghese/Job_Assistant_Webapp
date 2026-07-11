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

from extensions import db
from models import Employer, Seeker


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
