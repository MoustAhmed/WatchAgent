from fastapi.testclient import TestClient

from app.db import insert_event, insert_reading_if_new
from app.main import app

client = TestClient(app)

# checks /health endpoint matches the required API shap
def test_health_returns_correct_shape(clean_db):
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert "readings_stored" in data
    assert "events_stored" in data
    assert isinstance(data["readings_stored"], int)
    assert isinstance(data["events_stored"], int)

# checks the API can access stored database readings
def test_readings_returns_readings_array(clean_db):
    # adds a reading to the database
    reading = {
        "city": "Ottawa",
        "timestamp": "2026-05-27T12:00:00",
        "temperature_2m": 21.5,
        "apparent_temperature": 23.0,
        "precipitation": 0.0,
        "wind_speed_10m": 12.0,
        "weather_code": 3,
    }

    insert_reading_if_new(reading)

    response = client.get("/readings?city=Ottawa&limit=50")

    assert response.status_code == 200

    data = response.json()

    assert "readings" in data
    assert len(data["readings"]) == 1

    stored = data["readings"][0]

    assert stored["city"] == "Ottawa"
    assert stored["temperature_2m"] == 21.5
    assert stored["apparent_temperature"] == 23.0
    assert stored["precipitation"] == 0.0
    assert stored["wind_speed_10m"] == 12.0
    assert stored["weather_code"] == 3

#  
def test_events_returns_events_array(clean_db):
    reading = {
        "city": "Toronto",
        "timestamp": "2026-05-27T12:00:00",
        "temperature_2m": 18.0,
        "apparent_temperature": 17.0,
        "precipitation": 0.0,
        "wind_speed_10m": 48.0,
        "weather_code": 3,
    }

    reading_id = insert_reading_if_new(reading)

    event = {
        "city": "Toronto",
        "timestamp": "2026-05-27T12:00:00",
        "event_type": "high_wind",
        "severity": "high",
        "message": "Toronto is experiencing high wind.",
        "reason": "Wind speed is 48.0 km/h, above the 45 km/h threshold.",
    }

    insert_event(event, reading_id)

    response = client.get("/events?city=Toronto&limit=50")

    assert response.status_code == 200

    data = response.json()

    assert "events" in data
    assert len(data["events"]) == 1

    stored = data["events"][0]

    assert stored["city"] == "Toronto"
    assert stored["reading_id"] == reading_id
    assert stored["event_type"] == "high_wind"
    assert stored["severity"] == "high"
    assert stored["message"] == "Toronto is experiencing high wind."
    assert stored["reason"] == "Wind speed is 48.0 km/h, above the 45 km/h threshold."