"""Tests for req_replay.header_size."""
from __future__ import annotations

import pytest

from req_replay.header_size import HeaderSizeStats, _header_bytes, analyze_header_sizes
from req_replay.models import CapturedRequest


def _req(
    req_id: str = "r1",
    headers: dict | None = None,
) -> CapturedRequest:
    return CapturedRequest(
        id=req_id,
        method="GET",
        url="https://example.com/api",
        headers=headers or {},
        body=None,
        timestamp="2024-01-01T00:00:00",
        tags=[],
        metadata={},
    )


def test_empty_list_returns_zero_stats():
    stats = analyze_header_sizes([])
    assert stats.total_requests == 0
    assert stats.min_bytes is None
    assert stats.max_bytes is None
    assert stats.mean_bytes == 0.0
    assert stats.over_threshold == 0


def test_single_request_counted():
    req = _req(headers={"content-type": "application/json"})
    stats = analyze_header_sizes([req])
    assert stats.total_requests == 1
    assert stats.min_bytes == stats.max_bytes
    assert stats.min_bytes is not None and stats.min_bytes > 0


def test_header_bytes_sums_key_and_value():
    req = _req(headers={"x-foo": "bar"})
    size = _header_bytes(req)
    # "x-foo" = 5 bytes, "bar" = 3 bytes
    assert size == 8


def test_header_bytes_empty_headers():
    req = _req(headers={})
    assert _header_bytes(req) == 0


def test_multiple_requests_min_max():
    small = _req("r1", headers={"a": "b"})
    large = _req("r2", headers={"authorization": "Bearer " + "x" * 200})
    stats = analyze_header_sizes([small, large])
    assert stats.min_bytes is not None
    assert stats.max_bytes is not None
    assert stats.min_bytes < stats.max_bytes


def test_over_threshold_counted():
    big_headers = {f"x-custom-header-{i}": "value" * 20 for i in range(20)}
    req = _req("r1", headers=big_headers)
    stats = analyze_header_sizes([req], threshold=100)
    assert stats.over_threshold == 1


def test_under_threshold_not_counted():
    req = _req(headers={"accept": "*/*"})
    stats = analyze_header_sizes([req], threshold=8192)
    assert stats.over_threshold == 0


def test_by_request_populated():
    req = _req("abc123", headers={"x-id": "1"})
    stats = analyze_header_sizes([req])
    assert "abc123" in stats.by_request
    assert stats.by_request["abc123"] > 0


def test_mean_bytes_correct():
    r1 = _req("r1", headers={"a": "bb"})
    r2 = _req("r2", headers={"cc": "d"})
    stats = analyze_header_sizes([r1, r2])
    expected_r1 = _header_bytes(r1)
    expected_r2 = _header_bytes(r2)
    assert stats.mean_bytes == pytest.approx((expected_r1 + expected_r2) / 2)
