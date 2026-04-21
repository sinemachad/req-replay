"""Tests for req_replay.header_count."""
from __future__ import annotations

import pytest

from req_replay.header_count import analyze_header_counts, HeaderCountStats
from req_replay.models import CapturedRequest


def _req(headers: dict) -> CapturedRequest:
    return CapturedRequest(
        id="test-id",
        method="GET",
        url="https://example.com/api",
        headers=headers,
        body=None,
        metadata={},
        tags=[],
    )


def test_empty_list_returns_zero_stats():
    result = analyze_header_counts([])
    assert result.total_requests == 0
    assert result.min_headers is None
    assert result.max_headers is None
    assert result.avg_headers == 0.0
    assert result.over_threshold == 0


def test_single_request_counted():
    req = _req({"content-type": "application/json", "accept": "*/*"})
    result = analyze_header_counts([req])
    assert result.total_requests == 1
    assert result.min_headers == 2
    assert result.max_headers == 2
    assert result.avg_headers == pytest.approx(2.0)


def test_multiple_requests_min_max():
    r1 = _req({"a": "1"})
    r2 = _req({"a": "1", "b": "2", "c": "3"})
    result = analyze_header_counts([r1, r2])
    assert result.min_headers == 1
    assert result.max_headers == 3
    assert result.avg_headers == pytest.approx(2.0)


def test_over_threshold_counted():
    headers_many = {str(i): str(i) for i in range(25)}
    headers_few = {"a": "1"}
    result = analyze_header_counts(
        [_req(headers_many), _req(headers_few)],
        threshold=20,
    )
    assert result.over_threshold == 1


def test_none_over_threshold_when_all_under():
    req = _req({"a": "1", "b": "2"})
    result = analyze_header_counts([req], threshold=10)
    assert result.over_threshold == 0


def test_distribution_keys_match_counts():
    r1 = _req({"a": "1"})
    r2 = _req({"a": "1"})
    r3 = _req({"a": "1", "b": "2"})
    result = analyze_header_counts([r1, r2, r3])
    assert result.distribution[1] == 2
    assert result.distribution[2] == 1


def test_display_empty():
    result = analyze_header_counts([])
    assert "No requests" in result.display()


def test_display_contains_fields():
    req = _req({"x-request-id": "abc", "authorization": "Bearer tok"})
    result = analyze_header_counts([req])
    output = result.display()
    assert "Total requests" in output
    assert "Min headers" in output
    assert "Max headers" in output
    assert "Avg headers" in output
