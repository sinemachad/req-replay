"""Tests for req_replay.rate."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from req_replay.models import CapturedRequest
from req_replay.rate import analyze_rate, RateWindow


def _req(ts: datetime, method: str = "GET") -> CapturedRequest:
    return CapturedRequest(
        id="test-id",
        timestamp=ts,
        method=method,
        url="http://example.com/",
        headers={},
        body=None,
        tags=[],
    )


DT = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


def _dt(seconds: float) -> datetime:
    from datetime import timedelta
    return DT + timedelta(seconds=seconds)


def test_empty_returns_no_windows():
    assert analyze_rate([]) == []


def test_single_request_creates_one_window():
    windows = analyze_rate([_req(_dt(0))], window_seconds=60)
    assert len(windows) == 1
    assert windows[0].count == 1


def test_requests_within_window_grouped():
    reqs = [_req(_dt(i)) for i in range(5)]
    windows = analyze_rate(reqs, window_seconds=60)
    assert len(windows) == 1
    assert windows[0].count == 5


def test_requests_across_windows_split():
    reqs = [_req(_dt(0)), _req(_dt(30)), _req(_dt(61)), _req(_dt(90))]
    windows = analyze_rate(reqs, window_seconds=60)
    assert len(windows) == 2
    assert windows[0].count == 2
    assert windows[1].count == 2


def test_method_counts_tracked():
    reqs = [
        _req(_dt(0), "GET"),
        _req(_dt(1), "POST"),
        _req(_dt(2), "GET"),
    ]
    windows = analyze_rate(reqs, window_seconds=60)
    assert windows[0].methods["GET"] == 2
    assert windows[0].methods["POST"] == 1


def test_requests_per_second():
    reqs = [_req(_dt(i)) for i in range(60)]
    windows = analyze_rate(reqs, window_seconds=60)
    rps = windows[0].requests_per_second
    assert rps > 0


def test_requests_per_minute():
    reqs = [_req(_dt(i)) for i in range(60)]
    windows = analyze_rate(reqs, window_seconds=60)
    assert windows[0].requests_per_minute == pytest.approx(windows[0].requests_per_second * 60)


def test_summary_contains_count():
    w = RateWindow(start=_dt(0), end=_dt(60), count=10, methods={"GET": 10})
    assert "count=10" in w.summary()


def test_unsorted_input_is_handled():
    reqs = [_req(_dt(30)), _req(_dt(0)), _req(_dt(15))]
    windows = analyze_rate(reqs, window_seconds=60)
    assert windows[0].count == 3
