from flask import Blueprint, render_template, request, jsonify
import re
import json

from config import client
from utils import extract_text

ats_checker_bp = Blueprint("ats_checker", __name__)


# ==========================================
# AI call helper -- robust JSON parsing
# ==========================================
def _extract_json_block(raw_text):
    """Pulls out the {...} block and tries to parse it. Returns the
    parsed dict, or None if it still isn't valid JSON."""
    raw_text = raw_text.replace("```json", "").replace("```", "").strip()

    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if not match:
        return None

    candidate = match.group()

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    # Common LLM slip-up: a trailing comma before a closing ] or } --
    # strip those and try again before giving up.
    cleaned = re.sub(r",\s*([\]}])", r"\1", candidate)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


def ask_ai(prompt, retry_note=None):
    """Calls the model and returns a parsed dict. If the first response
    isn't valid JSON, asks once more with an explicit correction note
    instead of failing immediately -- LLMs occasionally emit a stray
    trailing comma or get cut off, and a single retry clears most of
    those without the user ever seeing an error."""

    full_prompt = prompt if not retry_note else f"{prompt}\n\n{retry_note}"

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        temperature=0,
        max_tokens=2048,
        messages=[{"role": "user", "content": full_prompt}],
    )

    result = _extract_json_block(response.choices[0].message.content)

    if result is None and retry_note is None:
        # One retry with a stricter instruction -- covers truncated or
        # slightly malformed JSON from the first attempt.
        return ask_ai(
            prompt,
            retry_note="Your previous response was not valid JSON. "
                        "Return ONLY a single valid JSON object -- no "
                        "trailing commas, no comments, no text before "
                        "or after the braces.",
        )

    return result


