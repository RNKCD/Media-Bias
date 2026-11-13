
from transformers import pipeline

MODEL_NAME = "j-hartmann/emotion-english-distilroberta-base"

emotion_classifier = None


def get_emotion_classifier():
    global emotion_classifier

    if emotion_classifier is None:
        emotion_classifier = pipeline(
            task="text-classification",
            model=MODEL_NAME,
            tokenizer=MODEL_NAME,
            top_k=None,
            device=-1
        )

    return emotion_classifier


def analyze_emotion(text):
    if not text or not text.strip():
        return {
            "emotion_label": "unknown",
            "emotion_scores": {}
        }

    classifier = get_emotion_classifier()

    predictions = classifier(
        text,
        truncation=True,
        max_length=512
    )

    # Handle nested output returned by some
    # Transformers versions.
    if predictions and isinstance(predictions[0], list):
        predictions = predictions[0]

    scores = {
        item["label"].lower(): round(
            float(item["score"]), 4
        )
        for item in predictions
    }

    dominant_emotion = max(
        scores,
        key=scores.get
    )

    return {
        "emotion_label": dominant_emotion,
        "emotion_scores": scores
    }
