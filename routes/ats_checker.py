from flask import Blueprint, render_template, request, jsonify
import re
import json

from config import client
from utils import extract_text

ats_checker_bp = Blueprint("ats_checker", __name__)


def ask_ai(prompt):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    result = response.choices[0].message.content

    result = result.replace("```json", "")
    result = result.replace("```", "").strip()

    match = re.search(r"\{.*\}", result, re.DOTALL)

    if match:
        return json.loads(match.group())

    return None


def extract_resume_details_ai(text):

    prompt = f"""
    You are an Applicant Tracking System.

    Analyze the following RESUME.

    Extract ONLY the candidate's information.

    Return ONLY valid JSON.

    Do not explain anything.
    Do not use markdown.
    Do not use backticks.

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

    if result is None:
        return {}

    return result


def extract_jd_details_ai(text):

    prompt = f"""
    You are an Applicant Tracking System.

    Analyze the following JOB DESCRIPTION.

    Extract ONLY the employer requirements.

    Return ONLY valid JSON.

    Do not explain anything.
    Do not use markdown.
    Do not use backticks.

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

    if result is None:
        return {}

    return result


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

    except Exception as e:
        return jsonify({"error": str(e)}), 500
