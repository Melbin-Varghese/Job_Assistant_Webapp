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
import json

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

    # "Active" / "Verifying" / "Suspended" / "Blocked" -- set by the super
    # admin from the Total Recruiters page. Suspend is meant to be
    # reversible (Unsuspend); Block is the harder action (Unblock).
    status = db.Column(db.String(20), nullable=False, default="Verifying")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        # Prefixed so Flask-Login's user_loader knows which table to check.
        return f"employer-{self.id}"

    def is_active_account(self):
        return self.status not in ("Suspended", "Blocked")

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

    # "Active" / "Blocked" -- set by the super admin from the Total Users page.
    status = db.Column(db.String(20), nullable=False, default="Active")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return f"seeker-{self.id}"

    def is_active_account(self):
        return self.status != "Blocked"

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

    # "Pending" / "Approved" / "Rejected" -- set by the super admin from the
    # Total Job Posts page. Only "Approved" jobs are shown to seekers.
    status = db.Column(db.String(20), nullable=False, default="Pending")

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


class SeekerProfile(db.Model):
    """
    Extra profile info for a Seeker, kept in its own table (one row
    per seeker) rather than bolted onto the Seeker login table --
    keeps auth concerns (email/password) separate from profile
    content (skills, experience, etc).

    Repeating sections (experience, projects, education) are stored
    as JSON text rather than separate tables, since they're always
    read/written as a whole list from the profile page's JS -- no
    need to query into individual entries.
    """
    __tablename__ = "seeker_profiles"

    id = db.Column(db.Integer, primary_key=True)
    seeker_id = db.Column(db.Integer, db.ForeignKey("seekers.id"), unique=True, nullable=False)

    headline = db.Column(db.String(150), nullable=True)
    location = db.Column(db.String(150), nullable=True)
    linkedin = db.Column(db.String(255), nullable=True)
    github = db.Column(db.String(255), nullable=True)
    summary = db.Column(db.Text, nullable=True)

    # Comma-separated, matching the Job.skills pattern.
    skills = db.Column(db.Text, nullable=True)
    additional_skills = db.Column(db.Text, nullable=True)

    # JSON-encoded lists of objects, e.g.
    #   experience: [{"role": "...", "company": "...", "period": "...", "desc": "..."}]
    #   projects:   [{"title": "...", "stack": "...", "desc": "..."}]
    #   education:  [{"degree": "...", "school": "...", "period": "..."}]
    experience = db.Column(db.Text, nullable=True)
    projects = db.Column(db.Text, nullable=True)
    education = db.Column(db.Text, nullable=True)

    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    seeker = db.relationship("Seeker", backref=db.backref("profile", uselist=False))

    def skills_list(self):
        return [s.strip() for s in (self.skills or "").split(",") if s.strip()]

    def additional_skills_list(self):
        return [s.strip() for s in (self.additional_skills or "").split(",") if s.strip()]

    def experience_list(self):
        return json.loads(self.experience) if self.experience else []

    def projects_list(self):
        return json.loads(self.projects) if self.projects else []

    def education_list(self):
        return json.loads(self.education) if self.education else []

    def __repr__(self):
        return f"<SeekerProfile seeker_id={self.seeker_id}>"


class Application(db.Model):
    """
    A seeker applying to a job. One row per (job, seeker) pair -- the
    unique constraint below stops the same seeker from applying to
    the same job twice via a double-click or resubmitted form.
    """
    __tablename__ = "applications"
    __table_args__ = (
        db.UniqueConstraint("job_id", "seeker_id", name="uq_application_job_seeker"),
    )

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False)
    seeker_id = db.Column(db.Integer, db.ForeignKey("seekers.id"), nullable=False)

    # "Applied" -> "Shortlisted" / "Interview" / "Offer" / "Rejected",
    # set by the employer from the Candidates page.
    status = db.Column(db.String(30), nullable=False, default="Applied")

    applied_at = db.Column(db.DateTime, default=datetime.utcnow)

    job = db.relationship("Job", backref=db.backref("applications", lazy=True))
    seeker = db.relationship("Seeker", backref=db.backref("applications", lazy=True))

    def __repr__(self):
        return f"<Application job_id={self.job_id} seeker_id={self.seeker_id} status={self.status}>"


class Follow(db.Model):
    """
    An employer following a seeker's profile -- surfaced from the
    candidate search page. One row per (employer, seeker) pair; the
    unique constraint stops a double-click from creating duplicates.
    """
    __tablename__ = "follows"
    __table_args__ = (
        db.UniqueConstraint("employer_id", "seeker_id", name="uq_follow_employer_seeker"),
    )

    id = db.Column(db.Integer, primary_key=True)
    employer_id = db.Column(db.Integer, db.ForeignKey("employers.id"), nullable=False)
    seeker_id = db.Column(db.Integer, db.ForeignKey("seekers.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    employer = db.relationship("Employer", backref=db.backref("follows", lazy=True))
    seeker = db.relationship("Seeker", backref=db.backref("followers", lazy=True))

    def __repr__(self):
        return f"<Follow employer_id={self.employer_id} seeker_id={self.seeker_id}>"


class Message(db.Model):
    """
    A single chat message between one employer and one seeker. There's
    no separate "conversation" table -- the (employer_id, seeker_id)
    pair on each row IS the thread, since only employer<->seeker
    messaging exists (no seeker<->seeker or employer<->employer).

    sender_role tells you which side of the pair sent it ("employer"
    or "seeker"), since both participants are fixed per-thread but
    either one can be the sender of any given message.
    """
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    employer_id = db.Column(db.Integer, db.ForeignKey("employers.id"), nullable=False)
    seeker_id = db.Column(db.Integer, db.ForeignKey("seekers.id"), nullable=False)

    sender_role = db.Column(db.String(10), nullable=False)  # "employer" or "seeker"

    # Either body, attachment, or both may be present -- a message can
    # be text-only, a file with no caption, or both together.
    body = db.Column(db.Text, nullable=True)

    # Attachment storage: stored_filename is the random on-disk name
    # (avoids collisions/path traversal from the original filename);
    # original_filename is what's shown to the user.
    attachment_stored_filename = db.Column(db.String(255), nullable=True)
    attachment_original_filename = db.Column(db.String(255), nullable=True)
    attachment_content_type = db.Column(db.String(100), nullable=True)

    is_read = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    employer = db.relationship("Employer", backref=db.backref("messages", lazy=True))
    seeker = db.relationship("Seeker", backref=db.backref("messages", lazy=True))

    def is_image(self):
        return bool(self.attachment_content_type and self.attachment_content_type.startswith("image/"))

    def __repr__(self):
        return f"<Message employer_id={self.employer_id} seeker_id={self.seeker_id} sender={self.sender_role}>"


class Notification(db.Model):
    """
    A single notification for a seeker -- currently only created when
    an employer changes an application's status (Shortlisted/Rejected/
    etc), but kept general (not tied to Application specifically) so
    other event types can create these later without a new table.
    """
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    seeker_id = db.Column(db.Integer, db.ForeignKey("seekers.id"), nullable=False)

    message = db.Column(db.String(255), nullable=False)

    # Optional -- lets the notification link back to the job it's about.
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=True)

    is_read = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    seeker = db.relationship("Seeker", backref=db.backref("notifications", lazy=True))
    job = db.relationship("Job")

    def __repr__(self):
        return f"<Notification seeker_id={self.seeker_id} read={self.is_read}>"