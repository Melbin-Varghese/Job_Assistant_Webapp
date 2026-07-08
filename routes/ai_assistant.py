"""
routes/ai_assistant.py
The AI Career Coach page: handles resume upload, skill extraction,
and generating the AI response for the selected task.
"""

import io

from flask import Blueprint, render_template, request

from config import client
from txt_ext import extract_from_pdf, extract_from_docx
from prompts.ai_assistant_prompts import (
    skill_extraction_prompt,
    build_task_prompt,
    SYSTEM_PROMPT,
)

ai_assistant_bp = Blueprint("ai_assistant", __name__)


def extract_resume_text(resume_file):
    """Reads an uploaded PDF or DOCX file and returns its text.
    Raises ValueError if the file type isn't supported."""
    filename = resume_file.filename.lower()

    if filename.endswith(".pdf"):
        return extract_from_pdf(resume_file)

    if filename.endswith(".docx"):
        return extract_from_docx(io.BytesIO(resume_file.read()))

    raise ValueError("Only PDF and DOCX files are supported.")


def extract_skills(resume_text):
    """Asks the AI to pull technical skills out of the resume text."""
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": skill_extraction_prompt(resume_text)}
            ],
            temperature=0
        )
        return completion.choices[0].message.content.strip()

    except Exception:
        return "Skill extraction failed."


def generate_ai_response(prompt):
    """Sends the task prompt to the AI and returns its reply."""
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7
        )
        return completion.choices[0].message.content

    except Exception as e:
        return f"Groq API Error: {str(e)}"


@ai_assistant_bp.route("/ai_assistant.html", methods=["GET", "POST"])
def ai_assistant():
    response_text = ""
    extracted_skills = ""

    if request.method == "POST":
        task = request.form.get("task")
        job_description = request.form.get("job_description", "")
        resume = request.files.get("resume")

        # ---------- Resume required ----------
        if not resume or resume.filename == "":
            return render_template(
                "ai_assistant.html",
                response="Please upload your resume.",
                skills=""
            )

        # ---------- Extract resume text ----------
        try:
            resume_text = extract_resume_text(resume)
        except ValueError as e:
            return render_template(
                "ai_assistant.html",
                response=str(e),
                skills=""
            )
        except Exception as e:
            return render_template(
                "ai_assistant.html",
                response=f"Resume Extraction Error: {str(e)}",
                skills=""
            )

        # ---------- Extract skills, build prompt, get AI response ----------
        extracted_skills = extract_skills(resume_text)
        prompt = build_task_prompt(task, resume_text, extracted_skills, job_description)
        response_text = generate_ai_response(prompt)

    return render_template(
        "ai_assistant.html",
        response=response_text,
        skills=extracted_skills
    )
