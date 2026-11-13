
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
                    a.full_text
                FROM articles a
                WHERE (
                    CAST(:event_id AS INTEGER) IS NULL
                    OR a.event_id = :event_id
                )
                ORDER BY a.id
            """),
            {"event_id": event_id}
        ).mappings().all()

        for article in articles:

            full_text = (article["full_text"] or "").strip()
            description = (article["description"] or "").strip()
            headline = (article["title"] or "").strip()

            if full_text:
                source_text = full_text
            elif description:
                source_text = description
            else:
                source_text = headline

            if not source_text:
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
                    DO UPDATE SET
                        cleaned_text = EXCLUDED.cleaned_text,
                        word_count = EXCLUDED.word_count,
                        tokens = EXCLUDED.tokens,
                        keywords = EXCLUDED.keywords,
                        entities = EXCLUDED.entities,
                        model_name = EXCLUDED.model_name
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
