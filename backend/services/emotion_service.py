
from transformers import pipeline

MODEL_NAME = "j-hartmann/emotion-english-distilroberta-base"

emotion_classifier = None

MAX_CONTENT_TOKENS = 510


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
    tokenizer = classifier.tokenizer

    token_ids = tokenizer.encode(
        text,
        add_special_tokens=False,
        truncation=False
    )

    if not token_ids:
        return {
            "emotion_label": "unknown",
            "emotion_scores": {}
        }

    special_tokens = tokenizer.num_special_tokens_to_add(
        pair=False
    )

    chunk_size = min(
        MAX_CONTENT_TOKENS,
        tokenizer.model_max_length - special_tokens
    )

    chunks = [
        token_ids[i:i + chunk_size]
        for i in range(0, len(token_ids), chunk_size)
    ]

    weighted_scores = {}
    total_tokens = 0

    for chunk in chunks:
        chunk_text = tokenizer.decode(
            chunk,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=True
        )

        predictions = classifier(
            chunk_text,
            truncation=True,
            max_length=chunk_size + special_tokens
        )

        if predictions and isinstance(predictions[0], list):
            predictions = predictions[0]

        weight = len(chunk)
        total_tokens += weight

        for item in predictions:
            label = item["label"].lower()

            weighted_scores[label] = (
                weighted_scores.get(label, 0.0)
                + float(item["score"]) * weight
            )

    scores = {
        label: round(value / total_tokens, 4)
        for label, value in weighted_scores.items()
    }

    dominant_emotion = max(
        scores,
        key=scores.get
    )

    return {
        "emotion_label": dominant_emotion,
        "emotion_scores": scores
    }
