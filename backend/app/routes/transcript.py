from flask import Blueprint, request, jsonify
from app import db
from app.models import Transcript
from app.middleware.auth import token_required
from app.services.encryption import encrypt, decrypt

transcript_bp = Blueprint('transcript', __name__)

@transcript_bp.route('/append', methods=['POST'])
@token_required
def append_transcript(current_user):
    data       = request.get_json()
    meeting_id = data.get('meetingId')
    entries    = data.get('entries', [])
    if not meeting_id or not entries:
        return jsonify({'error': 'meetingId and entries required'}), 400

    for entry in entries:
        text = entry.get('text', '').strip()
        if not text:
            continue
        enc = encrypt(text)
        t = Transcript(
            meeting_id     = meeting_id,
            speaker        = entry.get('speaker', 'Unknown')[:100],
            text_encrypted = enc['ciphertext'],
            iv             = enc['iv'],
            timestamp_ms   = entry.get('ts', 0)
        )
        db.session.add(t)
    db.session.commit()
    return jsonify({'saved': len(entries)})

@transcript_bp.route('/<meeting_id>', methods=['GET'])
@token_required
def get_transcript(current_user, meeting_id):
    entries = Transcript.query.filter_by(meeting_id=meeting_id).order_by(Transcript.timestamp_ms).all()
    result  = []
    for e in entries:
        try:
            text = decrypt(e.text_encrypted, e.iv)
        except Exception:
            text = '[decryption error]'
        result.append({
            'speaker':   e.speaker,
            'text':      text,
            'timestamp': e.timestamp_ms,
            'sentiment': e.sentiment
        })
    return jsonify({'transcript': result})
