"""
utils.py
Shared helper for pulling plain text out of an uploaded file.
Used by any feature that needs to read a resume or job description
file, regardless of format (PDF, DOCX, or TXT).
"""

import io

import pdfplumber
import docx


def extract_text(file):
    """
    Takes an uploaded file (Flask FileStorage) and returns its text
    content as a string. Supports .pdf, .docx, and .txt.
    Raises ValueError if the file type isn't supported.
    """
    filename = file.filename.lower()

    if filename.endswith(".pdf"):
        return _extract_from_pdf(file)

    if filename.endswith(".docx"):
        return _extract_from_docx(file)

    if filename.endswith(".txt"):
        return _extract_from_txt(file)

    raise ValueError("Only PDF, DOCX, and TXT files are supported.")


def _extract_from_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()


def _extract_from_docx(file):
    doc = docx.Document(io.BytesIO(file.read()))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def _extract_from_txt(file):
    return file.read().decode("utf-8", errors="ignore").strip()
