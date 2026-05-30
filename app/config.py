import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://watchagent:watchagent@localhost:5432/watchagent"
)

POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "300"))