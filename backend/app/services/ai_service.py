import openai, json, os
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

openai.api_key = os.getenv('OPENAI_API_KEY')
analyzer = SentimentIntensityAnalyzer()

SYSTEM_PROMPT = """You are an expert meeting analyst. Analyze the transcript and return ONLY valid JSON
with exactly these keys (no extra text):
{
  "executive_summary": "3-5 sentences overview",
  "detailed_summary": "comprehensive explanation of all topics discussed",
  "key_decisions": ["decision 1", "decision 2"],
  "action_items": [{"task": "...", "owner": "...", "deadline": "YYYY-MM-DD", "priority": "high|medium|low"}],
  "risks": ["risk 1", "risk 2"],
  "meeting_type": "planning|review|standup|retrospective|other",
  "productivity_score": 78,
  "dynamics": {
     "agreement_score": 85,
     "frustration_level": 12,
     "engagement_level": 90,
     "excitement_level": 40
  }
}"""

def process_transcript(entries: list) -> dict:
    """Send transcript to GPT-4o and get structured meeting analysis."""
    transcript_text = "\n".join([f"{e['speaker']}: {e['text']}" for e in entries])

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": f"TRANSCRIPT:\n{transcript_text}"}
        ],
        response_format={"type": "json_object"},
        max_tokens=2000,
        temperature=0.3
    )
    return json.loads(response.choices[0].message.content)

def score_sentiment(text: str) -> str:
    """Score a single utterance. Returns 'pos', 'neu', or 'neg'."""
    scores = analyzer.polarity_scores(text)
    if scores['compound'] >= 0.05:  return 'pos'
    if scores['compound'] <= -0.05: return 'neg'
    return 'neu'

def calculate_speaker_stats(entries: list) -> dict:
    """Calculate participation stats per speaker."""
    stats = {}
    for e in entries:
        speaker = e['speaker']
        words   = len(e['text'].split())
        if speaker not in stats:
            stats[speaker] = {'messages': 0, 'words': 0, 'sentiment_counts': {'pos':0,'neu':0,'neg':0}}
        stats[speaker]['messages'] += 1
        stats[speaker]['words']    += words
        stats[speaker]['sentiment_counts'][e.get('sentiment','neu')] += 1

    total_words = sum(s['words'] for s in stats.values()) or 1
    for speaker, s in stats.items():
        s['speaking_time_mins'] = round(s['words'] / 130, 1)   # avg 130wpm
        s['participation_pct']  = round(s['words'] / total_words * 100, 1)

    return stats

def extract_tasks_with_ai(transcript_text: str) -> list:
    """Dedicated task extraction call."""
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Extract all action items from this meeting transcript. Return ONLY JSON: {\"tasks\": [{\"task\": \"...\", \"owner\": \"...\", \"deadline\": \"...\", \"priority\": \"high|medium|low\"}]}"},
            {"role": "user",   "content": transcript_text}
        ],
        response_format={"type": "json_object"},
        max_tokens=800
    )
    data = json.loads(response.choices[0].message.content)
    return data.get('tasks', [])

def rag_chat(question: str, context_chunks: list) -> str:
    """Answer a question about a meeting using retrieved transcript chunks."""
    context = "\n".join(context_chunks)
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You answer questions about a meeting based only on the provided transcript context. Be concise and accurate."},
            {"role": "user",   "content": f"CONTEXT:\n{context}\n\nQUESTION: {question}"}
        ],
        max_tokens=500
    )
    return response.choices[0].message.content
