
import os
import requests

from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

NEWS_API_KEY = os.getenv("NEWS_API_KEY")

NEWS_API_URL = "https://newsapi.org/v2/everything"

OUTLETS = {
    "CNN": "cnn.com",
    "Reuters": "reuters.com",
    "Fox News": "foxnews.com"
}


def search_news(event, page_size=10):
    if not NEWS_API_KEY:
        raise ValueError("NEWS_API_KEY is missing")

    results = []

    for outlet, domain in OUTLETS.items():
        params = {
            "q": event,
            "domains": domain,
            "language": "en",
            "sortBy": "relevancy",
            "pageSize": page_size,
            "apiKey": NEWS_API_KEY
        }

        response = requests.get(
            NEWS_API_URL,
            params=params,
            timeout=20
        )

        response.raise_for_status()
        data = response.json()

        if data.get("status") != "ok":
            raise ValueError(
                data.get("message", "NewsAPI request failed")
            )

        for article in data.get("articles", []):
            results.append({
                "outlet": outlet,
                "title": article.get("title"),
                "description": article.get("description"),
                "url": article.get("url"),
                "published_at": article.get("publishedAt"),
                "content": article.get("content")
            })

    return results
