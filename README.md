# WatchAgent: Weather Monitor & AI Assistant

WatchAgent is a Python-based weather monitoring service built for an Infrastructure & AI take-home challenge. It monitors live weather across Ottawa, Toronto, and Vancouver, stores timestamped readings, detects notable weather events, and exposes the data through a FastAPI HTTP API.

The project is designed around a simple monitoring idea:

> Poll frequently, store only new timestamped readings, classify meaningful events, and expose everything through an API.

---

## Current Features

- Polls Open-Meteo weather data for: Ottawa, Toronto, Vancouver
- Stores weather readings in PostgreSQL
- Deduplicates readings by `city + timestamp`
- Detects basic notable weather events
- Stores events in the database
- Exposes readings and events through FastAPI
- Runs with Docker Compose
- Includes unit tests for:
  - API response shape
  - database deduplication
  - event storage
  - classifier logic
  - poller behavior with mocked weather data
- Includes GitHub Actions CI for tests and Docker build

---

## Tech Stack

- **Python 3.11**
- **FastAPI** for the HTTP API
- **PostgreSQL** for persistent storage
- **psycopg** for direct database access
- **requests** for Open-Meteo API calls
- **pytest** for testing
- **Docker + Docker Compose** for local deployment
- **GitHub Actions** for CI
  
---

## Architecture
<img width="1672" height="941" alt="image" src="https://github.com/user-attachments/assets/15b57fe8-1861-4b97-b437-20cb42e05373" />

---

## Event Detection Design

WatchAgent groups notable weather events into four families:

- **Current-risk events** identify hazards in the current reading, such as high wind or storm-like conditions.
- **State-transition events** compare the current reading with the previous reading for the same city to detect when precipitation or snow starts or ends.
- **Prolonged-condition events** use a 120-minute recent-reading window to detect sustained precipitation or sustained high wind.
- **Cross-city anomaly events** compare the current city with the latest readings from the other monitored cities.

Supported event types:

- `high_wind`
- `precipitation_started`
- `precipitation_ended`
- `snow_started`
- `snow_ended`
- `storm_conditions`
- `winter_storm_conditions`
- `prolonged_precipitation`
- `prolonged_high_wind`
- `weather_outlier`

### Event Catalog

| event_type | Trigger condition | Required context | Scoring formula | Why it is meaningful |
| --- | --- | --- | --- | --- |
| `high_wind` | Current wind speed is at least 45.0 km/h | Current reading | `min(wind_speed_10m / 60.0, 1.0)` | High wind can affect infrastructure, travel, and outdoor safety. |
| `precipitation_started` | Previous reading was dry and current precipitation is greater than 0 | `previous_reading` | `min(current precipitation / 5.0, 1.0)` | Detects a meaningful state change from dry to wet conditions. |
| `precipitation_ended` | Previous reading had precipitation and current reading is dry | `previous_reading` | `min(previous precipitation / 5.0, 1.0)` | Marks the end of an active precipitation period. |
| `snow_started` | Previous reading was not snow and current weather code is a snow code | `previous_reading` | `max(0.6, min(current wind_speed_10m / 60.0, 1.0))` | Snow onset is operationally important even when accumulation is not yet prolonged. |
| `snow_ended` | Previous reading was snow and current weather code is not a snow code | `previous_reading` | `0.3` | Records the end of snow conditions as a low-severity recovery signal. |
| `storm_conditions` | Wind is at least 45.0 km/h, precipitation is at least 3.0 mm, and current weather is not snow | Current reading | Average of `min(wind_speed_10m / 60.0, 1.0)` and `min(precipitation / 10.0, 1.0)` | Combines wind and rain intensity into a compound risk signal. |
| `winter_storm_conditions` | Wind is at least 45.0 km/h and current weather code is a snow code | Current reading | `min(wind_speed_10m / 60.0, 1.0)` | Captures wind-driven snow conditions separately from rain storms. |
| `prolonged_precipitation` | All readings in the 120-minute window have precipitation | `recent_readings` | `min(average precipitation / 5.0, 1.0)` | Sustained precipitation is more actionable than a single wet reading. |
| `prolonged_high_wind` | All readings in the 120-minute window have wind speed at least 45.0 km/h | `recent_readings` | `min(average wind_speed_10m / 60.0, 1.0)` | Sustained high wind is more disruptive than a single gusty reading. |
| `weather_outlier` | Current city is at least 8.0°C warmer or colder than the average of the other monitored cities | `latest_readings_by_city` with at least two other cities | `min(temperature difference / 15.0, 1.0)` | Flags city-level anomalies that stand out from the monitored region. |

