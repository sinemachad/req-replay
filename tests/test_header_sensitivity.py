"""Tests for req_replay.header_sensitivity."""
from __future__ import annotations

import pytest
from click.testing import CliRunner

from req_replay.header_sensitivity import (
    SensitivityResult,
    SensitivityWarning,
    analyze_sensitivity,
)


def _req(headers: dict) -> dict:
    return headers


# ---------------------------------------------------------------------------
# Unit tests – analyze_sensitivity
# ---------------------------------------------------------------------------

def test_clean_request_passes():
    result = analyze_sensitivity("req-1", {"Content-Type": "application/json", "Accept": "*/*"})
    assert result.passed
    assert result.warnings == []


def test_authorization_header_flagged():
    result = analyze_sensitivity("req-2", {"Authorization": "Bearer abc123"})
    assert not result.passed
    assert any(w.header == "Authorization" for w in result.warnings)


def test_cookie_header_flagged():
    result = analyze_sensitivity("req-3", {"Cookie": "session=xyz"})
    assert not result.passed
    codes = [w.code for w in result.warnings]
    assert "HS001" in codes


def test_x_api_key_flagged():
    result = analyze_sensitivity("req-4", {"X-Api-Key": "secret-value"})
    assert not result.passed


def test_case_insensitive_matching():
    result = analyze_sensitivity("req-5", {"AUTHORIZATION": "Basic dXNlcjpwYXNz"})
    assert not result.passed


def test_extra_patterns_extend_detection():
    result = analyze_sensitivity(
        "req-6",
        {"X-Internal-Key": "super-secret"},
        extra_patterns=["internal-key"],
    )
    assert not result.passed
    assert result.warnings[0].header == "X-Internal-Key"


def test_no_false_positive_on_content_type():
    result = analyze_sensitivity("req-7", {"Content-Type": "text/plain"})
    assert result.passed


def test_multiple_sensitive_headers_all_flagged():
    headers = {
        "Authorization": "Bearer tok",
        "X-Api-Key": "key123",
        "Accept": "application/json",
    }
    result = analyze_sensitivity("req-8", headers)
    assert len(result.warnings) == 2


def test_summary_ok_when_clean():
    result = analyze_sensitivity("req-9", {})
    assert "OK" in result.summary()


def test_summary_warn_when_sensitive():
    result = analyze_sensitivity("req-10", {"Cookie": "a=b"})
    assert "WARN" in result.summary()


def test_display_lists_warnings():
    result = analyze_sensitivity("req-11", {"Authorization": "Bearer x"})
    display = result.display()
    assert "HS001" in display
    assert "Authorization" in display


def test_warning_to_dict():
    w = SensitivityWarning(code="HS001", header="Cookie", message="sensitive")
    d = w.to_dict()
    assert d == {"code": "HS001", "header": "Cookie", "message": "sensitive"}


def test_empty_headers_returns_clean():
    result = analyze_sensitivity("req-12", {})
    assert result.passed
    assert result.warnings == []
