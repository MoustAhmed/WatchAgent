from app.classifier import classify_reading


def test_high_wind_event_fires_when_wind_is_above_threshold():
    reading = {
        "city": "Toronto",
        "timestamp": "2026-05-27T12:00:00",
        "temperature_2m": 18.0,
        "apparent_temperature": 17.0,
        "precipitation": 0.0,
        "wind_speed_10m": 48.0,
        "weather_code": 3,
    }

    events = classify_reading(reading)

    assert len(events) == 1
    assert events[0]["event_type"] == "high_wind"
    assert events[0]["city"] == "Toronto"
    assert events[0]["severity"] == "high"
    assert "48.0" in events[0]["reason"]


def test_high_wind_event_does_not_fire_below_threshold():
    reading = {
        "city": "Toronto",
        "timestamp": "2026-05-27T12:00:00",
        "temperature_2m": 18.0,
        "apparent_temperature": 17.0,
        "precipitation": 0.0,
        "wind_speed_10m": 30.0,
        "weather_code": 3,
    }

    events = classify_reading(reading)

    assert events == []