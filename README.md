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

