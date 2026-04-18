"""Tests for req_replay.payload."""
import pytest
from req_replay.payload import analyze_payload, analyze_request_payload, PayloadInfo
from req_replay.models import CapturedRequest
import base64
import datetime


def _req(body=None, content_type=None) -> CapturedRequest:
    headers = {}
    if content_type:
        headers["Content-Type"] = content_type
    return CapturedRequest(
        id="test-1",
        method="POST",
        url="http://example.com/",
        headers=headers,
        body=body,
        timestamp=datetime.datetime.utcnow(),
        tags=[],
    )


def test_empty_body_returns_empty_encoding():
    info = analyze_payload(None, {})
    assert info.encoding == "empty"
    assert info.size_bytes == 0
    assert info.preview == ""


def test_empty_string_body_returns_empty_encoding():
    info = analyze_payload("", {})
    assert info.encoding == "empty"


def test_json_body_detected():
    info = analyze_payload('{"key": "value"}', {"Content-Type": "application/json"})
    assert info.encoding == "json"
    assert info.is_binary is False


def test_invalid_json_body_is_unknown():
    info = analyze_payload("not-json", {"Content-Type": "application/json"})
    assert info.encoding == "unknown"


def test_form_body_detected():
    info = analyze_payload("a=1&b=2", {"content-type": "application/x-www-form-urlencoded"})
    assert info.encoding == "form"


def test_base64_body_detected():
    encoded = base64.b64encode(b"binary data here").decode()
    info = analyze_payload(encoded, {})
    assert info.encoding == "base64"
    assert info.is_binary is True


def test_text_body_detected():
    info = analyze_payload("hello world", {"Content-Type": "text/plain"})
    assert info.encoding == "text"
    assert info.is_binary is False


def test_size_bytes_calculated():
    body = "hello"
    info = analyze_payload(body, {})
    assert info.size_bytes == 5


def test_preview_truncated_at_120():
    body = "x" * 200
    info = analyze_payload(body, {"Content-Type": "text/plain"})
    assert len(info.preview) == 120


def test_analyze_request_payload_uses_request_body():
    req = _req(body='{"a": 1}', content_type="application/json")
    info = analyze_request_payload(req)
    assert info.encoding == "json"


def test_display_contains_encoding():
    info = PayloadInfo(encoding="json", size_bytes=42, is_binary=False, preview="{...}")
    out = info.display()
    assert "json" in out
    assert "42" in out
