from datetime import datetime, timezone
from typing import Any

import psycopg

from app.config import DATABASE_URL


def get_conn():
    return psycopg.connect(DATABASE_URL)


def init_db() -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS readings (
                    id SERIAL PRIMARY KEY,
                    city TEXT NOT NULL,
                    timestamp TIMESTAMPTZ NOT NULL,
                    temperature_2m DOUBLE PRECISION NOT NULL,
                    apparent_temperature DOUBLE PRECISION NOT NULL,
                    precipitation DOUBLE PRECISION NOT NULL,
                    wind_speed_10m DOUBLE PRECISION NOT NULL,
                    weather_code INTEGER NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE (city, timestamp)
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id SERIAL PRIMARY KEY,
                    city TEXT NOT NULL,
                    reading_id INTEGER REFERENCES readings(id) ON DELETE CASCADE,
                    timestamp TIMESTAMPTZ NOT NULL,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )


def insert_reading_if_new(reading: dict[str, Any]) -> int | None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO readings (
                    city,
                    timestamp,
                    temperature_2m,
                    apparent_temperature,
                    precipitation,
                    wind_speed_10m,
                    weather_code
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (city, timestamp) DO NOTHING
                RETURNING id;
                """,
                (
                    reading["city"],
                    reading["timestamp"],
                    reading["temperature_2m"],
                    reading["apparent_temperature"],
                    reading["precipitation"],
                    reading["wind_speed_10m"],
                    reading["weather_code"],
                ),
            )

            row = cur.fetchone()
            return row[0] if row else None


def count_readings() -> int:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM readings;")
            return cur.fetchone()[0]


def count_events() -> int:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM events;")
            return cur.fetchone()[0]


def get_readings(city: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            if city:
                cur.execute(
                    """
                    SELECT id, city, timestamp, temperature_2m, apparent_temperature,
                           precipitation, wind_speed_10m, weather_code, created_at
                    FROM readings
                    WHERE city = %s
                    ORDER BY timestamp DESC
                    LIMIT %s;
                    """,
                    (city, limit),
                )
            else:
                cur.execute(
                    """
                    SELECT id, city, timestamp, temperature_2m, apparent_temperature,
                           precipitation, wind_speed_10m, weather_code, created_at
                    FROM readings
                    ORDER BY timestamp DESC
                    LIMIT %s;
                    """,
                    (limit,),
                )

            rows = cur.fetchall()

    return [
        {
            "id": row[0],
            "city": row[1],
            "timestamp": row[2].isoformat(),
            "temperature_2m": row[3],
            "apparent_temperature": row[4],
            "precipitation": row[5],
            "wind_speed_10m": row[6],
            "weather_code": row[7],
            "created_at": row[8].isoformat(),
        }
        for row in rows
    ]

def insert_event(event: dict[str, Any], reading_id: int) -> int:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO events (
                    city,
                    reading_id,
                    timestamp,
                    event_type,
                    severity,
                    message,
                    reason
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
                """,
                (
                    event["city"],
                    reading_id,
                    event["timestamp"],
                    event["event_type"],
                    event["severity"],
                    event["message"],
                    event["reason"],
                ),
            )

            row = cur.fetchone()
            return row[0]


def get_events(city: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            if city:
                cur.execute(
                    """
                    SELECT id, city, reading_id, timestamp, event_type, severity,
                           message, reason, created_at
                    FROM events
                    WHERE city = %s
                    ORDER BY timestamp DESC
                    LIMIT %s;
                    """,
                    (city, limit),
                )
            else:
                cur.execute(
                    """
                    SELECT id, city, reading_id, timestamp, event_type, severity,
                           message, reason, created_at
                    FROM events
                    ORDER BY timestamp DESC
                    LIMIT %s;
                    """,
                    (limit,),
                )

            rows = cur.fetchall()

    return [
        {
            "id": row[0],
            "city": row[1],
            "reading_id": row[2],
            "timestamp": row[3].isoformat(),
            "event_type": row[4],
            "severity": row[5],
            "message": row[6],
            "reason": row[7],
            "created_at": row[8].isoformat(),
        }
        for row in rows
    ]

# db helper that gets the previous reading for a given city and timestamp
def get_previous_reading(city: str, timestamp: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, city, timestamp, temperature_2m, apparent_temperature,
                       precipitation, wind_speed_10m, weather_code, created_at
                FROM readings
                WHERE city = %s AND timestamp < %s
                ORDER BY timestamp DESC
                LIMIT 1;
                """,
                (city, timestamp),
            )

            row = cur.fetchone()

    if row is None:
        return None

    return {
        "id": row[0],
        "city": row[1],
        "timestamp": row[2].isoformat(),
        "temperature_2m": row[3],
        "apparent_temperature": row[4],
        "precipitation": row[5],
        "wind_speed_10m": row[6],
        "weather_code": row[7],
        "created_at": row[8].isoformat(),
    }