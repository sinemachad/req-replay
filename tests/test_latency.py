"""Tests for req_replay.latency."""
from __future__ import annotations

import pytest

from req_replay.latency import analyze_latency, _percentile
from req_replay.models import CapturedRequest


def _req(duration_ms: float | None = None) -> CapturedRequest:
    meta = {}
    if duration_ms is not None:
        meta["duration_ms"] = duration_ms
    return CapturedRequest(
        id="test",
        method="GET",
        url="http://example.com",
        headers={},
        body=None,
        timestamp="2024-01-01T00:00:00",
        tags=[],
        metadata=meta,
    )


def test_empty_list_returns_none():
    assert analyze_latency([]) is None


def test_no_duration_metadata_returns_none():
    assert analyze_latency([_req()]) is None


def test_single_sample_stats():
    result = analyze_latency([_req(100.0)])
    assert result is not None
    assert result.count == 1
    assert result.min_ms == 100.0
    assert result.max_ms == 100.0
    assert result.mean_ms == 100.0
    assert result.stdev_ms is None


def test_multiple_samples_min_max():
    reqs = [_req(10.0), _req(50.0), _req(90.0)]
    result = analyze_latency(reqs)
    assert result.min_ms == 10.0
    assert result.max_ms == 90.0


def test_mean_and_median():
    reqs = [_req(10.0), _req(20.0), _req(30.0)]
    result = analyze_latency(reqs)
    assert result.mean_ms == pytest.approx(20.0)
    assert result.median_ms == pytest.approx(20.0)


def test_stdev_computed_for_multiple():
    reqs = [_req(10.0), _req(20.0), _req(30.0)]
    result = analyze_latency(reqs)
    assert result.stdev_ms is not None
    assert result.stdev_ms > 0


def test_p95_within_range():
    reqs = [_req(float(i)) for i in range(1, 101)]
    result = analyze_latency(reqs)
    assert 94.0 <= result.p95_ms <= 100.0


def test_non_numeric_duration_ignored():
    r = _req()
    r.metadata["duration_ms"] = "fast"
    result = analyze_latency([r, _req(50.0)])
    assert result.count == 1


def test_display_contains_mean():
    result = analyze_latency([_req(42.0), _req(58.0)])
    assert "Mean" in result.display()
    assert "50.0" in result.display()


def test_percentile_empty():
    assert _percentile([], 0.95) == 0.0
