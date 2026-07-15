"""
routes/automation.py
AI Job Application Automation: upload a CV, parse it with AI, draft a
cover letter, and email both to a list of HR addresses via Gmail API.
Keeps its own SQLite log table (sent_applications) and its own Gmail
OAuth files -- everything else plugs into the main app as a Blueprint.
"""

from flask import Blueprint, render_template, request, jsonify
import os
import re
import json
import uuid
import sqlite3
import pickle
from datetime import datetime

# Reuse the one shared Groq client / .env loading already set up by
# the rest of the project instead of creating a second client.
from config import client

# Try Gmail imports
try:
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    import googleapiclient.discovery
    from googleapiclient.errors import HttpError
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False
    print("⚠️  Gmail API not available")

# Email libraries
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formatdate, make_msgid
import base64

try:
    import pdfplumber
except ImportError:
    pdfplumber = None
    print("⚠️  pdfplumber not available")

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("⚠️  reportlab not available (pip install reportlab) - cover letter PDF export will fail")

automation_bp = Blueprint("automation", __name__)

# Project root = one level up from this routes/ folder, so every path
# below lands next to app.py / config.py instead of inside routes/.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Folders
UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, "uploads", "cv")
GENERATED_FOLDER = os.path.join(PROJECT_ROOT, "generated")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GENERATED_FOLDER, exist_ok=True)

# Database (kept as its own SQLite file -- separate from the main
# MySQL database used by seeker/employer accounts; this table is just
# an application-send log, not core relational data)
DB_PATH = os.path.join(PROJECT_ROOT, "career_momentum.db")

def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sent_applications (
            id TEXT PRIMARY KEY,
            user_email TEXT,
            company TEXT,
            job_role TEXT,
            hr_email TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            email_status TEXT,
            error_message TEXT,
            subject TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Gmail setup
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
CREDENTIALS_FILE = os.path.join(PROJECT_ROOT, 'credentials.json')
TOKEN_FILE = os.path.join(PROJECT_ROOT, 'token.pickle')

def get_gmail_service():
    """Get Gmail service with OAuth2"""
    if not GMAIL_AVAILABLE:
        return None
    
    try:
        credentials = None
        
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'rb') as token:
                credentials = pickle.load(token)
                print("[DEBUG] Loaded credentials from token.pickle")
        
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                print("[DEBUG] Refreshing credentials...")
                credentials.refresh(Request())
            elif os.path.exists(CREDENTIALS_FILE):
                print("[DEBUG] Getting new credentials from credentials.json...")
                from google_auth_oauthlib.flow import InstalledAppFlow
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE, SCOPES)
                credentials = flow.run_local_server(port=0)
                
                with open(TOKEN_FILE, 'wb') as token:
                    pickle.dump(credentials, token)
                print("[DEBUG] Saved credentials to token.pickle")
            else:
                print("[ERROR] credentials.json not found")
                return None
        
        service = googleapiclient.discovery.build('gmail', 'v1', credentials=credentials)
        print("[DEBUG] Gmail service created successfully")
        return service
        
    except Exception as e:
        print(f"[ERROR] Gmail service error: {str(e)}")
        return None

def send_email_via_gmail(sender_email, recipient_email, subject, body_html, attachments=None):
    """
    Send email via Gmail API.
    attachments: list of (file_path, display_filename) tuples, e.g.
        [("/path/resume_abc.pdf", "Akshay_CV.pdf"), ("/path/cover_letter_xyz.pdf", "Akshay_Cover_Letter.pdf")]
    """
    if not GMAIL_AVAILABLE:
        return False, "Gmail API not available"

    try:
        service = get_gmail_service()
        if not service:
            return False, "Could not connect to Gmail"

        message = MIMEMultipart('mixed')
        message['to'] = recipient_email
        message['from'] = sender_email
        message['subject'] = subject
        message['date'] = formatdate(localtime=True)
        message['message-id'] = make_msgid(domain=sender_email.split('@')[-1])
        message['mime-version'] = '1.0'

        alt_part = MIMEMultipart('alternative')
        alt_part.attach(MIMEText(body_html, 'html'))
        message.attach(alt_part)

        for attachment_path, display_filename in (attachments or []):
            if not attachment_path or not os.path.exists(attachment_path):
                continue
            try:
                with open(attachment_path, 'rb') as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="{display_filename}"')
                message.attach(part)
            except Exception as e:
                return False, f"Failed to attach {display_filename}: {str(e)}"

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        send_message = {'raw': raw_message}

        result = service.users().messages().send(userId='me', body=send_message).execute()
        return True, result.get('id', 'Email sent')

    except Exception as e:
        return False, f"Error: {str(e)}"