# ==========================================
# Normalizers -- make AI output safe to use
# ==========================================
def _as_str_list(value):
    """Coerces whatever the AI returned for a 'list of strings' field
    into an actual flat list of strings. Handles the common failure
    modes seen in practice: a single string instead of a list, a
    nested list (e.g. [["Python", "SQL"]]), or the key missing/None
    entirely -- all of which previously caused
    `'list' object has no attribute 'lower'` deep inside keyword_score
    or experience_score."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, (list, tuple)):
        flat = []
        for item in value:
            if isinstance(item, str):
                if item.strip():
                    flat.append(item)
            elif isinstance(item, (list, tuple)):
                flat.extend(_as_str_list(item))
            elif item is not None:
                flat.append(str(item))
        return flat
    return [str(value)]


def _normalize_extraction(data):
    """Runs every list-of-strings field in a resume/JD extraction
    through _as_str_list, and makes sure experience/education always
    have the sub-keys the scoring functions expect -- so a field the
    AI omitted or malformed never crashes calculate_ats() downstream."""
    data = data or {}

    list_fields = [
        "technical_skills", "soft_skills", "tools", "frameworks",
        "databases", "cloud", "methodologies", "certifications", "projects",
    ]
    for field in list_fields:
        data[field] = _as_str_list(data.get(field))

    experience = data.get("experience") or {}
    if not isinstance(experience, dict):
        experience = {}
    years = experience.get("years", 0)
    if not isinstance(years, (int, float)):
        years = 0
    data["experience"] = {
        "years": years,
        "roles": _as_str_list(experience.get("roles")),
        "internships": _as_str_list(experience.get("internships")),
    }

    education = data.get("education") or {}
    if not isinstance(education, dict):
        education = {}
    data["education"] = {
        "degree": str(education.get("degree") or ""),
        "branch": str(education.get("branch") or ""),
    }

    return data


def extract_resume_details_ai(text):

    prompt = f"""
    You are an Applicant Tracking System.

    Analyze the following RESUME.

    Extract ONLY the candidate's information.

    Return ONLY valid JSON.

    Do not explain anything.
    Do not use markdown.
    Do not use backticks.

    IMPORTANT: every list field (technical_skills, soft_skills, tools,
    frameworks, databases, cloud, methodologies, certifications,
    projects, experience.roles, experience.internships) must be a
    FLAT array of plain strings -- never a nested array, never an
    object.

    Example:
        {{
        "technical_skills": [],
        "soft_skills": [],
        "tools": [],
        "frameworks": [],
        "databases": [],
        "cloud": [],
        "methodologies": [],

        "experience":{{
        "years":2,
        "roles":[
            "Python Developer"
        ],
        "internships":[
            "Backend Intern"
        ]}},

        "education": {{
            "degree": "",
            "branch": ""
        }},

        "certifications": [],

        "projects": []
        }}

    Resume:

    {text}
    """
    result = ask_ai(prompt)
    return _normalize_extraction(result)


def extract_jd_details_ai(text):

    prompt = f"""
    You are an Applicant Tracking System.

    Analyze the following JOB DESCRIPTION.

    Extract ONLY the employer requirements.

    Return ONLY valid JSON.

    Do not explain anything.
    Do not use markdown.
    Do not use backticks.

    IMPORTANT: every list field (technical_skills, soft_skills, tools,
    frameworks, databases, cloud, methodologies, certifications,
    projects, experience.roles) must be a FLAT array of plain strings
    -- never a nested array, never an object.

    Example:
    {{
        "technical_skills": [],
        "soft_skills": [],
        "tools": [],
        "frameworks": [],
        "databases": [],
        "cloud": [],
        "methodologies": [],

        "experience": {{
            "years": 0,
            "roles": []
        }},

        "education": {{
            "degree": "",
            "branch": ""
        }},

        "certifications": [],

        "projects": []
    }}

    Job Description:

    {text}
    """
    result = ask_ai(prompt)
    return _normalize_extraction(result)


def evaluate_resume_quality_ai(text):

    prompt = f"""
    You are an experienced HR recruiter.

    Analyze this resume.

    Evaluate the following:

    1. Action verbs
    2. Quantified achievements
    3. Grammar
    4. Professional writing
    5. Readability

    Return ONLY valid JSON.

    Example:

    {{
        "score": 82,
        "strengths":[
            "Uses strong action verbs",
            "Good formatting"
        ],
        "weaknesses":[
            "No quantified achievements",
            "Few measurable results"
        ]
    }}

    Resume:

    {text}
    """

    result = ask_ai(prompt)

    if result is None:
        raise Exception("Resume quality analysis failed. Please try again.")

    result["score"] = result.get("score", 0) or 0
    result["strengths"] = _as_str_list(result.get("strengths"))
    result["weaknesses"] = _as_str_list(result.get("weaknesses"))

    return result


def keyword_score(resume, jd):

    resume_keywords = set(
        map(str.lower,
            resume["technical_skills"] +
            resume["tools"] +
            resume["frameworks"] +
            resume["databases"] +
            resume["cloud"] +
            resume["methodologies"] +
            resume["soft_skills"])
    )

    jd_keywords = set(
        map(str.lower,
            jd["technical_skills"] +
            jd["tools"] +
            jd["frameworks"] +
            jd["databases"] +
            jd["cloud"] +
            jd["methodologies"] +
            jd["soft_skills"])
    )

    matched = list(resume_keywords & jd_keywords)

    missing = list(jd_keywords - resume_keywords)

    score = round(
        len(matched) / len(jd_keywords) * 100
    ) if jd_keywords else 0

    return {
        "score": score,
        "matched": matched,
        "missing": missing,
        "total_skills": len(jd_keywords)
    }


def formatting_score(resume_text):

    resume = resume_text.lower()

    score = 0

    sections = [
        "education",
        "skills",
        "experience",
        "projects",
        "certifications"
    ]

    for section in sections:

        if section in resume:

            score += 15

    if len(resume_text.split()) > 250:

        score += 25

    return min(score, 100)


def experience_score(resume, jd):

    candidate_years = resume["experience"]["years"]

    required_years = jd["experience"]["years"]

    score = 0

    if required_years == 0:
        score += 50

    else:

        score += min(
            (candidate_years / required_years) * 50,
            50
        )

    candidate_roles = set(
        map(str.lower, resume["experience"]["roles"])
    )

    required_roles = set(
        map(str.lower, jd["experience"]["roles"])
    )

    if required_roles:

        role_match = len(
            candidate_roles & required_roles
        ) / len(required_roles)

        score += role_match * 50

    else:

        score += 50

    return round(score)


def education_score(resume, jd):

    candidate_degree = resume["education"]["degree"].lower()
    required_degree = jd["education"]["degree"].lower()

    candidate_branch = resume["education"]["branch"].lower()
    required_branch = jd["education"]["branch"].lower()

    score = 0

    if required_degree == "":
        score += 50
    elif candidate_degree == required_degree:
        score += 50

    if required_branch == "":
        score += 50
    elif candidate_branch == required_branch:
        score += 50

    return score


def recruiter_quality_score(resume_text):

    quality = evaluate_resume_quality_ai(resume_text)

    return quality["score"]


# ATS CALCULATION

def calculate_ats(resume_text, jd_text):

    resume = extract_resume_details_ai(resume_text)

    jd = extract_jd_details_ai(jd_text)

    keyword = keyword_score(
        resume,
        jd
    )

    experience = experience_score(
        resume,
        jd
    )

    formatting = formatting_score(
        resume_text
    )

    education = education_score(
        resume,
        jd
    )

    quality_details = evaluate_resume_quality_ai(resume_text)
    quality = quality_details["score"]

    final_score = (

        keyword["score"] * 0.45 +

        experience * 0.25 +

        formatting * 0.15 +

        education * 0.10 +

        quality * 0.05

    )

    return {

        "overall_score": round(final_score),

        "mode": "AI ATS Analyzer",

        "breakdown": {

            "keyword": keyword["score"],

            "experience": experience,

            "education": education,

            "formatting": formatting,

            "quality": quality

        },

        "matched": keyword["matched"],

        "missing": keyword["missing"],

        "total_skills": keyword["total_skills"],

        "strengths": quality_details["strengths"],

        "weaknesses": quality_details["weaknesses"]
    }


# ==========================================
# Routes
# ==========================================
@ats_checker_bp.route("/ats_checker.html")
def ats_checker_page():
    return render_template("ats_checker.html")


@ats_checker_bp.route("/check-ats", methods=["POST"])
def check_ats():
    try:
        resume_file = request.files.get("resume")
        if not resume_file or resume_file.filename == "":
            return jsonify({"error": "Resume file missing"}), 400

        try:
            resume_text = extract_text(resume_file)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        jd_text = request.form.get("jd_text", "").strip()
        jd_file = request.files.get("jd_file")

        if not jd_text and jd_file and jd_file.filename:
            try:
                jd_text = extract_text(jd_file)
            except ValueError as e:
                return jsonify({"error": str(e)}), 400

        if not jd_text:
            return jsonify({"error": "Please provide Job Description"}), 400

        result = calculate_ats(resume_text, jd_text)

        return jsonify(result)

    except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
        # The AI response didn't come back in the expected shape --
        # surface a clear, actionable message instead of a raw
        # traceback / Python exception string.
        return jsonify({
            "error": "The AI had trouble analyzing this resume/job description. Please try again."
        }), 502

    except Exception as e:
        return jsonify({"error": str(e)}), 500