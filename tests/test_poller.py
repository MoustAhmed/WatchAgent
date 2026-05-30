from app.db import count_readings
from app.poller import poll_once


def test_poller_stores_new_reading_and_skips_duplicate(mocker, clean_db):
    fake_reading = {
        "city": "Ottawa",
        "timestamp": "2026-05-29T20:00:00",
        "temperature_2m": 21.0,
        "apparent_temperature": 22.0,
        "precipitation": 0.0,
        "wind_speed_10m": 10.0,
        "weather_code": 3,
    }

    mocker.patch("app.poller.CITIES", {"Ottawa": {"lat": 45.42, "lon": -75.69}})
    mocker.patch("app.poller.fetch_current_weather", return_value=fake_reading)

    poll_once()
    poll_once()

    assert count_readings() == 1