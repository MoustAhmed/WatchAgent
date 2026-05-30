import logging
import time

from app.classifier import classify_reading
from app.config import POLL_INTERVAL_SECONDS
from app.db import init_db, insert_event, insert_reading_if_new
from app.open_meteo import CITIES, fetch_current_weather



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def poll_once() -> None:
    
    for city in CITIES:
        try:

            reading = fetch_current_weather(city)
            reading_id = insert_reading_if_new(reading)

            if reading_id is None:
                logger.info("Duplicate reading skipped for %s at %s", city, reading["timestamp"])
                continue

            logger.info("Stored new reading for %s at %s", city, reading["timestamp"])

            events = classify_reading(reading)

            for event in events:
                logger.info("Classifier produced event: %s", event)

        except Exception as exc:
            logger.warning("Poll failed for %s: %s", city, exc)


def run() -> None:
    init_db()

    while True:
        poll_once()
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    run()