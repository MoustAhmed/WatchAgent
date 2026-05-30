from fastapi import FastAPI, Query

from app.db import count_events, count_readings, get_events, get_readings, init_db


app = FastAPI(title="WatchAgent")


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "readings_stored": count_readings(),
        "events_stored": count_events(),
    }


@app.get("/readings")
def readings(city: str | None = None, limit: int = Query(50, ge=1, le=500)):
    return {
        "readings": get_readings(city=city, limit=limit)
    }


@app.get("/events")
def events(city: str | None = None, limit: int = Query(50, ge=1, le=500)):
    return {
        "events": get_events(city=city, limit=limit)
    }