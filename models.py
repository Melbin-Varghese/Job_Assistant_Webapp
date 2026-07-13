"""
models.py
Database tables. Employers and Seekers are kept as two separate
tables (not one shared "User" table) since their registration forms
collect genuinely different information -- an Employer has a company
name and no work status, a Seeker has a work status and no company.

Both inherit UserMixin so Flask-Login can manage sessions for either
type. Since Flask-Login normally expects ONE user table, we tell them
apart using a prefixed ID: "employer-5" or "seeker-5". See
extensions.py's user_loader for how that gets resolved back to the
right table.
"""

from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db


class Employer(db.Model, UserMixin):
    __tablename__ = "employers"

    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(150), nullable=False)
    employer_name = db.Column(db.String(100), nullable=False)
    company_email = db.Column(db.String(150), unique=True, nullable=False)
    mobile_number = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        # Prefixed so Flask-Login's user_loader knows which table to check.
        return f"employer-{self.id}"

    def __repr__(self):
        return f"<Employer {self.company_email}>"


class Seeker(db.Model, UserMixin):
    __tablename__ = "seekers"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    mobile_number = db.Column(db.String(20), nullable=False)

    # "experienced" or "fresher" -- matches the Work Status radio buttons
    work_status = db.Column(db.String(20), nullable=False, default="fresher")

    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return f"seeker-{self.id}"

    def __repr__(self):
        return f"<Seeker {self.email}>"


class Job(db.Model):
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)
    employer_id = db.Column(db.Integer, db.ForeignKey("employers.id"), nullable=False)

    title = db.Column(db.String(150), nullable=False)
    company_name = db.Column(db.String(150), nullable=False)
    company_website = db.Column(db.String(255), nullable=True)
    company_email = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(150), nullable=True)
    job_type = db.Column(db.String(30), nullable=False, default="Full-time")
    experience_level = db.Column(db.String(30), nullable=False, default="Entry")
    description = db.Column(db.Text, nullable=False)

    # Stored as a comma-separated string (e.g. "Figma,SQL,Excel") --
    # simplest option without a separate skills/tags table.
    skills = db.Column(db.String(500), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    employer = db.relationship("Employer", backref=db.backref("jobs", lazy=True))

    def skills_list(self):
        """Splits the stored comma-separated skills string into a list,
        stripping whitespace and dropping empty entries."""
        if not self.skills:
            return []
        return [s.strip() for s in self.skills.split(",") if s.strip()]

    def __repr__(self):
        return f"<Job {self.title} @ {self.company_name}>"