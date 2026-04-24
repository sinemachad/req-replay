"""Tests for req_replay.header_merge."""
from __future__ import annotations

import pytest

from req_replay.header_merge import merge_headers, MergeResult
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


def test_empty_list_returns_empty_merge():
    result = merge_headers([])
    assert result.merged == {}
    assert result.conflicts == {}
    assert result.sources == 0


def test_single_request_returns_all_headers():
    req = _req({"Content-Type": "application/json", "Accept": "*/*"})
    result = merge_headers([req])
    assert result.merged == {"content-type": "application/json", "accept": "*/*"}
    assert not result.has_conflicts


def test_keys_normalised_to_lowercase():
    req = _req({"X-Custom-Header": "value"})
    result = merge_headers([req])
    assert "x-custom-header" in result.merged


def test_no_conflict_when_values_identical():
    r1 = _req({"Accept": "application/json"})
    r2 = _req({"Accept": "application/json"})
    result = merge_headers([r1, r2])
    assert not result.has_conflicts
    assert result.merged["accept"] == "application/json"


def test_strategy_first_keeps_first_value():
    r1 = _req({"Accept": "text/html"})
    r2 = _req({"Accept": "application/json"})
    result = merge_headers([r1, r2], strategy="first")
    assert result.merged["accept"] == "text/html"


def test_strategy_last_keeps_last_value():
    r1 = _req({"Accept": "text/html"})
    r2 = _req({"Accept": "application/json"})
    result = merge_headers([r1, r2], strategy="last")
    assert result.merged["accept"] == "application/json"


def test_strategy_last_records_conflict():
    r1 = _req({"Accept": "text/html"})
    r2 = _req({"Accept": "application/json"})
    result = merge_headers([r1, r2], strategy="last")
    assert "accept" in result.conflicts


def test_strategy_union_records_conflict_without_changing_value():
    r1 = _req({"Accept": "text/html"})
    r2 = _req({"Accept": "application/json"})
    result = merge_headers([r1, r2], strategy="union")
    assert result.has_conflicts
    assert set(result.conflicts["accept"]) == {"text/html", "application/json"}


def test_extra_headers_injected():
    req = _req({"Accept": "*/*"})
    result = merge_headers([req], extra={"X-Trace-Id": "abc123"})
    assert result.merged["x-trace-id"] == "abc123"


def test_extra_headers_overwrite_merged():
    req = _req({"Accept": "text/html"})
    result = merge_headers([req], extra={"Accept": "application/json"})
    assert result.merged["accept"] == "application/json"


def test_invalid_strategy_raises():
    with pytest.raises(ValueError, match="Unknown strategy"):
        merge_headers([], strategy="bogus")


def test_display_contains_source_count():
    r1 = _req({"A": "1"})
    r2 = _req({"A": "2"})
    result = merge_headers([r1, r2], strategy="union")
    assert "2 request" in result.display()


def test_display_no_conflicts_message():
    req = _req({"Accept": "*/*"})
    result = merge_headers([req])
    assert "No conflicts" in result.display()
