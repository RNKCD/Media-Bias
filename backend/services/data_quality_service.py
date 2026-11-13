
import re

from sqlalchemy import text
from database import engine


def count_words(value):
    return len(re.findall(r"\b[\w'-]+\b", value or ""))


def assess_article(article):
    full_text = (article["full_text"] or "").strip()
    description = (article["description"] or "").strip()
    headline = (article["title"] or "").strip()

    if full_text and count_words(full_text) >= 150:
        source = "full_text"
        selected_text = full_text
        status = "usable_full_text"
        notes = "Full text available; completeness not independently verified."
        is_full_text = True

    elif description:
        source = "description"
        selected_text = description
        status = "limited_text"
        notes = "Only article description available."
        is_full_text = False

    elif headline:
        source = "headline"
        selected_text = headline
        status = "headline_only"
        notes = "Only article headline available."
        is_full_text = False

    else:
        source = "missing"
        selected_text = ""
        status = "insufficient_data"
        notes = "No usable article text."
        is_full_text = False

    return {
        "text_source": source,
        "text_word_count": count_words(selected_text),
        "is_full_text": is_full_text,
        "quality_status": status,
        "quality_notes": notes
    }


def evaluate_dataset_quality():
    updated = 0

    with engine.begin() as connection:
        articles = connection.execute(
            text("""
                SELECT
                    id,
                    title,
                    description,
                    full_text
                FROM articles
            """)
        ).mappings().all()

        for article in articles:
            quality = assess_article(article)

            connection.execute(
                text("""
                    UPDATE articles
                    SET
                        text_source = :text_source,
                        text_word_count = :text_word_count,
                        is_full_text = :is_full_text,
                        quality_status = :quality_status,
                        quality_notes = :quality_notes
                    WHERE id = :article_id
                """),
                {
                    "article_id": article["id"],
                    **quality
                }
            )

            updated += 1

    return {
        "evaluated_articles": updated
    }

