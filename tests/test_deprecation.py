"""Tests for req_replay.deprecation."""
from __future__ import annotations

import pytest

from req_replay.models import CapturedRequest, CapturedResponse
from req_replay.deprecation import check_deprecations, DeprecationResult


def _req(headers: dict | None = None) -> CapturedRequest:
    return CapturedRequest(
        id="test-id",
        method="GET",
        url="https://example.com/api",
        headers=headers or {},
        body=None,
        timestamp="2024-01-01T00:00:00",
        tags=[],
        metadata={},
    )


def _resp(headers: dict | None = None, status: int = 200) -> CapturedResponse:
    return CapturedResponse(
        status_code=status,
        headers=headers or {},
        body=None,
    )


def test_clean_request_passes():
    result = check_deprecations(_req({"Content-Type": "application/json"}))
    assert result.passed
    assert result.warnings == []


def test_pragma_in_request_flagged():
    result = check_deprecations(_req({"Pragma": "no-cache"}))
    assert not result.passed
    assert any(w.header == "pragma" for w in result.warnings)


def test_deprecated_header_case_insensitive():
    result = check_deprecations(_req({"PRAGMA": "no-cache"}))
    assert not result.passed


def test_x_forwarded_host_flagged():
    result = check_deprecations(_req({"X-Forwarded-Host": "example.com"}))
    assert not result.passed
    assert result.warnings[0].source == "request"


def test_clean_response_passes():
    result = check_deprecations(_req(), _resp({"Content-Type": "application/json"}))
    assert result.passed


def test_x_xss_protection_in_response_flagged():
    result = check_deprecations(_req(), _resp({"X-XSS-Protection": "1; mode=block"}))
    assert not result.passed
    assert result.warnings[0].source == "response"
    assert result.warnings[0].header == "x-xss-protection"


def test_p3p_flagged():
    result = check_deprecations(_req(), _resp({"P3P": 'CP="NON DSP COR NID"'}))
    assert not result.passed


def test_multiple_deprecated_headers_all_reported():
    result = check_deprecations(
        _req({"Pragma": "no-cache"}),
        _resp({"X-XSS-Protection": "0", "P3P": "obsolete"}),
    )
    assert len(result.warnings) == 3


def test_summary_no_warnings():
    result = check_deprecations(_req())
    assert "No deprecated" in result.summary()


def test_summary_with_warnings():
    result = check_deprecations(_req({"Pragma": "no-cache"}))
    assert "Deprecated" in result.summary()
    assert "pragma" in result.summary()


def test_to_dict_structure():
    result = check_deprecations(_req({"Pragma": "no-cache"}))
    d = result.to_dict()
    assert "passed" in d
    assert "warnings" in d
    assert d["warnings"][0]["header"] == "pragma"


def test_no_response_does_not_raise():
    result = check_deprecations(_req())
    assert isinstance(result, DeprecationResult)
