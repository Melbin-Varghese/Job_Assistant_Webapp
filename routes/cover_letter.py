"""
ats.py
Backend for the "Inkwell" Cover Letter Generator page.
One file: the route, the AI calls, and the PDF download — matching
the file you uploaded (ats.html) so it's a direct drop-in pair.

Uses your existing config.py (Groq client) and txt_ext.py (resume
text extraction) — nothing new to install for those.

To use the PDF download link, also run: pip install fpdf2
"""

import io
import os
import re
import uuid

from flask import Blueprint, render_template, request, send_from_directory
from fpdf import FPDF

from config import client
from txt_ext import extract_from_pdf, extract_from_docx

cover_letter_bp = Blueprint("cover_letter", __name__)

PDF_FOLDER = os.path.join(os.path.dirname(__file__), "generated_pdfs")
os.makedirs(PDF_FOLDER, exist_ok=True)


# ==========================================
# Resume text extraction
# ==========================================
def extract_resume_text(resume_file):
    filename = resume_file.filename.lower()

    if filename.endswith(".pdf"):
        return extract_from_pdf(resume_file)

    if filename.endswith(".docx"):
        return extract_from_docx(io.BytesIO(resume_file.read()))

    raise ValueError("Only PDF and DOCX files are supported.")


# ==========================================
# AI: skill extraction
# ==========================================
def extract_skills(resume_text):
    prompt = f"""
Extract ONLY the technical and professional skills from this resume.

Resume:
{resume_text}

Return them as a comma-separated list. Remove duplicates. Ignore
education, projects and personal details.
"""
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        return completion.choices[0].message.content.strip()
    except Exception:
        return ""


# ==========================================
# AI: cover letter drafting
# ==========================================
def draft_cover_letter(resume_text, extracted_skills, job_role, company,
                        company_address, job_description, experience):
    system_prompt = """
You are Inkwell, an expert cover letter writer.

Output ONLY the body of the cover letter as clean HTML paragraphs,
using <p>...</p> tags for each paragraph. No markdown, no code fences,
no text outside the <p> tags. Do not invent experience or skills that
were not provided. If there is no listed experience, write the letter
around the candidate's skills and enthusiasm instead. Keep it to
3-5 paragraphs. Tone: professional, warm, specific.
"""

    user_prompt = f"""
Candidate Resume:
{resume_text}

Candidate Skills:
{extracted_skills}

Candidate's Relevant Experience (may be blank if a fresher):
{experience}

Job Title: {job_role}
Company: {company}
Company Address: {company_address}

Job Description:
{job_description}
"""

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        return f"<p>Groq API Error: {str(e)}</p>"


# ==========================================
# PDF generation
# ==========================================
def generate_pdf(cover_letter_html):
    paragraphs = re.findall(r"<p>(.*?)</p>", cover_letter_html, flags=re.DOTALL)
    paragraphs = [re.sub(r"<[^>]+>", "", p).strip() for p in paragraphs]

    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    pdf.set_margins(20, 20, 20)
    pdf.set_font("Helvetica", size=11)

    for paragraph in paragraphs:
        pdf.multi_cell(0, 7, paragraph)
        pdf.ln(4)

    filename = f"cover_letter_{uuid.uuid4().hex[:8]}.pdf"
    pdf.output(os.path.join(PDF_FOLDER, filename))
    return filename


# ==========================================
# Routes
# ==========================================
@cover_letter_bp.route("/cover_letter.html", methods=["GET", "POST"])
def cover_letter():

    if request.method != "POST":
        return render_template("cover_letter.html")

    job_role = request.form.get("job_role", "")
    company = request.form.get("company", "")
    company_address = request.form.get("company_address", "")
    job_description = request.form.get("job_description", "")
    experience = request.form.get("experience", "")
    resume = request.files.get("resume")

    if not resume or resume.filename == "":
        return render_template("ats.html", error="Please attach your resume.")

    try:
        resume_text = extract_resume_text(resume)
    except ValueError as e:
        return render_template("cover_letter.html", error="Please attach your resume")
    except Exception as e:
        return render_template("cover_letter.html", error=str(e))

    extracted_skills = extract_skills(resume_text)

    cover_letter_output = draft_cover_letter(
        resume_text, extracted_skills, job_role, company,
        company_address, job_description, experience
    )

    try:
        pdf_filename = generate_pdf(cover_letter_output)
    except Exception:
        pdf_filename = None

    return render_template(
        "cover_letter.html",
        extracted_skills=extracted_skills,
        cover_letter_output=cover_letter_output,
        pdf_filename=pdf_filename,
    )


@cover_letter_bp.route("/download/<filename>")
def download(filename):
    return send_from_directory(PDF_FOLDER, filename, as_attachment=True)
