
import time

import trafilatura
from sqlalchemy import text

from database import engine


MIN_WORDS = 150


def extract_article_text(url):
    try:
        downloaded = trafilatura.fetch_url(url)

        if not downloaded:
            return None

        extracted = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=False,
            favor_precision=True,
        )

        if not extracted:
            return None

        extracted = extracted.strip()

        if len(extracted.split()) < MIN_WORDS:
            return None

        return extracted

    except Exception as error:
        print(f"Extraction failed for {url}: {error}")
        return None


def extract_event_articles(event_id):
    with engine.connect() as connection:
        articles = connection.execute(
            text("""
                SELECT id, url
                FROM articles
                WHERE event_id = :event_id
                  AND url IS NOT NULL
                  AND (
                      full_text IS NULL
                      OR LENGTH(TRIM(full_text)) = 0
                  )
                ORDER BY id
            """),
            {"event_id": event_id}
        ).mappings().all()

    extracted_count = 0
    failed_count = 0

    for article in articles:
        full_text = extract_article_text(article["url"])

        if full_text:
            with engine.begin() as connection:
                connection.execute(
                    text("""
                        UPDATE articles
                        SET full_text = :full_text,
                            text_source = 'full_text',
                            text_word_count = :word_count,
                            is_full_text = TRUE,
                            quality_status = 'usable_full_text',
                            quality_notes = :notes
                        WHERE id = :article_id
                    """),
                    {
                        "article_id": article["id"],
                        "full_text": full_text,
                        "word_count": len(full_text.split()),
                        "notes": (
                            "Text extracted from publisher page; "
                            "completeness not independently verified."
                        ),
                    }
                )

            extracted_count += 1
        else:
            failed_count += 1

        time.sleep(1)

    return {
        "event_id": event_id,
        "attempted": len(articles),
        "extracted": extracted_count,
        "failed": failed_count,
    }
