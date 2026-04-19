"""Tests for req_replay.security."""
import pytest
from req_replay.models import CapturedRequest, CapturedResponse
from req_replay.security import analyze_security, SecurityResult


def _resp(headers: dict) -> CapturedResponse:
    return CapturedResponse(status_code=200, headers=headers, body=None)


def _req(url: str = "https://example.com/api") -> CapturedRequest:
    return CapturedRequest(
        method="GET",
        url=url,
        headers={},
        body=None,
        tags=[],
        metadata={},
    )


FULL_HEADERS = {
    "strict-transport-security": "max-age=31536000",
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "content-security-policy": "default-src 'self'",
    "referrer-policy": "no-referrer",
    "permissions-policy": "geolocation=()",
}


def test_all_headers_present_passes():
    result = analyze_security(_resp(FULL_HEADERS))
    assert result.passed()


def test_empty_headers_produces_six_warnings():
    result = analyze_security(_resp({}))
    assert not result.passed()
    assert len(result.warnings) == 6


def test_missing_hsts_flagged():
    headers = {k: v for k, v in FULL_HEADERS.items() if k != "strict-transport-security"}
    result = analyze_security(_resp(headers))
    codes = [w.code for w in result.warnings]
    assert "SEC001" in codes


def test_missing_csp_flagged():
    headers = {k: v for k, v in FULL_HEADERS.items() if k != "content-security-policy"}
    result = analyze_security(_resp(headers))
    codes = [w.code for w in result.warnings]
    assert "SEC004" in codes


def test_header_matching_is_case_insensitive():
    headers = {k.upper(): v for k, v in FULL_HEADERS.items()}
    result = analyze_security(_resp(headers))
    assert result.passed()


def test_hsts_over_http_flagged():
    headers = dict(FULL_HEADERS)
    result = analyze_security(_resp(headers), request=_req(url="http://example.com/api"))
    codes = [w.code for w in result.warnings]
    assert "SEC007" in codes


def test_hsts_over_https_not_flagged():
    headers = dict(FULL_HEADERS)
    result = analyze_security(_resp(headers), request=_req(url="https://example.com/api"))
    assert result.passed()


def test_summary_ok_when_passed():
    result = analyze_security(_resp(FULL_HEADERS))
    assert "OK" in result.summary()


def test_summary_lists_warnings():
    result = analyze_security(_resp({}))
    summary = result.summary()
    assert "SEC001" in summary
    assert "Security issues found" in summary


def test_to_dict_structure():
    result = analyze_security(_resp({}))
    d = result.warnings[0].to_dict()
    assert "code" in d and "message" in d and "header" in d
