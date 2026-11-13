
import logging

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import test_connection, engine

from services.news_service import search_news
from services.article_service import save_articles
from services.nlp_pipeline import process_saved_articles
from services.sentiment_pipeline import process_sentiment
from services.emotion_pipeline import process_emotions

from sqlalchemy import text

logger = logging.getLogger(__name__)

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

    if not event:
        raise HTTPException(
            status_code=400,
            detail="Please enter a political event."
        )

    try:
        articles = search_news(event, page_size=10)
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

    try:
        storage = save_articles(event, articles)
        event_id = storage["event_id"]

        # Process the new articles so NLP/sentiment results exist
        # by the time React asks for them.
        nlp = process_saved_articles(event_id=event_id)
        sentiment = process_sentiment(event_id=event_id)
    except Exception:
        logger.exception("Failed to store or process articles")
        raise HTTPException(
            status_code=500,
            detail="Articles were retrieved, but saving or analysis failed. Check server logs."
        )

    print("NEWSAPI ARTICLES:", len(articles), flush=True)
    print("DATABASE STORAGE:", storage, flush=True)

    return {
        "event": event,
        "event_id": event_id,
        "status": "analysis_complete",
        "total_articles": len(articles),
        "storage": storage,
        "processing": {
            "nlp": nlp,
            "sentiment": sentiment
        },
        "articles": articles
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


@app.post("/api/nlp/process")
def run_nlp_processing():
    try:
        result = process_saved_articles()

        return {
            "status": "completed",
            "processed_articles": result["processed"],
            "skipped_articles": result["skipped"]
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="NLP processing failed. Check server logs."
        )




@app.get("/api/nlp/results")
def get_nlp_results(event_id: int):
    with engine.connect() as connection:
        rows = connection.execute(
            text("""
                SELECT
                    a.id AS article_id,
                    a.title,
                    o.name AS outlet,
                    n.word_count,
                    n.keywords,
                    n.entities
                FROM nlp_results n
                JOIN articles a ON a.id = n.article_id
                JOIN outlets o ON a.outlet_id = o.id
                WHERE a.event_id = :event_id
                ORDER BY a.id DESC
            """),
            {"event_id": event_id}
        ).mappings().all()

    return {
        "event_id": event_id,
        "total": len(rows),
        "results": [dict(row) for row in rows]
    }

    with engine.connect() as connection:
        rows = connection.execute(
            text("""
                SELECT
                    a.id AS article_id,
                    a.title,
                    o.name AS outlet,
                    n.word_count,
                    n.keywords,
                    n.entities
                FROM nlp_results n
                JOIN articles a ON a.id = n.article_id
                JOIN outlets o ON a.outlet_id = o.id
                ORDER BY a.id DESC
                LIMIT 100
            """)
        ).mappings().all()

    return {
        "total": len(rows),
        "results": [dict(row) for row in rows]
    }



@app.post("/api/sentiment/process")
def run_sentiment_processing():
    try:
        return process_sentiment()
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Sentiment processing failed. Check server logs."
        )


@app.get("/api/sentiment/results")
def get_sentiment_results(event_id: int):
    with engine.connect() as connection:
        rows = connection.execute(
            text("""
                SELECT
                    a.id AS article_id,
                    a.title,
                    o.name AS outlet,
                    ar.sentiment_label,
                    ar.sentiment_score,
                    ar.headline_sentiment,
                    ar.body_sentiment,
                    ar.text_source
                FROM analysis_results ar
                JOIN articles a ON a.id = ar.article_id
                JOIN outlets o ON o.id = a.outlet_id
                WHERE a.event_id = :event_id
                  AND ar.model_name = 'VADER'
                ORDER BY a.id DESC
            """),
            {"event_id": event_id}
        ).mappings().all()

    return {
        "event_id": event_id,
        "total": len(rows),
        "results": [dict(row) for row in rows]
    }

    with engine.connect() as connection:
        rows = connection.execute(
            text("""
                SELECT
                    a.id AS article_id,
                    a.title,
                    o.name AS outlet,
                    ar.sentiment_label,
                    ar.sentiment_score,
                    ar.headline_sentiment,
                    ar.body_sentiment,
                    ar.text_source
                FROM analysis_results ar
                JOIN articles a ON a.id = ar.article_id
                JOIN outlets o ON o.id = a.outlet_id
                WHERE ar.model_name = 'VADER'
                ORDER BY a.id DESC
                LIMIT 100
            """)
        ).mappings().all()

    return {
        "total": len(rows),
        "results": [dict(row) for row in rows]
    }



@app.post("/api/emotion/process")
def run_emotion_processing():
    return process_emotions()


@app.get("/api/emotion/results")
def get_emotion_results(event_id: int):
    with engine.connect() as connection:
        rows = connection.execute(
            text("""
                SELECT
                    a.id AS article_id,
                    a.title,
                    o.name AS outlet,
                    ar.emotion_label,
                    ar.emotion_scores
                FROM analysis_results ar
                JOIN articles a
                    ON a.id = ar.article_id
                JOIN outlets o
                    ON o.id = a.outlet_id
                WHERE a.event_id = :event_id
                  AND ar.model_name = 'VADER'
                  AND ar.emotion_label IS NOT NULL
                ORDER BY a.id DESC
            """),
            {"event_id": event_id}
        ).mappings().all()

    return {
        "event_id": event_id,
        "total": len(rows),
        "results": [dict(row) for row in rows]
    }
