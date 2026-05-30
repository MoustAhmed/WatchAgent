from app.db import count_events, insert_event, insert_reading_if_new


def test_insert_event_stores_event(clean_db):
    reading = {
        "city": "Ottawa",
        "timestamp": "2026-05-27T12:00:00",
        "temperature_2m": 20.0,
        "apparent_temperature": 19.0,
        "precipitation": 0.0,
        "wind_speed_10m": 50.0,
        "weather_code": 3,
    }

    reading_id = insert_reading_if_new(reading)

    event = {
        "city": "Ottawa",
        "timestamp": "2026-05-27T12:00:00",
        "event_type": "high_wind",
        "severity": "high",
        "message": "Ottawa is experiencing high wind.",
        "reason": "Wind speed is 50.0 km/h, above the 45 km/h threshold.",
    }

    event_id = insert_event(event, reading_id)

    assert event_id is not None
    assert count_events() == 1