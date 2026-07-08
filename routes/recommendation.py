"""
recommendation.py
Backend for the AI Job Recommender page. One file: the page route,
the resume-stats calculation, the AI call, and the job-search link
builder — matching the pattern used in ats.py.

Uses your existing config.py (Groq client) and utils.py (resume text
extraction for PDF/DOCX/TXT) — nothing new to install.
"""

import json
from urllib.parse import quote_plus

from flask import Blueprint, render_template, request, jsonify

from config import client
from utils import extract_text

recommendation_bp = Blueprint("recommendation", __name__)


# ==========================================
# Job search links (built directly, not by the AI, so they're always
# valid working URLs instead of something the model might hallucinate)
# ==========================================
def build_job_links(job_title):
    query = quote_plus(job_title)

    return {
        "naukri": {
            "name": "Naukri",
            "color": "#4A90D9",
            "url": f"https://www.naukri.com/{job_title.lower().replace(' ', '-')}-jobs",
        },
        "linkedin": {
            "name": "LinkedIn",
            "color": "#0077B5",
            "url": f"https://www.linkedin.com/jobs/search/?keywords={query}",
        },
        "glassdoor": {
            "name": "Glassdoor",
            "color": "#0CAA41",
            "url": f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={query}",
        },
        "indeed": {
            "name": "Indeed",
            "color": "#2164F3",
            "url": f"https://www.indeed.com/jobs?q={query}",
        },
        "infopark": {
            "name": "Infopark",
            "color": "#E65C00",
            "url": f"https://www.google.com/search?q={query}+jobs+site:infopark.in",
        },
    }


# ==========================================
# Resume stats (word/char/line counts)
# ==========================================
def get_resume_stats(resume_text):
    return {
        "words": len(resume_text.split()),
        "chars": len(resume_text),
        "lines": len(resume_text.splitlines()),
    }


# ==========================================
# AI: generate role recommendations
# ==========================================
SYSTEM_PROMPT = """
You are an AI Job Recommendation engine.

Respond with ONLY a valid JSON object. No markdown, no code fences,
no explanation text before or after it.
"""


def build_prompt(resume_text):
    return f"""
Analyze this resume and recommend the best-fit job roles.

Resume:
{resume_text}

Return a JSON object with EXACTLY this shape:

{{
  "candidate_level": "e.g. Entry-level / Mid-level / Senior",
  "strongest_domain": "e.g. Data Science, Frontend Development",
  "summary": "2-3 sentence summary of the candidate's profile",
  "top_roles": [
    {{
      "title": "Job title",
      "match_score": 0-100 integer,
      "reason": "1-2 sentences on why this role fits",
      "required_skills_present": ["skill the candidate already has", "..."],
      "skills_to_add": ["skill the candidate is missing for this role", "..."]
    }}
  ]
}}

Return 3 to 5 roles in top_roles, ordered by match_score descending.
"""


def get_ai_recommendations(resume_text):
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_prompt(resume_text)},
            ],
            temperature=0.4,
        )

        raw_text = completion.choices[0].message.content.strip()

        if raw_text.startswith("```"):
            raw_text = raw_text.strip("`")
            raw_text = raw_text.replace("json", "", 1).strip()

        return json.loads(raw_text)

    except json.JSONDecodeError:
        raise ValueError("The AI response wasn't valid JSON. Please try again.")

    except Exception as e:
        raise ValueError(f"Groq API Error: {str(e)}")


# ==========================================
# Routes
# ==========================================
@recommendation_bp.route("/recommendation.html")
def recommendation_page():
    return render_template("recommendation.html")


@recommendation_bp.route("/recommend", methods=["POST"])
def recommend():
    resume = request.files.get("resume")

    if not resume or resume.filename == "":
        return jsonify({"error": "Please upload your resume."}), 400

    try:
        resume_text = extract_text(resume)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Resume Extraction Error: {str(e)}"}), 500

    try:
        recommendations = get_ai_recommendations(resume_text)
    except ValueError as e:
        return jsonify({"error": str(e)}), 500

    # Attach real, working job-search links to each recommended role
    for role in recommendations.get("top_roles", []):
        role["job_links"] = build_job_links(role.get("title", ""))

    return jsonify({
        "recommendations": recommendations,
        "extracted": get_resume_stats(resume_text),
    })
