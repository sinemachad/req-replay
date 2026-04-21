"""Tests for req_replay.header_validate."""
import pytest

from req_replay.models import CapturedRequest
from req_replay.header_validate import (
    validate_request_headers,
    HeaderValidationResult,
)


def _req(
    method: str = "GET",
    url: str = "https://example.com/api",
    headers: dict | None = None,
    body: str | None = None,
) -> CapturedRequest:
    return CapturedRequest(
        id="test-id",
        method=method,
        url=url,
        headers=headers if headers is not None else {"Host": "example.com"},
        body=body,
        metadata={},
        tags=[],
    )


def test_clean_get_request_passes():
    result = validate_request_headers(_req(method="GET"))
    assert result.passed()
    assert result.warnings == []


def test_clean_get_summary_ok():
    result = validate_request_headers(_req(method="GET"))
    assert "OK" in result.summary()


def test_hv001_missing_content_type_on_post_with_body():
    result = validate_request_headers(
        _req(method="POST", headers={"Host": "example.com"}, body='{"x": 1}')
    )
    codes = [w.code for w in result.warnings]
    assert "HV001" in codes


def test_hv001_not_raised_when_content_type_present():
    result = validate_request_headers(
        _req(
            method="POST",
            headers={"Host": "example.com", "Content-Type": "application/json"},
            body='{"x": 1}',
        )
    )
    codes = [w.code for w in result.warnings]
    assert "HV001" not in codes


def test_hv001_not_raised_for_post_without_body():
    result = validate_request_headers(
        _req(method="POST", headers={"Host": "example.com"}, body=None)
    )
    codes = [w.code for w in result.warnings]
    assert "HV001" not in codes


def test_hv002_content_length_flagged():
    result = validate_request_headers(
        _req(headers={"Host": "example.com", "Content-Length": "42"})
    )
    codes = [w.code for w in result.warnings]
    assert "HV002" in codes


def test_hv003_missing_host_flagged():
    result = validate_request_headers(_req(headers={}))
    codes = [w.code for w in result.warnings]
    assert "HV003" in codes


def test_hv003_host_present_not_flagged():
    result = validate_request_headers(_req(headers={"Host": "example.com"}))
    codes = [w.code for w in result.warnings]
    assert "HV003" not in codes


def test_hv004_empty_authorization_flagged():
    result = validate_request_headers(
        _req(headers={"Host": "example.com", "Authorization": "   "})
    )
    codes = [w.code for w in result.warnings]
    assert "HV004" in codes


def test_hv004_non_empty_authorization_not_flagged():
    result = validate_request_headers(
        _req(headers={"Host": "example.com", "Authorization": "Bearer token123"})
    )
    codes = [w.code for w in result.warnings]
    assert "HV004" not in codes


def test_display_contains_warning_details():
    result = validate_request_headers(_req(headers={}))
    display = result.display()
    assert "HV003" in display
    assert "host" in display.lower()


def test_summary_lists_codes_on_failure():
    result = validate_request_headers(
        _req(headers={"Content-Length": "5"})
    )
    summary = result.summary()
    assert "HV002" in summary
    assert "HV003" in summary
