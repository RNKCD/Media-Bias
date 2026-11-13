
from collections import defaultdict

import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy import text

from database import engine


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
SIMILARITY_THRESHOLD = 0.75

_model = None


def get_model():
    global _model

    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)

    return _model


def find_event_matches(event_id):
    with engine.connect() as connection:
        articles = connection.execute(
            text("""
                SELECT
                    a.id,
                    a.title,
                    a.description,
                    a.published_at,
                    o.name AS outlet
                FROM articles a
                JOIN outlets o ON o.id = a.outlet_id
                WHERE a.event_id = :event_id
                ORDER BY a.id
            """),
            {"event_id": event_id}
        ).mappings().all()

    articles = [dict(article) for article in articles]

    if len(articles) < 2:
        return {
            "event_id": event_id,
            "matches": []
        }

    texts = [
        " ".join(
            part for part in [
                article["title"],
                article["description"]
            ]
            if part
        )
        for article in articles
    ]

    model = get_model()

    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=False
    )

    similarity_matrix = embeddings @ embeddings.T

    matches = []

    for i in range(len(articles)):
        for j in range(i + 1, len(articles)):

            if articles[i]["outlet"] == articles[j]["outlet"]:
                continue

            similarity = float(similarity_matrix[i][j])

            if similarity >= SIMILARITY_THRESHOLD:
                matches.append({
                    "article_1": {
                        "id": articles[i]["id"],
                        "title": articles[i]["title"],
                        "outlet": articles[i]["outlet"]
                    },
                    "article_2": {
                        "id": articles[j]["id"],
                        "title": articles[j]["title"],
                        "outlet": articles[j]["outlet"]
                    },
                    "similarity": round(similarity, 4)
                })

    matches.sort(
        key=lambda item: item["similarity"],
        reverse=True
    )

    return {
        "event_id": event_id,
        "total_articles": len(articles),
        "candidate_matches": len(matches),
        "matches": matches
    }
