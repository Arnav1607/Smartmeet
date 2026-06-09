from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
from app import db
from app.models import Meeting, Participant, Transcript, Report, Task
from app.middleware.auth import token_required
import threading

meetings_bp = Blueprint('meetings', __name__)

@meetings_bp.route('/start', methods=['POST'])
@token_required
def start_meeting(current_user):
    data = request.get_json() or {}
    
    # Generate meeting id if content script didn't provide one
    meeting_id = data.get('meetingId') or f"mtg_{int(datetime.utcnow().timestamp())}"
    
    # Check if meeting already exists (e.g. extension retrying)
    existing = Meeting.query.get(meeting_id)
    if existing:
        return jsonify({'meeting_id': meeting_id, 'message': 'Meeting already active'}), 200

    meeting = Meeting(
        meeting_id  = meeting_id,
        title       = data.get('title', 'Untitled Meeting'),
        platform    = data.get('platform', 'other'),
        host_id     = current_user.user_id,
        started_at  = datetime.utcnow(),
        status      = 'active'
    )
    db.session.add(meeting)
    
    # Add host as first participant
    participant = Participant(
        meeting_id = meeting.meeting_id,
        user_id    = current_user.user_id,
        name       = current_user.name,
        email      = current_user.email,
        joined_at  = datetime.utcnow(),
        duration_mins = 0
    )
    db.session.add(participant)
    db.session.commit()
    
    return jsonify({'meeting_id': meeting.meeting_id, 'message': 'Meeting started'}), 201

@meetings_bp.route('/<meeting_id>/end', methods=['POST'])
@token_required
def end_meeting(current_user, meeting_id):
    meeting = Meeting.query.get_or_404(meeting_id)
    meeting.ended_at = datetime.utcnow()
    meeting.status = 'processing'
    
    if meeting.started_at:
        delta = meeting.ended_at - meeting.started_at
        meeting.duration_mins = max(1, int(delta.total_seconds() / 60))
    else:
        meeting.duration_mins = 1
        
    db.session.commit()

    # Capture the application instance from current request context
    app = current_app._get_current_object()

    def process_async(flask_app):
        # Run inside the Flask application context so database queries succeed
        with flask_app.app_context():
            try:
                from app.services.ai_service import process_transcript, score_sentiment, calculate_speaker_stats
                from app.services.encryption import decrypt
                from app.services.pdf_generator import generate_pdf
                from app.services.email_service import send_report_email
                from app.services.rag_service import index_transcript
                
                # Fetch transcripts
                entries_raw = Transcript.query.filter_by(meeting_id=meeting_id).order_by(Transcript.timestamp_ms).all()
                entries = []
                sentiments = {'pos': 0, 'neu': 0, 'neg': 0}
                
                for e in entries_raw:
                    try:
                        text = decrypt(e.text_encrypted, e.iv)
                        sentiment = score_sentiment(text)
                        e.sentiment = sentiment
                        sentiments[sentiment] += 1
                        entries.append({'speaker': e.speaker, 'text': text, 'sentiment': sentiment})
                    except Exception as ex:
                        print(f"[Decrypt Error] transcript {e.transcript_id}: {ex}")
                
                # Save sentiments back
                db.session.commit()

                # If no transcripts captured, save empty placeholder reports
                if not entries:
                    meeting.status = 'completed'
                    db.session.commit()
                    return

                # Calculate stats
                speaker_stats = calculate_speaker_stats(entries)
                ai_result = process_transcript(entries)

                # Sentiment summary
                total_sent = sum(sentiments.values()) or 1
                sentiment_breakdown = {
                    'positive': sentiments['pos'],
                    'neutral': sentiments['neu'],
                    'negative': sentiments['neg']
                }
                # Score between -1.0 and 1.0
                sentiment_score = round((sentiments['pos'] - sentiments['neg']) / total_sent, 2)

                # Calculate AI Productivity Score (fallback if not in AI results)
                # Weights: Attendance Skew, Sentiments, Tasks, Dialogue Skew
                prod_score = ai_result.get('productivity_score', 80)

                # Update/Create Report
                report = Report(
                    meeting_id          = meeting_id,
                    executive_summary   = ai_result.get('executive_summary', ''),
                    detailed_summary    = ai_result.get('detailed_summary', ''),
                    key_decisions       = ai_result.get('key_decisions', []),
                    risks               = ai_result.get('risks', []),
                    speaker_stats       = speaker_stats,
                    sentiment_score     = sentiment_score,
                    sentiment_breakdown = sentiment_breakdown,
                    productivity_score  = prod_score,
                    dynamics            = ai_result.get('dynamics', {
                        'agreement_score': 80,
                        'frustration_level': 10,
                        'engagement_level': 85,
                        'excitement_level': 45
                    }),
                    meeting_type        = ai_result.get('meeting_type', 'other')
                )
                db.session.add(report)

                # Extract and store tasks
                for item in ai_result.get('action_items', []):
                    # Try to parse target deadline date or keep none
                    deadline_date = None
                    deadline_str = item.get('deadline')
                    if deadline_str:
                        try:
                            # Try simple formats
                            deadline_date = datetime.strptime(deadline_str, "%Y-%m-%d").date()
                        except Exception:
                            deadline_date = datetime.utcnow().date() + timedelta(days=7)

                    task = Task(
                        meeting_id  = meeting_id,
                        description = item.get('task', 'No description'),
                        owner_name  = item.get('owner', 'Unassigned'),
                        priority    = item.get('priority', 'medium'),
                        deadline    = deadline_date,
                        status      = 'pending'
                    )
                    db.session.add(task)
                db.session.commit()

                # Index meeting into ChromaDB persistent RAG vector store
                try:
                    index_transcript(meeting_id, entries)
                except Exception as ex:
                    print(f"[RAG Index Error] ChromaDB failed to index meeting {meeting_id}: {ex}")

                # Update participant durations (mock logic based on meeting length)
                participants = Participant.query.filter_by(meeting_id=meeting_id).all()
                for p in participants:
                    if not p.duration_mins or p.duration_mins == 0:
                        p.duration_mins = meeting.duration_mins
                db.session.commit()

                # Generate PDF and upload/save locally
                pdf_url = generate_pdf(meeting, report, participants, Task.query.filter_by(meeting_id=meeting_id).all())
                report.pdf_s3_url = pdf_url
                meeting.status = 'completed'
                db.session.commit()

                # Send email reports
                try:
                    send_report_email(participants, meeting, report, pdf_url)
                except Exception as ex:
                    print(f"[Email Error] Failed to distribute email: {ex}")

            except Exception as e:
                print(f"[Async Process Crash] Meeting {meeting_id}: {e}")
                meeting.status = 'failed'
                db.session.commit()

    # Start processing thread
    threading.Thread(target=process_async, args=(app,), daemon=True).start()
    return jsonify({'message': 'Meeting ended. Processing analytics and summaries in background.', 'meeting_id': meeting_id})

