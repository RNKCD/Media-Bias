
import json

from sqlalchemy import text

from database import engine
from services.nlp_service import process_text


def process_saved_articles(event_id=None):
    processed = 0
    skipped = 0

    with engine.begin() as connection:

        articles = connection.execute(
            text("""
                SELECT
                    a.id,
                    a.title,
                    a.description,
                    a.content,
                    a.full_text
                FROM articles a
                LEFT JOIN nlp_results n
                    ON a.id = n.article_id
                WHERE n.article_id IS NULL
                  AND (CAST(:event_id AS INTEGER) IS NULL
                       OR a.event_id = :event_id)
                ORDER BY a.id
            """),
            {"event_id": event_id}
        ).mappings().all()

        for article in articles:

            # Prefer full text when available.
            # Do not concatenate NewsAPI snippets as if
            # they were complete article bodies.
            if article["full_text"]:
                source_text = article["full_text"]
            else:
                source_text = " ".join(
                    part for part in [
                        article["title"],
                        article["description"]
                    ]
                    if part
                )

            if not source_text.strip():
                skipped += 1
                continue

            result = process_text(source_text)

            connection.execute(
                text("""
                    INSERT INTO nlp_results (
                        article_id,
                        cleaned_text,
                        word_count,
                        tokens,
                        keywords,
                        entities,
                        model_name
                    )
                    VALUES (
                        :article_id,
                        :cleaned_text,
                        :word_count,
                        CAST(:tokens AS JSONB),
                        CAST(:keywords AS JSONB),
                        CAST(:entities AS JSONB),
                        :model_name
                    )
                    ON CONFLICT (article_id)
                    DO NOTHING
                """),
                {
                    "article_id": article["id"],
                    "cleaned_text": result["cleaned_text"],
                    "word_count": result["word_count"],
                    "tokens": json.dumps(result["tokens"]),
                    "keywords": json.dumps(result["keywords"]),
                    "entities": json.dumps(result["entities"]),
                    "model_name": "en_core_web_sm"
                }
            )

            processed += 1

    return {
        "processed": processed,
        "skipped": skipped
    }
