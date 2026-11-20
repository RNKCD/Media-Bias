
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


def get_saved_articles(event_name, selected_outlets=None):
    """
    Retrieve previously saved articles for an event.

    If selected_outlets is provided, return only
    articles from those outlets.
    """

    with engine.connect() as connection:
        event_id = connection.execute(
            text("""
                SELECT id
                FROM events
                WHERE LOWER(name) = LOWER(:name)
                LIMIT 1
            """),
            {"name": event_name.strip()}
        ).scalar_one_or_none()

        if event_id is None:
            return {
                "event_id": None,
                "total_articles": 0,
                "articles": []
            }

        query = """
            SELECT
                a.id,
                a.title,
                a.description,
                a.url,
                a.published_at,
                a.content,
                o.name AS outlet
            FROM articles a
            JOIN outlets o ON o.id = a.outlet_id
            WHERE a.event_id = :event_id
        """

        params = {"event_id": event_id}

        if selected_outlets is not None:
            query += " AND o.name = ANY(:outlets)"
            params["outlets"] = selected_outlets

        query += " ORDER BY a.published_at DESC NULLS LAST"

        rows = connection.execute(
            text(query),
            params
        ).mappings().all()

    articles = []

    for row in rows:
        article = dict(row)

        if article["published_at"] is not None:
            article["published_at"] = (
                article["published_at"].isoformat()
            )

        articles.append(article)

    return {
        "event_id": event_id,
        "total_articles": len(articles),
        "articles": articles
    }

