"""Tests for req_replay.timeline."""

from datetime import datetime, timezone

import pytest

from req_replay.models import CapturedRequest
from req_replay.timeline import TimelineBucket, build_timeline, _bucket_label


def _req(method: str, ts: str) -> CapturedRequest:
    return CapturedRequest(
        id=ts,
        method=method,
        url="https://example.com/api",
        headers={},
        body=None,
        timestamp=datetime.fromisoformat(ts).replace(tzinfo=timezone.utc),
    )


# ---------------------------------------------------------------------------
# _bucket_label
# ---------------------------------------------------------------------------

def test_bucket_label_minute():
    ts = datetime(2024, 1, 15, 14, 5, 30, tzinfo=timezone.utc)
    assert _bucket_label(ts, "minute") == "2024-01-15 14:05"


def test_bucket_label_hour():
    ts = datetime(2024, 1, 15, 14, 5, 30, tzinfo=timezone.utc)
    assert _bucket_label(ts, "hour") == "2024-01-15 14:00"


def test_bucket_label_day():
    ts = datetime(2024, 1, 15, 14, 5, 30, tzinfo=timezone.utc)
    assert _bucket_label(ts, "day") == "2024-01-15"


def test_bucket_label_invalid_granularity():
    ts = datetime(2024, 1, 15, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="Unknown granularity"):
        _bucket_label(ts, "week")


# ---------------------------------------------------------------------------
# TimelineBucket helpers
# ---------------------------------------------------------------------------

def test_bucket_count_and_methods():
    reqs = [_req("GET", "2024-01-15T10:00:00"), _req("POST", "2024-01-15T10:00:30")]
    bucket = TimelineBucket(label="2024-01-15 10:00", requests=reqs)
    assert bucket.count == 2
    assert bucket.methods == {"GET": 1, "POST": 1}


def test_bucket_summary_format():
    reqs = [_req("GET", "2024-01-15T10:00:00"), _req("GET", "2024-01-15T10:00:10")]
    bucket = TimelineBucket(label="2024-01-15 10:00", requests=reqs)
    summary = bucket.summary()
    assert "2024-01-15 10:00" in summary
    assert "2" in summary
    assert "GET:2" in summary


# ---------------------------------------------------------------------------
# build_timeline
# ---------------------------------------------------------------------------

def test_build_timeline_groups_by_minute():
    reqs = [
        _req("GET", "2024-01-15T10:00:05"),
        _req("POST", "2024-01-15T10:00:55"),
        _req("DELETE", "2024-01-15T10:01:10"),
    ]
    timeline = build_timeline(reqs, granularity="minute")
    assert len(timeline) == 2
    assert timeline[0].label == "2024-01-15 10:00"
    assert timeline[0].count == 2
    assert timeline[1].label == "2024-01-15 10:01"
    assert timeline[1].count == 1


def test_build_timeline_groups_by_hour():
    reqs = [
        _req("GET", "2024-01-15T09:45:00"),
        _req("GET", "2024-01-15T10:15:00"),
        _req("GET", "2024-01-15T10:55:00"),
    ]
    timeline = build_timeline(reqs, granularity="hour")
    assert len(timeline) == 2
    assert timeline[0].count == 1
    assert timeline[1].count == 2


def test_build_timeline_empty_input():
    assert build_timeline([]) == []


def test_build_timeline_filters_by_start_end():
    reqs = [
        _req("GET", "2024-01-15T08:00:00"),
        _req("GET", "2024-01-15T10:00:00"),
        _req("GET", "2024-01-15T12:00:00"),
    ]
    start = datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc)
    end = datetime(2024, 1, 15, 11, 0, tzinfo=timezone.utc)
    timeline = build_timeline(reqs, granularity="hour", start=start, end=end)
    assert len(timeline) == 1
    assert timeline[0].label == "2024-01-15 10:00"


def test_build_timeline_sorted_labels():
    reqs = [
        _req("GET", "2024-01-15T12:00:00"),
        _req("GET", "2024-01-15T08:00:00"),
        _req("GET", "2024-01-15T10:00:00"),
    ]
    timeline = build_timeline(reqs, granularity="hour")
    labels = [b.label for b in timeline]
    assert labels == sorted(labels)
