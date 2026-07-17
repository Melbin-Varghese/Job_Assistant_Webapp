"""
routes/job_browse.py
Public job browsing -- reached from the main index's "Popular
Categories" cards and its search bar. Anyone can view/search jobs
here without logging in. Applying still requires a seeker login (see
the Apply button logic in templates/jobs_browse.html) -- this route
itself has no @login_required on it.

Job has no dedicated "category" column, so each Popular Categories
card is approximated as a keyword search (matched against
title/company/skills via crud.search_jobs) or, for "Remote", a
location filter instead. If you later add a real category field to
Job, swap CATEGORY_FILTERS for a direct column filter.
"""

from flask import Blueprint, render_template, request
from flask_login import current_user

from crud import search_jobs, list_all_jobs, list_applied_job_ids, get_job_by_id
from models import Seeker

job_browse_bp = Blueprint("job_browse", __name__)


CATEGORY_FILTERS = {
    "engineering": {"keyword": "engineer"},
    "remote": {"location": "remote"},
    "creative": {"keyword": "design"},
    "finance": {"keyword": "finance"},
    "data-science": {"keyword": "data"},
    "marketing": {"keyword": "marketing"},
    "hr-people": {"keyword": "hr"},
    "healthcare": {"keyword": "health"},
    "software-dev": {"keyword": "developer"},
    "all": {},
}

CATEGORY_LABELS = {
    "engineering": "Engineering",
    "remote": "Remote",
    "creative": "Creative",
    "finance": "Finance",
    "data-science": "Data Science",
    "marketing": "Marketing",
    "hr-people": "HR & People",
    "healthcare": "Healthcare",
    "software-dev": "Software Dev",
    "all": "All Industries",
}


@job_browse_bp.route("/jobs")
def browse():
    job_id = request.args.get("job_id", type=int)
    category = request.args.get("category", "").strip()
    keyword = request.args.get("keyword", "").strip()
    location = request.args.get("location", "").strip()
    job_type = request.args.get("job_type", "").strip()

    if job_id:
        # Came from a specific "View & Apply" card (e.g. Featured
        # Opportunities on the main index) -- show just that one job,
        # still gated by status="Approved" so a stale/unapproved link
        # can't be used to view a job that isn't public yet.
        job = get_job_by_id(job_id)
        jobs = [job] if job and job.status == "Approved" else []
        category = keyword = location = job_type = ""
    else:
        # A category click pre-fills keyword/location. If the person
        # has ALSO typed their own search terms, those take priority
        # over the category's defaults.
        if category in CATEGORY_FILTERS:
            cat_filter = CATEGORY_FILTERS[category]
            keyword = keyword or cat_filter.get("keyword", "")
            location = location or cat_filter.get("location", "")

        is_filtered = bool(category or keyword or location or job_type)

        jobs = (
            search_jobs(keyword=keyword or None, location=location or None, job_type=job_type or None)
            if is_filtered
            else list_all_jobs()
        )

    is_seeker = current_user.is_authenticated and isinstance(current_user, Seeker)
    applied_job_ids = list_applied_job_ids(current_user.id) if is_seeker else set()

    return render_template(
        "jobs_browse.html",
        jobs=jobs,
        category=category,
        category_label=CATEGORY_LABELS.get(category, ""),
        keyword=keyword,
        location=location,
        job_type=job_type,
        is_seeker=is_seeker,
        is_logged_in=current_user.is_authenticated,
        applied_job_ids=applied_job_ids,
    )