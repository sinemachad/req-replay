"""Tests for req_replay.timeout."""
from __future__ import annotations

import pytest

from req_replay.models import CapturedRequest, CapturedResponse
from req_replay.timeout import TimeoutStats, _duration_ms, analyze_timeouts


def _req(url: str = "http://example.com", duration_ms: float | None = None) -> CapturedRequest:
    meta = {}
    if duration_ms is not None:
        meta["duration_ms"] = duration_ms
    return CapturedRequest(
        id="test-id",
        method="GET",
        url=url,
        headers={},
        body=None,
        metadata=meta,
    )


def _resp() -> CapturedResponse:
    return CapturedResponse(status_code=200, headers={}, body=None)


def test_empty_pairs_returns_zero_stats():
    stats = analyze_timeouts([])
    assert stats.total == 0
    assert stats.timed_out == 0
    assert stats.timeout_rate == 0.0
    assert stats.slowest_ms is None


def test_no_duration_metadata_excluded():
    pairs = [(_req(), _resp()), (_req(), _resp())]
    stats = analyze_timeouts(pairs, threshold_ms=1000.0)
    assert stats.total == 2
    assert stats.timed_out == 0
    assert stats.slowest_ms is None


def test_single_fast_request_not_timed_out():
    pairs = [(_req(duration_ms=200.0), _resp())]
    stats = analyze_timeouts(pairs, threshold_ms=1000.0)
    assert stats.timed_out == 0
    assert stats.timeout_rate == 0.0


def test_single_slow_request_timed_out():
    pairs = [(_req(url="http://slow.com", duration_ms=6000.0), _resp())]
    stats = analyze_timeouts(pairs, threshold_ms=5000.0)
    assert stats.timed_out == 1
    assert stats.timeout_rate == pytest.approx(1.0)
    assert stats.slowest_url == "http://slow.com"
    assert stats.slowest_ms == pytest.approx(6000.0)


def test_mixed_requests_counts_correctly():
    pairs = [
        (_req(duration_ms=100.0), _resp()),
        (_req(duration_ms=7000.0), _resp()),
        (_req(duration_ms=3000.0), _resp()),
        (_req(duration_ms=9000.0), _resp()),
    ]
    stats = analyze_timeouts(pairs, threshold_ms=5000.0)
    assert stats.total == 4
    assert stats.timed_out == 2
    assert stats.timeout_rate == pytest.approx(0.5)


def test_slowest_url_is_tracked():
    pairs = [
        (_req(url="http://a.com", duration_ms=1000.0), _resp()),
        (_req(url="http://b.com", duration_ms=9999.0), _resp()),
        (_req(url="http://c.com", duration_ms=500.0), _resp()),
    ]
    stats = analyze_timeouts(pairs, threshold_ms=5000.0)
    assert stats.slowest_url == "http://b.com"
    assert stats.slowest_ms == pytest.approx(9999.0)


def test_display_contains_threshold():
    stats = analyze_timeouts([], threshold_ms=3000.0)
    assert "3000" in stats.display()


def test_duration_ms_helper_returns_none_when_missing():
    req = _req()
    assert _duration_ms(req) is None


def test_duration_ms_helper_returns_value():
    req = _req(duration_ms=1234.5)
    assert _duration_ms(req) == pytest.approx(1234.5)
