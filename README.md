# SmartMeet AI

AI-powered Chrome Extension that captures meeting transcripts from Google Meet, Zoom, and Microsoft Teams, processes them with GPT-4o, and delivers intelligent summaries, action items, speaker analytics, sentiment analysis, and PDF reports.

## Project Structure

```
smartmeet-ai/
├── extension/     ← Chrome Extension (Manifest V3)
├── backend/       ← Flask REST API + AI Pipeline
└── dashboard/     ← React Web Dashboard
```

## Quick Start

### 1. Backend
```bash
cd backend
cp .env.example .env          # Fill in API keys
pip install -r requirements.txt
python run.py
```

### 2. Dashboard
```bash
cd dashboard
cp .env.example .env          # Set VITE_API_URL
npm install
npm run dev
```

### 3. Chrome Extension
1. Open Chrome → `chrome://extensions`
2. Enable **Developer mode** (top right)
3. Click **Load unpacked**
4. Select the `extension/` folder
5. Sign in via the popup

## Environment Variables (Backend)
| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | Your OpenAI API key (server-side ONLY) |
| `JWT_SECRET` | Secret for signing JWTs |
| `DATABASE_URL` | MySQL connection string |
| `ENCRYPTION_KEY` | 32-byte hex key for AES-256 |
| `AWS_S3_BUCKET` | S3 bucket for PDF storage |
| `SENDGRID_API_KEY` | SendGrid key for email reports |

## Modules
1. **Meeting Detection** — URL pattern matching in service worker
2. **Transcript Capture** — MutationObserver on caption DOM
3. **AI Processing** — GPT-4o with JSON mode
4. **Speaker Analytics** — Word count, participation %
5. **Sentiment Analysis** — VADER + per-utterance scoring
6. **Attendance Tracking** — Join/leave time recording
7. **Task Extraction** — AI-extracted owners and deadlines
8. **Email Reports** — SendGrid with PDF attachment
9. **Dashboard** — React + Recharts analytics
10. **PDF Generation** — ReportLab professional reports

## Security
- API keys stored on backend server only (never in extension)
- AES-256-GCM encryption for all transcript data
- JWT authentication with 1hr expiry
- Role-based access control (admin/manager/user)
- Rate limiting on all endpoints
- CORS restricted to allowed origins