@meetings_bp.route('/', methods=['GET'])
@token_required
def list_meetings(current_user):
    page = int(request.args.get('page', 1))
    q    = request.args.get('q', '').strip()
    
    # In a multi-tenant environment, managers/admins see more. Users see meetings they hosted.
    # For user ease, show all meetings owned by host.
    query = Meeting.query.filter_by(host_id=current_user.user_id)
    
    if q:
        query = query.filter(Meeting.title.ilike(f'%{q}%'))
        
    meetings = query.order_by(Meeting.started_at.desc()).paginate(page=page, per_page=15, error_out=False)
    
    return jsonify({
        'meetings': [{
            'meeting_id':    m.meeting_id,
            'title':         m.title,
            'platform':      m.platform,
            'started_at':    m.started_at.isoformat() if m.started_at else None,
            'duration_mins': m.duration_mins,
            'status':        m.status,
            'has_report':    m.report is not None
        } for m in meetings.items],
        'total': meetings.total,
        'pages': meetings.pages
    })

@meetings_bp.route('/<meeting_id>', methods=['GET'])
@token_required
def get_meeting(current_user, meeting_id):
    m = Meeting.query.get_or_404(meeting_id)
    r = m.report
    tasks = Task.query.filter_by(meeting_id=meeting_id).all()
    participants = Participant.query.filter_by(meeting_id=meeting_id).all()

    return jsonify({
        'meeting_id':    m.meeting_id,
        'title':         m.title,
        'platform':      m.platform,
        'started_at':    m.started_at.isoformat() if m.started_at else None,
        'ended_at':      m.ended_at.isoformat() if m.ended_at else None,
        'duration_mins': m.duration_mins,
        'status':        m.status,
        'report': {
            'summary':            r.executive_summary,
            'detailed_summary':   r.detailed_summary,
            'key_decisions':      r.key_decisions,
            'risks':              r.risks,
            'productivity_score': r.productivity_score,
            'sentiment_score':    r.sentiment_score,
            'sentiment_breakdown':r.sentiment_breakdown,
            'speaker_stats':      r.speaker_stats,
            'meeting_type':       r.meeting_type,
            'pdf_url':            r.pdf_s3_url,
            'tasks':              [t.to_dict() for t in tasks],
            'attendance':         [p.to_dict() for p in participants]
        } if r else None
    })

@meetings_bp.route('/search', methods=['GET'])
@token_required
def search(current_user):
    """Keyword search across meeting titles, and semantic fallback."""
    q = request.args.get('q', '').strip()
    platform = request.args.get('platform', '')
    
    query = Meeting.query.filter_by(host_id=current_user.user_id)
    if platform:
        query = query.filter_by(platform=platform)
        
    if q:
        query = query.filter(Meeting.title.ilike(f'%{q}%'))
        
    meetings = query.order_by(Meeting.started_at.desc()).all()
    
    # If a semantic search is wanted, we could also search the transcripts.
    return jsonify({
        'meetings': [{
            'meeting_id':    m.meeting_id,
            'title':         m.title,
            'platform':      m.platform,
            'started_at':    m.started_at.isoformat() if m.started_at else None,
            'duration_mins': m.duration_mins,
            'status':        m.status,
            'has_report':    m.report is not None
        } for m in meetings]
    })

@meetings_bp.route('/<meeting_id>', methods=['DELETE'])
@token_required
def delete_meeting(current_user, meeting_id):
    m = Meeting.query.get_or_404(meeting_id)
    if m.host_id != current_user.user_id and current_user.role != 'admin':
        return jsonify({'error': 'Forbidden'}), 403
    db.session.delete(m)
    db.session.commit()
    return jsonify({'message': 'Meeting deleted'})
