from app.db import count_readings, insert_reading_if_new


def test_same_city_same_timestamp_only_stores_once(clean_db):
    reading = {
        "city": "Ottawa",
        "timestamp": "2026-05-27T12:00:00",
        "temperature_2m": 21.5,
        "apparent_temperature": 23.0,
        "precipitation": 0.0,
        "wind_speed_10m": 12.0,
        "weather_code": 3,
    }

    first_id = insert_reading_if_new(reading)
    second_id = insert_reading_if_new(reading)

    assert first_id is not None
    assert second_id is None
    assert count_readings() == 1


def test_same_timestamp_different_city_is_allowed(clean_db):
    ottawa = {
        "city": "Ottawa",
        "timestamp": "2026-05-27T12:00:00",
        "temperature_2m": 21.5,
        "apparent_temperature": 23.0,
        "precipitation": 0.0,
        "wind_speed_10m": 12.0,
        "weather_code": 3,
    }

    toronto = {
        "city": "Toronto",
        "timestamp": "2026-05-27T12:00:00",
        "temperature_2m": 22.5,
        "apparent_temperature": 24.0,
        "precipitation": 0.0,
        "wind_speed_10m": 10.0,
        "weather_code": 2,
    }

    first_id = insert_reading_if_new(ottawa)
    second_id = insert_reading_if_new(toronto)

    assert first_id is not None
    assert second_id is not None
    assert count_readings() == 2