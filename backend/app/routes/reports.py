from flask import Blueprint, jsonify, redirect, request, current_app, send_file
from app.models import Report, Meeting, Participant, Task
from app.middleware.auth import token_required
import os

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/<meeting_id>', methods=['GET'])
@token_required
def get_report(current_user, meeting_id):
    r = Report.query.filter_by(meeting_id=meeting_id).first_or_404()
    tasks = Task.query.filter_by(meeting_id=meeting_id).all()
    participants = Participant.query.filter_by(meeting_id=meeting_id).all()
    
    return jsonify({
        'report_id':          r.report_id,
        'summary':            r.executive_summary,  # maintain API property name
        'detailed_summary':   r.detailed_summary,
        'key_decisions':      r.key_decisions,
        'risks':              r.risks,
        'productivity_score': r.productivity_score,
        'sentiment_score':    r.sentiment_score,
        'sentiment_breakdown':r.sentiment_breakdown,
        'speaker_stats':      r.speaker_stats,
        'meeting_type':       r.meeting_type,
        'pdf_url':            r.pdf_s3_url,
        'tasks': [{
            'task_id':     t.task_id,
            'description': t.description,
            'owner_name':  t.owner_name,
            'deadline':    str(t.deadline) if t.deadline else None,
            'priority':    t.priority,
            'status':      t.status
        } for t in tasks],
        'attendance': [{
            'name':          p.name,
            'email':         p.email,
            'joined_at':     p.joined_at.isoformat() if p.joined_at else None,
            'duration_mins': p.duration_mins
        } for p in participants]
    })

@reports_bp.route('/<meeting_id>/download', methods=['GET'])
@token_required
def download_report(current_user, meeting_id):
    r = Report.query.filter_by(meeting_id=meeting_id).first_or_404()
    if not r.pdf_s3_url:
        return jsonify({'error': 'PDF not yet generated'}), 404
        
    # Serve locally if it starts with '/uploads'
    if r.pdf_s3_url.startswith('/uploads/'):
        filename = r.pdf_s3_url.split('/')[-1]
        upload_dir = os.path.join(current_app.root_path, '..', 'uploads')
        return send_file(
            os.path.join(upload_dir, filename), 
            mimetype='application/pdf', 
            as_attachment=True,
            download_name=f"SmartMeet_Report_{meeting_id}.pdf"
        )
    return redirect(r.pdf_s3_url)

@reports_bp.route('/<meeting_id>/excel', methods=['GET'])
@token_required
def download_excel(current_user, meeting_id):
    meeting = Meeting.query.get_or_404(meeting_id)
    report = meeting.report
    if not report:
        return jsonify({'error': 'Analytics report details not yet available'}), 404
        
    participants = Participant.query.filter_by(meeting_id=meeting_id).all()
    tasks = Task.query.filter_by(meeting_id=meeting_id).all()
    
    from app.services.report_exporter import generate_excel_report
    excel_buffer = generate_excel_report(meeting, report, participants, tasks)
    
    return send_file(
        excel_buffer,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"SmartMeet_Report_{meeting_id}.xlsx"
    )

@reports_bp.route('/<meeting_id>/docx', methods=['GET'])
@token_required
def download_docx(current_user, meeting_id):
    meeting = Meeting.query.get_or_404(meeting_id)
    report = meeting.report
    if not report:
        return jsonify({'error': 'Analytics report details not yet available'}), 404
        
    participants = Participant.query.filter_by(meeting_id=meeting_id).all()
    tasks = Task.query.filter_by(meeting_id=meeting_id).all()
    
    from app.services.report_exporter import generate_docx_report
    docx_buffer = generate_docx_report(meeting, report, participants, tasks)
    
    return send_file(
        docx_buffer,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        as_attachment=True,
        download_name=f"SmartMeet_Report_{meeting_id}.docx"
    )

@reports_bp.route('/chat', methods=['POST'])
@token_required
def chat_with_meeting(current_user):
    data       = request.get_json() or {}
    meeting_id = data.get('meeting_id') or data.get('meetingId')
    question   = data.get('question', '').strip()
    if not meeting_id or not question:
        return jsonify({'error': 'meeting_id and question required'}), 400
        
    # Standard fallback RAG query route
    from app.services.rag_service import query_transcript
    answer = query_transcript(meeting_id, question)
    return jsonify({'answer': answer})
