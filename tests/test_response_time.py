"""Tests for req_replay.response_time."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import pytest

from req_replay.models import CapturedRequest
from req_replay.response_time import (
    ResponseTimeBucket,
    ResponseTimeReport,
    _duration_ms,
    analyze_response_times,
)


def _req(duration_ms: Optional[float] = None, method: str = "GET") -> CapturedRequest:
    meta = {}
    if duration_ms is not None:
        meta["duration_ms"] = duration_ms
    return CapturedRequest(
        id="test-id",
        method=method,
        url="https://example.com/api",
        headers={},
        body=None,
        timestamp=datetime.now(timezone.utc).isoformat(),
        tags=[],
        metadata=meta,
    )


def test_duration_ms_from_metadata():
    req = _req(duration_ms=250.0)
    assert _duration_ms(req) == 250.0


def test_duration_ms_missing_returns_none():
    req = _req()
    assert _duration_ms(req) is None


def test_duration_ms_elapsed_ms_fallback():
    req = _req()
    req.metadata["elapsed_ms"] = 120
    assert _duration_ms(req) == 120.0


def test_empty_list_returns_zero_totals():
    report = analyze_response_times([])
    assert report.total == 0
    assert report.skipped == 0
    assert all(b.count == 0 for b in report.buckets)


def test_no_duration_metadata_skipped():
    req = _req()
    report = analyze_response_times([req])
    assert report.skipped == 1
    assert report.total == 0


def test_fast_request_in_first_bucket():
    req = _req(duration_ms=50.0)
    report = analyze_response_times([req])
    assert report.buckets[0].label == "<100ms"
    assert report.buckets[0].count == 1
    assert "test-id" in report.buckets[0].request_ids


def test_slow_request_in_last_bucket():
    req = _req(duration_ms=1500.0)
    report = analyze_response_times([req])
    last = report.buckets[-1]
    assert last.label == ">1s"
    assert last.count == 1


def test_multiple_requests_distributed():
    reqs = [
        _req(50),
        _req(150),
        _req(400),
        _req(750),
        _req(2000),
    ]
    report = analyze_response_times(reqs)
    assert report.total == 5
    counts = [b.count for b in report.buckets]
    assert counts == [1, 1, 1, 1, 1]


def test_display_contains_bucket_labels():
    reqs = [_req(50), _req(200)]
    report = analyze_response_times(reqs)
    text = report.display()
    assert "<100ms" in text
    assert "100-300ms" in text


def test_bucket_to_dict_structure():
    b = ResponseTimeBucket(label="<100ms", min_ms=0, max_ms=100, count=3, request_ids=["a", "b", "c"])
    d = b.to_dict()
    assert d["label"] == "<100ms"
    assert d["count"] == 3
    assert len(d["request_ids"]) == 3
