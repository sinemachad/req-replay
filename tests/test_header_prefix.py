"""Tests for req_replay.header_prefix."""
from __future__ import annotations

import pytest

from req_replay.header_prefix import (
    PrefixResult,
    find_by_prefix,
    strip_by_prefix,
    strip_request_headers_by_prefix,
)
from req_replay.models import CapturedRequest


def _req(headers: dict) -> CapturedRequest:
    return CapturedRequest(
        id="abc",
        method="GET",
        url="https://example.com/",
        headers=headers,
        body=None,
        timestamp="2024-01-01T00:00:00Z",
        tags=[],
        metadata={},
    )


# ---------------------------------------------------------------------------
# find_by_prefix
# ---------------------------------------------------------------------------

def test_find_no_match_returns_empty():
    headers = {"content-type": "application/json", "accept": "*/*"}
    assert find_by_prefix(headers, "x-") == {}


def test_find_matches_prefix_case_insensitive():
    headers = {"X-Request-Id": "123", "X-Trace-Id": "456", "Accept": "*/*"}
    result = find_by_prefix(headers, "x-")
    assert set(result.keys()) == {"X-Request-Id", "X-Trace-Id"}


def test_find_case_sensitive_no_match_when_case_differs():
    headers = {"X-Request-Id": "123"}
    result = find_by_prefix(headers, "x-", case_sensitive=True)
    assert result == {}


def test_find_case_sensitive_match():
    headers = {"x-custom": "val", "Accept": "*/*"}
    result = find_by_prefix(headers, "x-", case_sensitive=True)
    assert result == {"x-custom": "val"}


def test_find_returns_values_correctly():
    headers = {"x-foo": "bar", "x-baz": "qux"}
    result = find_by_prefix(headers, "x-")
    assert result["x-foo"] == "bar"
    assert result["x-baz"] == "qux"


# ---------------------------------------------------------------------------
# strip_by_prefix
# ---------------------------------------------------------------------------

def test_strip_removes_matching_headers():
    headers = {"x-foo": "1", "x-bar": "2", "content-type": "text/plain"}
    result = strip_by_prefix(headers, "x-")
    assert result.changed is True
    assert result.original_count == 3
    assert result.final_count == 1
    assert "x-foo" in result.stripped
    assert "x-bar" in result.stripped


def test_strip_no_match_not_changed():
    headers = {"content-type": "text/plain"}
    result = strip_by_prefix(headers, "x-")
    assert result.changed is False
    assert result.final_count == 1


def test_strip_empty_headers():
    result = strip_by_prefix({}, "x-")
    assert result.changed is False
    assert result.original_count == 0


# ---------------------------------------------------------------------------
# strip_request_headers_by_prefix
# ---------------------------------------------------------------------------

def test_strip_request_returns_new_object():
    req = _req({"x-custom": "val", "accept": "*/*"})
    new_req, result = strip_request_headers_by_prefix(req, "x-")
    assert new_req is not req
    assert "x-custom" not in new_req.headers
    assert "accept" in new_req.headers


def test_strip_request_does_not_mutate_original():
    req = _req({"x-custom": "val"})
    strip_request_headers_by_prefix(req, "x-")
    assert "x-custom" in req.headers


def test_strip_request_preserves_id_and_metadata():
    req = _req({"x-foo": "bar"})
    new_req, _ = strip_request_headers_by_prefix(req, "x-")
    assert new_req.id == req.id
    assert new_req.method == req.method
    assert new_req.url == req.url


# ---------------------------------------------------------------------------
# PrefixResult.display
# ---------------------------------------------------------------------------

def test_display_contains_counts():
    result = PrefixResult(
        matched={"x-foo": "bar"},
        stripped={"x-foo": "bar"},
        original_count=3,
        final_count=2,
    )
    text = result.display()
    assert "3" in text
    assert "2" in text
    assert "x-foo" in text


def test_display_no_stripped_omits_removed_section():
    result = PrefixResult(original_count=2, final_count=2)
    text = result.display()
    assert "Removed" not in text
