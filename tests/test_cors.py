"""Tests for req_replay.cors."""
from __future__ import annotations
import pytest
from req_replay.cors import analyze_cors
from req_replay.models import CapturedRequest, CapturedResponse


def _req(method="GET", headers=None) -> CapturedRequest:
    return CapturedRequest(
        id="r1",
        method=method,
        url="https://api.example.com/data",
        headers=headers or {},
        body=None,
        timestamp="2024-01-01T00:00:00",
        tags=[],
        metadata={},
    )


def _resp(status=200, headers=None) -> CapturedResponse:
    return CapturedResponse(
        status_code=status,
        headers=headers or {},
        body=None,
    )


def test_non_cors_request_is_not_cors():
    info = analyze_cors(_req(), _resp())
    assert not info.is_cors_request


def test_origin_header_marks_cors():
    info = analyze_cors(_req(headers={"Origin": "https://app.example.com"}), _resp())
    assert info.is_cors_request
    assert info.origin == "https://app.example.com"


def test_missing_allow_origin_warns():
    req = _req(headers={"Origin": "https://app.example.com"})
    resp = _resp(headers={})
    info = analyze_cors(req, resp)
    assert not info.passed()
    assert any("Allow-Origin" in w for w in info.warnings)


def test_valid_cors_response_passes():
    req = _req(headers={"Origin": "https://app.example.com"})
    resp = _resp(headers={"Access-Control-Allow-Origin": "https://app.example.com"})
    info = analyze_cors(req, resp)
    assert info.passed()


def test_wildcard_with_credentials_warns():
    req = _req(headers={"Origin": "https://app.example.com"})
    resp = _resp(headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Credentials": "true",
    })
    info = analyze_cors(req, resp)
    assert not info.passed()
    assert any("Wildcard" in w for w in info.warnings)


def test_preflight_detected():
    req = _req(method="OPTIONS", headers={"Origin": "https://app.example.com"})
    resp = _resp(headers={
        "Access-Control-Allow-Origin": "https://app.example.com",
        "Access-Control-Allow-Methods": "GET, POST",
    })
    info = analyze_cors(req, resp)
    assert info.is_preflight
    assert info.passed()


def test_preflight_missing_methods_warns():
    req = _req(method="OPTIONS", headers={"Origin": "https://app.example.com"})
    resp = _resp(headers={"Access-Control-Allow-Origin": "https://app.example.com"})
    info = analyze_cors(req, resp)
    assert not info.passed()
    assert any("Allow-Methods" in w for w in info.warnings)


def test_allow_credentials_false_by_default():
    req = _req(headers={"Origin": "https://app.example.com"})
    resp = _resp(headers={"Access-Control-Allow-Origin": "https://app.example.com"})
    info = analyze_cors(req, resp)
    assert not info.allow_credentials


def test_display_contains_key_fields():
    req = _req(headers={"Origin": "https://app.example.com"})
    resp = _resp(headers={"Access-Control-Allow-Origin": "https://app.example.com"})
    info = analyze_cors(req, resp)
    out = info.display()
    assert "CORS Request" in out
    assert "Allow-Origin" in out
