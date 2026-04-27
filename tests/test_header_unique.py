"""Tests for req_replay.header_unique."""
from __future__ import annotations

import pytest

from req_replay.models import CapturedRequest
from req_replay.header_unique import (
    analyze_unique_headers,
    UniqueHeaderStats,
    UniqueHeaderResult,
)


def _req(id_: str, headers: dict) -> CapturedRequest:
    return CapturedRequest(
        id=id_,
        method="GET",
        url="https://example.com/",
        headers=headers,
        body=None,
        timestamp="2024-01-01T00:00:00",
        tags=[],
        metadata={},
    )


def test_empty_list_returns_zero_stats():
    result = analyze_unique_headers([])
    assert result.total_requests == 0
    assert result.total_unique_headers == 0
    assert result.results == []


def test_single_request_all_headers_are_unique():
    req = _req("r1", {"X-Custom": "foo", "Authorization": "Bearer abc"})
    result = analyze_unique_headers([req])
    assert result.total_requests == 1
    assert result.total_unique_headers == 2
    assert len(result.results) == 1
    assert set(result.results[0].unique_headers) == {"x-custom", "authorization"}


def test_shared_header_not_flagged():
    r1 = _req("r1", {"Content-Type": "application/json", "X-Only-In-R1": "yes"})
    r2 = _req("r2", {"Content-Type": "text/plain"})
    result = analyze_unique_headers([r1, r2])
    # content-type appears in both — not unique
    # x-only-in-r1 appears only in r1 — unique
    assert result.total_unique_headers == 1
    assert len(result.results) == 1
    assert result.results[0].request_id == "r1"
    assert result.results[0].unique_headers == ["x-only-in-r1"]


def test_no_unique_headers_returns_empty_results():
    r1 = _req("r1", {"Accept": "*/*"})
    r2 = _req("r2", {"Accept": "application/json"})
    result = analyze_unique_headers([r1, r2])
    assert result.total_unique_headers == 0
    assert result.results == []


def test_unique_headers_sorted_alphabetically():
    req = _req("r1", {"Z-Header": "z", "A-Header": "a", "M-Header": "m"})
    result = analyze_unique_headers([req])
    assert result.results[0].unique_headers == ["a-header", "m-header", "z-header"]


def test_header_keys_normalised_case_insensitive():
    r1 = _req("r1", {"Content-Type": "application/json"})
    r2 = _req("r2", {"content-type": "text/html"})
    # Both map to 'content-type' — not unique
    result = analyze_unique_headers([r1, r2])
    assert result.total_unique_headers == 0
    assert result.results == []


def test_multiple_unique_headers_across_requests():
    r1 = _req("r1", {"X-Alpha": "1", "Shared": "yes"})
    r2 = _req("r2", {"X-Beta": "2", "Shared": "yes"})
    r3 = _req("r3", {"X-Gamma": "3", "Shared": "yes"})
    result = analyze_unique_headers([r1, r2, r3])
    assert result.total_unique_headers == 3
    assert len(result.results) == 3
    ids = {r.request_id for r in result.results}
    assert ids == {"r1", "r2", "r3"}


def test_display_contains_request_id():
    req = _req("abc123", {"X-Only": "value"})
    result = analyze_unique_headers([req])
    output = result.display()
    assert "abc123" in output
    assert "x-only" in output


def test_display_shows_totals():
    r1 = _req("r1", {"X-Unique": "u", "Common": "c"})
    r2 = _req("r2", {"Common": "c"})
    result = analyze_unique_headers([r1, r2])
    output = result.display()
    assert "2" in output  # total_requests
    assert "1" in output  # total_unique_headers


def test_to_dict_structure():
    r = UniqueHeaderResult(request_id="x1", unique_headers=["x-foo", "x-bar"])
    d = r.to_dict()
    assert d["request_id"] == "x1"
    assert d["unique_headers"] == ["x-foo", "x-bar"]
