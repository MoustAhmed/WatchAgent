from app.classifier import classify_reading


def make_reading(
    city="Ottawa",
    timestamp="2026-05-29T20:00:00",
    precipitation=0.0,
    wind_speed_10m=10.0,
    weather_code=3,
    temperature_2m=20.0,
    apparent_temperature=20.0,
):
    return {
        "city": city,
        "timestamp": timestamp,
        "temperature_2m": temperature_2m,
        "apparent_temperature": apparent_temperature,
        "precipitation": precipitation,
        "wind_speed_10m": wind_speed_10m,
        "weather_code": weather_code,
    }


def event_types(events):
    return {event["event_type"] for event in events}


def test_high_wind_event_fires_when_wind_is_above_threshold():
    reading = make_reading(city="Toronto", wind_speed_10m=48.0)

    events = classify_reading(reading)

    assert "high_wind" in event_types(events)


def test_high_wind_event_does_not_fire_below_threshold():
    reading = make_reading(city="Toronto", wind_speed_10m=30.0)

    events = classify_reading(reading)

    assert "high_wind" not in event_types(events)


def test_precipitation_started_after_dry_previous_reading():
    previous = make_reading(precipitation=0.0)
    current = make_reading(precipitation=1.2)

    events = classify_reading(current, {"previous_reading": previous})

    assert "precipitation_started" in event_types(events)


def test_precipitation_started_does_not_fire_when_already_precipitating():
    previous = make_reading(precipitation=0.8)
    current = make_reading(precipitation=1.2)

    events = classify_reading(current, {"previous_reading": previous})

    assert "precipitation_started" not in event_types(events)


def test_precipitation_ended_after_wet_previous_reading():
    previous = make_reading(precipitation=1.1)
    current = make_reading(precipitation=0.0)

    events = classify_reading(current, {"previous_reading": previous})

    assert "precipitation_ended" in event_types(events)


def test_precipitation_ended_does_not_fire_when_already_dry():
    previous = make_reading(precipitation=0.0)
    current = make_reading(precipitation=0.0)

    events = classify_reading(current, {"previous_reading": previous})

    assert "precipitation_ended" not in event_types(events)


def test_snow_started_when_weather_code_enters_snow_group():
    previous = make_reading(weather_code=3)
    current = make_reading(weather_code=71)

    events = classify_reading(current, {"previous_reading": previous})

    assert "snow_started" in event_types(events)


def test_snow_ended_when_weather_code_leaves_snow_group():
    previous = make_reading(weather_code=71)
    current = make_reading(weather_code=3)

    events = classify_reading(current, {"previous_reading": previous})

    assert "snow_ended" in event_types(events)


def test_storm_conditions_fire_with_high_wind_and_heavy_precipitation():
    reading = make_reading(
        wind_speed_10m=50.0,
        precipitation=4.0,
        weather_code=61,
    )

    events = classify_reading(reading)

    assert "storm_conditions" in event_types(events)


def test_storm_conditions_do_not_fire_with_only_heavy_precipitation():
    reading = make_reading(
        wind_speed_10m=20.0,
        precipitation=4.0,
        weather_code=61,
    )

    events = classify_reading(reading)

    assert "storm_conditions" not in event_types(events)


def test_winter_storm_conditions_fire_with_snow_and_high_wind():
    reading = make_reading(
        wind_speed_10m=50.0,
        precipitation=1.0,
        weather_code=71,
    )

    events = classify_reading(reading)

    assert "winter_storm_conditions" in event_types(events)


def test_winter_storm_conditions_do_not_fire_with_snow_only():
    reading = make_reading(
        wind_speed_10m=20.0,
        precipitation=1.0,
        weather_code=71,
    )

    events = classify_reading(reading)

    assert "winter_storm_conditions" not in event_types(events)