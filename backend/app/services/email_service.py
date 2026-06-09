import os
import base64
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition

def send_report_email(participants, meeting, report, pdf_url: str):
    """Send HTML email with PDF attachment to all meeting participants."""
    to_emails = [p.email for p in participants if p.email]
    if not to_emails:
        print("[Email Service] No recipient emails found. Skipping.")
        return

    html_body = f"""
    <div style="font-family:sans-serif;max-width:600px;margin:0 auto">
      <div style="background:#1a1a2e;padding:24px;border-radius:12px 12px 0 0">
        <h1 style="color:#a78bfa;margin:0;font-size:22px">SmartMeet AI Report</h1>
        <p style="color:#8080c0;margin:6px 0 0">{meeting.title or 'Meeting Report'}</p>
      </div>
      <div style="background:#f9f9fc;padding:24px;border-radius:0 0 12px 12px">
        <h2 style="color:#1a1a2e;font-size:16px">Executive Summary</h2>
        <p style="color:#444;line-height:1.6">{report.executive_summary or 'No summary available.'}</p>

        <h2 style="color:#1a1a2e;font-size:16px;margin-top:20px">Key Decisions</h2>
        <ul style="color:#444;line-height:1.8">
          {''.join(f'<li>{d}</li>' for d in (report.key_decisions or []))}
        </ul>
        
        <p style="margin-top:24px;color:#1a1a2e;font-size:14px;font-weight:bold">Meeting Analytics Overview:</p>
        <p style="color:#444;font-size:13px">Productivity Rating: {report.productivity_score}/100 | Sentiment score: {report.sentiment_score}</p>

        <div style="margin-top:24px;padding:16px;background:#eeeeff;border-radius:8px;text-align:center">
          <a href="{pdf_url}" style="background:#7c6fff;color:white;padding:10px 24px;border-radius:6px;text-decoration:none;font-weight:600">
            Download Full PDF Report
          </a>
        </div>

        <p style="color:#aaa;font-size:12px;margin-top:20px;text-align:center">
          Sent by SmartMeet AI · final year project presentation
        </p>
      </div>
    </div>
    """

    subject = f"Meeting Report: {meeting.title or 'Your Meeting'}"
    
    # Retrieve PDF content for attachment
    pdf_content = None
    try:
        # If it is local url, read file directly
        if pdf_url.startswith('/uploads/'):
            base_dir = os.path.abspath(os.path.dirname(__file__))
            file_path = os.path.join(base_dir, '..', '..', 'uploads', pdf_url.split('/')[-1])
            with open(file_path, 'rb') as f:
                pdf_content = f.read()
        elif pdf_url.startswith('http'):
            # Fetch remote PDF
            pdf_response = requests.get(pdf_url, timeout=10)
            if pdf_response.ok:
                pdf_content = pdf_response.content
    except Exception as e:
        print(f"[Email Service] PDF attachment retrieval failed: {e}")

    sg_key = os.getenv('SENDGRID_API_KEY')
    from_email = os.getenv('FROM_EMAIL', 'reports@smartmeet.ai')

    if sg_key:
        # Send via SendGrid
        try:
            message = Mail(
                from_email=from_email,
                to_emails=to_emails,
                subject=subject,
                html_content=html_body
            )
            
            if pdf_content:
                encoded_pdf = base64.b64encode(pdf_content).decode()
                attachment = Attachment(
                    FileContent(encoded_pdf),
                    FileName('meeting-report.pdf'),
                    FileType('application/pdf'),
                    Disposition('attachment')
                )
                message.attachment = attachment
                
            sg = SendGridAPIClient(sg_key)
            sg.send(message)
            print(f"[Email Service] Successfully sent report email via SendGrid to {to_emails}")
            return
        except Exception as e:
            print(f"[Email Service] SendGrid failed, falling back to SMTP: {e}")

    # Fallback to local SMTP or console logs
    smtp_server = os.getenv('SMTP_SERVER', 'localhost')
    smtp_port = int(os.getenv('SMTP_PORT', 1025))
    smtp_user = os.getenv('SMTP_USERNAME')
    smtp_pass = os.getenv('SMTP_PASSWORD')

    # Try SMTP
    try:
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = ", ".join(to_emails)
        msg['Subject'] = subject
        msg.attach(MIMEText(html_body, 'html'))

        if pdf_content:
            part = MIMEApplication(pdf_content, Name="meeting-report.pdf")
            part['Content-Disposition'] = 'attachment; filename="meeting-report.pdf"'
            msg.attach(part)

        # Attempt connection
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=5)
        if smtp_user and smtp_pass:
            server.login(smtp_user, smtp_pass)
        server.sendmail(from_email, to_emails, msg.as_string())
        server.quit()
        print(f"[Email Service] Successfully sent report email via SMTP ({smtp_server}:{smtp_port}) to {to_emails}")
        return
    except Exception as e:
        print(f"[Email Service] SMTP connection failed ({e}). Bypassing email send.")

    # MOCK Logger fallback if all else fails
    print("=" * 60)
    print(f"[MOCK EMAIL LOGGER] Email Simulation triggered for {to_emails}")
    print(f"Subject: {subject}")
    print(f"Body snippet: {report.executive_summary[:200]}...")
    print(f"Attachment PDF URL: {pdf_url}")
    print("=" * 60)
