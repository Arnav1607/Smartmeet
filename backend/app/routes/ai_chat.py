# app/routes/ai_chat.py — RAG-based Chat with Meeting Transcript
from flask import Blueprint, request, jsonify
from app.models.models import Meeting
from app.middleware.auth import token_required
from app.services.rag_service import query_transcript

ai_chat_bp = Blueprint("ai_chat", __name__)

@ai_chat_bp.route("/chat", methods=["POST"])
@token_required
def chat(current_user):
    data       = request.get_json() or {}
    meeting_id = data.get('meeting_id') or data.get('meetingId')
    question   = data.get('question', '').strip()

    if not meeting_id or not question:
        return jsonify({"error": "meeting_id and question required"}), 400

    # Ensure meeting exists
    meeting = Meeting.query.get_or_404(meeting_id)

    # In a multi-tenant application, ensure user has access to this meeting
    if meeting.host_id != current_user.user_id and current_user.role != 'admin':
        # Check if user is a participant
        from app.models import Participant
        part = Participant.query.filter_by(meeting_id=meeting_id, user_id=current_user.user_id).first()
        if not part:
            return jsonify({"error": "Unauthorized access to this meeting's history"}), 403

    try:
        # Run RAG query
        answer = query_transcript(meeting_id, question)
        return jsonify({
            "answer": answer,
            "meeting_id": meeting_id
        })
    except Exception as e:
        print(f"[Chat Endpoint Error] Chat processing failed: {e}")
        return jsonify({"answer": "I'm sorry, I encountered an issue accessing the AI engine. Please verify the server configuration."}), 500
