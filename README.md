# WatchAgent: Weather Monitor & AI Assistant

WatchAgent is a Python-based weather monitoring service built for an Infrastructure & AI take-home challenge. It monitors live weather across Ottawa, Toronto, and Vancouver, stores timestamped readings, detects notable weather events, and exposes readings/events through a FastAPI API.

Core idea:

> Poll frequently, store only new timestamped readings, classify meaningful events, suppress noisy repeats, and expose everything through an API.

---

## Architecture

<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/f16ff737-d95c-4cae-98d4-d21365c1eacb" />

---

## 1. Overview

### Features

- Polls Open-Meteo weather data for Ottawa, Toronto, and Vancouver
- Stores readings in PostgreSQL
- Deduplicates readings by `city + timestamp`
- Detects notable events using current, previous, recent, and cross-city context
- Stores events with `severity`, `score`, `message`, and `reason`
- Suppresses repeated same/lower-severity alerts within a cooldown window
- Exposes `/health`, `/readings`, and `/events`
- Runs with Docker Compose
- Includes GitHub Actions CI for tests and Docker build
- Includes Cursor rules, reviewer agents, and a read-only data-analysis skill

### Tech Stack

- **Python 3.11**
- **FastAPI**
- **PostgreSQL**
- **psycopg**
- **requests**
- **pytest**
- **Docker + Docker Compose**
- **GitHub Actions**

I used direct SQL through `psycopg` instead of an ORM because the schema is small, the queries are explicit, and database-level deduplication is easy to reason about.

---

## 2. Quick Start

### macOS / Linux / Git Bash

```bash
git clone https://github.com/MoustAhmed/WatchAgent.git
cd WatchAgent
cp .env.example .env
docker compose up --build
```

### Windows PowerShell

```powershell
git clone https://github.com/MoustAhmed/WatchAgent.git
cd WatchAgent
Copy-Item .env.example .env -Force
docker compose up --build
```

After startup, the stack runs:

| Service | Purpose |
|---|---|
| `db` | PostgreSQL database |
| `api` | FastAPI server at `http://localhost:8000` |
| `poller` | Background Open-Meteo polling service |

The API and poller wait for PostgreSQL to become healthy before starting. The poller then begins collecting readings automatically.

### Environment Variables

`.env.example`:

```env
DATABASE_URL=postgresql://watchagent:watchagent@db:5432/watchagent
POLL_INTERVAL_SECONDS=300
```

No external API keys are required.

---

## 3. API Examples

Run these in a second terminal while `docker compose up --build` is running.

### Health Check

```bash
curl http://localhost:8000/health
```

Windows PowerShell:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Expected shape:

```json
{
  "status": "ok",
  "readings_stored": 3,
  "events_stored": 0
}
```

### Latest Readings

```bash
curl "http://localhost:8000/readings?limit=5"
```

Windows PowerShell:

```powershell
Invoke-RestMethod "http://localhost:8000/readings?limit=5" | ConvertTo-Json -Depth 5
```

### Readings by City

```bash
curl "http://localhost:8000/readings?city=Ottawa&limit=5"
curl "http://localhost:8000/readings?city=Toronto&limit=5"
curl "http://localhost:8000/readings?city=Vancouver&limit=5"
```

Windows PowerShell:

```powershell
Invoke-RestMethod "http://localhost:8000/readings?city=Ottawa&limit=5" | ConvertTo-Json -Depth 5
Invoke-RestMethod "http://localhost:8000/readings?city=Toronto&limit=5" | ConvertTo-Json -Depth 5
Invoke-RestMethod "http://localhost:8000/readings?city=Vancouver&limit=5" | ConvertTo-Json -Depth 5
```

### Latest Events

```bash
curl "http://localhost:8000/events?limit=5"
```

Windows PowerShell:

```powershell
Invoke-RestMethod "http://localhost:8000/events?limit=5" | ConvertTo-Json -Depth 5
```

The response may be empty if live weather has not triggered a notable event yet:

```json
{
  "events": []
}
```

That is expected. Event logic is tested with controlled unit-test data.

### Events by City

