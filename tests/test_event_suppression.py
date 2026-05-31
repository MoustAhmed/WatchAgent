from app.poller import should_store_event


def test_same_event_is_suppressed_when_recent_severity_is_same():
    event = {
        "severity": "medium",
    }

    recent_event = {
        "severity": "medium",
    }

    assert should_store_event(event, recent_event) is False


def test_same_event_can_store_when_severity_increases():
    event = {
        "severity": "high",
    }

    recent_event = {
        "severity": "medium",
    }

    assert should_store_event(event, recent_event) is True


def test_event_stores_when_no_recent_event_exists():
    event = {
        "severity": "low",
    }

    assert should_store_event(event, None) is True