
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()


def analyze_sentiment(text):
    if not text or not text.strip():
        return {
            "label": "unknown",
            "score": None,
            "positive": None,
            "negative": None,
            "neutral": None
        }

    scores = analyzer.polarity_scores(text)

    compound = scores["compound"]

    if compound >= 0.05:
        label = "positive"
    elif compound <= -0.05:
        label = "negative"
    else:
        label = "neutral"

    return {
        "label": label,
        "score": compound,
        "positive": scores["pos"],
        "negative": scores["neg"],
        "neutral": scores["neu"]
    }