```bash
curl "http://localhost:8000/events?city=Ottawa&limit=5"
curl "http://localhost:8000/events?city=Toronto&limit=5"
curl "http://localhost:8000/events?city=Vancouver&limit=5"
```

Windows PowerShell:

```powershell
Invoke-RestMethod "http://localhost:8000/events?city=Ottawa&limit=5" | ConvertTo-Json -Depth 5
Invoke-RestMethod "http://localhost:8000/events?city=Toronto&limit=5" | ConvertTo-Json -Depth 5
Invoke-RestMethod "http://localhost:8000/events?city=Vancouver&limit=5" | ConvertTo-Json -Depth 5
```

### Poller Logs

```bash
docker compose logs --tail=30 poller
```

Example:

```text
poller-1 | Stored new reading for Ottawa at 2026-05-31T20:15
poller-1 | Stored new reading for Toronto at 2026-05-31T20:15
poller-1 | Stored new reading for Vancouver at 2026-05-31T17:15
```

If Open-Meteo returns the same timestamp again, WatchAgent skips the duplicate.

---

```text
Open-Meteo API
      ↓
Poller Container
      ↓
Deduplication by city + timestamp
      ↓
PostgreSQL
      ↓
Classifier Context
(previous reading, recent readings, latest readings by city)
      ↓
Event Classifier
      ↓
Suppression / Cooldown
      ↓
Events Table
      ↓
FastAPI API
```

The API and poller run as separate containers but share the same PostgreSQL database.

---

## 4. Event Detection Design

WatchAgent groups events into four families:

1. **Current-risk events**  
   Detect hazards in the current reading.

2. **State-transition events**  
   Compare the current reading with the previous reading for the same city.

3. **Prolonged-condition events**  
   Use a 120-minute recent-reading window.

4. **Cross-city anomaly events**  
   Compare one city against the latest readings from the other monitored cities.

### Supported Events

| Event Type | Trigger | Context | Score |
|---|---|---|---|
| `high_wind` | Wind speed ≥ `45.0 km/h` | Current reading | `min(wind / 60.0, 1.0)` |
| `precipitation_started` | Previous dry, current precipitation > `0` | `previous_reading` | `min(current_precip / 5.0, 1.0)` |
| `precipitation_ended` | Previous wet, current dry | `previous_reading` | `min(previous_precip / 5.0, 1.0)` |
| `snow_started` | Previous not snow, current snow code | `previous_reading` | `max(0.6, min(wind / 60.0, 1.0))` |
| `snow_ended` | Previous snow, current not snow | `previous_reading` | `0.3` |
| `storm_conditions` | Wind ≥ `45.0`, precipitation ≥ `3.0`, not snow | Current reading | Average of wind score and precipitation score |
| `winter_storm_conditions` | Wind ≥ `45.0` and snow code | Current reading | `min(wind / 60.0, 1.0)` |
| `prolonged_precipitation` | All readings in 120-minute window have precipitation | `recent_readings` | `min(avg_precip / 5.0, 1.0)` |
| `prolonged_high_wind` | All readings in 120-minute window have wind ≥ `45.0` | `recent_readings` | `min(avg_wind / 60.0, 1.0)` |
| `weather_outlier` | City differs by ≥ `8.0°C` from other-city average | `latest_readings_by_city` | `min(temp_diff / 15.0, 1.0)` |

### Thresholds

| Constant | Value |
|---|---:|
| `HIGH_WIND_THRESHOLD` | `45.0 km/h` |
| `HEAVY_PRECIP_THRESHOLD` | `3.0 mm` |
| `PROLONGED_WINDOW_MINUTES` | `120` |
| `WEATHER_OUTLIER_TEMP_DIFF` | `8.0°C` |
| `SNOW_CODES` | `71, 73, 75, 77, 85, 86` |

### Score and Severity

Every event has a score from `0.0` to `1.0`.

| Score Range | Severity |
|---|---|
| `< 0.4` | `low` |
| `0.4 <= score < 0.7` | `medium` |
| `>= 0.7` | `high` |

### Suppression / Alert Noise

The poller applies a 120-minute cooldown per `city + event_type`.

If the same event was recently stored for the same city:

