
from sqlalchemy import text

from database import engine
from services.sentiment_service import analyze_sentiment


def process_sentiment(event_id=None):
    processed = 0

    with engine.begin() as connection:
        articles = connection.execute(
            text("""
                SELECT
                    a.id,
                    a.title,
                    a.description,
                    a.full_text
                FROM articles a
                WHERE CAST(:event_id AS INTEGER) IS NULL
                   OR a.event_id = :event_id
                ORDER BY a.id
            """),
            {"event_id": event_id}
        ).mappings().all()

        for article in articles:
            headline = article["title"] or ""

            if article["full_text"]:
                body = article["full_text"]
                text_source = "full_text"
            else:
                body = article["description"] or ""
                text_source = "description"

            headline_result = analyze_sentiment(headline)
            body_result = analyze_sentiment(body)

            # Use available body/description when present,
            # otherwise use headline sentiment.
            main_result = (
                body_result
                if body.strip()
                else headline_result
            )

            connection.execute(
                text("""
                    INSERT INTO analysis_results (
                        article_id,
                        sentiment_label,
                        sentiment_score,
                        headline_sentiment,
                        body_sentiment,
                        positive_score,
                        negative_score,
                        neutral_score,
                        text_source,
                        model_name
                    )
                    VALUES (
                        :article_id,
                        :label,
                        :score,
                        :headline_score,
                        :body_score,
                        :positive,
                        :negative,
                        :neutral,
                        :text_source,
                        :model_name
                    )
                    ON CONFLICT (article_id, model_name)
                    DO UPDATE SET
                        sentiment_label =
                            EXCLUDED.sentiment_label,
                        sentiment_score =
                            EXCLUDED.sentiment_score,
                        headline_sentiment =
                            EXCLUDED.headline_sentiment,
                        body_sentiment =
                            EXCLUDED.body_sentiment,
                        positive_score =
                            EXCLUDED.positive_score,
                        negative_score =
                            EXCLUDED.negative_score,
                        neutral_score =
                            EXCLUDED.neutral_score,
                        text_source =
                            EXCLUDED.text_source,
                        analyzed_at = NOW()
                """),
                {
                    "article_id": article["id"],
                    "label": main_result["label"],
                    "score": main_result["score"],
                    "headline_score": headline_result["score"],
                    "body_score": body_result["score"],
                    "positive": main_result["positive"],
                    "negative": main_result["negative"],
                    "neutral": main_result["neutral"],
                    "text_source": text_source,
                    "model_name": "VADER"
                }
            )

            processed += 1

    return {"processed_articles": processed}
