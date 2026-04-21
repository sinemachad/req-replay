"""Tests for req_replay.header_diff."""
from __future__ import annotations

import pytest

from req_replay.header_diff import HeaderDiffResult, diff_headers
from req_replay.models import CapturedRequest


def _req(id_: str, headers: dict) -> CapturedRequest:
    return CapturedRequest(
        id=id_,
        method="GET",
        url="https://example.com/api",
        headers=headers,
        body=None,
        metadata={},
        tags=[],
    )


def test_identical_headers_are_identical():
    a = _req("a", {"Content-Type": "application/json", "Accept": "*/*"})
    b = _req("b", {"Content-Type": "application/json", "Accept": "*/*"})
    result = diff_headers(a, b)
    assert result.identical is True
    assert result.added == {}
    assert result.removed == {}
    assert result.changed == {}


def test_added_header_detected():
    a = _req("a", {"Accept": "*/*"})
    b = _req("b", {"Accept": "*/*", "X-Custom": "value"})
    result = diff_headers(a, b)
    assert "x-custom" in result.added
    assert result.added["x-custom"] == "value"
    assert result.identical is False


def test_removed_header_detected():
    a = _req("a", {"Accept": "*/*", "X-Old": "gone"})
    b = _req("b", {"Accept": "*/*"})
    result = diff_headers(a, b)
    assert "x-old" in result.removed
    assert result.removed["x-old"] == "gone"


def test_changed_header_detected():
    a = _req("a", {"Content-Type": "application/json"})
    b = _req("b", {"Content-Type": "text/plain"})
    result = diff_headers(a, b)
    assert "content-type" in result.changed
    assert result.changed["content-type"] == ("application/json", "text/plain")


def test_ignore_excludes_header():
    a = _req("a", {"Accept": "*/*", "X-Request-Id": "aaa"})
    b = _req("b", {"Accept": "*/*", "X-Request-Id": "bbb"})
    result = diff_headers(a, b, ignore={"X-Request-Id"})
    assert result.identical is True


def test_authorization_change_triggers_hd001():
    a = _req("a", {"Authorization": "Bearer old"})
    b = _req("b", {"Authorization": "Bearer new"})
    result = diff_headers(a, b)
    codes = [w.code for w in result.warnings]
    assert "HD001" in codes


def test_content_type_change_triggers_hd002():
    a = _req("a", {"Content-Type": "application/json"})
    b = _req("b", {"Content-Type": "text/xml"})
    result = diff_headers(a, b)
    codes = [w.code for w in result.warnings]
    assert "HD002" in codes


def test_no_warnings_for_clean_diff():
    a = _req("a", {"Accept": "application/json"})
    b = _req("b", {"Accept": "text/html"})
    result = diff_headers(a, b)
    assert result.warnings == []


def test_summary_identical():
    a = _req("a", {"Accept": "*/*"})
    b = _req("b", {"Accept": "*/*"})
    result = diff_headers(a, b)
    assert "identical" in result.summary().lower()


def test_summary_shows_counts():
    a = _req("a", {"Accept": "*/*", "X-Old": "1"})
    b = _req("b", {"Accept": "text/html", "X-New": "2"})
    result = diff_headers(a, b)
    summary = result.summary()
    assert "+1" in summary
    assert "-1" in summary
    assert "~1" in summary


def test_request_ids_stored():
    a = _req("req-001", {})
    b = _req("req-002", {})
    result = diff_headers(a, b)
    assert result.request_id_a == "req-001"
    assert result.request_id_b == "req-002"
