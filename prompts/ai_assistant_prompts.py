"""
prompts/ai_assistant_prompts.py
Prompt templates for the AI Career Coach form (ai_assistant.py).

NOTE: this file was referenced by ai_assistant.py's import but was
never uploaded, so this is a reconstruction covering the four
options in the form's <select name="task"> (cover_letter, interview,
analyze, skills). If you already have your own version of this file
elsewhere in the project, use that one instead -- this is a
best-effort stand-in, not a recovery of your original prompts.
"""

SYSTEM_PROMPT = """
You are the AI Career Coach for CareerMomentum.

You help job seekers get more out of their resume: drafting cover
letters, prepping for interviews, analyzing job descriptions against
their background, and identifying skill gaps.

Rules:
- Base everything on the resume text and job description provided.
  Never invent experience, skills, or qualifications the candidate
  doesn't have.
- Be specific and actionable, not generic.
- Keep a warm, encouraging, professional tone.
- Format your response in clean HTML using <p>, <ul>/<li>, and
  <strong> tags where useful -- it will be rendered directly into
  the page.
"""


def skill_extraction_prompt(resume_text):
    """Prompt used to pull a flat list of skills out of resume text."""
    return f"""
Extract ONLY the technical and professional skills from this resume.

Resume:
{resume_text}

Return them as a comma-separated list. Remove duplicates. Ignore
education, projects, and personal details. Return nothing except
the comma-separated list.
"""


def build_task_prompt(task, resume_text, extracted_skills, job_description):
    """Builds the user-facing prompt for whichever task was selected
    in the form. Falls back to the "analyze" prompt for any unknown
    task value."""

    if task == "cover_letter":
        return f"""
Write a professional cover letter body (3-4 paragraphs) for this
candidate, tailored to the job description below. Use their real
skills and background only -- do not invent experience.

Resume:
{resume_text}

Extracted Skills:
{extracted_skills}

Job Description:
{job_description}
"""

    if task == "interview":
        return f"""
Generate a mock interview prep set for this candidate based on the
job description below: 5 likely HR/behavioral questions and 5 likely
technical questions, each with a short note on what a strong answer
should cover given this candidate's background.

Resume:
{resume_text}

Extracted Skills:
{extracted_skills}

Job Description:
{job_description}
"""

    if task == "skills":
        return f"""
Compare this candidate's skills against the job description and
produce a skill gap analysis: which required skills they already
have, which they're missing, and 2-3 concrete suggestions for
closing the biggest gaps (courses, projects, certifications).

Resume:
{resume_text}

Extracted Skills:
{extracted_skills}

Job Description:
{job_description}
"""

    # "analyze" and any unrecognized task fall back to this
    return f"""
Analyze how well this candidate's resume matches the job description
below. Cover: overall fit, strongest matching qualifications, key
gaps, and 2-3 suggestions for improving their application.

Resume:
{resume_text}

Extracted Skills:
{extracted_skills}

Job Description:
{job_description}
"""