"""Tests for req_replay.export module."""
import json
import pytest

from req_replay.models import CapturedRequest, CapturedResponse
from req_replay.export import to_curl, to_httpie, to_har_entry


@pytest.fixture()
def sample_request() -> CapturedRequest:
    return CapturedRequest(
        id="test-id",
        method="POST",
        url="https://api.example.com/items",
        headers={"Content-Type": "application/json", "Authorization": "Bearer tok"},
        params={"page": "1"},
        body=json.dumps({"name": "widget", "price": 9.99}),
        tags=["test"],
        timestamp="2024-01-01T00:00:00",
    )


@pytest.fixture()
def sample_response() -> CapturedResponse:
    return CapturedResponse(
        status_code=201,
        headers={"Content-Type": "application/json"},
        body=json.dumps({"id": 42}),
    )


def test_to_curl_contains_method(sample_request: CapturedRequest) -> None:
    result = to_curl(sample_request)
    assert "-X POST" in result


def test_to_curl_contains_url(sample_request: CapturedRequest) -> None:
    result = to_curl(sample_request)
    assert "https://api.example.com/items" in result


def test_to_curl_contains_headers(sample_request: CapturedRequest) -> None:
    result = to_curl(sample_request)
    assert "Authorization" in result
    assert "Bearer tok" in result


def test_to_curl_excludes_content_length(sample_request: CapturedRequest) -> None:
    sample_request.headers["Content-Length"] = "42"
    result = to_curl(sample_request)
    assert "Content-Length" not in result


def test_to_curl_includes_body(sample_request: CapturedRequest) -> None:
    result = to_curl(sample_request)
    assert "--data" in result
    assert "widget" in result


def test_to_httpie_starts_with_http(sample_request: CapturedRequest) -> None:
    result = to_httpie(sample_request)
    assert result.startswith("http POST")


def test_to_httpie_includes_url(sample_request: CapturedRequest) -> None:
    result = to_httpie(sample_request)
    assert "https://api.example.com/items" in result


def test_to_httpie_json_body_expanded(sample_request: CapturedRequest) -> None:
    result = to_httpie(sample_request)
    assert "name" in result
    assert "price" in result


def test_to_har_entry_request_fields(sample_request: CapturedRequest) -> None:
    entry = to_har_entry(sample_request)
    req = entry["request"]
    assert req["method"] == "POST"
    assert req["url"] == "https://api.example.com/items"
    assert any(h["name"] == "Authorization" for h in req["headers"])
    assert any(q["name"] == "page" for q in req["queryString"])


def test_to_har_entry_with_response(sample_request: CapturedRequest, sample_response: CapturedResponse) -> None:
    entry = to_har_entry(sample_request, sample_response)
    resp = entry["response"]
    assert resp["status"] == 201
    assert "42" in resp["content"]["text"]


def test_to_har_entry_no_response(sample_request: CapturedRequest) -> None:
    entry = to_har_entry(sample_request)
    assert entry["response"] == {}
