"""Tests for req_replay.auth."""
from __future__ import annotations

import pytest
from req_replay.models import CapturedRequest
from req_replay.auth import detect_auth, analyze_auth, _mask


def _req(headers: dict) -> CapturedRequest:
    return CapturedRequest(
        id="test-id",
        method="GET",
        url="https://example.com/api",
        headers=headers,
        body=None,
        timestamp="2024-01-01T00:00:00",
        tags=[],
    )


def test_mask_short_value():
    assert _mask("abc", keep=6) == "***"


def test_mask_long_value():
    result = _mask("Bearer abc123xyz", keep=6)
    assert result.startswith("Bearer")
    assert "*" in result


def test_detect_bearer_token():
    req = _req({"Authorization": "Bearer supersecrettoken"})
    summary = detect_auth(req)
    assert summary is not None
    assert summary.scheme == "Bearer"
    assert summary.header == "Authorization"
    assert summary.masked_value.startswith("supers")


def test_detect_basic_auth():
    req = _req({"Authorization": "Basic dXNlcjpwYXNz"})
    summary = detect_auth(req)
    assert summary is not None
    assert summary.scheme == "Basic"


def test_detect_api_key_x_api_key():
    req = _req({"X-Api-Key": "mykey12345"})
    summary = detect_auth(req)
    assert summary is not None
    assert summary.scheme == "ApiKey"
    assert summary.header == "X-Api-Key"


def test_detect_api_key_case_insensitive():
    req = _req({"x-auth-token": "tok"})
    summary = detect_auth(req)
    assert summary is not None
    assert summary.scheme == "ApiKey"


def test_detect_no_auth():
    req = _req({"Content-Type": "application/json"})
    assert detect_auth(req) is None


def test_display_contains_scheme():
    req = _req({"Authorization": "Bearer mytoken"})
    summary = detect_auth(req)
    assert summary is not None
    assert "Bearer" in summary.display()


def test_analyze_auth_counts_schemes():
    reqs = [
        _req({"Authorization": "Bearer tok1"}),
        _req({"Authorization": "Bearer tok2"}),
        _req({"X-Api-Key": "key1"}),
        _req({"Content-Type": "text/plain"}),
    ]
    counts = analyze_auth(reqs)
    assert counts["Bearer"] == 2
    assert counts["ApiKey"] == 1
    assert counts["None"] == 1


def test_analyze_auth_empty_list():
    assert analyze_auth([]) == {}
