
from sqlalchemy import text
from database import engine


def save_articles(event_name, articles):
    saved = 0
    duplicates = 0

    with engine.begin() as connection:
        # Find or create the event
        event_id = connection.execute(
            text("""
                SELECT id FROM events
                WHERE LOWER(name) = LOWER(:name)
                LIMIT 1
            """),
            {"name": event_name}
        ).scalar_one_or_none()

        if event_id is None:
            event_id = connection.execute(
                text("""
                    INSERT INTO events (name)
                    VALUES (:name)
                    RETURNING id
                """),
                {"name": event_name}
            ).scalar_one()

        for article in articles:
            url = article.get("url")

            if not url:
                continue

            outlet_name = article["outlet"]

            outlet_id = connection.execute(
                text("""
                    SELECT id FROM outlets
                    WHERE name = :name
                """),
                {"name": outlet_name}
            ).scalar_one_or_none()

            if outlet_id is None:
                outlet_id = connection.execute(
                    text("""
                        INSERT INTO outlets (name)
                        VALUES (:name)
                        RETURNING id
                    """),
                    {"name": outlet_name}
                ).scalar_one()

            inserted_id = connection.execute(
                text("""
                    INSERT INTO articles (
                        event_id,
                        outlet_id,
                        title,
                        url,
                        published_at,
                        description,
                        content
                    )
                    VALUES (
                        :event_id,
                        :outlet_id,
                        :title,
                        :url,
                        :published_at,
                        :description,
                        :content
                    )
                    ON CONFLICT (url) DO NOTHING
                    RETURNING id
                """),
                {
                    "event_id": event_id,
                    "outlet_id": outlet_id,
                    "title": article.get("title") or "Untitled",
                    "url": url,
                    "published_at": article.get("published_at"),
                    "description": article.get("description"),
                    "content": article.get("content")
                }
            ).scalar_one_or_none()

            if inserted_id is not None:
                saved += 1
            else:
                duplicates += 1

    return {
        "event_id": event_id,
        "saved": saved,
        "duplicates": duplicates
    }
