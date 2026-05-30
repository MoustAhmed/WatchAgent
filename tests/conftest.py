import pytest

from app.db import get_conn, init_db


@pytest.fixture()
def clean_db():
    init_db()

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE events, readings RESTART IDENTITY CASCADE;")

    yield

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE events, readings RESTART IDENTITY CASCADE;")