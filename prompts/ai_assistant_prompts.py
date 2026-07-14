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
You are the AI Career Coach for CareerMomentum, a career platform
that helps job seekers present themselves professionally and prepare
for their next opportunity.

Your job is to help candidates get more out of their resume: drafting
cover letters, preparing for interviews, analyzing how well they match
a job description, and identifying skill gaps to close.

Rules:
- Base everything strictly on the resume text and job description
  provided. Never invent experience, skills, employers, degrees, or
  qualifications the candidate hasn't stated.
- Write at a professional, industry-standard level -- the kind of
  language a career counselor or hiring manager would recognize as
  polished and credible, not generic filler.
- Be specific and actionable. Reference the candidate's actual
  background and the actual job requirements rather than offering
  advice that could apply to anyone.
- Keep a warm, encouraging, professional tone throughout. Never be
  dismissive of a candidate's experience, even when identifying gaps.
- Format your response in clean HTML using <p>, <ul>/<li>, and
  <strong> tags where useful -- it will be rendered directly into
  the page. Do not include <html>, <head>, or <body> tags.
"""


def skill_extraction_prompt(resume_text):
    """Prompt used to pull a flat list of skills out of resume text."""
    return f"""
Extract ONLY the technical and professional skills demonstrated in
this resume -- tools, technologies, methodologies, certifications,
and professional competencies.

Resume:
{resume_text}

Return them as a single comma-separated list, using standard,
industry-recognized naming for each skill (e.g. "Project Management"
rather than "managing projects"). Remove duplicates and near-duplicates.
Ignore education, job titles, employers, and personal details. Return
nothing except the comma-separated list -- no headings, no commentary.
"""


def build_task_prompt(task, resume_text, extracted_skills, job_description):
    """Builds the user-facing prompt for whichever task was selected
    in the form. Falls back to the "analyze" prompt for any unknown
    task value."""

    if task == "cover_letter":
        return f"""
Write a professional cover letter body (3-4 paragraphs) for this
candidate, tailored specifically to the job description below.

Follow standard cover letter conventions:
- Open by naming the role and expressing genuine, specific interest
  in it -- not a generic opening line.
- In the body, connect the candidate's real experience and skills
  directly to the job's stated requirements, using concrete examples
  from their resume rather than vague claims.
- Close with a confident, professional call to action (e.g.
  welcoming the opportunity to discuss further).
- Use a natural, first-person voice appropriate for a job application
  -- confident and professional, not stiff or overly formal.
- Use only the candidate's real skills and background. Do not invent
  experience, metrics, or accomplishments that aren't supported by
  the resume.

Resume:
{resume_text}

Extracted Skills:
{extracted_skills}

Job Description:
{job_description}
"""

    if task == "interview":
        return f"""
Generate a mock interview preparation set for this candidate, tailored
to the job description below.

Include:
- 5 likely behavioral/HR interview questions
- 5 likely technical or role-specific interview questions

For each question, add a short, concrete note on what a strong answer
should cover, drawing on this specific candidate's background and
experience wherever possible (e.g. which of their projects or skills
they could reference) rather than generic interview advice.

Resume:
{resume_text}

Extracted Skills:
{extracted_skills}

Job Description:
{job_description}
"""

    if task == "skills":
        return f"""
Produce a skill gap analysis comparing this candidate's skills to the
requirements in the job description below.

Structure the analysis clearly into:
1. Matching skills -- required or preferred skills the candidate
   already has, drawn from their resume.
2. Missing or underdeveloped skills -- requirements from the job
   description not evidenced in the resume.
3. Recommendations -- 2-3 concrete, actionable next steps for closing
   the most significant gaps (e.g. specific types of courses,
   certifications, or portfolio projects), prioritized by impact.

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
below, as a career coach would in a professional resume review.

Structure the analysis clearly into:
1. Overall fit -- a brief, honest summary of how well the candidate
   matches this role.
2. Strongest matching qualifications -- the specific experience and
   skills that make the strongest case for this candidate.
3. Key gaps -- requirements from the job description the resume
   doesn't clearly address.
4. Recommendations -- 2-3 concrete suggestions for strengthening this
   application (e.g. resume wording, skills to highlight, gaps worth
   addressing).

Resume:
{resume_text}

Extracted Skills:
{extracted_skills}

Job Description:
{job_description}
"""