### Thresholds

- `HIGH_WIND_THRESHOLD = 45.0` km/h
- `HEAVY_PRECIP_THRESHOLD = 3.0` mm
- `PROLONGED_WINDOW_MINUTES = 120`
- `WEATHER_OUTLIER_TEMP_DIFF = 8.0`°C
- Snow WMO weather codes: `71`, `73`, `75`, `77`, `85`, `86`

### Score and Severity

Every event includes a score from `0.0` to `1.0`. Severity is derived from score:

- `low`: score < `0.4`
- `medium`: `0.4 <= score < 0.7`
- `high`: score >= `0.7`

Transition events also receive scores:

- `precipitation_started`: `min(current precipitation / 5.0, 1.0)`
- `precipitation_ended`: `min(previous precipitation / 5.0, 1.0)`
- `snow_started`: `max(0.6, min(current wind_speed_10m / 60.0, 1.0))`
- `snow_ended`: `0.3`

### Suppression / Alert Noise

The poller applies a 120-minute cooldown per `city + event_type` before storing events. If the same event type was recently stored for the same city, repeated events with the same or lower severity are suppressed. A repeated event is stored only when its severity increases.

This reduces alert fatigue during long-running weather conditions: a city with hours of high wind should not create a new identical alert every poll, but a worsening event can still be recorded.

### Classifier Context

`classify_reading()` accepts optional context so it can detect events that require more than the current reading:

- `previous_reading` is used for state transitions such as precipitation or snow starting and ending.
- `recent_readings` over the previous 120 minutes are used for prolonged precipitation and prolonged high wind.
- `latest_readings_by_city` is used for `weather_outlier` comparisons across Ottawa, Toronto, and Vancouver.

If required context is missing, context-dependent events do not fire.

---

## Cursor Setup

This repository includes Cursor project guidance for event detection, testing, and review workflows.

Rules:

- `.cursor/rules/event-schema.mdc` defines the event schema expectations: each event includes `city`, `timestamp`, `event_type`, `severity`, `score`, `message`, and `reason`; score stays between `0.0` and `1.0`; severity matches the score bands.
- `.cursor/rules/classifier-noise-control.mdc` guides event rule design toward meaningful state changes, compound risks, prolonged conditions, severity increases, and cross-city anomalies.
- `.cursor/rules/poller-error-handling.mdc` mirrors the classifier noise-control guidance for poller-facing event behavior and alert suppression.
- `.cursor/rules/testin-policy.mdc` requires deterministic tests, mocked Open-Meteo calls in poller tests, `clean_db` for PostgreSQL tests, and positive/negative event detection coverage.

Agents:

- `.cursor/agents/event-detection-reviewer.md` reviews event rules, scoring, severity, context usage, suppression, test coverage, and README alignment.
- `.cursor/agents/test-coverage-reviewer.md` reviews deterministic test coverage, Open-Meteo mocking, `clean_db` usage, API response shape tests, and event positive/negative cases.

Skill:

- `.cursor/skills/analyze_weather_data.py` is a read-only reporting script. It uses `SELECT` queries only and outputs structured JSON with reading counts, event counts, events by type, latest city readings, highest wind, largest apparent-temperature gap, and average event score.

The Event Detection Reviewer was used during development to identify missing poller context, missing event suppression wiring, transition events without scores, and missing positive/negative tests.