def generate_cover_letter_pdf(cover_letter_body, applicant_name, applicant_phone, applicant_email,
                               applicant_linkedin, applicant_github, company, job_role,
                               recipient_email=None, applicant_location=None):
    """Render the cover letter text into a standalone PDF file, formatted like a real letter
    (name/contact header, date, recipient block, Re: line, salutation, body, signed closing).
    Returns the file path."""
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("reportlab is not installed. Run: pip install reportlab")

    filename = f"cover_letter_{uuid.uuid4().hex[:8]}.pdf"
    filepath = os.path.join(GENERATED_FOLDER, filename)

    doc = SimpleDocTemplate(
        filepath, pagesize=letter,
        leftMargin=0.9 * inch, rightMargin=0.9 * inch,
        topMargin=0.9 * inch, bottomMargin=0.9 * inch
    )

    styles = getSampleStyleSheet()
    name_style = ParagraphStyle(
        'CoverLetterName', parent=styles['Normal'],
        fontSize=13, leading=16, spaceAfter=2, alignment=1  # centered
    )
    contact_style = ParagraphStyle(
        'CoverLetterContact', parent=styles['Normal'],
        fontSize=9.5, leading=13, spaceAfter=2, alignment=1  # centered
    )
    header_style = ParagraphStyle(
        'CoverLetterHeader', parent=styles['Normal'],
        fontSize=11, leading=15, spaceAfter=2
    )
    body_style = ParagraphStyle(
        'CoverLetterBody', parent=styles['Normal'],
        fontSize=11, leading=16, spaceAfter=12
    )

    # Contact line: location, phone, email
    contact_bits = [b for b in [applicant_location, applicant_phone, applicant_email] if b]
    contact_line = " | ".join(contact_bits)

    # Links line: linkedin, github
    link_bits = [b for b in [applicant_linkedin, applicant_github] if b]
    links_line = "   ".join(link_bits)

    story = []
    story.append(Paragraph(applicant_name, name_style))
    if contact_line:
        story.append(Paragraph(contact_line, contact_style))
    if links_line:
        story.append(Paragraph(links_line, contact_style))
    story.append(Spacer(1, 16))

    story.append(Paragraph(datetime.now().strftime("%B %d, %Y"), header_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph(f"Hiring Team, {company}", header_style))
    if recipient_email:
        story.append(Paragraph(recipient_email, header_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph(f"Re: Application for {job_role}", header_style))
    story.append(Spacer(1, 14))

    story.append(Paragraph("Dear Hiring Team,", body_style))

    for para in cover_letter_body.split('\n'):
        para = para.strip()
        if para:
            story.append(Paragraph(para, body_style))

    story.append(Spacer(1, 4))
    story.append(Paragraph("Warm regards,", header_style))
    story.append(Paragraph(applicant_name, header_style))
    if applicant_phone:
        story.append(Paragraph(applicant_phone, header_style))
    if applicant_email:
        story.append(Paragraph(applicant_email, header_style))

    doc.build(story)
    return filepath

def generate_application_email_html(name, phone, email, linkedin, github, company, job_role):
    """
    Generate the SHORT professional email body sent alongside the CV and
    cover letter attachments (the cover letter itself is NOT repeated here,
    it goes out as its own PDF attachment).
    """
    contact_html = f"<p style=\"margin: 8px 0; font-weight: bold;\">{name}</p>"

    if phone:
        contact_html += f"<p style=\"margin: 8px 0;\">{phone}</p>"

    if email:
        contact_html += f"<p style=\"margin: 8px 0;\"><a href=\"mailto:{email}\" style=\"color: #14B8A6; text-decoration: none;\">{email}</a></p>"

    if linkedin:
        contact_html += f"<p style=\"margin: 8px 0;\"><a href=\"{linkedin}\" style=\"color: #14B8A6; text-decoration: none;\">LinkedIn</a></p>"

    if github:
        contact_html += f"<p style=\"margin: 8px 0;\"><a href=\"{github}\" style=\"color: #14B8A6; text-decoration: none;\">GitHub</a></p>"

    intro = (
        f"I am writing to apply for the <b>{job_role}</b> position at <b>{company}</b>. "
        f"I believe my background and hands-on experience make me a strong fit for this role."
    )
    closing = (
        "Please find my resume and cover letter attached for your review. "
        "Thank you for your time and consideration &mdash; I look forward to hearing from you."
    )

    html = f"""
    <html>
        <body style="font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 650px; margin: 0 auto; padding: 20px;">
                <p style="margin: 0 0 16px 0;">Dear Hiring Team,</p>
                <p style="margin: 0 0 16px 0;">{intro}</p>
                <p style="margin: 0 0 16px 0;">{closing}</p>

                <div style="margin-top: 30px; border-top: 1px solid #ddd; padding-top: 20px;">
                    <p style="margin: 8px 0;">Warm regards,</p>
                    {contact_html}
                </div>
            </div>
        </body>
    </html>
    """
    return html

def log_application(user_email, company, job_role, hr_email, subject, email_status, error_message=None):
    """Log to database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        app_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO sent_applications 
            (id, user_email, company, job_role, hr_email, subject, email_status, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (app_id, user_email, company, job_role, hr_email, subject, email_status, error_message))
        
        conn.commit()
        conn.close()
        return app_id
    except Exception as e:
        print(f"Database error: {str(e)}")
        return None

@automation_bp.route("/automation", methods=["GET"])
def automation():
    """AI Job Application Automation page"""
    return render_template("automation.html")

@automation_bp.route("/api/upload-cv", methods=["POST"])
def upload_cv():
    """Upload CV file"""
    try:
        print("[DEBUG] Upload CV endpoint called")
        print(f"[DEBUG] Files in request: {request.files.keys()}")
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'success': False, 'error': 'Only PDF files allowed'}), 400
        
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > 5 * 1024 * 1024:
            return jsonify({'success': False, 'error': 'File too large'}), 400
        
        filename = f"resume_{uuid.uuid4().hex[:8]}.pdf"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        print(f"[DEBUG] Saving to: {filepath}")
        file.save(filepath)
        
        if not os.path.exists(filepath):
            return jsonify({'success': False, 'error': 'File save failed'}), 500
        
        print(f"[DEBUG] File saved successfully")
        
        return jsonify({
            'success': True,
            'filename': filename,
            'path': filepath,
            'size': file_size
        }), 200
    
    except Exception as e:
        print(f"[ERROR] Upload error: {str(e)}")
        return jsonify({'success': False, 'error': f'Upload failed: {str(e)}'}), 500

@automation_bp.route("/api/parse-cv", methods=["POST"])
def parse_cv():
    """Parse CV and extract details"""
    try:
        print("[DEBUG] Parse CV endpoint called")
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'success': False, 'error': 'Only PDF files allowed'}), 400
        
        print("[DEBUG] Extracting text from PDF...")
        pdf_text = ""
        
        try:
            if not pdfplumber:
                return jsonify({'success': False, 'error': 'PDF support not installed'}), 400
            
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    pdf_text += page.extract_text() + "\n"
        except Exception as e:
            print(f"[ERROR] PDF extraction failed: {str(e)}")
            return jsonify({'success': False, 'error': f'PDF parsing failed'}), 400
        
        print("[DEBUG] Extracting details using AI...")
        
        prompt = f"""Extract contact information from this CV text. Return ONLY valid data found.

CV Text:
{pdf_text[:2000]}

Return ONLY JSON (no other text):
{{
  "name": "Full name or null",
  "phone": "phone number or null",
  "email": "email or null",
  "linkedin": "linkedin URL or null",
  "github": "github URL or null"
}}"""

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300
        )
        
        response_text = completion.choices[0].message.content.strip()
        
        try:
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response_text[start:end]
                parsed_data = json.loads(json_str)
            else:
                parsed_data = {}
        except:
            parsed_data = {}
        
        extracted = {
            'name': parsed_data.get('name') or None,
            'phone': parsed_data.get('phone') or None,
            'email': parsed_data.get('email') or None,
            'linkedin': parsed_data.get('linkedin') or None,
            'github': parsed_data.get('github') or None
        }
        
        print(f"[DEBUG] Extracted: {extracted}")
        
        return jsonify({
            'success': True,
            'extracted_data': extracted
        }), 200
    
    except Exception as e:
        print(f"[ERROR] CV parsing error: {str(e)}")
        return jsonify({'success': False, 'error': f'Parsing failed: {str(e)}'}), 500

@automation_bp.route("/api/generate-cover-letter", methods=["POST"])
def generate_cover_letter():
    """Generate cover letter"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data'}), 400
        
        company = data.get('company', '').strip()
        job_role = data.get('job_role', '').strip()
        job_description = data.get('job_description', '').strip()
        
        if not all([company, job_role, job_description]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        prompt = f"""Generate a professional cover letter:

Company: {company}
Job Role: {job_role}
Job Description: {job_description}

Write 3-4 paragraphs. No salutation or closing. Be specific to role and company."""

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600
        )
        
        cover_letter = completion.choices[0].message.content.strip()
        
        return jsonify({
            'success': True,
            'cover_letter': cover_letter
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error: {str(e)}'}), 500

@automation_bp.route("/api/send-applications", methods=["POST"])
def send_applications():
    """Send applications"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data'}), 400
        
        user_name = data.get('user_name', 'Applicant').strip()
        user_phone = data.get('user_phone', '').strip()
        user_email = data.get('user_email', '').strip()
        user_linkedin = data.get('user_linkedin', '').strip()
        user_github = data.get('user_github', '').strip()
        
        company = data.get('company', '').strip()
        job_role = data.get('job_role', '').strip()
        hr_emails = data.get('hr_emails', [])
        cover_letter_body = data.get('cover_letter_body', '').strip()
        subject = data.get('subject', f'Application for {job_role} at {company}').strip()
        cv_path = data.get('cv_path', '')
        
        if not all([user_email, company, job_role, hr_emails, cover_letter_body]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        if not isinstance(hr_emails, list) or len(hr_emails) == 0:
            return jsonify({'success': False, 'error': 'No emails provided'}), 400

        if not cv_path or not os.path.exists(cv_path):
            return jsonify({'success': False, 'error': 'CV file not found. Please re-upload your CV.'}), 400

        # Short professional email body (NOT the full cover letter text)
        email_html = generate_application_email_html(
            user_name, user_phone, user_email, user_linkedin, user_github, company, job_role
        )

        # Render the cover letter into its own PDF to attach alongside the CV
        try:
            cover_letter_pdf_path = generate_cover_letter_pdf(
                cover_letter_body, user_name, user_phone, user_email,
                user_linkedin, user_github, company, job_role,
                recipient_email=hr_emails[0] if hr_emails else None
            )
        except Exception as e:
            return jsonify({'success': False, 'error': f'Failed to create cover letter PDF: {str(e)}'}), 500

        safe_name = re.sub(r'[^A-Za-z0-9_]+', '_', user_name).strip('_') or 'Applicant'
        cv_display_name = f"{safe_name}_CV.pdf"
        cover_letter_display_name = f"{safe_name}_Cover_Letter.pdf"

        attachments = [
            (cv_path, cv_display_name),
            (cover_letter_pdf_path, cover_letter_display_name),
        ]

        results = []
        sent_count = 0
        
        for hr_email in hr_emails:
            try:
                success, message = send_email_via_gmail(
                    sender_email=user_email,
                    recipient_email=hr_email,
                    subject=subject,
                    body_html=email_html,
                    attachments=attachments
                )
                
                if success:
                    sent_count += 1
                
                log_application(
                    user_email=user_email,
                    company=company,
                    job_role=job_role,
                    hr_email=hr_email,
                    subject=subject,
                    email_status="sent" if success else "failed",
                    error_message=None if success else message
                )
                
                results.append({
                    'hr_email': hr_email,
                    'success': success,
                    'message': message
                })
            
            except Exception as e:
                log_application(
                    user_email=user_email,
                    company=company,
                    job_role=job_role,
                    hr_email=hr_email,
                    subject=subject,
                    email_status="failed",
                    error_message=str(e)
                )
                
                results.append({
                    'hr_email': hr_email,
                    'success': False,
                    'message': str(e)
                })
        
        return jsonify({
            'success': True,
            'sent_count': sent_count,
            'total_count': len(hr_emails),
            'results': results,
            'message': f'Sent to {sent_count}/{len(hr_emails)} recipients'
        }), 200
    
    except Exception as e:
        print(f"[ERROR] Send error: {str(e)}")
        return jsonify({'success': False, 'error': f'Error: {str(e)}'}), 500

@automation_bp.route("/api/applications-history", methods=["GET"])
def get_applications_history():
    """Get application history"""
    try:
        user_email = request.args.get('email', '').strip()
        
        if not user_email:
            return jsonify({'success': False, 'error': 'Email required'}), 400
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM sent_applications 
            WHERE user_email = ? 
            ORDER BY sent_at DESC
            LIMIT 50
        """, (user_email,))
        
        rows = cursor.fetchall()
        conn.close()
        
        applications = [dict(row) for row in rows]
        return jsonify({
            'success': True,
            'applications': applications
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@automation_bp.route("/health", methods=["GET"])
def health():
    """Health check"""
    return jsonify({
        'status': 'ok',
        'gmail_available': GMAIL_AVAILABLE,
        'database': os.path.exists(DB_PATH),
        'timestamp': datetime.now().isoformat()
    }), 200