"""
prompts/seeker_profile_prompts.py
Prompt used to turn raw resume text into structured profile data for
the "Upload Resume -> auto-fill profile" feature on profile_user.html.
"""


def build_profile_extraction_prompt(resume_text):
    return f"""
You are extracting structured profile data from a resume for a job
seeker's profile page.

Return ONLY valid JSON, no markdown, no code fences, no explanation.

Use exactly this shape:

{{
  "name": "Full name, or null if not found",
  "headline": "A short professional headline, e.g. 'AI / ML Engineer' -- infer from the resume if not explicit",
  "location": "City, Country if mentioned, else null",
  "phone": "Phone number if present, else null",
  "email": "Email if present, else null",
  "linkedin": "linkedin.com/in/... URL if present, else null",
  "github": "github.com/... URL if present, else null",
  "summary": "A 2-3 sentence professional summary based on the resume",
  "skills": ["skill1", "skill2", "..."],
  "experience": [
    {{"role": "Job title", "company": "Company name", "period": "e.g. Jan 2023 - Present", "desc": "1-2 sentence summary of what they did"}}
  ],
  "projects": [
    {{"title": "Project name", "stack": "Comma-separated tech used", "desc": "1-2 sentence summary"}}
  ],
  "education": [
    {{"degree": "Degree / course name", "school": "Institution name", "period": "e.g. 2021 - 2025"}}
  ]
}}

Rules:
- Never invent information that isn't in the resume. Use null or an
  empty list/string if something isn't present.
- "skills" should be a flat list of technical and professional
  skills actually mentioned or clearly implied by the resume content.
- Keep descriptions concise -- 1-2 sentences each, not full paragraphs.

Resume:
{resume_text}
"""
