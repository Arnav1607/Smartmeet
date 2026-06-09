import io, boto3, os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

BRAND_PURPLE = colors.HexColor('#7c6fff')
BRAND_DARK   = colors.HexColor('#1a1a2e')
LIGHT_GRAY   = colors.HexColor('#f5f5f8')

def generate_pdf(meeting, report, participants, tasks) -> str:
    """Generate PDF report and upload to S3 (or save locally). Returns URL."""
    buffer = io.BytesIO()
    doc    = SimpleDocTemplate(buffer, pagesize=letter,
                               leftMargin=0.75*inch, rightMargin=0.75*inch,
                               topMargin=0.75*inch, bottomMargin=0.75*inch)
    styles = getSampleStyleSheet()
    story  = []

    # ── Cover ──
    title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=28, textColor=BRAND_PURPLE, spaceAfter=6)
    sub_style   = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=13, textColor=colors.gray)
    story.append(Paragraph("SmartMeet AI", title_style))
    story.append(Paragraph("Meeting Intelligence Report", sub_style))
    story.append(HRFlowable(width="100%", thickness=2, color=BRAND_PURPLE, spaceAfter=20))

    # ── Meeting metadata ──
    meta = [
        ["Meeting Title", meeting.title or "Untitled Meeting"],
        ["Platform",      meeting.platform.upper()],
        ["Date",          meeting.started_at.strftime('%B %d, %Y') if meeting.started_at else "—"],
        ["Duration",      f"{meeting.duration_mins} minutes"],
        ["Participants",  str(len(participants))],
        ["Productivity",  f"{report.productivity_score}/100"],
    ]
    t = Table(meta, colWidths=[2*inch, 4.5*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), LIGHT_GRAY),
        ('FONTNAME',   (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE',   (0,0), (-1,-1), 10),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [colors.white, LIGHT_GRAY]),
        ('GRID',       (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('PADDING',    (0,0), (-1,-1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.3*inch))

    # ── Executive Summary ──
    h2 = ParagraphStyle('H2', parent=styles['Heading2'], textColor=BRAND_PURPLE, fontSize=14, spaceBefore=12)
    body = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, leading=14)
    story.append(Paragraph("Executive Summary", h2))
    story.append(Paragraph(report.executive_summary or "No summary available.", body))
    story.append(Spacer(1, 0.2*inch))

    # ── Key Decisions ──
    story.append(Paragraph("Key Decisions", h2))
    decisions = report.key_decisions or []
    for d in decisions:
        story.append(Paragraph(f"• {d}", body))
    if not decisions:
        story.append(Paragraph("No key decisions recorded.", body))
    story.append(Spacer(1, 0.2*inch))

    # ── Action Items ──
    story.append(Paragraph("Action Items", h2))
    if tasks:
        task_data = [["Task", "Owner", "Deadline", "Priority"]]
        for task in tasks:
            task_data.append([task.description or "", task.owner_name or "", str(task.deadline or "—"), task.priority or "medium"])
        t = Table(task_data, colWidths=[2.5*inch, 1.3*inch, 1.2*inch, 1*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), BRAND_PURPLE),
            ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
            ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',   (0,0), (-1,-1), 9),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LIGHT_GRAY]),
            ('GRID',       (0,0), (-1,-1), 0.5, colors.lightgrey),
            ('PADDING',    (0,0), (-1,-1), 6),
        ]))
        story.append(t)
    else:
        story.append(Paragraph("No action items extracted.", body))
    story.append(Spacer(1, 0.2*inch))

    # ── Attendance ──
    story.append(Paragraph("Attendance Report", h2))
    if participants:
        att_data = [["Name", "Email", "Joined", "Duration"]]
        for p in participants:
            att_data.append([p.name or "—", p.email or "—",
                             p.joined_at.strftime('%H:%M') if p.joined_at else "—",
                             f"{p.duration_mins}m"])
        t = Table(att_data, colWidths=[1.8*inch, 2.2*inch, 1*inch, 1*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), BRAND_DARK),
            ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
            ('FONTSIZE',   (0,0), (-1,-1), 9),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LIGHT_GRAY]),
            ('GRID',       (0,0), (-1,-1), 0.5, colors.lightgrey),
            ('PADDING',    (0,0), (-1,-1), 6),
        ]))
        story.append(t)
    story.append(Spacer(1, 0.3*inch))

    # ── Footer ──
    story.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
    story.append(Paragraph(f"Generated by SmartMeet AI · {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", sub_style))

    doc.build(story)
    buffer.seek(0)

    # Smart S3 vs Local File System Fallback
    aws_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret = os.getenv('AWS_SECRET_ACCESS_KEY')
    bucket = os.getenv('AWS_S3_BUCKET')

    if aws_key and aws_secret and bucket:
        try:
            return _upload_to_s3(buffer, meeting.meeting_id)
        except Exception as e:
            print(f"[PDF S3 Upload Error] Upload failed, falling back to local storage: {e}")

    # Local Disk Fallback
    base_dir = os.path.abspath(os.path.dirname(__file__))
    upload_dir = os.path.join(base_dir, '..', '..', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    
    file_name = f"{meeting.meeting_id}.pdf"
    file_path = os.path.join(upload_dir, file_name)
    with open(file_path, "wb") as f:
        f.write(buffer.getvalue())

    return f"/uploads/{file_name}"

def _upload_to_s3(buffer, meeting_id: str) -> str:
    s3 = boto3.client('s3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION', 'us-east-1'))
    key = f"reports/{meeting_id}.pdf"
    bucket = os.getenv('AWS_S3_BUCKET', 'smartmeet-reports')
    s3.upload_fileobj(buffer, bucket, key, ExtraArgs={'ContentType': 'application/pdf'})
    return f"https://{bucket}.s3.amazonaws.com/{key}"
