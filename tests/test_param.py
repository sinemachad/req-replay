"""Tests for req_replay.param."""
import pytest
from req_replay.param import extract_query_params, extract_body_params, analyze_params
from req_replay.models import CapturedRequest
import json


def _req(
    url="https://example.com/api",
    method="GET",
    headers=None,
    body=None,
) -> CapturedRequest:
    return CapturedRequest(
        id="test-id",
        url=url,
        method=method,
        headers=headers or {},
        body=body,
        timestamp="2024-01-01T00:00:00",
        tags=[],
    )


def test_extract_query_params_empty():
    result = extract_query_params("https://example.com/path")
    assert result == {}


def test_extract_query_params_single():
    result = extract_query_params("https://example.com/path?foo=bar")
    assert result == {"foo": ["bar"]}


def test_extract_query_params_multiple():
    result = extract_query_params("https://example.com/?a=1&b=2&a=3")
    assert "a" in result
    assert result["a"] == ["1", "3"]
    assert result["b"] == ["2"]


def test_extract_body_params_no_body():
    req = _req()
    assert extract_body_params(req) == {}


def test_extract_body_params_json():
    body = json.dumps({"name": "alice", "age": 30})
    req = _req(
        method="POST",
        headers={"Content-Type": "application/json"},
        body=body,
    )
    result = extract_body_params(req)
    assert result["name"] == "alice"
    assert result["age"] == 30


def test_extract_body_params_form_encoded():
    req = _req(
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        body="username=bob&password=secret",
    )
    result = extract_body_params(req)
    assert result["username"] == "bob"
    assert result["password"] == "secret"


def test_extract_body_params_invalid_json_returns_empty():
    req = _req(
        method="POST",
        headers={"Content-Type": "application/json"},
        body="not-json",
    )
    assert extract_body_params(req) == {}


def test_analyze_params_combines_query_and_body():
    body = json.dumps({"key": "value"})
    req = _req(
        url="https://example.com/submit?page=1",
        method="POST",
        headers={"Content-Type": "application/json"},
        body=body,
    )
    summary = analyze_params(req)
    assert summary.query_params == {"page": ["1"]}
    assert summary.body_params == {"key": "value"}
    assert summary.request_id == "test-id"


def test_display_shows_no_params_message():
    req = _req()
    summary = analyze_params(req)
    output = summary.display()
    assert "no parameters" in output


def test_display_shows_query_params():
    req = _req(url="https://example.com/?search=hello")
    summary = analyze_params(req)
    output = summary.display()
    assert "search" in output
    assert "hello" in output
