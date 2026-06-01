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


def test_poller_passes_full_classifier_context(mocker):
    fake_reading = {
        "city": "Ottawa",
        "timestamp": "2026-05-29T20:00:00",
        "temperature_2m": 21.0,
        "apparent_temperature": 22.0,
        "precipitation": 0.0,
        "wind_speed_10m": 10.0,
        "weather_code": 3,
    }
    previous_reading = {"city": "Ottawa", "timestamp": "2026-05-29T19:55:00"}
    recent_readings = [{"city": "Ottawa", "timestamp": "2026-05-29T19:00:00"}]
    latest_readings_by_city = {
        "Ottawa": fake_reading,
        "Toronto": {"city": "Toronto"},
        "Vancouver": {"city": "Vancouver"},
    }

    captured_context = {}

    def fake_classify(reading, context):
        captured_context.update(context)
        return []

    mocker.patch("app.poller.CITIES", {"Ottawa": {"lat": 45.42, "lon": -75.69}})
    mocker.patch("app.poller.fetch_current_weather", return_value=fake_reading)
    mocker.patch("app.poller.insert_reading_if_new", return_value=1)
    mocker.patch("app.poller.get_previous_reading", return_value=previous_reading)
    mocker.patch("app.poller.get_recent_readings", return_value=recent_readings)
    mocker.patch("app.poller.get_latest_readings_by_city", return_value=latest_readings_by_city)
    mocker.patch("app.poller.classify_reading", side_effect=fake_classify)

    poll_once()

    assert captured_context["previous_reading"] == previous_reading
    assert captured_context["recent_readings"] == recent_readings
    assert captured_context["latest_readings_by_city"] == latest_readings_by_city