# app/services/analytics.py — Speaker Analytics & Sentiment Analysis
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()


def score_sentiment(text: str) -> str:
    """Return 'positive', 'neutral', or 'negative' for a single utterance."""
    scores = analyzer.polarity_scores(text)
    compound = scores["compound"]
    if compound >= 0.05:
        return "positive"
    elif compound <= -0.05:
        return "negative"
    return "neutral"


def score_sentiment_detailed(text: str) -> dict:
    """Return full sentiment breakdown for a text."""
    scores = analyzer.polarity_scores(text)
    sentiment = "positive" if scores["compound"] >= 0.05 else \
                "negative" if scores["compound"] <= -0.05 else "neutral"
    return {
        "compound": scores["compound"],
        "positive": scores["pos"],
        "neutral":  scores["neu"],
        "negative": scores["neg"],
        "label":    sentiment
    }


def calculate_speaker_stats(transcript_entries: list) -> dict:
    """
    Calculate per-speaker analytics:
    - word_count
    - message_count
    - estimated_speaking_time_secs
    - participation_pct
    - sentiment_distribution
    """
    stats = {}

    for entry in transcript_entries:
        speaker   = entry.get("speaker", "Unknown")
        text      = entry.get("text", "")
        words     = len(text.split())
        sentiment = score_sentiment(text)

        if speaker not in stats:
            stats[speaker] = {
                "word_count":    0,
                "message_count": 0,
                "sentiments":    {"positive": 0, "neutral": 0, "negative": 0}
            }

        stats[speaker]["word_count"]    += words
        stats[speaker]["message_count"] += 1
        stats[speaker]["sentiments"][sentiment] += 1

    # Calculate totals and percentages
    total_words = sum(s["word_count"] for s in stats.values()) or 1

    for speaker, s in stats.items():
        s["participation_pct"]          = round(s["word_count"] / total_words * 100, 1)
        s["estimated_speaking_secs"]    = round(s["word_count"] / 130 * 60)  # 130 wpm avg
        s["dominant_sentiment"]         = max(s["sentiments"], key=s["sentiments"].get)

    return stats


def calculate_overall_sentiment(transcript_entries: list) -> dict:
    """Calculate overall meeting sentiment stats."""
    counts = {"positive": 0, "neutral": 0, "negative": 0}
    scores = []

    for entry in transcript_entries:
        detail = score_sentiment_detailed(entry.get("text", ""))
        counts[detail["label"]] += 1
        scores.append(detail["compound"])

    total = len(transcript_entries) or 1
    avg_score = sum(scores) / len(scores) if scores else 0

    return {
        "average_compound": round(avg_score, 3),
        "breakdown": {k: round(v / total * 100, 1) for k, v in counts.items()},
        "dominant": max(counts, key=counts.get),
        "total_utterances": total
    }


def calculate_productivity_score(speaker_stats: dict, sentiment_data: dict, task_count: int) -> int:
    """
    Score = (participation_score × 0.4) + (sentiment_score × 0.3) + (task_score × 0.3)
    Returns 0-100 integer.
    """
    # Participation score: higher when participation is evenly distributed
    if len(speaker_stats) > 1:
        pcts = [s["participation_pct"] for s in speaker_stats.values()]
        ideal = 100 / len(pcts)
        deviation = sum(abs(p - ideal) for p in pcts) / len(pcts)
        participation_score = max(0, 100 - deviation * 2)
    else:
        participation_score = 50  # only one speaker — penalize

    # Sentiment score: map -1..1 to 0..100
    avg_compound    = sentiment_data.get("average_compound", 0)
    sentiment_score = (avg_compound + 1) / 2 * 100

    # Task score: more tasks extracted = more productive meeting (capped at 100)
    task_score = min(100, task_count * 20)

    score = (participation_score * 0.4) + (sentiment_score * 0.3) + (task_score * 0.3)
    return int(round(score))
