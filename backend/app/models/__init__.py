from app import db
import uuid
from datetime import datetime

def gen_uuid():
    return str(uuid.uuid4())

class User(db.Model):
    __tablename__ = 'users'
    user_id      = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    email        = db.Column(db.String(255), unique=True, nullable=False)
    name         = db.Column(db.String(100))
    role         = db.Column(db.Enum('admin','manager','user'), default='user')
    password_hash= db.Column(db.String(255))
    google_id    = db.Column(db.String(100))
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    meetings     = db.relationship('Meeting', backref='host', lazy=True)

class Meeting(db.Model):
    __tablename__ = 'meetings'
    meeting_id   = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    title        = db.Column(db.String(255))
    platform     = db.Column(db.Enum('gmeet','zoom','teams','other'), default='other')
    host_id      = db.Column(db.String(36), db.ForeignKey('users.user_id'))
    started_at   = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at     = db.Column(db.DateTime)
    duration_mins= db.Column(db.Integer, default=0)
    transcripts  = db.relationship('Transcript', backref='meeting', lazy=True)
    participants = db.relationship('Participant', backref='meeting', lazy=True)
    report       = db.relationship('Report', backref='meeting', uselist=False)
    tasks        = db.relationship('Task', backref='meeting', lazy=True)

class Transcript(db.Model):
    __tablename__   = 'transcripts'
    transcript_id   = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    meeting_id      = db.Column(db.String(36), db.ForeignKey('meetings.meeting_id'), nullable=False)
    speaker         = db.Column(db.String(100))
    text_encrypted  = db.Column(db.Text)
    iv              = db.Column(db.String(64))
    timestamp_ms    = db.Column(db.BigInteger)
    sentiment       = db.Column(db.Enum('pos','neu','neg'), default='neu')

class Participant(db.Model):
    __tablename__   = 'participants'
    participant_id  = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    meeting_id      = db.Column(db.String(36), db.ForeignKey('meetings.meeting_id'))
    user_id         = db.Column(db.String(36), db.ForeignKey('users.user_id'))
    name            = db.Column(db.String(100))
    email           = db.Column(db.String(255))
    joined_at       = db.Column(db.DateTime)
    left_at         = db.Column(db.DateTime)
    duration_mins   = db.Column(db.Integer, default=0)

class Task(db.Model):
    __tablename__ = 'tasks'
    task_id      = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    meeting_id   = db.Column(db.String(36), db.ForeignKey('meetings.meeting_id'))
    owner_name   = db.Column(db.String(100))
    description  = db.Column(db.Text)
    deadline     = db.Column(db.Date)
    priority     = db.Column(db.Enum('high','medium','low'), default='medium')
    status       = db.Column(db.Enum('pending','in_progress','done'), default='pending')
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

class Report(db.Model):
    __tablename__       = 'reports'
    report_id           = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    meeting_id          = db.Column(db.String(36), db.ForeignKey('meetings.meeting_id'), unique=True)
    summary             = db.Column(db.Text)
    detailed_summary    = db.Column(db.Text)
    key_decisions       = db.Column(db.JSON)
    risks               = db.Column(db.JSON)
    sentiment_score     = db.Column(db.Float, default=0.0)
    productivity_score  = db.Column(db.Integer, default=0)
    speaker_stats       = db.Column(db.JSON)
    pdf_s3_url          = db.Column(db.String(512))
    meeting_type        = db.Column(db.String(50))
    created_at          = db.Column(db.DateTime, default=datetime.utcnow)
