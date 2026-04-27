"""Tests for req_replay.header_fold."""
from __future__ import annotations

import pytest

from req_replay.header_fold import (
    FoldResult,
    FoldWarning,
    _is_folded,
    _unfold,
    analyze_header_fold,
)
from req_replay.models import CapturedRequest


def _req(headers: dict) -> CapturedRequest:
    return CapturedRequest(
        id="test-id",
        method="GET",
        url="https://example.com/",
        headers=headers,
        body=None,
        timestamp="2024-01-01T00:00:00Z",
        tags=[],
        metadata={},
    )


# --- _is_folded ---

def test_is_folded_with_newline():
    assert _is_folded("value\n continuation") is True


def test_is_folded_with_crlf():
    assert _is_folded("value\r\n continuation") is True


def test_is_folded_plain_value():
    assert _is_folded("application/json") is False


# --- _unfold ---

def test_unfold_lf_sequence():
    assert _unfold("foo\n bar") == "foo bar"


def test_unfold_crlf_sequence():
    assert _unfold("foo\r\n bar") == "foo bar"


def test_unfold_tab_continuation():
    assert _unfold("foo\r\n\tbaz") == "foo baz"


def test_unfold_no_fold_unchanged():
    assert _unfold("simple value") == "simple value"


# --- analyze_header_fold ---

def test_clean_request_passes():
    req = _req({"Content-Type": "application/json", "Accept": "*/*"})
    result = analyze_header_fold(req)
    assert result.passed is True
    assert result.warnings == []


def test_clean_request_summary_ok():
    req = _req({"Content-Type": "application/json"})
    result = analyze_header_fold(req)
    assert "OK" in result.summary()


def test_folded_header_detected():
    req = _req({"X-Custom": "part1\r\n part2"})
    result = analyze_header_fold(req)
    assert not result.passed
    assert len(result.warnings) == 1
    assert result.warnings[0].code == "HF001"
    assert result.warnings[0].header == "x-custom"


def test_folded_header_unfolded_in_result():
    req = _req({"X-Custom": "part1\r\n part2"})
    result = analyze_header_fold(req)
    assert result.unfolded["X-Custom"] == "part1 part2"


def test_multiple_folded_headers_all_detected():
    req = _req({
        "X-One": "a\n b",
        "X-Two": "c\r\n d",
        "X-Three": "clean",
    })
    result = analyze_header_fold(req)
    assert len(result.warnings) == 2


def test_summary_contains_warn_when_failed():
    req = _req({"X-Bad": "fold\n ed"})
    result = analyze_header_fold(req)
    assert "WARN" in result.summary()
    assert "HF001" in result.summary()


def test_empty_headers_returns_clean():
    req = _req({})
    result = analyze_header_fold(req)
    assert result.passed is True
    assert result.unfolded == {}


def test_none_headers_returns_clean():
    req = _req(None)
    result = analyze_header_fold(req)
    assert result.passed is True
