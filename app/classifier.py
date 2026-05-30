from typing import Any

# Very simple classifier iteration for now, just checking for high wind speed
def classify_reading(reading: dict[str, Any]) -> list[dict[str, Any]]:
    events = []

    if reading["wind_speed_10m"] >= 45:
        events.append(
            {
                "city": reading["city"],
                "timestamp": reading["timestamp"],
                "event_type": "high_wind",
                "severity": "high",
                "message": f"{reading['city']} is experiencing high wind.",
                "reason": f"Wind speed is {reading['wind_speed_10m']} km/h, above the 45 km/h threshold.",
            }
        )

    return events