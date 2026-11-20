
from sqlalchemy import text

from database import engine
from services.relevance_service import evaluate_event_relevance


def evaluate_relevance_model(
    event_id: int,
    source_event_id: int | None = None,
    threshold: float = 0.60
):
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("Threshold must be between 0 and 1.")

    # Get the model's similarity scores
    model_results = evaluate_event_relevance(
        event_id=event_id,
        source_event_id=source_event_id
    )

    # Retrieve human-reviewed classifications
    with engine.connect() as connection:
        reviews = connection.execute(
            text("""
                SELECT article_id, relevance_label
                FROM article_relevance_reviews
                WHERE target_event_id = :event_id
            """),
            {"event_id": event_id}
        ).mappings().all()

    review_lookup = {
        row["article_id"]: row["relevance_label"]
        for row in reviews
    }

    tp = 0
    fp = 0
    tn = 0
    fn = 0

    evaluated_articles = []

    for article in model_results["results"]:
        article_id = article["article_id"]

        if article_id not in review_lookup:
            continue

        human_label = review_lookup[article_id]

        # Relevant is positive; partial and irrelevant are negative
        actual = human_label == "relevant"
        predicted = article["relevance_score"] >= threshold

        if actual and predicted:
            tp += 1
        elif not actual and predicted:
            fp += 1
        elif not actual and not predicted:
            tn += 1
        else:
            fn += 1

        evaluated_articles.append({
            "article_id": article_id,
            "title": article["title"],
            "outlet": article["outlet"],
            "human_label": human_label,
            "relevance_score": article["relevance_score"],
            "predicted_relevant": predicted,
            "correct": actual == predicted
        })

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    specificity = tn / (tn + fp) if (tn + fp) else 0.0

    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0.0
    )

    accuracy = (
        (tp + tn) / len(evaluated_articles)
        if evaluated_articles
        else 0.0
    )

    return {
        "event_id": event_id,
        "source_event_id": model_results.get("source_event_id"),
        "threshold": threshold,
        "reviewed_articles": len(evaluated_articles),
        "metrics": {
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "specificity": round(specificity, 4),
            "f1_score": round(f1, 4)
        },
        "confusion_matrix": {
            "true_positive": tp,
            "false_positive": fp,
            "true_negative": tn,
            "false_negative": fn
        },
        "articles": evaluated_articles
    }
