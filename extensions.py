"""
extensions.py
Holds the Flask extension objects (database, login manager) in their
own file, separate from app.py and models.py, to avoid circular
imports.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()


@login_manager.user_loader
def load_user(prefixed_id):
    """
    Flask-Login calls this on every request to reload the logged-in
    account from its session ID. Since we have two account types
    sharing one login system, the ID is prefixed ("employer-5" or
    "seeker-5") so we know which table to look in.
    """
    # Imported here (not at the top) to avoid a circular import with models.py
    from models import Employer, Seeker

    try:
        account_type, real_id = prefixed_id.split("-", 1)
        real_id = int(real_id)
    except (ValueError, AttributeError):
        return None

    if account_type == "employer":
        return Employer.query.get(real_id)
    if account_type == "seeker":
        return Seeker.query.get(real_id)
    return None
