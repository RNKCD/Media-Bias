
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import test_connection, engine

from services.news_service import search_news
from services.article_service import save_articles

from sqlalchemy import text

app = FastAPI(title="MediaLens API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class EventRequest(BaseModel):
    event: str

@app.get("/api/health")
def health():
    return {"status": "healthy"}



@app.post("/api/analyze")
def analyze_event(request: EventRequest):
    event = request.event.strip()
    articles = search_news(event, page_size=10)
    storage = save_articles(event, articles)

    print("NEWSAPI ARTICLES:", len(articles), flush=True)
    print("DATABASE STORAGE:", storage, flush=True)

    if not event:
        raise HTTPException(
            status_code=400,
            detail="Please enter a political event."
        )

    try:
        articles = search_news(event, page_size=10)

        return {
            "event": event,
            "status": "articles_retrieved",
            "total_articles": len(articles),
            "articles": articles
        }

    except requests.exceptions.RequestException:
        raise HTTPException(
            status_code=502,
            detail="Unable to retrieve articles from NewsAPI."
        )

    except ValueError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

    return {
        "event": request.event,
        "message": "Event received successfully!",
        "articles": []
    }


@app.get("/api/db-health")
def database_health():
    try:
        database_name = test_connection()

        return {
            "status": "connected",
            "database": database_name
        }

    except Exception:
        return {
            "status": "error",
            "message": "Database connection failed"
        }


@app.get("/api/debug/articles")
def debug_articles():
    with engine.connect() as connection:
        database = connection.execute(
            text("SELECT current_database()")
        ).scalar_one()

        count = connection.execute(
            text("SELECT COUNT(*) FROM public.articles")
        ).scalar_one()

        return {
            "database": database,
            "article_count": count
        }
