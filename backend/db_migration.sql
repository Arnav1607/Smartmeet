-- =========================================================================
-- SMARTMEET AI: Database Schema and SQL Migration Scripts
-- Enterprise-grade MySQL relational schema with indexing and optimizations
-- =========================================================================

CREATE DATABASE IF NOT EXISTS smartmeet;
USE smartmeet;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NULL,
    google_id VARCHAR(100) UNIQUE NULL,
    role ENUM('admin', 'manager', 'team_member', 'student') DEFAULT 'student',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Meetings Table
CREATE TABLE IF NOT EXISTS meetings (
    meeting_id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    platform ENUM('gmeet', 'zoom', 'teams', 'other') DEFAULT 'other',
    host_id VARCHAR(36) NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP NULL,
    duration_mins INT DEFAULT 0,
    url VARCHAR(512) NULL,
    status ENUM('active', 'processing', 'completed', 'failed') DEFAULT 'active',
    FOREIGN KEY (host_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_meeting_host (host_id),
    INDEX idx_meeting_started (started_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Transcripts Table (Encrypted)
CREATE TABLE IF NOT EXISTS transcripts (
    transcript_id VARCHAR(36) PRIMARY KEY,
    meeting_id VARCHAR(36) NOT NULL,
    speaker VARCHAR(100) NOT NULL,
    text_encrypted TEXT NOT NULL,          -- AES-256-GCM ciphertext
    iv VARCHAR(64) NOT NULL,                -- AEAD Nonce/IV (base64)
    timestamp_ms BIGINT NOT NULL,
    sentiment ENUM('positive', 'neutral', 'negative') DEFAULT 'neutral',
    word_count INT DEFAULT 0,
    FOREIGN KEY (meeting_id) REFERENCES meetings(meeting_id) ON DELETE CASCADE,
    INDEX idx_transcript_meeting (meeting_id),
    INDEX idx_transcript_time (timestamp_ms)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Participants Table
CREATE TABLE IF NOT EXISTS participants (
    participant_id VARCHAR(36) PRIMARY KEY,
    meeting_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NULL,
    name VARCHAR(100) NULL,
    email VARCHAR(255) NULL,
    joined_at TIMESTAMP NULL,
    left_at TIMESTAMP NULL,
    duration_mins INT DEFAULT 0,
    FOREIGN KEY (meeting_id) REFERENCES meetings(meeting_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_participant_meeting (meeting_id),
    INDEX idx_participant_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Tasks / Action Items Table
CREATE TABLE IF NOT EXISTS tasks (
    task_id VARCHAR(36) PRIMARY KEY,
    meeting_id VARCHAR(36) NOT NULL,
    description TEXT NOT NULL,
    owner_name VARCHAR(100) DEFAULT 'Unassigned',
    deadline DATE NULL,
    priority ENUM('high', 'medium', 'low') DEFAULT 'medium',
    status ENUM('pending', 'in_progress', 'done') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (meeting_id) REFERENCES meetings(meeting_id) ON DELETE CASCADE,
    INDEX idx_task_meeting (meeting_id),
    INDEX idx_task_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Reports Table
CREATE TABLE IF NOT EXISTS reports (
    report_id VARCHAR(36) PRIMARY KEY,
    meeting_id VARCHAR(36) UNIQUE NOT NULL,
    executive_summary TEXT NULL,
    detailed_summary TEXT NULL,
    key_decisions JSON NULL,                -- Array format
    risks JSON NULL,                        -- Array format
    speaker_stats JSON NULL,                -- Speaking Skew Map
    sentiment_score FLOAT DEFAULT 0.0,
    sentiment_breakdown JSON NULL,          -- Pos/Neu/Neg counters
    productivity_score INT DEFAULT 0,       -- Range: 0-100
    dynamics JSON NULL,                     -- Engagement dynamics
    pdf_s3_url VARCHAR(512) NULL,
    meeting_type VARCHAR(50) DEFAULT 'other',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (meeting_id) REFERENCES meetings(meeting_id) ON DELETE CASCADE,
    INDEX idx_report_meeting (meeting_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. Refresh Tokens Table (Session Management)
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_refresh_token_value (token)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =========================================================================
-- OPTIMIZATIONS & INTEGRITY
-- =========================================================================
-- - ON DELETE CASCADE constraints ensure that purging a meeting automatically 
--   cascades and deletes associated transcripts, tasks, reports, and participant metrics.
-- - InnoDB storage engine supports row-level locking and ACID transactions.
-- - Index mappings (idx_) are placed on foreign keys and frequently queried 
--   columns (such as emails, status flags, timestamps) to optimize index scans.
