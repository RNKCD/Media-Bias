
import json

from sqlalchemy import text

from database import engine
from services.emotion_service import analyze_emotion


def process_emotions(event_id=None):
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
                article_text = full_text
            elif description:
                article_text = description
            else:
                article_text = headline

            if not article_text:
                skipped += 1
                continue

            result = analyze_emotion(article_text)

            connection.execute(
                text("""
                    INSERT INTO analysis_results (
                        article_id,
                        emotion_label,
                        emotion_scores,
                        model_name
                    )
                    VALUES (
                        :article_id,
                        :emotion_label,
                        CAST(:emotion_scores AS JSONB),
                        'VADER'
                    )
                    ON CONFLICT (article_id, model_name)
                    DO UPDATE SET
                        emotion_label =
                            EXCLUDED.emotion_label,
                        emotion_scores =
                            EXCLUDED.emotion_scores,
                        analyzed_at = NOW()
                """),
                {
                    "article_id": article["id"],
                    "emotion_label": result["emotion_label"],
                    "emotion_scores": json.dumps(
                        result["emotion_scores"]
                    )
                }
            )

            processed += 1

    return {
        "processed_articles": processed,
        "skipped_articles": skipped
    }