- same severity is suppressed
- lower severity is suppressed
- higher severity is stored

This reduces alert fatigue during long-running weather conditions while still recording worsening events.

### Classifier Context

| Context Field | Used For |
|---|---|
| `previous_reading` | Precipitation/snow starting or ending |
| `recent_readings` | Prolonged precipitation and prolonged high wind |
| `latest_readings_by_city` | Cross-city `weather_outlier` |

If required context is missing, context-dependent events do not fire.

---

## 5. Testing

The test suite covers:

- API response shape
- database deduplication
- event insertion
- classifier event logic
- transition event scoring
- event suppression
- poller context passing
- poller behavior with mocked weather data
- Cursor data-analysis skill execution

For local tests, run only the database container. The API and poller containers should not be running because tests reset database tables.

### Windows PowerShell

```powershell
docker compose down
docker compose up -d db
$env:DATABASE_URL="postgresql://watchagent:watchagent@127.0.0.1:5433/watchagent?connect_timeout=5"
.\.venv\Scripts\python.exe -m pytest -v
```

### macOS / Linux / Git Bash

```bash
docker compose down
docker compose up -d db
export DATABASE_URL="postgresql://watchagent:watchagent@127.0.0.1:5433/watchagent?connect_timeout=5"
python -m pytest -v
```

---

## 6. Cursor Setup

This repository includes a committed `.cursor/` folder with project-specific rules, agents, and a read-only data-analysis skill.

### Rules

- `.cursor/rules/event-schema.mdc`  
  Defines event schema expectations: `city`, `timestamp`, `event_type`, `severity`, `score`, `message`, and `reason`.

- `.cursor/rules/classifier-noise-control.mdc`  
  Guides event detection toward meaningful state changes, compound risk, prolonged conditions, severity increases, and cross-city anomalies.

- `.cursor/rules/poller-error-handling.mdc`  
  Defines poller behavior for failed API calls, duplicate readings, classifier execution, and event suppression.

- `.cursor/rules/testing-policy.mdc`  
  Requires deterministic tests, mocked Open-Meteo calls, `clean_db` usage for PostgreSQL tests, and positive/negative event coverage.

### Agents

- `.cursor/agents/event-detection-reviewer.md`  
  Reviews event rules, scoring, severity, context usage, suppression, tests, and README alignment.

- `.cursor/agents/test-coverage-reviewer.md`  
  Reviews deterministic test coverage, Open-Meteo mocking, DB test setup, API response tests, and event positive/negative cases.

### Skill

- `.cursor/skills/analyze_weather_data.py`  
  A read-only reporting script that uses `SELECT` queries only. It outputs JSON with reading counts, event counts, events by type, latest city readings, highest wind, largest apparent-temperature gap, and average event score.

Run the skill locally:

```powershell
docker compose up -d db
$env:DATABASE_URL="postgresql://watchagent:watchagent@127.0.0.1:5433/watchagent?connect_timeout=5"
.\.venv\Scripts\python.exe .\.cursor\skills\analyze_weather_data.py
```

The Event Detection Reviewer was used during development to identify missing poller context, missing event suppression wiring, transition events without scores, and missing positive/negative tests.

---

## 7. CI

GitHub Actions runs on every push to `main`.

The pipeline has two jobs:

1. **Test**
   - Starts PostgreSQL
   - Installs Python dependencies
   - Runs `pytest -v`

2. **Build**
   - Runs `docker build .`

This verifies that the test suite passes and the Docker image builds successfully on a clean machine.

---

## 8. Project Structure

```text
WatchAgent/
  app/
    classifier.py       Event detection logic
    config.py           Environment configuration
    db.py               PostgreSQL connection and queries
    main.py             FastAPI application
    open_meteo.py       Open-Meteo API client
    poller.py           Background polling loop

  tests/
    test_api.py
    test_classifier.py
    test_cursor_skill.py
    test_deduplication.py
    test_event_suppression.py
    test_events.py
    test_poller.py

  .cursor/
    agents/
    rules/
    skills/

  .github/
    workflows/
      ci.yml

  Dockerfile
  docker-compose.yml
  requirements.txt
  pytest.ini
  .env.example
  README.md
```
