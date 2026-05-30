from datetime import datetime
from typing import Any

import requests


CITIES = {
    "Ottawa": {"lat": 45.42, "lon": -75.69},
    "Toronto": {"lat": 43.70, "lon": -79.42},
    "Vancouver": {"lat": 49.25, "lon": -123.12},
}


def fetch_current_weather(city: str) -> dict[str, Any]:
    coords = CITIES[city]

    response = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": coords["lat"],
            "longitude": coords["lon"],
            "current": "temperature_2m,apparent_temperature,precipitation,wind_speed_10m,weather_code",
            "wind_speed_unit": "kmh",
            "timezone": "auto",
        },
        timeout=10,
    )

    response.raise_for_status()
    data = response.json()
    current = data["current"]

    return {
        "city": city,
        "timestamp": current["time"],
        "temperature_2m": current["temperature_2m"],
        "apparent_temperature": current["apparent_temperature"],
        "precipitation": current["precipitation"],
        "wind_speed_10m": current["wind_speed_10m"],
        "weather_code": current["weather_code"],
    }