from typing import Any

HIGH_WIND_THRESHOLD = 45.0
HEAVY_PRECIP_THRESHOLD = 3.0

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


def classify_reading(
    reading: dict[str, Any],
    context: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    context = context or {}
    previous = context.get("previous_reading")

    events = []

    events.extend(detect_high_wind(reading))
    events.extend(detect_storm_conditions(reading))
    events.extend(detect_winter_storm_conditions(reading))

    if previous:
        events.extend(detect_precipitation_started(reading, previous))
        events.extend(detect_precipitation_ended(reading, previous))
        events.extend(detect_snow_started(reading, previous))
        events.extend(detect_snow_ended(reading, previous))

    return events


def build_event(
    reading: dict[str, Any],
    event_type: str,
    severity: str,
    message: str,
    reason: str,
) -> dict[str, Any]:
    return {
        "city": reading["city"],
        "timestamp": reading["timestamp"],
        "event_type": event_type,
        "severity": severity,
        "message": message,
        "reason": reason,
    }


def detect_high_wind(reading: dict[str, Any]) -> list[dict[str, Any]]:
    wind = reading["wind_speed_10m"]

    if wind >= HIGH_WIND_THRESHOLD:
        return [
            build_event(
                reading,
                "high_wind",
                "high",
                f"{reading['city']} is experiencing high wind.",
                f"Wind speed is {wind:.1f} km/h, above the {HIGH_WIND_THRESHOLD:.0f} km/h threshold.",
            )
        ]

    return []


def detect_storm_conditions(reading: dict[str, Any]) -> list[dict[str, Any]]:
    wind = reading["wind_speed_10m"]
    precip = reading["precipitation"]

    if wind >= HIGH_WIND_THRESHOLD and precip >= HEAVY_PRECIP_THRESHOLD and not is_snow(reading):
        return [
            build_event(
                reading,
                "storm_conditions",
                "high",
                f"{reading['city']} is experiencing storm-like conditions.",
                (
                    f"Wind speed is {wind:.1f} km/h and precipitation is {precip:.1f} mm, "
                    f"exceeding storm-condition thresholds."
                ),
            )
        ]

    return []


def detect_winter_storm_conditions(reading: dict[str, Any]) -> list[dict[str, Any]]:
    wind = reading["wind_speed_10m"]

    if wind >= HIGH_WIND_THRESHOLD and is_snow(reading):
        return [
            build_event(
                reading,
                "winter_storm_conditions",
                "high",
                f"{reading['city']} is experiencing winter storm-like conditions.",
                (
                    f"Weather code {reading['weather_code']} indicates snow and wind speed is "
                    f"{wind:.1f} km/h, above the {HIGH_WIND_THRESHOLD:.0f} km/h threshold."
                ),
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