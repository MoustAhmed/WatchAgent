import json
import subprocess
import sys


def test_analyze_weather_data_skill_runs(clean_db):
    result = subprocess.run(
        [sys.executable, ".cursor/skills/analyze_weather_data.py"],
        capture_output=True,
        text=True,
        check=True,
    )

    data = json.loads(result.stdout)

    assert "total_readings" in data
    assert "total_events" in data
    assert "readings_by_city" in data
    assert "events_by_type" in data
    assert "average_event_score" in data