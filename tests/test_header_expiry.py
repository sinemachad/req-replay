"""Tests for req_replay.header_expiry."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

import pytest

from req_replay.header_expiry import ExpiryWarning, analyze_expiry
from req_replay.models import CapturedRequest, CapturedResponse


def _req(headers: dict | None = None) -> CapturedRequest:
    return CapturedRequest(
        id="req-1",
        method="GET",
        url="https://example.com/api",
        headers=headers or {},
        body=None,
        timestamp="2024-01-01T00:00:00Z",
    )


def _resp(headers: dict) -> CapturedResponse:
    return CapturedResponse(status_code=200, headers=headers, body=None)


def _future_date(seconds: int = 3600) -> str:
    dt = datetime.now(tz=timezone.utc) + timedelta(seconds=seconds)
    return format_datetime(dt, usegmt=True)


def _past_date(seconds: int = 3600) -> str:
    dt = datetime.now(tz=timezone.utc) - timedelta(seconds=seconds)
    return format_datetime(dt, usegmt=True)


def test_no_expiry_headers_passes():
    result = analyze_expiry(_req(), _resp({"Content-Type": "application/json"}))
    assert result.passed()


def test_future_expires_passes():
    result = analyze_expiry(_req(), _resp({"Expires": _future_date()}))
    assert result.passed()


def test_past_expires_warns_he002():
    result = analyze_expiry(_req(), _resp({"Expires": _past_date()}))
    assert not result.passed()
    codes = [w.code for w in result.warnings]
    assert "HE002" in codes


def test_invalid_expires_warns_he001():
    result = analyze_expiry(_req(), _resp({"Expires": "not-a-date"}))
    assert not result.passed()
    codes = [w.code for w in result.warnings]
    assert "HE001" in codes


def test_invalid_date_header_warns_he003():
    result = analyze_expiry(_req(), _resp({"Date": "garbage"}))
    codes = [w.code for w in result.warnings]
    assert "HE003" in codes


def test_valid_date_header_passes():
    result = analyze_expiry(_req(), _resp({"Date": _future_date()}))
    assert result.passed()


def test_summary_ok_when_passed():
    result = analyze_expiry(_req(), _resp({}))
    assert "OK" in result.summary()


def test_summary_contains_code_when_failed():
    result = analyze_expiry(_req(), _resp({"Expires": _past_date()}))
    assert "HE002" in result.summary()


def test_display_contains_header_name():
    result = analyze_expiry(_req(), _resp({"Expires": _past_date()}))
    assert "Expires" in result.display()


def test_no_response_uses_request_headers():
    req = _req(headers={"Expires": _past_date()})
    result = analyze_expiry(req)
    assert not result.passed()
    assert any(w.code == "HE002" for w in result.warnings)


def test_expiry_warning_to_dict():
    w = ExpiryWarning(code="HE002", header="Expires", message="expired")
    d = w.to_dict()
    assert d["code"] == "HE002"
    assert d["header"] == "Expires"
    assert d["message"] == "expired"
