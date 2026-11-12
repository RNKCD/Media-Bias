
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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
    return {
        "event": request.event,
        "message": "Event received successfully!",
        "articles": []
    }

