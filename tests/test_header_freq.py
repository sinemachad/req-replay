"""Tests for req_replay.header_freq."""
from __future__ import annotations

from req_replay.header_freq import analyze_header_freq
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
    stats = analyze_header_freq([])
    assert stats.total_requests == 0
    assert stats.header_counts == {}


def test_single_request_counts_headers():
    req = _req({"Content-Type": "application/json", "Authorization": "Bearer tok"})
    stats = analyze_header_freq([req])
    assert stats.total_requests == 1
    assert stats.header_counts["content-type"] == 1
    assert stats.header_counts["authorization"] == 1


def test_header_keys_normalised_to_lowercase():
    req = _req({"X-Custom-Header": "val"})
    stats = analyze_header_freq([req])
    assert "x-custom-header" in stats.header_counts
    assert "X-Custom-Header" not in stats.header_counts


def test_frequency_counts_multiple_requests():
    r1 = _req({"accept": "application/json"})
    r2 = _req({"accept": "text/html"})
    r3 = _req({"content-type": "application/json"})
    stats = analyze_header_freq([r1, r2, r3])
    assert stats.header_counts["accept"] == 2
    assert stats.header_counts["content-type"] == 1


def test_coverage_calculation():
    r1 = _req({"accept": "*/*"})
    r2 = _req({"content-type": "application/json"})
    stats = analyze_header_freq([r1, r2])
    assert stats.coverage("accept") == 0.5
    assert stats.coverage("content-type") == 0.5
    assert stats.coverage("x-missing") == 0.0


def test_top_headers_ordered_by_count():
    r1 = _req({"a": "1", "b": "2"})
    r2 = _req({"a": "1"})
    stats = analyze_header_freq([r1, r2])
    top = stats.top_headers(2)
    assert top[0][0] == "a"
    assert top[0][1] == 2


def test_top_values_returns_most_common():
    r1 = _req({"accept": "application/json"})
    r2 = _req({"accept": "application/json"})
    r3 = _req({"accept": "text/html"})
    stats = analyze_header_freq([r1, r2, r3])
    vals = stats.top_values("accept", 2)
    assert vals[0] == ("application/json", 2)
    assert vals[1] == ("text/html", 1)


def test_top_values_unknown_header_returns_empty():
    stats = analyze_header_freq([_req({"x-real": "1"})])
    assert stats.top_values("x-missing") == []


def test_display_contains_header_names():
    req = _req({"authorization": "Bearer tok", "content-type": "application/json"})
    stats = analyze_header_freq([req])
    out = stats.display()
    assert "authorization" in out
    assert "content-type" in out


def test_duplicate_header_keys_counted_once_per_request():
    # headers dict can't have true duplicates, but ensure one entry per request
    r1 = _req({"accept": "*/*"})
    r2 = _req({"accept": "*/*"})
    stats = analyze_header_freq([r1, r2])
    assert stats.header_counts["accept"] == 2
