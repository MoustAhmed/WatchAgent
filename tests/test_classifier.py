from app.classifier import classify_reading, severity_from_score


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


def event_by_type(events, event_type):
    return [event for event in events if event["event_type"] == event_type][0]


def assert_score_and_severity_match(event):
    assert event["score"] is not None
    assert 0.0 <= event["score"] <= 1.0
    assert event["severity"] == severity_from_score(event["score"])


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
    event = event_by_type(events, "precipitation_started")

    assert "precipitation_started" in event_types(events)
    assert_score_and_severity_match(event)


def test_precipitation_started_does_not_fire_when_already_precipitating():
    previous = make_reading(precipitation=0.8)
    current = make_reading(precipitation=1.2)

    events = classify_reading(current, {"previous_reading": previous})

    assert "precipitation_started" not in event_types(events)


def test_precipitation_ended_after_wet_previous_reading():
    previous = make_reading(precipitation=1.1)
    current = make_reading(precipitation=0.0)

    events = classify_reading(current, {"previous_reading": previous})
    event = event_by_type(events, "precipitation_ended")

    assert "precipitation_ended" in event_types(events)
    assert_score_and_severity_match(event)


def test_precipitation_ended_does_not_fire_when_already_dry():
    previous = make_reading(precipitation=0.0)
    current = make_reading(precipitation=0.0)

    events = classify_reading(current, {"previous_reading": previous})

    assert "precipitation_ended" not in event_types(events)


def test_snow_started_when_weather_code_enters_snow_group():
    previous = make_reading(weather_code=3)
    current = make_reading(weather_code=71)

    events = classify_reading(current, {"previous_reading": previous})
    event = event_by_type(events, "snow_started")

    assert "snow_started" in event_types(events)
    assert_score_and_severity_match(event)


def test_snow_started_does_not_fire_when_already_snowing():
    previous = make_reading(weather_code=71)
    current = make_reading(weather_code=73)

    events = classify_reading(current, {"previous_reading": previous})

    assert "snow_started" not in event_types(events)


def test_snow_ended_when_weather_code_leaves_snow_group():
    previous = make_reading(weather_code=71)
    current = make_reading(weather_code=3)

    events = classify_reading(current, {"previous_reading": previous})
    event = event_by_type(events, "snow_ended")

    assert "snow_ended" in event_types(events)
    assert_score_and_severity_match(event)


def test_snow_ended_does_not_fire_when_still_snowing():
    previous = make_reading(weather_code=71)
    current = make_reading(weather_code=73)

    events = classify_reading(current, {"previous_reading": previous})

    assert "snow_ended" not in event_types(events)


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


def test_storm_conditions_do_not_fire_when_weather_code_is_snow():
    reading = make_reading(
        wind_speed_10m=50.0,
        precipitation=4.0,
        weather_code=71,
    )

    events = classify_reading(reading)

    assert "storm_conditions" not in event_types(events)
    assert "winter_storm_conditions" in event_types(events)


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


def test_prolonged_precipitation_fires_after_two_hour_window():
    recent = [
        make_reading(timestamp="2026-05-29T18:00:00", precipitation=1.0),
        make_reading(timestamp="2026-05-29T19:00:00", precipitation=1.2),
    ]
    current = make_reading(timestamp="2026-05-29T20:00:00", precipitation=1.4)

    events = classify_reading(current, {"recent_readings": recent})

    assert "prolonged_precipitation" in event_types(events)

def test_prolonged_precipitation_does_not_fire_without_enough_duration():
    recent = [
        make_reading(timestamp="2026-05-29T19:30:00", precipitation=1.0),
    ]
    current = make_reading(timestamp="2026-05-29T20:00:00", precipitation=1.4)

    events = classify_reading(current, {"recent_readings": recent})

    assert "prolonged_precipitation" not in event_types(events)


def test_prolonged_high_wind_fires_after_two_hour_window():
    recent = [
        make_reading(timestamp="2026-05-29T18:00:00", wind_speed_10m=46.0),
        make_reading(timestamp="2026-05-29T19:00:00", wind_speed_10m=48.0),
    ]
    current = make_reading(timestamp="2026-05-29T20:00:00", wind_speed_10m=50.0)

    events = classify_reading(current, {"recent_readings": recent})

    assert "prolonged_high_wind" in event_types(events)


def test_prolonged_high_wind_does_not_fire_when_wind_drops_in_window():
    recent = [
        make_reading(timestamp="2026-05-29T18:00:00", wind_speed_10m=46.0),
        make_reading(timestamp="2026-05-29T19:00:00", wind_speed_10m=20.0),
    ]
    current = make_reading(timestamp="2026-05-29T20:00:00", wind_speed_10m=50.0)

    events = classify_reading(current, {"recent_readings": recent})

    assert "prolonged_high_wind" not in event_types(events)


def test_weather_outlier_fires_when_city_differs_from_others():
    current = make_reading(city="Vancouver", temperature_2m=30.0)

    latest_by_city = {
        "Ottawa": make_reading(city="Ottawa", temperature_2m=18.0),
        "Toronto": make_reading(city="Toronto", temperature_2m=19.0),
        "Vancouver": current,
    }

    events = classify_reading(
        current,
        {"latest_readings_by_city": latest_by_city},
    )

    assert "weather_outlier" in event_types(events)


def test_weather_outlier_does_not_fire_for_small_difference():
    current = make_reading(city="Vancouver", temperature_2m=22.0)

    latest_by_city = {
        "Ottawa": make_reading(city="Ottawa", temperature_2m=19.0),
        "Toronto": make_reading(city="Toronto", temperature_2m=20.0),
        "Vancouver": current,
    }

    events = classify_reading(
        current,
        {"latest_readings_by_city": latest_by_city},
    )

    assert "weather_outlier" not in event_types(events)


def test_weather_outlier_does_not_fire_without_two_other_cities():
    current = make_reading(city="Vancouver", temperature_2m=30.0)

    latest_by_city = {
        "Ottawa": make_reading(city="Ottawa", temperature_2m=18.0),
        "Vancouver": current,
    }

    events = classify_reading(
        current,
        {"latest_readings_by_city": latest_by_city},
    )

    assert "weather_outlier" not in event_types(events)


def test_event_contains_score_when_scored_rule_fires():
    reading = make_reading(wind_speed_10m=50.0)

    events = classify_reading(reading)

    high_wind = [event for event in events if event["event_type"] == "high_wind"][0]

    assert high_wind["score"] is not None
    assert 0.0 <= high_wind["score"] <= 1.0