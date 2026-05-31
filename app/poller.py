import logging
import time

from app.classifier import classify_reading
from app.config import POLL_INTERVAL_SECONDS
from app.db import (
    get_latest_readings_by_city,
    get_previous_reading,
    get_recent_event,
    get_recent_readings,
    init_db,
    insert_event,
    insert_reading_if_new,
)
from app.open_meteo import CITIES, fetch_current_weather


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EVENT_COOLDOWN_MINUTES = 120

SEVERITY_RANK = {
    "low": 1,
    "medium": 2,
    "high": 3,
}


def should_store_event(event: dict, recent_event: dict | None) -> bool:
    if recent_event is None:
        return True

    current_rank = SEVERITY_RANK.get(event["severity"], 0)
    previous_rank = SEVERITY_RANK.get(recent_event["severity"], 0)

    return current_rank > previous_rank


def poll_once() -> None:
    for city in CITIES:
        try:
            reading = fetch_current_weather(city)
            reading_id = insert_reading_if_new(reading)

            if reading_id is None:
                logger.info(
                    "Duplicate reading skipped for %s at %s",
                    city,
                    reading["timestamp"],
                )
                continue

            logger.info(
                "Stored new reading for %s at %s",
                city,
                reading["timestamp"],
            )

            previous_reading = get_previous_reading(
                city=city,
                timestamp=reading["timestamp"],
            )

            context = {
                "previous_reading": previous_reading,
            }

            events = classify_reading(reading, context)

            for event in events:
                event_id = insert_event(event, reading_id)
                logger.info(
                    "Stored event %s for %s: %s",
                    event_id,
                    city,
                    event["event_type"],
                )

        except Exception as exc:
            logger.warning("Poll failed for %s: %s", city, exc)


def run() -> None:
    init_db()

    while True:
        poll_once()
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    run()