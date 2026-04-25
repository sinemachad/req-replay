"""Tests for req_replay.header_casing."""
from __future__ import annotations

import pytest

from req_replay.header_casing import (
    CasingResult,
    CasingWarning,
    _to_title_case,
    analyze_casing,
)
from req_replay.models import CapturedRequest


def _req(headers: dict) -> CapturedRequest:
    return CapturedRequest(
        id="test-id",
        method="GET",
        url="https://example.com/",
        headers=headers,
        body=None,
        metadata={},
        tags=[],
        timestamp="2024-01-01T00:00:00",
    )


# ---------------------------------------------------------------------------
# _to_title_case
# ---------------------------------------------------------------------------

def test_to_title_case_simple():
    assert _to_title_case("content-type") == "Content-Type"


def test_to_title_case_already_correct():
    assert _to_title_case("Content-Type") == "Content-Type"


def test_to_title_case_single_word():
    assert _to_title_case("authorization") == "Authorization"


# ---------------------------------------------------------------------------
# analyze_casing – title convention (default)
# ---------------------------------------------------------------------------

def test_clean_title_case_passes():
    req = _req({"Content-Type": "application/json", "Authorization": "Bearer x"})
    result = analyze_casing(req)
    assert result.passed


def test_lowercase_key_fails_title_convention():
    req = _req({"content-type": "application/json"})
    result = analyze_casing(req)
    assert not result.passed
    assert len(result.warnings) == 1
    w = result.warnings[0]
    assert w.code == "HC001"
    assert w.actual == "content-type"
    assert w.expected == "Content-Type"


def test_multiple_bad_keys_all_reported():
    req = _req({"content-type": "text/plain", "x-request-id": "abc"})
    result = analyze_casing(req)
    assert len(result.warnings) == 2


def test_empty_headers_passes():
    req = _req({})
    result = analyze_casing(req)
    assert result.passed


# ---------------------------------------------------------------------------
# analyze_casing – lower convention
# ---------------------------------------------------------------------------

def test_lowercase_convention_passes_lowercase():
    req = _req({"content-type": "application/json"})
    result = analyze_casing(req, convention="lower")
    assert result.passed


def test_lowercase_convention_fails_title_case():
    req = _req({"Content-Type": "application/json"})
    result = analyze_casing(req, convention="lower")
    assert not result.passed
    assert result.warnings[0].expected == "content-type"


# ---------------------------------------------------------------------------
# CasingResult helpers
# ---------------------------------------------------------------------------

def test_summary_ok():
    result = CasingResult(request_id="abc", warnings=[])
    assert result.summary() == "abc: OK"


def test_summary_fail_contains_code():
    w = CasingWarning(code="HC001", header="x", expected="X", actual="x")
    result = CasingResult(request_id="abc", warnings=[w])
    assert "FAIL" in result.summary()
    assert "HC001" in result.summary()


def test_warning_to_dict():
    w = CasingWarning(code="HC001", header="x-foo", expected="X-Foo", actual="x-foo")
    d = w.to_dict()
    assert d["code"] == "HC001"
    assert d["expected"] == "X-Foo"
    assert d["actual"] == "x-foo"
