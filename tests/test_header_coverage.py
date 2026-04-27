"""Tests for req_replay.header_coverage."""
from __future__ import annotations

import pytest

from req_replay.header_coverage import analyze_header_coverage, HeaderCoverageStats
from req_replay.models import CapturedRequest


def _req(headers: dict) -> CapturedRequest:
    return CapturedRequest(
        id="test",
        method="GET",
        url="https://example.com/",
        headers=headers,
        body=None,
        timestamp="2024-01-01T00:00:00",
        tags=[],
        metadata={},
    )


def test_empty_list_returns_zero_stats():
    stats = analyze_header_coverage([])
    assert stats.total_requests == 0
    assert stats.header_presence == {}
    assert stats.header_coverage == {}


def test_single_request_counts_all_headers():
    req = _req({"Content-Type": "application/json", "Accept": "*/*"})
    stats = analyze_header_coverage([req])
    assert stats.total_requests == 1
    assert stats.header_presence["content-type"] == 1
    assert stats.header_presence["accept"] == 1


def test_header_keys_normalised_to_lowercase():
    req = _req({"X-Custom-Header": "value"})
    stats = analyze_header_coverage([req])
    assert "x-custom-header" in stats.header_presence
    assert "X-Custom-Header" not in stats.header_presence


def test_coverage_percentage_calculated():
    reqs = [
        _req({"authorization": "Bearer tok"}),
        _req({"authorization": "Bearer tok", "accept": "*/*"}),
    ]
    stats = analyze_header_coverage(reqs)
    assert stats.header_coverage["authorization"] == pytest.approx(100.0)
    assert stats.header_coverage["accept"] == pytest.approx(50.0)


def test_multiple_requests_same_header_counted_once_per_request():
    # Even if a request has duplicate keys (dict won't, but guard against it)
    reqs = [
        _req({"x-trace": "a"}),
        _req({"x-trace": "b"}),
        _req({"x-trace": "c"}),
    ]
    stats = analyze_header_coverage(reqs)
    assert stats.header_presence["x-trace"] == 3
    assert stats.header_coverage["x-trace"] == pytest.approx(100.0)


def test_top_returns_most_common_headers():
    reqs = [
        _req({"a": "1", "b": "2", "c": "3"}),
        _req({"a": "1", "b": "2"}),
        _req({"a": "1"}),
    ]
    stats = analyze_header_coverage(reqs)
    top = stats.top(2)
    assert top[0] == "a"
    assert top[1] == "b"


def test_missing_from_returns_absent_headers():
    reqs = [
        _req({"content-type": "application/json", "accept": "*/*"}),
        _req({"content-type": "text/plain"}),
    ]
    stats = analyze_header_coverage(reqs)
    sparse = _req({"content-type": "application/json"})
    missing = stats.missing_from(sparse)
    assert "accept" in missing
    assert "content-type" not in missing


def test_missing_from_returns_empty_when_all_present():
    reqs = [_req({"content-type": "application/json"})]
    stats = analyze_header_coverage(reqs)
    full = _req({"content-type": "text/html", "accept": "*/*"})
    assert stats.missing_from(full) == []


def test_display_contains_header_names():
    reqs = [_req({"x-request-id": "abc"})]
    stats = analyze_header_coverage(reqs)
    output = stats.display()
    assert "x-request-id" in output
    assert "100.0%" in output


def test_display_empty_store():
    stats = analyze_header_coverage([])
    output = stats.display()
    assert "No headers found" in output
