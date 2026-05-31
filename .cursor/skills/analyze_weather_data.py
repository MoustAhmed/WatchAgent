# query DB and output JSON.

import json
import os
from typing import Any

import psycopg


DEFAULT_DATABASE_URL = "postgresql://watchagent:watchagent@127.0.0.1:5433/watchagent?connect_timeout=5"


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


def rows_to_dict(rows: list[tuple[Any, ...]]) -> dict[str, int]:
    return {str(row[0]): int(row[1]) for row in rows}


def analyze_weather_data() -> dict[str, Any]:
    database_url = get_database_url()

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM readings;")
            total_readings = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM events;")
            total_events = cur.fetchone()[0]

            cur.execute(
                """
                SELECT city, COUNT(*)
                FROM readings
                GROUP BY city
                ORDER BY city;
                """
            )
            readings_by_city = rows_to_dict(cur.fetchall())

            cur.execute(
                """
                SELECT city, COUNT(*)
                FROM events
                GROUP BY city
                ORDER BY city;
                """
            )
            events_by_city = rows_to_dict(cur.fetchall())

            cur.execute(
                """
                SELECT event_type, COUNT(*)
                FROM events
                GROUP BY event_type
                ORDER BY event_type;
                """
            )
            events_by_type = rows_to_dict(cur.fetchall())

            cur.execute(
                """
                SELECT DISTINCT ON (city)
                       city, timestamp, temperature_2m, apparent_temperature,
                       precipitation, wind_speed_10m, weather_code
                FROM readings
                ORDER BY city, timestamp DESC;
                """
            )
            latest_readings = cur.fetchall()

            cur.execute(
                """
                SELECT city, timestamp, wind_speed_10m
                FROM readings
                ORDER BY wind_speed_10m DESC
                LIMIT 1;
                """
            )
            highest_wind = cur.fetchone()

            cur.execute(
                """
                SELECT city, timestamp, temperature_2m, apparent_temperature,
                       ABS(apparent_temperature - temperature_2m) AS gap
                FROM readings
                ORDER BY gap DESC
                LIMIT 1;
                """
            )
            largest_gap = cur.fetchone()

            cur.execute(
                """
                SELECT AVG(score)
                FROM events
                WHERE score IS NOT NULL;
                """
            )
            average_score = cur.fetchone()[0]

    return {
        "total_readings": int(total_readings),
        "total_events": int(total_events),
        "readings_by_city": readings_by_city,
        "events_by_city": events_by_city,
        "events_by_type": events_by_type,
        "latest_readings_by_city": [
            {
                "city": row[0],
                "timestamp": row[1].isoformat(),
                "temperature_2m": row[2],
                "apparent_temperature": row[3],
                "precipitation": row[4],
                "wind_speed_10m": row[5],
                "weather_code": row[6],
            }
            for row in latest_readings
        ],
        "highest_wind_reading": None
        if highest_wind is None
        else {
            "city": highest_wind[0],
            "timestamp": highest_wind[1].isoformat(),
            "wind_speed_10m": highest_wind[2],
        },
        "largest_apparent_temperature_gap": None
        if largest_gap is None
        else {
            "city": largest_gap[0],
            "timestamp": largest_gap[1].isoformat(),
            "temperature_2m": largest_gap[2],
            "apparent_temperature": largest_gap[3],
            "gap": largest_gap[4],
        },
        "average_event_score": None if average_score is None else float(average_score),
    }


if __name__ == "__main__":
    try:
        print(json.dumps(analyze_weather_data(), indent=2))
    except Exception as exc:
        print(
            json.dumps(
                {
                    "error": str(exc),
                    "hint": "Start the database container and set DATABASE_URL before running this skill.",
                },
                indent=2,
            )
        )
        raise