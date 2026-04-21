"""Tests for req_replay.header_order."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from req_replay.models import CapturedRequest
from req_replay.header_order import (
    analyze_header_order,
    summarize_header_orders,
    HeaderOrderResult,
    HeaderOrderStats,
)


def _req(headers: dict, req_id: str = "req-1") -> CapturedRequest:
    return CapturedRequest(
        id=req_id,
        method="GET",
        url="https://example.com/api",
        headers=headers,
        body=None,
        timestamp=datetime.now(timezone.utc),
        tags=[],
        metadata={},
    )


def test_canonical_order_detected():
    req = _req({"accept": "*/*", "content-type": "application/json", "x-request-id": "abc"})
    result = analyze_header_order(req)
    assert result.is_canonical
    assert result.deviations == []


def test_non_canonical_order_detected():
    # 'z-header' before 'a-header' is not sorted
    req = _req({"z-header": "1", "a-header": "2"})
    result = analyze_header_order(req)
    assert not result.is_canonical
    assert len(result.deviations) > 0


def test_ordered_keys_are_lowercased():
    req = _req({"Content-Type": "application/json", "Accept": "*/*"})
    result = analyze_header_order(req)
    assert all(k == k.lower() for k in result.ordered_keys)


def test_canonical_keys_are_sorted():
    req = _req({"z": "1", "a": "2", "m": "3"})
    result = analyze_header_order(req)
    assert result.canonical_keys == sorted(result.canonical_keys)


def test_display_contains_request_id():
    req = _req({"accept": "*/*"}, req_id="my-req-42")
    result = analyze_header_order(req)
    assert "my-req-42" in result.display()


def test_display_canonical_shows_checkmark():
    req = _req({"accept": "*/*", "content-type": "text/plain"})
    result = analyze_header_order(req)
    assert "✓" in result.display()


def test_display_non_canonical_shows_cross():
    req = _req({"z": "1", "a": "2"})
    result = analyze_header_order(req)
    assert "✗" in result.display() or "non-canonical" in result.display()


def test_empty_headers_is_canonical():
    req = _req({})
    result = analyze_header_order(req)
    assert result.is_canonical
    assert result.ordered_keys == []


def test_summarize_empty_list_returns_zero_stats():
    stats = summarize_header_orders([])
    assert stats.total == 0
    assert stats.canonical_count == 0
    assert stats.non_canonical_count == 0


def test_summarize_counts_canonical_correctly():
    r1 = _req({"a": "1", "b": "2"}, "r1")  # canonical
    r2 = _req({"z": "1", "a": "2"}, "r2")  # non-canonical
    stats = summarize_header_orders([r1, r2])
    assert stats.total == 2
    assert stats.canonical_count == 1
    assert stats.non_canonical_count == 1


def test_summarize_display_contains_totals():
    r1 = _req({"a": "1"}, "r1")
    stats = summarize_header_orders([r1])
    output = stats.display()
    assert "1" in output
    assert "100.0%" in output


def test_summarize_most_common_order():
    r1 = _req({"a": "1", "b": "2"}, "r1")
    r2 = _req({"a": "1", "b": "2"}, "r2")
    r3 = _req({"b": "2", "a": "1"}, "r3")
    stats = summarize_header_orders([r1, r2, r3])
    assert stats.most_common_order == ["a", "b"]
