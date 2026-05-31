from datetime import datetime
from typing import Any

HIGH_WIND_THRESHOLD = 45.0
HEAVY_PRECIP_THRESHOLD = 3.0
PROLONGED_WINDOW_MINUTES = 120
WEATHER_OUTLIER_TEMP_DIFF = 8.0

SNOW_CODES = {
    71, 73, 75, 77, 85, 86
}

RAIN_CODES = {
    51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82
}


def is_precipitating(reading: dict[str, Any]) -> bool:
    return reading["precipitation"] > 0


def is_snow(reading: dict[str, Any]) -> bool:
    return reading["weather_code"] in SNOW_CODES


def parse_timestamp(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def estimate_duration_minutes(readings: list[dict[str, Any]]) -> float:
    timestamps = [parse_timestamp(item["timestamp"]) for item in readings]
    earliest = min(timestamps)
    latest = max(timestamps)
    return (latest - earliest).total_seconds() / 60.0


def severity_from_score(score: float) -> str:
    if score >= 0.7:
        return "high"
    if score >= 0.4:
        return "medium"
    return "low"


def high_wind_score(wind_speed: float) -> float:
    return min(wind_speed / 60.0, 1.0)


def storm_score(wind_speed: float, precipitation: float) -> float:
    wind_score = min(wind_speed / 60.0, 1.0)
    precip_score = min(precipitation / 10.0, 1.0)
    return round((0.5 * wind_score) + (0.5 * precip_score), 2)


def build_event(
    reading: dict[str, Any],
    event_type: str,
    severity: str,
    message: str,
    reason: str,
    score: float | None = None,
) -> dict[str, Any]:
    return {
        "city": reading["city"],
        "timestamp": reading["timestamp"],
        "event_type": event_type,
        "severity": severity,
        "score": score,
        "message": message,
        "reason": reason,
    }


def classify_reading(
    reading: dict[str, Any],
    context: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    context = context or {}

    previous = context.get("previous_reading")
    recent_readings = context.get("recent_readings", [])
    latest_readings_by_city = context.get("latest_readings_by_city", {})

    events = []

    events.extend(detect_high_wind(reading))
    events.extend(detect_storm_conditions(reading))
    events.extend(detect_winter_storm_conditions(reading))
    events.extend(detect_prolonged_precipitation(reading, recent_readings))
    events.extend(detect_prolonged_high_wind(reading, recent_readings))
    events.extend(detect_weather_outlier(reading, latest_readings_by_city))

    if previous:
        events.extend(detect_precipitation_started(reading, previous))
        events.extend(detect_precipitation_ended(reading, previous))
        events.extend(detect_snow_started(reading, previous))
        events.extend(detect_snow_ended(reading, previous))

    return events


def detect_high_wind(reading: dict[str, Any]) -> list[dict[str, Any]]:
    wind = reading["wind_speed_10m"]

    if wind >= HIGH_WIND_THRESHOLD:
        score = round(high_wind_score(wind), 2)

        return [
            build_event(
                reading,
                "high_wind",
                severity_from_score(score),
                f"{reading['city']} is experiencing high wind.",
                (
                    f"Wind speed is {wind:.1f} km/h, above the "
                    f"{HIGH_WIND_THRESHOLD:.0f} km/h threshold. Score={score:.2f}."
                ),
                score,
            )
        ]

    return []


def detect_storm_conditions(reading: dict[str, Any]) -> list[dict[str, Any]]:
    wind = reading["wind_speed_10m"]
    precip = reading["precipitation"]

    if wind >= HIGH_WIND_THRESHOLD and precip >= HEAVY_PRECIP_THRESHOLD and not is_snow(reading):
        score = storm_score(wind, precip)

        return [
            build_event(
                reading,
                "storm_conditions",
                severity_from_score(score),
                f"{reading['city']} is experiencing storm-like conditions.",
                (
                    f"Wind speed is {wind:.1f} km/h and precipitation is {precip:.1f} mm, "
                    f"exceeding storm-condition thresholds. Score={score:.2f}."
                ),
                score,
            )
        ]

    return []


def detect_winter_storm_conditions(reading: dict[str, Any]) -> list[dict[str, Any]]:
    wind = reading["wind_speed_10m"]

    if wind >= HIGH_WIND_THRESHOLD and is_snow(reading):
        score = round(high_wind_score(wind), 2)

        return [
            build_event(
                reading,
                "winter_storm_conditions",
                severity_from_score(score),
                f"{reading['city']} is experiencing winter storm-like conditions.",
                (
                    f"Weather code {reading['weather_code']} indicates snow and wind speed is "
                    f"{wind:.1f} km/h, above the {HIGH_WIND_THRESHOLD:.0f} km/h threshold. "
                    f"Score={score:.2f}."
                ),
                score,
            )
        ]

    return []


def detect_precipitation_started(
    reading: dict[str, Any],
    previous: dict[str, Any],
) -> list[dict[str, Any]]:
    if not is_precipitating(previous) and is_precipitating(reading):
        return [
            build_event(
                reading,
                "precipitation_started",
                "medium",
                f"Precipitation started in {reading['city']}.",
                (
                    f"Previous reading had {previous['precipitation']:.1f} mm precipitation, "
                    f"current reading has {reading['precipitation']:.1f} mm."
                ),
            )
        ]

    return []


def detect_precipitation_ended(
    reading: dict[str, Any],
    previous: dict[str, Any],
) -> list[dict[str, Any]]:
    if is_precipitating(previous) and not is_precipitating(reading):
        return [
            build_event(
                reading,
                "precipitation_ended",
                "low",
                f"Precipitation ended in {reading['city']}.",
                (
                    f"Previous reading had {previous['precipitation']:.1f} mm precipitation, "
                    "current reading is dry."
                ),
            )
        ]

    return []


def detect_snow_started(
    reading: dict[str, Any],
    previous: dict[str, Any],
) -> list[dict[str, Any]]:
    if not is_snow(previous) and is_snow(reading):
        return [
            build_event(
                reading,
                "snow_started",
                "medium",
                f"Snow started in {reading['city']}.",
                (
                    f"Weather code changed from {previous['weather_code']} to "
                    f"{reading['weather_code']}, entering a snow condition."
                ),
            )
        ]

    return []


def detect_snow_ended(
    reading: dict[str, Any],
    previous: dict[str, Any],
) -> list[dict[str, Any]]:
    if is_snow(previous) and not is_snow(reading):
        return [
            build_event(
                reading,
                "snow_ended",
                "low",
                f"Snow ended in {reading['city']}.",
                (
                    f"Weather code changed from {previous['weather_code']} to "
                    f"{reading['weather_code']}, leaving a snow condition."
                ),
            )
        ]

    return []


def detect_prolonged_precipitation(
    reading: dict[str, Any],
    recent_readings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    window = recent_readings + [reading]

    if len(window) < 2:
        return []

    if not all(is_precipitating(item) for item in window):
        return []

    duration_minutes = estimate_duration_minutes(window)

    if duration_minutes < PROLONGED_WINDOW_MINUTES:
        return []

    avg_precip = sum(item["precipitation"] for item in window) / len(window)
    score = round(min(avg_precip / 5.0, 1.0), 2)

    return [
        build_event(
            reading,
            "prolonged_precipitation",
            severity_from_score(score),
            f"{reading['city']} has had prolonged precipitation.",
            (
                f"Precipitation persisted for approximately {duration_minutes:.0f} minutes "
                f"with average precipitation {avg_precip:.1f} mm. Score={score:.2f}."
            ),
            score,
        )
    ]


def detect_prolonged_high_wind(
    reading: dict[str, Any],
    recent_readings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    window = recent_readings + [reading]

    if len(window) < 2:
        return []

    if not all(item["wind_speed_10m"] >= HIGH_WIND_THRESHOLD for item in window):
        return []

    duration_minutes = estimate_duration_minutes(window)

    if duration_minutes < PROLONGED_WINDOW_MINUTES:
        return []

    avg_wind = sum(item["wind_speed_10m"] for item in window) / len(window)
    score = round(high_wind_score(avg_wind), 2)

    return [
        build_event(
            reading,
            "prolonged_high_wind",
            severity_from_score(score),
            f"{reading['city']} has had prolonged high wind.",
            (
                f"Wind stayed above {HIGH_WIND_THRESHOLD:.0f} km/h for approximately "
                f"{duration_minutes:.0f} minutes with average wind {avg_wind:.1f} km/h. "
                f"Score={score:.2f}."
            ),
            score,
        )
    ]


def detect_weather_outlier(
    reading: dict[str, Any],
    latest_readings_by_city: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    other_readings = [
        city_reading
        for city, city_reading in latest_readings_by_city.items()
        if city != reading["city"]
    ]

    if len(other_readings) < 2:
        return []

    other_avg = sum(item["temperature_2m"] for item in other_readings) / len(other_readings)
    diff = abs(reading["temperature_2m"] - other_avg)

    if diff < WEATHER_OUTLIER_TEMP_DIFF:
        return []

    score = round(min(diff / 15.0, 1.0), 2)
    direction = "warmer" if reading["temperature_2m"] > other_avg else "colder"

    return [
        build_event(
            reading,
            "weather_outlier",
            severity_from_score(score),
            f"{reading['city']} is a temperature outlier.",
            (
                f"{reading['city']} is {diff:.1f}°C {direction} than the average of the "
                f"other monitored cities. Score={score:.2f}."
            ),
            score,
        )
    ]