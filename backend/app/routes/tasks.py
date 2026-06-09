from flask import Blueprint, request, jsonify
from app import db
from app.models import Task, Meeting, User
from app.middleware.auth import token_required

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('/', methods=['GET'])
@token_required
def list_tasks(current_user):
    status = request.args.get('status')
    
    # Isolate tasks to meetings hosted by this user
    query = Task.query.join(Meeting).filter(Meeting.host_id == current_user.user_id)
    
    if status:
        query = query.filter(Task.status == status)
        
    tasks = query.order_by(Task.deadline).all()
    
    return jsonify({'tasks': [{
        'task_id':     t.task_id,
        'meeting_id':  t.meeting_id,
        'description': t.description,
        'owner_name':  t.owner_name,
        'deadline':    str(t.deadline) if t.deadline else None,
        'priority':    t.priority,
        'status':      t.status
    } for t in tasks]})

@tasks_bp.route('/<task_id>/complete', methods=['POST'])
@token_required
def complete_task(current_user, task_id):
    task = Task.query.get_or_404(task_id)
    
    # Verify ownership
    meeting = Meeting.query.get(task.meeting_id)
    if meeting.host_id != current_user.user_id and current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    task.status = 'done'
    db.session.commit()
    return jsonify({'message': 'Task marked complete', 'task_id': task_id, 'status': 'done'})

@tasks_bp.route('/<task_id>/status', methods=['POST'])
@token_required
def update_status(current_user, task_id):
    """Update task status to any valid state: pending, in_progress, done."""
    data = request.get_json() or {}
    new_status = data.get('status', '').strip().lower()
    
    if new_status not in ['pending', 'in_progress', 'done']:
        return jsonify({'error': 'Invalid status. Must be pending, in_progress, or done'}), 400
        
    task = Task.query.get_or_404(task_id)
    
    # Verify ownership
    meeting = Meeting.query.get(task.meeting_id)
    if meeting.host_id != current_user.user_id and current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    task.status = new_status
    db.session.commit()
    return jsonify({'message': f'Task status updated to {new_status}', 'task_id': task_id, 'status': task.status})

@tasks_bp.route('/<task_id>/remind', methods=['POST'])
@token_required
def remind_task(current_user, task_id):
    task = Task.query.get_or_404(task_id)
    meeting = Meeting.query.get(task.meeting_id)
    
    if meeting.host_id != current_user.user_id and current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
        
    # Simulate email reminder
    print(f"[Smart Reminders] Reminder triggered by {current_user.name} for task: '{task.description}' assigned to '{task.owner_name or 'Unassigned'}'")
    
    # We can invoke SMTP email mock sending logic
    from_email = os.getenv('FROM_EMAIL', 'reminders@smartmeet.ai')
    subject = f"ACTION REQUIRED: Task Reminder - {meeting.title}"
    body = f"Hello,\n\nThis is a friendly reminder for the task assigned to you during the meeting '{meeting.title}':\n\nTask: {task.description}\nPriority: {task.priority.upper()}\nDue Date: {task.deadline or 'As soon as possible'}\n\nPlease update the status in your SmartMeet AI Dashboard.\n\nBest regards,\nSmartMeet Assistant"
    
    # We can write it to console log
    print(f"SMTP Mock Reminder Email Sent.\nSubject: {subject}\nRecipient: {task.owner_name or 'Owner'}\nBody:\n{body}")
    
    return jsonify({'message': f'Reminder sent successfully for: {task.description}'})
