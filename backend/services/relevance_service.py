
from sqlalchemy import text

from database import engine
from services.event_matching_service import get_model


RELEVANCE_THRESHOLD = 0.60


def evaluate_event_relevance(
    event_id: int,
    source_event_id: int | None = None
):
    # Target event: the specific event we want to analyze
    # Source event: where existing articles are stored

    article_event_id = (
        source_event_id
        if source_event_id is not None
        else event_id
    )

    with engine.connect() as connection:

        # 1. Retrieve the TARGET event
        event = connection.execute(
            text("""
                SELECT id, name, description
                FROM events
                WHERE id = :event_id
            """),
            {"event_id": event_id}
        ).mappings().first()

        if event is None:
            raise ValueError(
                f"Target event {event_id} not found."
            )

        # 2. Retrieve articles from the SOURCE event
        articles = connection.execute(
            text("""
                SELECT
                    a.id,
                    a.title,
                    a.description,
                    o.name AS outlet
                FROM articles a
                JOIN outlets o
                    ON o.id = a.outlet_id
                WHERE a.event_id = :source_event_id
                ORDER BY a.id
            """),
            {"source_event_id": article_event_id}
        ).mappings().all()

    # 3. Debug information
    print("DEBUG TARGET EVENT:", dict(event))
    print("DEBUG SOURCE EVENT ID:", article_event_id)
    print("DEBUG ARTICLES:", len(articles))

    # 4. Construct target event text
    event_text = " ".join(
        str(part)
        for part in [event["name"], event["description"]]
        if part
    )

    if not event_text.strip():
        raise ValueError(
            "Event name or description is required."
        )

    # 5. Handle events without articles
    if not articles:
        return {
            "event_id": event_id,
            "event_name": event["name"],
            "source_event_id": article_event_id,
            "threshold": RELEVANCE_THRESHOLD,
            "total_articles": 0,
            "relevant_articles": 0,
            "results": []
        }

    # 6. Construct article text
    article_texts = [
        " ".join(
            str(part)
            for part in [
                article["title"],
                article["description"]
            ]
            if part
        )
        for article in articles
    ]

    # 7. Load sentence-transformer model
    model = get_model()

    # 8. Generate normalized embeddings
    embeddings = model.encode(
        [event_text] + article_texts,
        normalize_embeddings=True,
        show_progress_bar=False
    )

    # 9. Calculate cosine similarity
    event_embedding = embeddings[0]
    article_embeddings = embeddings[1:]

    similarities = article_embeddings @ event_embedding

    # 10. Build relevance results
    results = []

    for article, similarity in zip(
        articles,
        similarities
    ):
        score = float(similarity)

        results.append({
            "article_id": article["id"],
            "title": article["title"],
            "outlet": article["outlet"],
            "relevance_score": round(score, 4),
            "is_relevant": score >= RELEVANCE_THRESHOLD
        })

    # 11. Sort by relevance score
    results.sort(
        key=lambda item: item["relevance_score"],
        reverse=True
    )

    # 12. Return results
    return {
        "event_id": event_id,
        "event_name": event["name"],
        "source_event_id": article_event_id,
        "threshold": RELEVANCE_THRESHOLD,
        "total_articles": len(results),
        "relevant_articles": sum(
            item["is_relevant"]
            for item in results
        ),
        "results": results
    }
