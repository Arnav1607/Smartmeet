# app/models/models.py — SQLAlchemy Database Models
import uuid
from datetime import datetime
from app import db


def gen_uuid():
    return str(uuid.uuid4())


class User(db.Model):
    __tablename__ = "users"

    user_id       = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    email         = db.Column(db.String(255), unique=True, nullable=False)
    name          = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255))
    google_id     = db.Column(db.String(100), unique=True)
    role          = db.Column(db.Enum("admin", "manager", "team_member", "student"), default="student")
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    meetings      = db.relationship("Meeting", backref="host", lazy=True, foreign_keys="Meeting.host_id")
    participations= db.relationship("Participant", backref="user", lazy=True)

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "email":   self.email,
            "name":    self.name,
            "role":    self.role
        }


class Meeting(db.Model):
    __tablename__ = "meetings"

    meeting_id    = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    title         = db.Column(db.String(255), nullable=False)
    platform      = db.Column(db.Enum("gmeet", "zoom", "teams", "other"), default="other")
    host_id       = db.Column(db.String(36), db.ForeignKey("users.user_id"), nullable=False)
    started_at    = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at      = db.Column(db.DateTime)
    duration_mins = db.Column(db.Integer, default=0)
    url           = db.Column(db.String(512))
    status        = db.Column(db.Enum("active", "processing", "completed", "failed"), default="active")

    transcripts   = db.relationship("Transcript", backref="meeting", lazy=True, cascade="all, delete")
    participants  = db.relationship("Participant", backref="meeting", lazy=True, cascade="all, delete")
    report        = db.relationship("Report", backref="meeting", uselist=False, cascade="all, delete")
    tasks         = db.relationship("Task", backref="meeting", lazy=True, cascade="all, delete")

    def to_dict(self):
        return {
            "meeting_id":    self.meeting_id,
            "title":         self.title,
            "platform":      self.platform,
            "started_at":    self.started_at.isoformat() if self.started_at else None,
            "ended_at":      self.ended_at.isoformat()   if self.ended_at   else None,
            "duration_mins": self.duration_mins,
            "status":        self.status
        }


class Transcript(db.Model):
    __tablename__ = "transcripts"

    transcript_id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    meeting_id    = db.Column(db.String(36), db.ForeignKey("meetings.meeting_id"), nullable=False)
    speaker       = db.Column(db.String(100), nullable=False)
    text_encrypted= db.Column(db.Text, nullable=False)   # AES-256-GCM ciphertext (base64)
    iv            = db.Column(db.String(64), nullable=False)  # initialization vector
    timestamp_ms  = db.Column(db.BigInteger, nullable=False)
    sentiment     = db.Column(db.Enum("positive", "neutral", "negative"), default="neutral")
    word_count    = db.Column(db.Integer, default=0)


class Participant(db.Model):
    __tablename__ = "participants"

    participant_id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    meeting_id     = db.Column(db.String(36), db.ForeignKey("meetings.meeting_id"), nullable=False)
    user_id        = db.Column(db.String(36), db.ForeignKey("users.user_id"))
    name           = db.Column(db.String(100))
    email          = db.Column(db.String(255))
    joined_at      = db.Column(db.DateTime)
    left_at        = db.Column(db.DateTime)
    duration_mins  = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            "participant_id": self.participant_id,
            "name":           self.name,
            "email":          self.email,
            "joined_at":      self.joined_at.isoformat() if self.joined_at else None,
            "left_at":        self.left_at.isoformat()   if self.left_at   else None,
            "duration_mins":  self.duration_mins
        }


class Task(db.Model):
    __tablename__ = "tasks"

    task_id     = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    meeting_id  = db.Column(db.String(36), db.ForeignKey("meetings.meeting_id"), nullable=False)
    description = db.Column(db.Text, nullable=False)
    owner_name  = db.Column(db.String(100))
    deadline    = db.Column(db.Date)
    priority    = db.Column(db.Enum("high", "medium", "low"), default="medium")
    status      = db.Column(db.Enum("pending", "in_progress", "done"), default="pending")
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "task_id":     self.task_id,
            "meeting_id":  self.meeting_id,
            "description": self.description,
            "owner_name":  self.owner_name,
            "deadline":    self.deadline.isoformat() if self.deadline else None,
            "priority":    self.priority,
            "status":      self.status
        }


class Report(db.Model):
    __tablename__ = "reports"

    report_id           = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    meeting_id          = db.Column(db.String(36), db.ForeignKey("meetings.meeting_id"), nullable=False)
    executive_summary   = db.Column(db.Text)
    detailed_summary    = db.Column(db.Text)
    key_decisions       = db.Column(db.JSON)     # list of strings
    risks               = db.Column(db.JSON)     # list of strings
    speaker_stats       = db.Column(db.JSON)     # {speaker: {words, time_secs, pct}}
    sentiment_score     = db.Column(db.Float)    # -1.0 to 1.0
    sentiment_breakdown = db.Column(db.JSON)     # {positive: n, neutral: n, negative: n}
    productivity_score  = db.Column(db.Integer)  # 0-100
    dynamics            = db.Column(db.JSON)     # {agreement, frustration, engagement, excitement}
    pdf_s3_url          = db.Column(db.String(512))
    meeting_type        = db.Column(db.String(50))
    created_at          = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def summary(self):
        return self.executive_summary

    @summary.setter
    def summary(self, value):
        self.executive_summary = value

    def to_dict(self):
        return {
            "report_id":           self.report_id,
            "meeting_id":          self.meeting_id,
            "executive_summary":   self.executive_summary,
            "detailed_summary":    self.detailed_summary,
            "key_decisions":       self.key_decisions,
            "risks":               self.risks,
            "speaker_stats":       self.speaker_stats,
            "sentiment_score":     self.sentiment_score,
            "sentiment_breakdown": self.sentiment_breakdown,
            "productivity_score":  self.productivity_score,
            "dynamics":            self.dynamics,
            "pdf_s3_url":          self.pdf_s3_url,
            "meeting_type":        self.meeting_type
        }


class RefreshToken(db.Model):
    __tablename__ = "refresh_tokens"

    id         = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    user_id    = db.Column(db.String(36), db.ForeignKey("users.user_id"), nullable=False)
    token      = db.Column(db.String(255), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
