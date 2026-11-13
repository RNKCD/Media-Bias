
import os
import requests

from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
NEWS_API_URL = "https://newsapi.org/v2/everything"

NEWS_OUTLETS = {
    "CNN": "cnn.com",
    "Reuters": "reuters.com",
    "Fox News": "foxnews.com",
    "BBC News": "bbc.com",
    "Associated Press": "apnews.com",
    "The Guardian": "theguardian.com",
    "NBC News": "nbcnews.com",
    "ABC News": "abcnews.go.com",
    "Al Jazeera": "aljazeera.com",
    "The Hill": "thehill.com",
    "NPR": "npr.org",
    "Politico": "politico.com",
    "The New York Times": "nytimes.com",
    "The Washington Post": "washingtonpost.com",
    "Wall Street Journal": "wsj.com",
    "USA Today": "usatoday.com",
    "CBS News": "cbsnews.com",
    "MSNBC": "msnbc.com",
    "Newsweek": "newsweek.com",
    "Breitbart": "breitbart.com",
    "New York Post": "nypost.com",
    "HuffPost": "huffpost.com",
    "Vox": "vox.com",
    "Axios": "axios.com",
    "Bloomberg": "bloomberg.com",
    "The Daily Wire": "dailywire.com",
}

DEFAULT_OUTLETS = ["CNN", "Reuters", "Fox News"]
MAX_OUTLETS = 15


def normalize_domain(value):
    """Turn user input like 'https://www.Example.com/news' into 'example.com'."""
    domain = (value or "").strip().lower()

    for prefix in ("https://", "http://"):
        if domain.startswith(prefix):
            domain = domain[len(prefix):]

    domain = domain.split("/")[0].split("?")[0].split(":")[0]

    if domain.startswith("www."):
        domain = domain[4:]

    if (
        not domain
        or "." not in domain
        or " " in domain
        or not all(c.isalnum() or c in ".-" for c in domain)
    ):
        raise ValueError(f"Invalid outlet domain: '{value}'")

    return domain


def resolve_targets(selected_outlets=None, custom_outlets=None):
    """Return an ordered {display name: domain} map of outlets to search."""
    custom_outlets = custom_outlets or []

    if selected_outlets is None and not custom_outlets:
        selected_outlets = DEFAULT_OUTLETS

    selected_outlets = selected_outlets or []

    invalid_outlets = [
        outlet for outlet in selected_outlets
        if outlet not in NEWS_OUTLETS
    ]

    if invalid_outlets:
        raise ValueError(
            f"Unsupported news outlets: {invalid_outlets}"
        )

    # Build an ordered {display name: domain} map of everything to search.
    targets = {}

    for outlet in selected_outlets:
        targets[outlet] = NEWS_OUTLETS[outlet]

    for custom in custom_outlets:
        domain = normalize_domain(custom)

        # Reuse the preset name if the domain is already a known outlet.
        known = next(
            (n for n, d in NEWS_OUTLETS.items() if d == domain),
            None
        )
        targets.setdefault(known or domain, domain)

    if not targets:
        raise ValueError("Select at least one news outlet")

    if len(targets) > MAX_OUTLETS:
        raise ValueError(
            f"Please select at most {MAX_OUTLETS} outlets"
        )

    return targets


def search_news(
    event,
    page_size=10,
    selected_outlets=None,
    custom_outlets=None
):
    if not NEWS_API_KEY:
        raise ValueError("NEWS_API_KEY is missing")

    targets = resolve_targets(selected_outlets, custom_outlets)

    results = []

    for outlet, domain in targets.items():

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
