from flask import Blueprint, jsonify
from app.models import Meeting, Task, Participant, Report
from app.middleware.auth import token_required
from sqlalchemy import func
from app import db
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/stats', methods=['GET'])
@token_required
def stats(current_user):
    # Base count isolated to current user
    total_meetings = Meeting.query.filter_by(host_id=current_user.user_id).count()
    total_mins     = db.session.query(func.sum(Meeting.duration_mins)).filter_by(host_id=current_user.user_id).scalar() or 0
    
    # Secure isolated tasks
    total_tasks    = Task.query.join(Meeting).filter(Meeting.host_id == current_user.user_id).count()
    pending_tasks  = Task.query.join(Meeting).filter(Meeting.host_id == current_user.user_id, Task.status != 'done').count()
    completed_tasks = total_tasks - pending_tasks
    task_completion_rate = round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0.0

    # Calculate average AI Productivity Score across reports
    avg_prod_score = db.session.query(func.avg(Report.productivity_score)).join(Meeting).filter(Meeting.host_id == current_user.user_id).scalar()
    avg_prod_score = int(avg_prod_score) if avg_prod_score is not None else 80
    
    # Calculate average participant attendance rate
    # Average of (participant duration / meeting duration)
    # Filter by user meetings
    attendance_rate = 100.0
    try:
        meeting_durations = db.session.query(
            Meeting.meeting_id, Meeting.duration_mins
        ).filter(Meeting.host_id == current_user.user_id).subquery()
        
        avg_att = db.session.query(
            func.avg(Participant.duration_mins)
        ).join(meeting_durations, Participant.meeting_id == meeting_durations.c.meeting_id).scalar()
        
        avg_meet_len = db.session.query(
            func.avg(meeting_durations.c.duration_mins)
        ).scalar()
        
        if avg_att and avg_meet_len:
            attendance_rate = round(min(100.0, (avg_att / avg_meet_len) * 100), 1)
    except Exception:
        pass

    # Recent meetings
    recent = Meeting.query.filter_by(host_id=current_user.user_id).order_by(Meeting.started_at.desc()).limit(5).all()
    
    # Calculate weekly activity (meetings count in last 7 days)
    # Construct last 7 days list with counts
    weekly_activity = []
    today = datetime.utcnow().date()
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_str = day.strftime('%a')
        
        count = Meeting.query.filter(
            Meeting.host_id == current_user.user_id,
            func.date(Meeting.started_at) == day
        ).count()
        
        weekly_activity.append({
            'name': day_str,
            'Meetings': count
        })

    # Platform breakdown pie-chart stats
    platforms = db.session.query(
        Meeting.platform, func.count(Meeting.meeting_id)
    ).filter_by(host_id=current_user.user_id).group_by(Meeting.platform).all()
    
    platform_breakdown = [{'name': p[0].upper(), 'value': p[1]} for p in platforms]
    if not platform_breakdown:
        platform_breakdown = [{'name': 'None', 'value': 1}]

    # Return stats payload
    return jsonify({
        'total_meetings': total_meetings,
        'total_hours':    round(total_mins / 60, 1),
        'pending_tasks':  pending_tasks,
        'this_week':      Meeting.query.filter(Meeting.host_id == current_user.user_id, Meeting.started_at >= (datetime.utcnow() - timedelta(days=7))).count(),
        'task_completion_rate': task_completion_rate,
        'avg_productivity_score': avg_prod_score,
        'avg_attendance_rate':    attendance_rate,
        'weekly_activity':        weekly_activity,
        'platform_breakdown':     platform_breakdown,
        'recent_meetings': [{
            'meeting_id':    m.meeting_id,
            'title':         m.title,
            'platform':      m.platform,
            'started_at':    m.started_at.isoformat() if m.started_at else None,
            'duration_mins': m.duration_mins,
            'has_report':    m.report is not None
        } for m in recent]
    })
