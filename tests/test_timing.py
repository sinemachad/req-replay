"""Tests for req_replay.timing."""
import pytest
from req_replay.timing import analyze_timing, summarize_timings, TimingBreakdown
from req_replay.models import CapturedRequest
from datetime import datetime, timezone


def _req(metadata=None) -> CapturedRequest:
    return CapturedRequest(
        id="abc123",
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
        method="GET",
        url="https://example.com/api",
        headers={},
        body=None,
        tags=[],
        metadata=metadata or {},
    )


def test_analyze_timing_all_fields():
    req = _req({"timing": {"dns_ms": 5, "connect_ms": 10, "tls_ms": 20,
                            "send_ms": 1, "wait_ms": 80, "receive_ms": 4, "total_ms": 120}})
    bd = analyze_timing(req)
    assert bd.dns_ms == 5.0
    assert bd.connect_ms == 10.0
    assert bd.tls_ms == 20.0
    assert bd.total_ms == 120.0
    assert bd.request_id == "abc123"


def test_analyze_timing_missing_fields():
    req = _req({"timing": {"total_ms": 99}})
    bd = analyze_timing(req)
    assert bd.total_ms == 99.0
    assert bd.dns_ms is None
    assert bd.tls_ms is None


def test_analyze_timing_no_timing_key():
    req = _req({})
    bd = analyze_timing(req)
    assert bd.total_ms is None
    assert bd.dns_ms is None


def test_display_contains_labels():
    req = _req({"timing": {"total_ms": 55.5, "wait_ms": 40.0}})
    bd = analyze_timing(req)
    out = bd.display()
    assert "Total" in out
    assert "55.50 ms" in out
    assert "Wait" in out
    assert "n/a" in out  # missing fields


def test_summarize_timings_filters_no_timing():
    r1 = _req({"timing": {"total_ms": 10}})
    r2 = _req({})
    results = summarize_timings([r1, r2])
    assert len(results) == 1
    assert results[0].total_ms == 10.0


def test_summarize_timings_empty():
    assert summarize_timings([]) == []


def test_summarize_timings_all_have_timing():
    reqs = [_req({"timing": {"total_ms": i}}) for i in range(3)]
    results = summarize_timings(reqs)
    assert len(results) == 3
